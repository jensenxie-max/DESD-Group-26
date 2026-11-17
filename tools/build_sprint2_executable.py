"""Build execution configuration on the saved F1/F2 collaboration diagrams.

The source exports and their business graph, lanes, layout, and form mappings
remain intact. This command performs static checks; it does not deploy or run a
process. Deploy the generated BPMN and Forms together on Camunda 8.10, then run
the accompanying worker and engine integration checks.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "review-evidence" / "responsibilities-2026-11-17"
FORM_SOURCE = ROOT / "review-evidence" / "forms-2026-11-11" / "proposed"
OUTPUT = ROOT / "models" / "operational"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "modeler": "http://camunda.org/schema/modeler/1.0",
    "zeebe": "http://camunda.org/schema/zeebe/1.0",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

FORMS = (
    "F1-Product-Details.form",
    "F1-Correct-Product-Details.form",
    "F2-Stock-and-Sale-Dates.form",
)

# Conditions follow the existing diagram's branches. Missing/unknown worker
# decisions create an incident, rather than silently choosing a business path.
CONDITIONS = {
    "F1_Flow_13": "= informationValid = true",
    "Flow_1ql8ek8": "= informationValid = false",
    "F1_Flow_05": "= organicClaim = true",
    "F1_Flow_15": "= organicClaim = false",
    "F1_Flow_16": '= verificationStatus = "verified"',
    "Flow_0tt0k2k": '= verificationStatus = "invalid"',
    "F1_Flow_19": '= verificationStatus = "unavailable"',
    "F2_Flow_14": '= update.source = "producer"',
    "F2_Flow_15": '= update.source = "order"',
    "F2_Flow_16": '= update.source = "season-check"',
    "F2_Flow_17": "= producerInputValid = true",
    "F2_Flow_18": "= producerInputValid = false",
    "F2_Flow_19": "= orderChangeApplicable = true",
    "F2_Flow_20": "= orderChangeApplicable = false",
    "F2_Flow_24": "= saleEligible = true",
    "F2_Flow_25": "= saleEligible = false",
    "F2_Flow_28": "= commitConfirmed = true",
    "F2_Flow_29": "= commitConfirmed = false",
    "F2_Flow_ProducerResult": '= update.source = "producer"',
    "F2_Flow_IntegrationResult": '= update.source = "order" or update.source = "season-check"',
    "F2_Flow_ProducerFailure": '= update.source = "producer"',
    "F2_Flow_IntegrationFailure": '= update.source = "order" or update.source = "season-check"',
}

DETAILS = ["requestId", "productId", "producerId", "businessDate", "details", "verificationOutcome"]
F2_OUTCOME = [
    "requestId", "productId", "product", "status", "validationErrors", "errors",
    "followUpRequired", "commitConfirmed", "customerAvailability",
]

# Both the BPMN receive mappings and the worker payload allowlist use this
# contract. No sender copies its entire process scope to the other participant.
MESSAGE_CONTRACTS = {
    "F1_Message_ProductDetails": {
        "name": "Product details", "senders": ["F1_SendDetails"],
        "receivers": ["F1_ReceiveDetails"], "payloadFields": DETAILS,
    },
    "F1_Message_CorrectedDetails": {
        "name": "Corrected product details", "senders": ["F1_ResendDetails"],
        "receivers": ["F1_ReceiveCorrected"], "payloadFields": DETAILS,
    },
    "F1_Message_Correction": {
        "name": "Correction required", "senders": ["F1_Correction"],
        "receivers": ["F1_ProducerCorrection"],
        "payloadFields": ["requestId", "validationErrors", "verificationStatus", "status"],
    },
    "F1_Message_Publication": {
        "name": "Listing published", "senders": ["F1_Notify"],
        "receivers": ["F1_ProducerPublished"],
        "payloadFields": ["requestId", "productId", "product", "verificationStatus", "status", "verificationMode"],
    },
    "F1_Message_Pending": {
        "name": "Verification pending", "senders": ["F1_PendingNotify"],
        "receivers": ["F1_ProducerPending"],
        "payloadFields": ["requestId", "productId", "verificationStatus", "status", "pendingReason", "followUpRequired", "verificationMode"],
    },
    "F2_Message_UpdateRequest": {
        "name": "F2 update request", "senders": ["F2_RequestContext"],
        "receivers": ["F2_Start"],
        "payloadFields": ["requestId", "productId", "producerId", "businessDate", "update"],
    },
    "F2_Message_StockContext": {
        "name": "F2 loaded product context", "senders": ["F2_SendContext"],
        "receivers": ["F2_ReceiveContext"],
        "payloadFields": ["requestId", "productId", "product", "update"],
    },
    "F2_Message_StockSubmission": {
        "name": "F2 producer stock and sale dates", "senders": ["F2_SubmitStockChange"],
        "receivers": ["F2_ReceiveStockChange"],
        "payloadFields": ["requestId", "productId", "producerId", "businessDate", "update"],
    },
    "F2_Message_ProducerOutcome": {
        "name": "F2 producer update outcome",
        "senders": ["F2_Notify", "F2_RejectInput", "F2_SendFollowUp"],
        "receivers": ["F2_ReceiveOutcome"], "payloadFields": F2_OUTCOME,
    },
}

SOURCES = [
    "https://docs.camunda.io/docs/components/modeler/bpmn/exclusive-gateways/",
    "https://docs.camunda.io/docs/components/modeler/bpmn/message-events/",
    "https://docs.camunda.io/docs/components/modeler/bpmn/send-tasks/",
    "https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/",
]


def tag(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def signature(element: ET.Element | None):
    """Structural signature: ignore indentation, preserve content and order."""
    if element is None:
        return None
    return (element.tag, tuple(sorted(element.attrib.items())),
            (element.text or "").strip(), tuple(signature(child) for child in element))


def extensions(element: ET.Element) -> ET.Element:
    ext = element.find("bpmn:extensionElements", NS)
    if ext is None:
        ext = ET.Element(tag("bpmn", "extensionElements"))
        # BPMN base-element extensions follow optional documentation.
        index = sum(child.tag == tag("bpmn", "documentation") for child in element)
        element.insert(index, ext)
    return ext


def replace_child(parent: ET.Element, child: ET.Element) -> None:
    for existing in list(parent):
        if existing.tag == child.tag:
            parent.remove(existing)
    parent.append(child)


def configure_task(node: ET.Element, job_type: str, headers: dict[str, str]) -> None:
    ext = extensions(node)
    replace_child(ext, ET.Element(tag("zeebe", "taskDefinition"), {"type": job_type, "retries": "3"}))
    header_element = ET.Element(tag("zeebe", "taskHeaders"))
    for key, value in headers.items():
        ET.SubElement(header_element, tag("zeebe", "header"), {"key": key, "value": value})
    replace_child(ext, header_element)


def configure(root: ET.Element) -> None:
    by_id = {node.get("id"): node for node in root.iter() if node.get("id")}
    for process in root.findall("bpmn:process", NS):
        process.set("isExecutable", "true")
    for node in root.findall(".//bpmn:serviceTask", NS):
        configure_task(node, "desd.business", {"action": node.attrib["id"]})
    for flow_id, condition in CONDITIONS.items():
        if flow_id in by_id:
            condition_node = ET.Element(tag("bpmn", "conditionExpression"),
                                        {tag("xsi", "type"): "bpmn:tFormalExpression"})
            condition_node.text = condition
            replace_child(by_id[flow_id], condition_node)
    for message_id, contract in MESSAGE_CONTRACTS.items():
        if message_id not in by_id:
            continue
        message = by_id[message_id]
        assert message.get("name") == contract["name"], message_id
        is_start = any(local_name(by_id[node_id]) == "startEvent" for node_id in contract["receivers"])
        if not is_start:
            replace_child(extensions(message), ET.Element(tag("zeebe", "subscription"),
                                                         {"correlationKey": "= requestId"}))
        for sender_id in contract["senders"]:
            sender = by_id[sender_id]
            sender.set("messageRef", message_id)
            configure_task(sender, "desd.message", {
                "action": sender_id,
                "messageName": contract["name"],
            })
        for receiver_id in contract["receivers"]:
            receiver = by_id[receiver_id]
            mapping = ET.Element(tag("zeebe", "ioMapping"))
            for name in contract["payloadFields"]:
                ET.SubElement(mapping, tag("zeebe", "output"), {"source": f"= {name}", "target": name})
            replace_child(extensions(receiver), mapping)
    for form_definition in root.findall(".//zeebe:formDefinition", NS):
        form_definition.set("bindingType", "deployment")


def check(root: ET.Element, original: ET.Element, form_ids: set[str]) -> dict:
    errors = []
    ids = [node.get("id") for node in root.iter() if node.get("id")]
    repeated = [key for key, count in Counter(ids).items() if count > 1]
    if repeated:
        errors.append(f"duplicate IDs: {repeated}")
    by_id = {node.get("id"): node for node in root.iter() if node.get("id")}
    original_ids = {node.get("id") for node in original.iter() if node.get("id")}
    if set(ids) != original_ids:
        errors.append("element IDs changed")
    # Check business graph and pool/lane ownership, rather than just node counts.
    for xpath in (".//bpmn:sequenceFlow", ".//bpmn:lane", ".//bpmn:participant", ".//bpmn:messageFlow"):
        old_items = original.findall(xpath, NS)
        for old in old_items:
            new = by_id[old.attrib["id"]]
            if old.attrib != new.attrib:
                errors.append(f"graph/ownership attributes changed: {old.get('id')}")
            if local_name(old) == "lane" and signature(old) != signature(new):
                errors.append(f"lane membership changed: {old.get('id')}")
    if signature(root.find("bpmndi:BPMNDiagram", NS)) != signature(original.find("bpmndi:BPMNDiagram", NS)):
        errors.append("diagram layout changed")
    for message_id, contract in MESSAGE_CONTRACTS.items():
        if message_id not in by_id:
            continue
        if by_id[message_id].get("name") != contract["name"]:
            errors.append(f"message name differs from execution contract: {message_id}")
        for receiver_id in contract["receivers"]:
            node = by_id[receiver_id]
            event = node.find("bpmn:messageEventDefinition", NS)
            ref = event.get("messageRef") if event is not None else node.get("messageRef")
            if ref != message_id:
                errors.append(f"receiver listens to a different message: {receiver_id}")
    task_manifest = []
    for process in root.findall("bpmn:process", NS):
        if process.get("isExecutable") != "true":
            errors.append(f"not executable: {process.get('id')}")
        local_ids = {child.get("id") for child in process}
        for flow in process.findall("bpmn:sequenceFlow", NS):
            if flow.get("sourceRef") not in local_ids or flow.get("targetRef") not in local_ids:
                errors.append(f"sequence flow crosses a pool: {flow.get('id')}")
            expected = CONDITIONS.get(flow.get("id"))
            actual = flow.find("bpmn:conditionExpression", NS)
            if expected is not None and (actual is None or (actual.text or "").strip() != expected):
                errors.append(f"branch differs from execution contract: {flow.get('id')}")
            if expected is None and actual is not None:
                errors.append(f"condition added to an unconditional business flow: {flow.get('id')}")
        for gateway in process.findall("bpmn:exclusiveGateway", NS):
            outgoing = [f for f in process.findall("bpmn:sequenceFlow", NS) if f.get("sourceRef") == gateway.get("id")]
            if len(outgoing) > 1:
                for flow in outgoing:
                    expr = flow.find("bpmn:conditionExpression", NS)
                    if expr is None or not (expr.text or "").startswith("= "):
                        errors.append(f"missing FEEL branch: {flow.get('id')}")
        for node in process:
            if local_name(node) in {"serviceTask", "sendTask"}:
                definition = node.find("bpmn:extensionElements/zeebe:taskDefinition", NS)
                headers = {h.get("key"): h.get("value") for h in node.findall("bpmn:extensionElements/zeebe:taskHeaders/zeebe:header", NS)}
                expected = "desd.message" if local_name(node) == "sendTask" else "desd.business"
                if definition is None or definition.get("type") != expected or headers.get("action") != node.get("id"):
                    errors.append(f"missing worker config: {node.get('id')}")
                task_manifest.append({"id": node.get("id"), "processId": process.get("id"),
                                      "jobType": expected, "headers": headers})
            if local_name(node) in {"receiveTask", "intermediateCatchEvent", "startEvent"}:
                ref = node.get("messageRef")
                event = node.find("bpmn:messageEventDefinition", NS)
                ref = event.get("messageRef") if event is not None else ref
                if ref:
                    subscription = by_id[ref].find("bpmn:extensionElements/zeebe:subscription", NS)
                    if local_name(node) == "startEvent":
                        if subscription is not None:
                            errors.append(f"start event must not have subscription expression: {node.get('id')}")
                    elif subscription is None or subscription.get("correlationKey") != "= requestId":
                        errors.append(f"missing request correlation: {node.get('id')}")
                    contract = MESSAGE_CONTRACTS.get(ref)
                    if contract:
                        fields = node.findall("bpmn:extensionElements/zeebe:ioMapping/zeebe:output", NS)
                        expected_fields = [{"source": f"= {field}", "target": field} for field in contract["payloadFields"]]
                        if [field.attrib for field in fields] != expected_fields:
                            errors.append(f"receive payload mapping differs from contract: {node.get('id')}")
            if local_name(node) == "userTask":
                old = next(n for n in original.iter() if n.get("id") == node.get("id"))
                path = "bpmn:extensionElements/zeebe:ioMapping"
                if signature(node.find(path, NS)) != signature(old.find(path, NS)):
                    errors.append(f"form mapping changed: {node.get('id')}")
                form = node.find("bpmn:extensionElements/zeebe:formDefinition", NS)
                if form is None or form.get("formId") not in form_ids or form.get("bindingType") != "deployment":
                    errors.append(f"form missing from deployment: {node.get('id')}")
                if node.find("bpmn:extensionElements/zeebe:userTask", NS) is None:
                    errors.append(f"not a Camunda user task: {node.get('id')}")
    for node in root.findall(".//bpmn:sendTask", NS):
        ref = node.get("messageRef")
        if ref not in MESSAGE_CONTRACTS:
            errors.append(f"send task has no payload contract: {node.get('id')}")
        else:
            headers = {h.get("key"): h.get("value") for h in node.findall("bpmn:extensionElements/zeebe:taskHeaders/zeebe:header", NS)}
            if headers.get("messageName") != MESSAGE_CONTRACTS[ref]["name"]:
                errors.append(f"message header differs from receiver subscription: {node.get('id')}")
    if errors:
        raise ValueError("\n".join(errors))
    return {"processIds": [p.get("id") for p in root.findall("bpmn:process", NS)],
            "pools": len(root.findall(".//bpmn:participant", NS)),
            "lanes": len(root.findall(".//bpmn:lane", NS)),
            "conditionExpressions": len(root.findall(".//bpmn:conditionExpression", NS)),
            "tasks": task_manifest, "staticChecks": "passed"}


def build(check_only: bool = False) -> dict:
    forms = {json.loads((FORM_SOURCE / name).read_text(encoding="utf-8"))["id"] for name in FORMS}
    manifest = {
        "schemaVersion": 1,
        "targetCamundaVersion": "8.10",
        "correlationVariable": "requestId",
        "messageTimeToLiveMs": 3600000,
        "messageIdRule": "Use the activated send-task jobKey as messageId; retries of the same job reuse it.",
        "jobTypes": ["desd.business", "desd.message"],
        "messages": MESSAGE_CONTRACTS,
        "models": {},
        "forms": [f"forms/{name}" for name in FORMS],
        "officialReferences": SOURCES,
        "validationScope": "Static XML/configuration preservation checks only. Engine deployment and running instances must be verified separately.",
    }
    if not check_only:
        (OUTPUT / "forms").mkdir(parents=True, exist_ok=True)
        for name in FORMS:
            shutil.copyfile(FORM_SOURCE / name, OUTPUT / "forms" / name)
    for name in ("F1", "F2"):
        source_path = SOURCE / f"{name}-saved.bpmn"
        original = ET.parse(source_path).getroot()
        if check_only:
            root = ET.parse(OUTPUT / f"{name}-Operational.bpmn").getroot()
        else:
            root = deepcopy(original)
            configure(root)
            ET.indent(root, space="  ")
            ET.ElementTree(root).write(OUTPUT / f"{name}-Operational.bpmn", encoding="utf-8", xml_declaration=True)
            root = ET.parse(OUTPUT / f"{name}-Operational.bpmn").getroot()
        model = check(root, original, forms)
        model["resource"] = f"{name}-Operational.bpmn"
        model["source"] = source_path.relative_to(ROOT).as_posix()
        model["sourceSha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
        model["sha256"] = hashlib.sha256((OUTPUT / model["resource"]).read_bytes()).hexdigest()
        manifest["models"][name] = model
    for name in FORMS:
        if (OUTPUT / "forms" / name).read_bytes() != (FORM_SOURCE / name).read_bytes():
            raise ValueError(f"Original form content changed: {name}")
    if not check_only:
        (OUTPUT / "execution-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    else:
        saved_manifest = json.loads((OUTPUT / "execution-manifest.json").read_text(encoding="utf-8"))
        if manifest != saved_manifest:
            raise ValueError("execution-manifest.json does not match the generated models/contracts; rebuild it")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate the existing generated files without writing.")
    args = parser.parse_args()
    result = build(check_only=args.check)
    print(json.dumps({"staticChecks": "passed", "targetCamundaVersion": result["targetCamundaVersion"],
                      "models": {name: {k: v for k, v in value.items() if k != "tasks"}
                                 for name, value in result["models"].items()}}, indent=2))
