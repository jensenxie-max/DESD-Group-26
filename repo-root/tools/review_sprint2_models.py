"""Reproduce the 18 November Sprint 2 static model review.

Checks the saved models and exact references. Real engine scenarios are
recorded separately; graph reachability alone does not prove runtime success.
"""
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {
    "b": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "d": "http://www.omg.org/spec/BPMN/20100524/DI",
    "c": "http://www.omg.org/spec/DD/20100524/DC",
}
NODE_TYPES = {
    "startEvent", "endEvent", "task", "userTask", "serviceTask", "sendTask",
    "receiveTask", "exclusiveGateway", "eventBasedGateway", "intermediateCatchEvent",
}
SOURCES = [
    "models/strategic/Strategic-BPMN.bpmn",
    "models/operational/F1-Operational.bpmn",
    "models/operational/F2-Operational.bpmn",
    "review-evidence/responsibilities-2026-11-17/F1-saved.bpmn",
    "review-evidence/responsibilities-2026-11-17/F2-saved.bpmn",
]


def local(node):
    return node.tag.rsplit("}", 1)[-1]


def closure(seeds, graph):
    reached = set(seeds)
    queue = list(seeds)
    while queue:
        for node in graph.get(queue.pop(), []):
            if node not in reached:
                reached.add(node)
                queue.append(node)
    return reached


def path_between(source, target, graph):
    queue = deque([[source]])
    seen = {source}
    while queue:
        path = queue.popleft()
        if path[-1] == target:
            return path
        for following in graph.get(path[-1], []):
            if following not in seen:
                seen.add(following)
                queue.append(path + [following])
    return None


def digest(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def audit_bpmn(relative):
    root = ET.parse(ROOT / relative).getroot()
    ids = [node.get("id") for node in root.iter() if node.get("id")]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {relative}"
    by_id = {node.get("id"): node for node in root.iter() if node.get("id")}
    shapes = {node.get("bpmnElement"): node.find("c:Bounds", NS)
              for node in root.findall(".//d:BPMNShape", NS)}
    owner = {}
    processes = []
    all_graph = {}
    all_lanes = {}
    for process in root.findall("b:process", NS):
        process_id = process.get("id")
        nodes = {node.get("id"): node for node in process if local(node) in NODE_TYPES}
        flows = process.findall("b:sequenceFlow", NS)
        graph = {node_id: [] for node_id in nodes}
        reverse = {node_id: [] for node_id in nodes}
        for node_id in nodes:
            owner[node_id] = process_id
            assert node_id in shapes, f"Missing diagram shape: {node_id}"
        flow_ids = {flow.get("id") for flow in flows}
        for flow in flows:
            source, target = flow.get("sourceRef"), flow.get("targetRef")
            assert source in nodes and target in nodes, f"Cross-pool/invalid sequence: {flow.get('id')}"
            graph[source].append(target)
            reverse[target].append(source)
        for node_id, node in nodes.items():
            declared_in = [child.text for child in node.findall("b:incoming", NS)]
            declared_out = [child.text for child in node.findall("b:outgoing", NS)]
            actual_in = [flow.get("id") for flow in flows if flow.get("targetRef") == node_id]
            actual_out = [flow.get("id") for flow in flows if flow.get("sourceRef") == node_id]
            assert set(declared_in) == set(actual_in), f"Incoming declaration differs: {node_id}"
            assert set(declared_out) == set(actual_out), f"Outgoing declaration differs: {node_id}"
            assert set(declared_in + declared_out) <= flow_ids
            if local(node) == "eventBasedGateway":
                assert len(actual_out) >= 2
                assert all(local(nodes[target]) in {"intermediateCatchEvent", "receiveTask"}
                           for target in graph[node_id]), f"Invalid event gateway target: {node_id}"
        starts = [key for key, node in nodes.items() if local(node) == "startEvent"]
        ends = [key for key, node in nodes.items() if local(node) == "endEvent"]
        assert starts and ends
        assert closure(starts, graph) == set(nodes), f"Unreachable node: {process_id}"
        assert closure(ends, reverse) == set(nodes), f"No end route: {process_id}"
        lanes = process.findall(".//b:lane", NS)
        memberships = Counter()
        lane_report = []
        for lane in lanes:
            refs = [node.text for node in lane.findall("b:flowNodeRef", NS)]
            assert set(refs) <= set(nodes), f"Lane refers outside its process: {lane.get('id')}"
            memberships.update(refs)
            bounds = shapes[lane.get("id")]
            x, y, width, height = [float(bounds.get(key)) for key in ("x", "y", "width", "height")]
            for ref in refs:
                n = shapes[ref]
                nx, ny, nw, nh = [float(n.get(key)) for key in ("x", "y", "width", "height")]
                assert x <= nx and y <= ny and nx + nw <= x + width and ny + nh <= y + height, (
                    f"Diagram shape outside assigned lane: {ref}")
                all_lanes[ref] = lane.get("id")
            lane_report.append({"id": lane.get("id"), "name": lane.get("name"), "nodes": refs})
        if lanes:
            assert set(memberships) == set(nodes)
            assert all(count == 1 for count in memberships.values()), f"Duplicate lane membership: {process_id}"
        owner[process_id] = process_id
        all_graph.update(graph)
        processes.append({
            "id": process_id, "executable": process.get("isExecutable") == "true",
            "flowNodes": len(nodes), "sequenceFlows": len(flows),
            "starts": starts, "ends": ends, "lanes": lane_report,
            "allNodesReachableFromStart": True, "allNodesCanReachEnd": True,
            "sequenceFlowsStayInsideProcess": True,
            "incomingOutgoingDeclarationsAgree": True,
            "laneReferencesAndDiagramPlacementAgree": True,
        })
    participants = root.findall(".//b:participant", NS)
    for participant in participants:
        ref = participant.get("processRef")
        if ref:
            assert ref in owner, f"Invalid participant process: {ref}"
        owner[participant.get("id")] = ref or participant.get("id")
    messages = []
    for flow in root.findall(".//b:messageFlow", NS):
        source, target = flow.get("sourceRef"), flow.get("targetRef")
        assert source in owner and target in owner
        assert owner[source] != owner[target], f"Message flow inside same participant: {flow.get('id')}"
        assert local(by_id[source]) not in {"exclusiveGateway", "eventBasedGateway", "endEvent"}
        assert local(by_id[target]) not in {"exclusiveGateway", "eventBasedGateway"}
        if flow.get("messageRef"):
            assert local(by_id[flow.get("messageRef")]) == "message"
        messages.append({"id": flow.get("id"), "from": source, "to": target,
                         "sourceParticipant": owner[source], "targetParticipant": owner[target]})
    # The producer submits/corrects information; platform tasks remain in the platform.
    if "F1_Operational" in relative.replace("-", "_") or relative.endswith("F1-saved.bpmn"):
        assert owner["F1_Submit"] == owner["F1_Edit"] == "F1_ProducerProcess"
        assert owner["F1_Validate"] == owner["F1_Verify"] == "F1_Process"
        assert all_lanes["F1_Availability"] == "F1_Lane_Inventory"
        assert all_lanes["F1_Validate"] == all_lanes["F1_Verify"] == "F1_Lane_Catalogue"
    if "F2_Operational" in relative.replace("-", "_") or relative.endswith("F2-saved.bpmn"):
        assert owner["F2_EnterStockChange"] == "F2_ProducerProcess"
        for node_id in ("F2_Load", "F2_Producer", "F2_Order", "F2_Save", "F2_Sync", "F2_Failed"):
            assert owner[node_id] == "F2_Process"
            assert all_lanes[node_id] == "F2_Lane_Inventory"
    return {
        "path": relative, "sha256": digest(relative), "status": "PASS",
        "participants": len(participants), "laneCount": len(root.findall(".//b:lane", NS)),
        "conditionExpressions": len(root.findall(".//b:conditionExpression", NS)),
        "messageFlows": messages, "processes": processes,
    }, all_graph


def review():
    result = subprocess.run([sys.executable, "models/istar/validate_models.py"], cwd=ROOT,
                            check=True, capture_output=True, text=True)
    istar = json.loads(result.stdout)
    result = subprocess.run([sys.executable, "tools/build_sprint2_executable.py", "--check"],
                            cwd=ROOT, check=True, capture_output=True, text=True)
    executable = json.loads(result.stdout)
    models = []
    graphs = {}
    for source in SOURCES:
        model, graph = audit_bpmn(source)
        models.append(model)
        if source.startswith("models/operational"):
            graphs.update(graph)
    alternatives = {
        "F1_invalid_information_correction": ("F1_Validate", "F1_Correction"),
        "F1_correction_resubmitted": ("F1_ReceiveCorrected", "F1_Validate"),
        "F1_invalid_certification_correction": ("F1_Result", "F1_Correction"),
        "F1_unavailable_verification_pending": ("F1_Result", "F1_PendingEnd"),
        "F1_verified_or_no_claim_publication": ("F1_Ready", "F1_End"),
        "F2_invalid_input_correction": ("F2_InputValid", "F2_InputEnd"),
        "F2_order_rejected_or_duplicate": ("F2_OrderValid", "F2_OrderEnd"),
        "F2_not_eligible_unavailable": ("F2_CanSell", "F2_Unavailable"),
        "F2_eligible_available": ("F2_CanSell", "F2_Available"),
        "F2_commit_success_sync": ("F2_Saved", "F2_Sync"),
        "F2_commit_failure_followup": ("F2_Saved", "F2_FailedEnd"),
        "F2_producer_success_outcome": ("F2_ResultForProducer", "F2_Notify"),
        "F2_integration_success_record": ("F2_ResultForProducer", "F2_IntegrationResult"),
        "F2_producer_failure_outcome": ("F2_FailureForProducer", "F2_SendFollowUp"),
    }
    # Across-pool communication is checked separately. Do not invent a sequence edge.
    routes = []
    for name, (source, target) in alternatives.items():
        path = path_between(source, target, graphs)
        assert path, f"Missing alternative: {name}"
        routes.append({"id": name, "path": path, "status": "PASS",
                       "scope": "Static graph path; runtime result is recorded separately"})
    semantic = json.loads((ROOT / "models/istar/enterprise-model.json").read_text(encoding="utf-8"))
    trace = json.loads((ROOT / "docs/sprint-2/traceability.json").read_text(encoding="utf-8"))
    assert {row["id"] for row in trace["rows"]} >= {f"R{i}" for i in range(1, 11)}
    for register in (semantic["evidence"], trace["source_register"]):
        for source in register:
            if source.get("path"):
                assert not source["path"].startswith("work/")
                assert (ROOT / source["path"]).is_file(), source["path"]
    source_files = ["docs/Use-Case-1-Requirements.xlsm",
                    "review-evidence/requirements-2026-11-18/case-study-preview.txt",
                    "models/istar/enterprise-model.json", "models/istar/SD.svg", "models/istar/SR.svg",
                    "models/istar/SD-SR.drawio", "docs/sprint-2/traceability.json"]
    runtime = []
    for scenario in ("happy", "correction", "invalid-certificate", "invalid-input", "organic", "pending", "boundaries"):
        relative = f"review-evidence/runtime-2026-11-18/{scenario}-engine.json"
        record = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        assert record["engineExecuted"] is True and record["allAssertionsPassed"] is True
        assert all(check["passed"] is True for check in record["assertions"])
        runtime.append({"scenario": scenario, "path": relative, "sha256": digest(relative),
                        "assertions": len(record["assertions"]), "allAssertionsPassed": True,
                        "runId": record["runId"],
                        "formInteraction": record["formInteraction"],
                        "scope": "Read existing real-engine scenario evidence; this audit does not rerun the scenario"})
    return {
        "date": "2026-11-18", "status": "PASS_WITH_DOCUMENTED_PROTOTYPE_BOUNDARIES",
        "scope": "Static semantic, ownership, reference, diagram placement and route review of saved files; no fresh cloud retrieval or human/tutor approval is implied.",
        "reproduce": ["python models/istar/validate_models.py",
                      "python tools/build_sprint2_executable.py --check",
                      "python tools/review_sprint2_models.py"],
        "sources": [{"path": source, "sha256": digest(source)} for source in source_files],
        "istar": istar, "executableConfiguration": executable,
        "bpmn": models, "alternativeRoutes": routes, "linkedRuntimeEvidence": runtime,
        "traceability": {"rows": len(trace["rows"]), "R1_R10Present": True,
                         "referencesResolve": True, "sourceFilesIncluded": True},
        "visualInspection": {"date": "2026-11-18", "files": ["models/istar/SD.png", "models/istar/SR.png"],
                             "finding": "Actors, dependency labels, six marketplace capability areas and reading key are legible when zoomed. Use SVG or cropped zoom during presentation; the full SR is dense at fit-to-screen scale."},
        "findings": [
            {"id": "M01", "status": "verified", "finding": "Teacher ownership feedback is represented: producer input tasks in producer pools; catalogue and inventory tasks in platform lanes; exchanges across participants use message flows."},
            {"id": "M02", "status": "verified", "finding": "No dangling flow references, duplicate IDs, unreachable flow nodes, lane membership gaps or nodes drawn outside their assigned lane were found in the five reviewed BPMN files."},
            {"id": "M03", "status": "verified", "finding": "The executable build preserves IDs, business graph, pools, lane membership and layout of the 17 November saved cloud design exports."},
            {"id": "M04", "status": "documented_boundary", "finding": "Cloud responsibility exports and strategic BPMN remain non-executable design baselines. Deploy the separate models/operational resources and forms."},
            {"id": "M05", "status": "documented_boundary", "finding": "Certification is a named simulated provider fixture; producer/order identity is trusted demo input; season checks are triggered manually rather than by a deployed recurring timer."},
            {"id": "M06", "status": "decision_retained", "finding": "Integer stock units, inclusive sale dates, explicit businessDate, pending verification follow-up and version/atomic commit handling are existing prototype choices, not new requirements or recorded tutor decisions."},
            {"id": "M07", "status": "documented_boundary", "finding": "The workbook does not settle category-specific food-information applicability. Current forms collect the fields; no universal mandatory-allergen/harvest/best-before rule was invented."},
        ],
        "modelGraphChanges": [],
        "approval": {"groupReview": "Not asserted by this technical review",
                     "tutorScopeDecision": "No decision record available; do not infer from issue closure"},
    }


if __name__ == "__main__":
    report = review()
    output = ROOT / "docs/sprint-2/evidence/model-review-2026-11-18.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "bpmnFiles": len(report["bpmn"]),
                      "istar": report["istar"]["status"], "traceabilityRows": report["traceability"]["rows"],
                      "alternativeRoutes": len(report["alternativeRoutes"]),
                      "output": output.relative_to(ROOT).as_posix()}, indent=2))
