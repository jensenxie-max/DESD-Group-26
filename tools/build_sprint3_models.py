"""Build the isolated Sprint 3 week-one BPMN resources and readable diagrams.

Sprint 2 exports are inputs and are never rewritten. Runtime verification is a
separate operation; this command validates structure, contracts and layout.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import html
import json
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models/operational"
OUT = ROOT / "models/sprint3"
NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
      "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
      "dc": "http://www.omg.org/spec/DD/20100524/DC",
      "di": "http://www.omg.org/spec/DD/20100524/DI",
      "zeebe": "http://camunda.org/schema/zeebe/1.0",
      "modeler": "http://camunda.org/schema/modeler/1.0",
      "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

FLOW_NODE_TYPES = {"task", "userTask", "serviceTask", "sendTask", "receiveTask",
                   "exclusiveGateway", "eventBasedGateway", "startEvent",
                   "endEvent", "intermediateCatchEvent"}
TASK_TYPES = {"task", "userTask", "serviceTask", "sendTask", "receiveTask"}


def q(prefix, name):
    return "{" + NS[prefix] + "}" + name


def tag(node):
    return node.tag.rsplit("}", 1)[-1]


def find(root, node_id):
    return next(node for node in root.iter() if node.get("id") == node_id)


def child(parent, kind, **attrs):
    return ET.SubElement(parent, q("bpmn", kind), attrs)


def flow(process, flow_id, source, target, name=None, condition=None):
    attrs = {"id": flow_id, "sourceRef": source, "targetRef": target}
    if name:
        attrs["name"] = name
    item = child(process, "sequenceFlow", **attrs)
    if condition:
        ET.SubElement(item, q("bpmn", "conditionExpression"),
                      {q("xsi", "type"): "bpmn:tFormalExpression"}).text = condition
    return item


def service(process, node_id, name, send=False, message_ref=None):
    node = child(process, "sendTask" if send else "serviceTask", id=node_id, name=name)
    if message_ref:
        node.set("messageRef", message_ref)
    ext = ET.SubElement(node, q("bpmn", "extensionElements"))
    ET.SubElement(ext, q("zeebe", "taskDefinition"),
                  {"type": "desd.s3.message" if send else "desd.s3.business", "retries": "3"})
    headers = ET.SubElement(ext, q("zeebe", "taskHeaders"))
    ET.SubElement(headers, q("zeebe", "header"), {"key": "action", "value": node_id})
    return node


def lane_add(root, lane_id, *nodes):
    lane = find(root, lane_id)
    for node_id in nodes:
        child(lane, "flowNodeRef").text = node_id


def prepare(name):
    root = deepcopy(ET.parse(SOURCE / f"{name}-Operational.bpmn").getroot())
    root.set("id", root.get("id") + "_S3")
    root.set("exporter", "Group 26 model workspace")
    root.set("exporterVersion", "3.1")
    process_map = {}
    for process in root.findall("bpmn:process", NS):
        old = process.get("id")
        process_map[old] = old + "_S3"
        process.set("id", old + "_S3")
        process.set("name", process.get("name", name).replace(" - Initial draft", "") + " | Sprint 3")
        doc = process.find("bpmn:documentation", NS)
        if doc is not None:
            doc.text = ("Sprint 3 week-one executable revision. Producer and Marketplace remain separate participants. "
                        "Deployment, Forms, worker and message contracts are included in models/sprint3. "
                        "Runtime results must be checked separately from this structural model.")
    for participant in root.findall(".//bpmn:participant", NS):
        if participant.get("processRef") in process_map:
            participant.set("processRef", process_map[participant.get("processRef")])
    for message in root.findall("bpmn:message", NS):
        message.set("name", "S3 Verification follow-up closed" if message.get("id") == "F1_Message_Pending" else "S3 " + message.get("name"))
    for definition in root.findall(".//zeebe:taskDefinition", NS):
        definition.set("type", definition.get("type").replace("desd.", "desd.s3.", 1))
    for header in root.findall(".//zeebe:header", NS):
        if header.get("key") == "messageName":
            header.set("value", "S3 " + header.get("value"))
    return root


def extend_f1(root):
    process = find(root, "F1_Process_S3")
    child(process, "exclusiveGateway", id="F1_VerifyJoin", gatewayDirection="Converging")
    find(root, "F1_Flow_05").set("targetRef", "F1_VerifyJoin")
    flow(process, "F1_S3_VerifyJoined", "F1_VerifyJoin", "F1_Verify")
    find(root, "F1_Flow_11").set("targetRef", "F1_ReviewPending")
    review = child(process, "userTask", id="F1_ReviewPending", name="Review verification follow-up")
    child(review, "documentation").text = (
        "Catalogue support chooses retry or cancel and records a note. Verification outcomes are named "
        "simulation inputs for this prototype. Retry always re-enters the verification task; review cannot "
        "publish a product or bypass validation.")
    ext = ET.SubElement(review, q("bpmn", "extensionElements"))
    ET.SubElement(ext, q("zeebe", "formDefinition"),
                  {"formId": "f1-verification-follow-up-s3", "bindingType": "deployment"})
    ET.SubElement(ext, q("zeebe", "userTask"))
    mapping = ET.SubElement(ext, q("zeebe", "ioMapping"))
    for field in ("followUpDecision", "verificationOutcome", "followUpNotes"):
        ET.SubElement(mapping, q("zeebe", "output"), {"source": "= " + field, "target": field})
    child(process, "exclusiveGateway", id="F1_FollowUpDecision", name="Retry verification?")
    service(process, "F1_ClosePending", "Close verification follow-up")
    flow(process, "F1_S3_ReviewDecision", "F1_ReviewPending", "F1_FollowUpDecision")
    flow(process, "F1_S3_RetryVerification", "F1_FollowUpDecision", "F1_VerifyJoin", "Retry",
         '= followUpDecision = "retry"')
    flow(process, "F1_S3_CancelVerification", "F1_FollowUpDecision", "F1_ClosePending", "Cancel",
         '= followUpDecision = "cancel"')
    flow(process, "F1_S3_CloseNotify", "F1_ClosePending", "F1_PendingNotify")
    find(root, "F1_PendingEnd").set("name", "Verification follow-up closed")
    find(root, "F1_PendingNotify").set("name", "Notify producer of closed request")
    find(root, "F1_ProducerPending").set("name", "Closed-request outcome received")
    find(root, "F1_ProducerPendingEnd").set("name", "Follow-up outcome received")
    find(root, "F1_Msg_Pending").set("name", "Closed follow-up outcome")
    lane_add(root, "F1_Lane_Catalogue", "F1_ReviewPending", "F1_FollowUpDecision", "F1_ClosePending", "F1_VerifyJoin")
    producer = find(root, "F1_ProducerProcess_S3")
    lane_set = child(producer, "laneSet", id="F1_ProducerLanes_S3")
    producer.remove(lane_set)
    producer.insert(1 if len(producer) and tag(producer[0]) == "documentation" else 0, lane_set)
    lane = child(lane_set, "lane", id="F1_Lane_Producer_S3", name="Producer")
    for node in producer:
        if tag(node) in FLOW_NODE_TYPES:
            child(lane, "flowNodeRef").text = node.get("id")


def extend_f2(root):
    process = find(root, "F2_Process_S3")
    producer = find(root, "F2_ProducerProcess_S3")
    find(root, "F2_Flow_02").set("targetRef", "F2_ContextAvailable")
    find(root, "F2_Flow_16").set("name", "Seasonal recheck")
    find(root, "F2_Sync").find("bpmn:documentation", NS).text = (
        "Update the local customer-availability projection from committed product state and version. "
        "This is a local read projection, not an external customer application. "
        "Ordering must still check the authoritative current product state.")
    child(process, "exclusiveGateway", id="F2_ContextAvailable", name="Product context available?")
    service(process, "F2_RejectContext", "Return rejected context request", True, "F2_Message_StockContext")
    child(process, "endEvent", id="F2_ContextRejectedEnd", name="Context request rejected")
    flow(process, "F2_S3_ContextAccepted", "F2_ContextAvailable", "F2_Source", "Yes",
         "= contextAvailable = true")
    flow(process, "F2_S3_ContextRejected", "F2_ContextAvailable", "F2_RejectContext", "No",
         "= contextAvailable = false")
    flow(process, "F2_S3_ContextRejectedEnd", "F2_RejectContext", "F2_ContextRejectedEnd")
    find(root, "F2_ProducerFlow_03").set("sourceRef", "F2_ProducerContextAvailable")
    item = find(root, "F2_ProducerFlow_03")
    item.set("name", "Yes")
    ET.SubElement(item, q("bpmn", "conditionExpression"),
                  {q("xsi", "type"): "bpmn:tFormalExpression"}).text = "= contextAvailable = true"
    child(producer, "exclusiveGateway", id="F2_ProducerContextAvailable", name="Context accepted?")
    child(producer, "endEvent", id="F2_ProducerRejectedEnd", name="Request rejected; no stock change")
    flow(producer, "F2_S3_ProducerContextDecision", "F2_ReceiveContext", "F2_ProducerContextAvailable")
    flow(producer, "F2_S3_ProducerContextRejected", "F2_ProducerContextAvailable", "F2_ProducerRejectedEnd", "No",
         "= contextAvailable = false")
    lane_add(root, "F2_Lane_Inventory", "F2_ContextAvailable", "F2_RejectContext", "F2_ContextRejectedEnd")
    lane_add(root, "F2_Lane_Producer", "F2_ProducerContextAvailable", "F2_ProducerRejectedEnd")
    collab = root.find("bpmn:collaboration", NS)
    child(collab, "messageFlow", id="F2_Msg_ContextRejected", name="Rejected context; no product data",
          sourceRef="F2_RejectContext", targetRef="F2_ReceiveContext", messageRef="F2_Message_StockContext")


def follow_up_form():
    def layout(row):
        return {"row": "row_" + str(row), "columns": None}
    return {"components": [
        {"type": "text", "id": "S3_FollowupTitle", "text": "## Verification follow-up", "layout": layout(0)},
        {"type": "text", "id": "S3_FollowupHelp", "text": "Choose a retry or close this request. A retry runs the verification task again before publication. Provider outcomes below are explicit demonstration fixtures.", "layout": layout(1)},
        {"type": "textfield", "id": "S3_FollowupProduct", "key": "productId", "label": "Product request", "readonly": True, "layout": layout(2)},
        {"type": "select", "id": "S3_FollowupDecision", "key": "followUpDecision", "label": "Follow-up action", "values": [{"label": "Retry verification", "value": "retry"}, {"label": "Close without publication", "value": "cancel"}], "validate": {"required": True}, "layout": layout(3)},
        {"type": "select", "id": "S3_FollowupOutcome", "key": "verificationOutcome", "label": "Simulated provider outcome", "values": [{"label": "Verified", "value": "verified"}, {"label": "Invalid certificate", "value": "invalid"}, {"label": "Service unavailable", "value": "unavailable"}], "validate": {"required": True}, "conditional": {"hide": '= followUpDecision != "retry"'}, "layout": layout(4)},
        {"type": "textarea", "id": "S3_FollowupNotes", "key": "followUpNotes", "label": "Review notes", "validate": {"required": True}, "layout": layout(5)},
        {"type": "button", "id": "S3_FollowupSubmit", "label": "Submit follow-up", "action": "submit", "layout": layout(6)}
    ], "type": "default", "id": "f1-verification-follow-up-s3", "executionPlatform": "Camunda Cloud", "executionPlatformVersion": "8.10.0", "exporter": {"name": "Group 26 forms", "version": "3.1"}, "schemaVersion": 19}


F1_POS = {
    "F1_Start": (180,170), "F1_Submit": (420,170), "F1_SendDetails": (660,170),
    "F1_ProducerAwaitMerge": (880,170), "F1_WaitOutcome": (1080,170),
    "F1_ProducerCorrection": (1320,320), "F1_Edit": (1550,320), "F1_ResendDetails": (1790,320),
    "F1_ProducerPublished": (2320,170), "F1_ProducerPublishedEnd": (2580,170),
    "F1_ProducerPending": (2320,320), "F1_ProducerPendingEnd": (2580,320),
    "F1_ReceiveDetails": (180,750), "F1_Entry": (400,750), "F1_Validate": (630,750),
    "F1_Valid": (860,750), "F1_Claim": (1080,750), "F1_VerifyJoin": (1190,750), "F1_Verify": (1320,750),
    "F1_Result": (1540,750), "F1_Ready": (1780,750), "F1_Publish": (2010,750),
    "F1_Availability": (2010,1370), "F1_Notify": (2320,750), "F1_End": (2580,750),
    "Gateway_1tq8q8b": (860,960), "F1_Correction": (1080,960), "F1_ReceiveCorrected": (1320,960),
    "F1_Pending": (1540,1150), "F1_ReviewPending": (1790,1150),
    "F1_FollowUpDecision": (2020,1150), "F1_ClosePending": (2260,1150),
    "F1_PendingNotify": (2500,1150), "F1_PendingEnd": (2740,1150),
}
F2_POS = {
    "F2_ProducerStart": (180,170), "F2_RequestContext": (420,170), "F2_ReceiveContext": (660,170),
    "F2_ProducerContextAvailable": (870,170), "F2_ProducerRejectedEnd": (1110,320),
    "F2_EnterStockChange": (1110,170), "F2_SubmitStockChange": (1350,170),
    "F2_ReceiveOutcome": (3820,170), "F2_ProducerEnd": (4100,170),
    "F2_Start": (180,1000), "F2_Load": (420,1000), "F2_ContextAvailable": (660,1000),
    "F2_RejectContext": (660,620), "F2_ContextRejectedEnd": (900,620), "F2_Source": (900,1000),
    "F2_SendContext": (1120,800), "F2_ReceiveStockChange": (1350,800),
    "F2_Producer": (1570,800), "F2_InputValid": (1790,800), "F2_Prepare": (2010,800),
    "F2_RejectInput": (2010,620), "F2_InputEnd": (2250,620),
    "F2_Order": (1120,1000), "F2_OrderValid": (1350,1000), "F2_Deduct": (1570,1000),
    "F2_RejectOrder": (1570,1160), "F2_OrderEnd": (1810,1160), "F2_Season": (1120,1290),
    "F2_Merge": (2250,1000), "F2_Assess": (2470,1000), "F2_CanSell": (2690,1000),
    "F2_Available": (2890,900), "F2_Unavailable": (2890,1100), "F2_StateMerge": (3100,1000),
    "F2_Save": (3300,1000), "F2_Saved": (3510,1000), "F2_Sync": (3730,1000),
    "F2_ResultForProducer": (3960,1000), "F2_Notify": (4180,800),
    "F2_IntegrationResult": (4180,1000), "F2_ResultMerge": (4430,1000), "F2_End": (4650,1000),
    "F2_Failed": (3510,1430), "F2_FailureForProducer": (3960,1430),
    "F2_SendFollowUp": (4180,1300), "F2_FailureMerge": (4430,1430), "F2_FailedEnd": (4650,1430),
}


def node_bounds(node, center):
    typ = tag(node)
    width, height = (170, 90) if typ in TASK_TYPES else (50, 50) if "Gateway" in typ else (36, 36)
    return (center[0] - width / 2, center[1] - height / 2, width, height)


def ports(bounds):
    x,y,w,h = bounds
    return {"L": (x,y+h/2), "R": (x+w,y+h/2), "T": (x+w/2,y), "B": (x+w/2,y+h)}


def clean(points):
    result = []
    for point in points:
        point = tuple(round(float(v), 2) for v in point)
        if not result or result[-1] != point:
            result.append(point)
    i = 1
    while i < len(result)-1:
        if ((result[i-1][0] == result[i][0] == result[i+1][0]) or
                (result[i-1][1] == result[i][1] == result[i+1][1])):
            result.pop(i)
        else:
            i += 1
    return result


def collisions(points, obstacles, excluded):
    count = 0
    for a,b in zip(points, points[1:]):
        for node_id, (x,y,w,h) in obstacles.items():
            if node_id in excluded:
                continue
            if a[0] == b[0] and x-5 < a[0] < x+w+5 and max(min(a[1],b[1]),y-5) < min(max(a[1],b[1]),y+h+5):
                count += 1
            if a[1] == b[1] and y-5 < a[1] < y+h+5 and max(min(a[0],b[0]),x-5) < min(max(a[0],b[0]),x+w+5):
                count += 1
    return count


def route(bounds, source, target, explicit=None):
    if explicit:
        return clean(explicit)
    s,t = ports(bounds[source]),ports(bounds[target])
    excluded = {source, target}
    candidates = []
    for sk in ("R","B","T","L"):
        for tk in ("L","T","B","R"):
            a,b = s[sk],t[tk]
            if a[0] == b[0] or a[1] == b[1]:
                candidates.append([a,b])
            for x in ((a[0]+b[0])/2, a[0]+40, b[0]-40, min(a[0],b[0])-65, max(a[0],b[0])+65):
                candidates.append([a,(x,a[1]),(x,b[1]),b])
            for y in ((a[1]+b[1])/2, a[1]+65, b[1]-65, min(a[1],b[1])-65, max(a[1],b[1])+65):
                candidates.append([a,(a[0],y),(b[0],y),b])
    def score(points):
        points = clean(points)
        hits = collisions(points,bounds,excluded)
        length = sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(points,points[1:]))
        # Enter/leave through the exterior of each shape, not its interior.
        endpoint_penalty = 0
        for node_id,pair in ((source,points[:2]),(target,list(reversed(points[-2:])))):
            if collisions(pair,bounds,set(bounds)-{node_id}):
                endpoint_penalty += 100000
        return hits*100000 + endpoint_penalty + length + len(points)*20
    return clean(min(candidates,key=score))


def diagram(root, name):
    old = root.find("bpmndi:BPMNDiagram",NS)
    if old is not None:
        root.remove(old)
    positions = F1_POS if name == "F1" else F2_POS
    all_nodes = {n.get("id"): n for p in root.findall("bpmn:process",NS) for n in p if tag(n) in FLOW_NODE_TYPES}
    assert set(positions) == set(all_nodes), (name,set(all_nodes)-set(positions),set(positions)-set(all_nodes))
    bounds = {node_id:node_bounds(node,positions[node_id]) for node_id,node in all_nodes.items()}
    width = 2920 if name == "F1" else 4820
    participant_bounds = ({"F1_ProducerPool":(40,40,width,380), "F1_Pool":(40,580,width,880),
                           "F1_VerifierPool":(1240,460,700,80)} if name == "F1" else
                          {"F2_ProducerPool":(40,40,width,380),"F2_Pool":(40,480,width,1120)})
    lane_bounds = ({"F1_Lane_Producer_S3":(70,40,width-30,380),
                    "F1_Lane_Catalogue":(70,580,width-30,700),
                    "F1_Lane_Inventory":(70,1280,width-30,180)} if name == "F1" else
                   {"F2_Lane_Producer":(70,40,width-30,380),"F2_Lane_Inventory":(70,480,width-30,1120)})
    bounds.update(participant_bounds)
    bounds.update(lane_bounds)
    dia = ET.SubElement(root,q("bpmndi","BPMNDiagram"),{"id":name+"_Diagram_S3"})
    plane = ET.SubElement(dia,q("bpmndi","BPMNPlane"),{"id":name+"_Plane_S3","bpmnElement":root.find("bpmn:collaboration",NS).get("id")})
    by_id = {node.get("id"):node for node in root.iter() if node.get("id")}
    for node_id,box in bounds.items():
        shape = ET.SubElement(plane,q("bpmndi","BPMNShape"),{"id":node_id+"_di","bpmnElement":node_id})
        if node_id in participant_bounds or node_id in lane_bounds:
            shape.set("isHorizontal","true")
        ET.SubElement(shape,q("dc","Bounds"),dict(zip(("x","y","width","height"),map(str,box))))
        if node_id in all_nodes and tag(all_nodes[node_id]) not in TASK_TYPES and all_nodes[node_id].get("name"):
            x,y,w,h=box
            label=ET.SubElement(shape,q("bpmndi","BPMNLabel"))
            ET.SubElement(label,q("dc","Bounds"),{"x":str(x+w/2-95),"y":str(y+h+8),"width":"190","height":"42"})
    override = {}
    if name == "F1":
        override = {
            "F1_S3_RetryVerification": [(2020,1125),(2020,1050),(1210,1050),(1210,820),(1190,820),(1190,775)],
            "F1_PlatformFlow_Corrected": [(1320,1005),(1320,1025),(300,1025),(300,650),(400,650),(400,725)],
            "F1_ProducerFlow_Resubmitted": [(1790,365),(1790,390),(880,390),(880,195)],
            "F1_Msg_Submit": [(660,215),(660,450),(180,450),(180,732)],
            "F1_Msg_Resubmit": [(1875,320),(2130,320),(2130,1020),(1320,1020),(1320,1005)],
            "F1_Msg_Correction": [(1080,915),(1080,900),(1140,900),(1140,440),(1320,440),(1320,338)],
            "F1_Msg_Publication": [(2320,705),(2320,560),(2190,560),(2190,100),(2320,100),(2320,152)],
            "F1_Msg_Pending": [(2500,1195),(2500,1240),(2860,1240),(2860,440),(2320,440),(2320,338)],
            "F1_Msg_CertRequest": [(1320,705),(1320,540)],
            "F1_Msg_CertResult": [(1860,540),(1860,650),(1405,650),(1405,750)],
            "F1_Flow_08": [(2095,750),(2135,750),(2135,1300),(2010,1300),(2010,1325)],
            "F1_Flow_09": [(2095,1370),(2380,1370),(2380,795),(2320,795)],
            "F1_Flow_15": [(1080,725),(1080,680),(1780,680),(1780,725)],
        }
    else:
        override = {
            "F2_Msg_Request": [(420,215),(420,450),(120,450),(120,1000),(162,1000)],
            "F2_Msg_Context": [(1120,755),(980,755),(980,450),(660,450),(660,188)],
            "F2_Msg_ContextRejected": [(575,620),(530,620),(530,430),(660,430),(660,188)],
            "F2_Msg_Submit": [(1350,215),(1350,782)],
            "F2_Msg_Result": [(4180,755),(4180,460),(3820,460),(3820,215)],
            "F2_Msg_Correction": [(2010,575),(2010,440),(3820,440),(3820,215)],
            "F2_Msg_FollowUp": [(4265,1300),(4750,1300),(4750,430),(3820,430),(3820,215)],
            "F2_Flow_14": [(900,975),(900,800),(1035,800)],
            "F2_Flow_16": [(900,1025),(900,1290),(1035,1290)],
            "F2_Flow_21": [(2095,800),(2250,800),(2250,975)],
            "F2_Flow_23": [(1205,1290),(2250,1290),(2250,1025)],
            "F2_Flow_12": [(4265,800),(4430,800),(4430,975)],
            "F2_Flow_ProducerFailureEnd": [(4265,1300),(4430,1300),(4430,1405)],
        }
    node_boxes = {node_id:bounds[node_id] for node_id in all_nodes}
    routing_boxes = dict(node_boxes)
    routing_boxes.update({k:v for k,v in participant_bounds.items() if k.endswith("VerifierPool")})
    for edge in root.findall(".//bpmn:sequenceFlow",NS)+root.findall(".//bpmn:messageFlow",NS):
        source,target=edge.get("sourceRef"),edge.get("targetRef")
        points=route(routing_boxes,source,target,override.get(edge.get("id")))
        rendered=ET.SubElement(plane,q("bpmndi","BPMNEdge"),{"id":edge.get("id")+"_di","bpmnElement":edge.get("id")})
        for x,y in points:
            ET.SubElement(rendered,q("di","waypoint"),{"x":str(x),"y":str(y)})
        if edge.get("name"):
            # Use the longest segment so labels do not crowd the source gateway.
            a,b=max(zip(points,points[1:]),key=lambda ab:abs(ab[0][0]-ab[1][0])+abs(ab[0][1]-ab[1][1]))
            label=ET.SubElement(rendered,q("bpmndi","BPMNLabel"))
            ET.SubElement(label,q("dc","Bounds"),{"x":str((a[0]+b[0])/2-85),"y":str((a[1]+b[1])/2-28),"width":"170","height":"26"})
    return width+80, 1510 if name=="F1" else 1650


def rebuild_declarations(root):
    for process in root.findall("bpmn:process",NS):
        flows=process.findall("bpmn:sequenceFlow",NS)
        for node in process:
            if tag(node) not in FLOW_NODE_TYPES:
                continue
            for item in list(node):
                if tag(item) in {"incoming","outgoing"}:
                    node.remove(item)
            insert_at = 0
            for index, item in enumerate(node):
                if tag(item) in {"documentation", "extensionElements"}:
                    insert_at = index + 1
            for edge in flows:
                if edge.get("targetRef")==node.get("id"):
                    item=ET.Element(q("bpmn","incoming"))
                    item.text=edge.get("id")
                    node.insert(insert_at,item)
                    insert_at += 1
            for edge in flows:
                if edge.get("sourceRef")==node.get("id"):
                    item=ET.Element(q("bpmn","outgoing"))
                    item.text=edge.get("id")
                    node.insert(insert_at,item)
                    insert_at += 1


def apply_contracts(root, contracts):
    for message_id,contract in contracts.items():
        present={n.get("id"):n for n in root.iter() if n.get("id")}
        if message_id not in present:
            continue
        for sender_id in contract["senders"]:
            node=present[sender_id]
            headers=node.find("bpmn:extensionElements/zeebe:taskHeaders",NS)
            header=next((n for n in headers if n.get("key")=="messageName"),None)
            if header is None:
                header=ET.SubElement(headers,q("zeebe","header"),{"key":"messageName"})
            header.set("value",contract["name"])
        for receiver_id in contract["receivers"]:
            node=present[receiver_id]
            ext=node.find("bpmn:extensionElements",NS)
            if ext is None:
                ext=ET.SubElement(node,q("bpmn","extensionElements"))
            mapping=ext.find("zeebe:ioMapping",NS)
            if mapping is None:
                mapping=ET.SubElement(ext,q("zeebe","ioMapping"))
            for output in list(mapping.findall("zeebe:output",NS)):
                mapping.remove(output)
            for field in contract["payloadFields"]:
                ET.SubElement(mapping,q("zeebe","output"),{"source":"= "+field,"target":field})


def svg(root, name, canvas):
    """A vector reading view of the same DI shapes and routes; XML stays editable."""
    plane=root.find(".//bpmndi:BPMNPlane",NS)
    nodes={n.get("id"):n for n in root.iter() if n.get("id")}
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas[0]}" height="{canvas[1]}" viewBox="0 0 {canvas[0]} {canvas[1]}">',
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#334155"/></marker><marker id="message-arrow" viewBox="0 0 12 10" refX="11" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M1 1 L11 5 L1 9" fill="none" stroke="#64748b" stroke-width="1.5"/></marker></defs>',
           '<rect width="100%" height="100%" fill="white"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#172f46} .label{font-size:13px}.node{font-size:15px}.type{font-size:10px;fill:#526579;letter-spacing:.5px}</style>']
    def txt(x,y,text,size=15,anchor="middle",color=None):
        lines=textwrap.wrap(text, max(12,int(160/(size*.5)))) or [""]
        at=y-(len(lines)-1)*(size+3)/2
        parts.append(f'<text x="{x}" y="{at}" font-size="{size}" text-anchor="{anchor}"'+(f' fill="{color}"' if color else '')+'>')
        for i,line in enumerate(lines):
            parts.append(f'<tspan x="{x}" dy="{0 if i==0 else size+3}">{html.escape(line)}</tspan>')
        parts.append('</text>')
    shapes=plane.findall("bpmndi:BPMNShape",NS)
    for shape in shapes:
        node=nodes[shape.get("bpmnElement")]
        typ=tag(node)
        if typ not in {"participant","lane"}:
            continue
        box=shape.find("dc:Bounds",NS)
        x,y,w,h=[float(box.get(k)) for k in ("x","y","width","height")]
        fill="#f8fafc" if typ=="participant" else "#ffffff"
        if typ=="participant" and node.get("processRef") is None:
            fill="#edf4fb"
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#6b7f91" stroke-width="1.3"/>')
        if typ=="participant" and node.get("processRef") is None:
            txt(x+w/2,y+h/2+5,node.get("name",""),15)
        else:
            parts.append(f'<text transform="translate({x+18},{y+h/2}) rotate(-90)" text-anchor="middle" font-size="13">{html.escape(node.get("name",""))}</text>')
    for edge in plane.findall("bpmndi:BPMNEdge",NS):
        node=nodes[edge.get("bpmnElement")]
        points=[(float(p.get("x")),float(p.get("y"))) for p in edge.findall("di:waypoint",NS)]
        is_message=tag(node)=="messageFlow"
        path="M"+" L".join(f'{x},{y}' for x,y in points)
        parts.append(f'<path d="{path}" fill="none" stroke="'+('#64748b' if is_message else '#334155')+'" stroke-width="1.5"'+(' stroke-dasharray="8 6"' if is_message else '')+' marker-end="url(#'+('message-arrow' if is_message else 'arrow')+')"/>')
        label=edge.find("bpmndi:BPMNLabel/dc:Bounds",NS)
        if label is not None and node.get("name"):
            x,y,w,h=[float(label.get(k)) for k in ("x","y","width","height")]
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white" fill-opacity=".94"/>')
            txt(x+w/2,y+h/2+4,node.get("name"),12)
    for shape in shapes:
        node=nodes[shape.get("bpmnElement")]
        typ=tag(node)
        if typ not in FLOW_NODE_TYPES:
            continue
        b=shape.find("dc:Bounds",NS)
        x,y,w,h=[float(b.get(k)) for k in ("x","y","width","height")]
        cx,cy=x+w/2,y+h/2
        if typ in TASK_TYPES:
            fill="#edf5ff" if typ=="userTask" else "#fff"
            if node.get("id") in {"F1_ClosePending","F2_RejectContext"}:
                fill="#fff7e8"
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="11" fill="{fill}" stroke="#334155" stroke-width="1.6"/>')
            txt(cx,cy+8,node.get("name",""),14)
            parts.append(f'<text class="type" x="{x+9}" y="{y+16}">{html.escape(typ.replace("Task", "").upper())}</text>')
        elif "Gateway" in typ:
            parts.append(f'<path d="M{cx},{y} L{x+w},{cy} L{cx},{y+h} L{x},{cy} Z" fill="white" stroke="#334155" stroke-width="1.6"/>')
            txt(cx,cy+6,"X" if typ=="exclusiveGateway" else "◇",20)
        else:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{w/2}" fill="white" stroke="#334155" stroke-width="{3.5 if typ=="endEvent" else 1.6}"/>')
            if typ=="intermediateCatchEvent":
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{w/2-4}" fill="none" stroke="#334155"/>')
            if node.find("bpmn:messageEventDefinition",NS) is not None:
                parts.append(f'<rect x="{cx-10}" y="{cy-7}" width="20" height="14" fill="none" stroke="#334155"/><path d="M{cx-10},{cy-7} L{cx},{cy+1} L{cx+10},{cy-7}" fill="none" stroke="#334155"/>')
        label=shape.find("bpmndi:BPMNLabel/dc:Bounds",NS)
        if label is not None:
            bx,by,bw,bh=[float(label.get(k)) for k in ("x","y","width","height")]
            txt(bx+bw/2,by+15,node.get("name",""),13)
    parts.append('</svg>')
    return "\n".join(parts)+"\n"


def audit(root, forms, contracts):
    ids=[n.get("id") for n in root.iter() if n.get("id")]
    assert len(ids)==len(set(ids)),"Duplicate IDs"
    by_id={n.get("id"):n for n in root.iter() if n.get("id")}
    tasks=[]
    for process in root.findall("bpmn:process",NS):
        nodes={n.get("id"):n for n in process if tag(n) in FLOW_NODE_TYPES}
        flows=process.findall("bpmn:sequenceFlow",NS)
        for edge in flows:
            assert edge.get("sourceRef") in nodes and edge.get("targetRef") in nodes
        for n in nodes.values():
            incoming={f.get("id") for f in flows if f.get("targetRef")==n.get("id")}
            outgoing={f.get("id") for f in flows if f.get("sourceRef")==n.get("id")}
            assert incoming=={i.text for i in n.findall("bpmn:incoming",NS)}
            assert outgoing=={i.text for i in n.findall("bpmn:outgoing",NS)}
            kinds=[tag(item) for item in n]
            incoming_positions=[i for i,k in enumerate(kinds) if k=="incoming"]
            outgoing_positions=[i for i,k in enumerate(kinds) if k=="outgoing"]
            event_positions=[i for i,k in enumerate(kinds) if k.endswith("EventDefinition")]
            if incoming_positions and outgoing_positions:
                assert max(incoming_positions)<min(outgoing_positions),"BPMN incoming/outgoing schema order"
            if event_positions and incoming_positions+outgoing_positions:
                assert max(incoming_positions+outgoing_positions)<min(event_positions),"BPMN event schema order"
            if tag(n)=="exclusiveGateway" and len(outgoing)>1:
                assert all(f.find("bpmn:conditionExpression",NS) is not None for f in flows if f.get("id") in outgoing)
            if tag(n) in {"serviceTask","sendTask"}:
                td=n.find("bpmn:extensionElements/zeebe:taskDefinition",NS)
                headers={h.get("key"):h.get("value") for h in n.findall("bpmn:extensionElements/zeebe:taskHeaders/zeebe:header",NS)}
                assert headers["action"]==n.get("id")
                assert td.get("type")==("desd.s3.message" if tag(n)=="sendTask" else "desd.s3.business")
                tasks.append({"id":n.get("id"),"processId":process.get("id"),"jobType":td.get("type"),"headers":headers})
            if tag(n)=="userTask":
                form=n.find("bpmn:extensionElements/zeebe:formDefinition",NS)
                assert form.get("formId") in forms and form.get("bindingType")=="deployment"
        starts={n.get("id") for n in nodes.values() if tag(n)=="startEvent"}
        ends={n.get("id") for n in nodes.values() if tag(n)=="endEvent"}
        def closure(seeds, reverse=False):
            reached=set(seeds)
            while True:
                extra={f.get("sourceRef" if reverse else "targetRef") for f in flows if f.get("targetRef" if reverse else "sourceRef") in reached}
                if extra<=reached:
                    return reached
                reached|=extra
        assert set(nodes)<=closure(starts),"Unreachable nodes"
        assert set(nodes)<=closure(ends,True),"Node cannot reach an end"
        lanes=process.findall(".//bpmn:lane",NS)
        if lanes:
            membership=[x.text for lane in lanes for x in lane.findall("bpmn:flowNodeRef",NS)]
            assert set(membership)==set(nodes) and len(membership)==len(nodes)
    for edge in root.findall(".//bpmn:messageFlow",NS):
        assert edge.get("sourceRef") in by_id and edge.get("targetRef") in by_id
    for message_id,contract in contracts.items():
        if message_id not in by_id:
            continue
        assert by_id[message_id].get("name")==contract["name"]
        for sender in contract["senders"]:
            h={x.get("key"):x.get("value") for x in by_id[sender].findall("bpmn:extensionElements/zeebe:taskHeaders/zeebe:header",NS)}
            assert h["messageName"]==contract["name"]
    boxes={shape.get("bpmnElement"):tuple(float(shape.find("dc:Bounds",NS).get(attr))
                 for attr in ("x","y","width","height"))
           for shape in root.findall(".//bpmndi:BPMNShape",NS)
           if tag(by_id[shape.get("bpmnElement")]) in FLOW_NODE_TYPES}
    for shape in root.findall(".//bpmndi:BPMNEdge",NS):
        edge=by_id[shape.get("bpmnElement")]
        points=[(float(p.get("x")),float(p.get("y"))) for p in shape.findall("di:waypoint",NS)]
        assert all(a[0]==b[0] or a[1]==b[1] for a,b in zip(points,points[1:])),"Non-orthogonal edge"
        assert not collisions(points,boxes,{edge.get("sourceRef"),edge.get("targetRef")}),"Edge crosses another flow node: "+edge.get("id")
    return {"processIds":[p.get("id") for p in root.findall("bpmn:process",NS)],
            "pools":len(root.findall(".//bpmn:participant",NS)),"lanes":len(root.findall(".//bpmn:lane",NS)),
            "conditionExpressions":len(root.findall(".//bpmn:conditionExpression",NS)),"tasks":tasks,
            "staticChecks":"passed","orthogonalEdges":True,"edgeNodeIntersections":0}


def generated():
    baseline=json.loads((SOURCE/"execution-manifest.json").read_text(encoding="utf-8"))
    contracts=deepcopy(baseline["messages"])
    for contract in contracts.values():
        contract["name"]="S3 "+contract["name"]
    contracts["F1_Message_Pending"]["name"]="S3 Verification follow-up closed"
    contracts["F1_Message_Pending"]["payloadFields"].append("followUpStatus")
    stock=contracts["F2_Message_StockContext"]
    stock["senders"].append("F2_RejectContext")
    for field in ("loadedVersion","contextAvailable","contextError","status","errors"):
        if field not in stock["payloadFields"]:
            stock["payloadFields"].append(field)
    form_files={name:(SOURCE/"forms"/name).read_bytes() for name in baseline["forms"] for name in [Path(name).name]}
    form_files["F1-Verification-Follow-up.form"]=(json.dumps(follow_up_form(),ensure_ascii=False,indent=2)+"\n").encode()
    form_ids={json.loads(data)["id"] for data in form_files.values()}
    manifest={"schemaVersion":1,"targetCamundaVersion":"8.10","correlationVariable":"requestId",
              "messageTimeToLiveMs":3600000,"messageIdRule":baseline["messageIdRule"],
              "jobTypes":["desd.s3.business","desd.s3.message"],"messages":contracts,"models":{},
              "forms":["forms/"+name for name in sorted(form_files)],
              "validationScope":"Static model, contract, reference, reachability and layout checks. Runtime evidence is recorded separately.",
              "baseline":"models/operational (retained Sprint 2 executable resources)"}
    outputs={"forms/"+name:data for name,data in form_files.items()}
    for name,extend in (("F1",extend_f1),("F2",extend_f2)):
        root=prepare(name)
        extend(root)
        apply_contracts(root,contracts)
        rebuild_declarations(root)
        size=diagram(root,name)
        info=audit(root,form_ids,contracts)
        ET.indent(root,space="  ")
        data=ET.tostring(root,encoding="utf-8",xml_declaration=True)
        resource=name+"-Sprint3.bpmn"
        info.update({"resource":resource,"sha256":hashlib.sha256(data).hexdigest(),
                     "source":"models/operational/"+name+"-Operational.bpmn",
                     "sourceSha256":hashlib.sha256((SOURCE/(name+"-Operational.bpmn")).read_bytes()).hexdigest()})
        outputs[resource]=data
        outputs[name+"-Sprint3.svg"]=svg(root,name,size).encode()
        manifest["models"][name]=info
    outputs["execution-manifest.json"]=(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n").encode()
    return outputs,manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="Check current generated files without writing.")
    args=parser.parse_args()
    outputs,manifest=generated()
    for relative,data in outputs.items():
        path=OUT/relative
        if args.check:
            if not path.is_file() or path.read_bytes()!=data:
                raise ValueError("Missing or stale Sprint 3 generated resource: "+relative)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
    print(json.dumps({"staticChecks":"passed","models":{name:{k:v for k,v in model.items() if k!="tasks"} for name,model in manifest["models"].items()},"resources":len(outputs)},indent=2))


if __name__=="__main__":
    main()
