"""Build a reviewable requirement-to-model reference register."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
rows=[]
def add(id,requirement,basis,sd,sr,strategic,operational,implementation,qualification):
 rows.append(dict(id=id,requirement=requirement,basis=basis,sd=sd.split(),sr=sr.split(),strategic=strategic.split(),operational=operational.split(),implementation=implementation,qualification=qualification))
add('R1','Registered producer submits a new product','Workbook R1 / Use Case 1',
 'D01 D02 D18','PRODUCER_T1 CAT_T1','Task_F1','F1_Submit F1_SendDetails F1_Validate',
 'F1 product-details form; src/sprint2_demo/f1.py', 'Producer registration is a precondition, not implemented account registration.')
add('R2','Product name, description, category, price, quantity, availability period and origin','Workbook R2 / Use Case 1',
 'D01 D09','CAT_R CAT_T1 CAT_Q1','Task_F1','F1_Submit F1_Validate',
 'F1 form and validation contract', 'Model mapping is verified; execution must demonstrate mandatory-field checks.')
add('R3','Relevant harvest date, allergen, certification and best-before information','Workbook R3 / Use Case 1',
 'D01 D07 D09','CAT_R CAT_T1 CAT_Q1 QLT_R','Task_F1 Task_Trace','F1_Submit F1_Validate F1_Claim',
 'F1 form and validation contract', 'Whether each field is always mandatory or conditionally relevant remains a business-rule decision.')
add('R4','Check information and request correction of invalid or missing details','Workbook R4 / Use Case 1',
 'D01 D02','CAT_T1 CAT_Q1 PRODUCER_T1','Task_F1 Task_CatalogResponse','F1_Validate F1_Valid F1_Correction F1_Edit F1_ReceiveCorrected',
 'F1 correction form; src/sprint2_demo/f1.py', 'The model includes the correction loop. Do not infer a tested Camunda loop from the diagram alone.')
add('R5','Verify a claimed organic certificate using an external or simulated service','Workbook R5 / Use Case 1',
 'D13 D09','CAT_T2 CAT_T_NO_CLAIM CAT_T_VERIFY CAT_Q1 VERIFIER_T1 VERIFIER_R','Task_F1','F1_Claim F1_Verify F1_Result',
 'F1 certification outcome input / service adapter', 'D13 is conditional on the claim. A simulated result must be presented as a simulation.')
add('R6','Publish only after successful validation','Workbook R6 / Use Case 1',
 'D02 D09','CAT_G CAT_T1 CAT_T2 CAT_T_NO_CLAIM CAT_T_VERIFY CAT_T3','Task_F1 Task_CatalogResponse','F1_Valid F1_Result F1_Publish F1_Availability F1_Notify',
 'src/sprint2_demo/f1.py', 'Publication correctness and sale availability are separate decisions; F2 does not grant publication.')
add('R7','Producer can update quantity and seasonal availability','Workbook R7 / Use Case 1',
 'D03 D04 D18','PRODUCER_T2 INV_R INV_T1','Task_F2','F2_Load F2_EnterStockChange F2_Producer F2_Prepare',
 'F2 stock/date form; src/sprint2_demo/f2.py', 'Loaded stock and version must reach the form; runtime data transfer is a separate execution check.')
add('R8','Zero stock makes the product unavailable for new orders','Workbook R8 / Use Case 1',
 'D04 D09','INV_G INV_T2 INV_T3 INV_Q1','Task_F2 Task_Visibility','F2_Assess F2_CanSell F2_Unavailable F2_Save F2_Sync',
 'src/sprint2_demo/common.py; src/sprint2_demo/f2.py', 'Shared availability rule must be exercised in the engine and persisted result, not just shown on a diagram.')
add('R9','Replenishment restores availability only inside the availability period','Workbook R9 / Use Case 1',
 'D03 D04 D09','INV_T1 INV_T2 INV_T3 INV_Q1','Task_F2 Task_Visibility','F2_Assess F2_CanSell F2_Available F2_Unavailable F2_Save F2_Sync',
 'src/sprint2_demo/common.py; src/sprint2_demo/f2.py', 'Boundary dates and timezone are design decisions; an unpublished product must remain unavailable.')
add('R10','Handle invalid input and unavailable verification service','Workbook R10 / Use Case 1',
 'D01 D02 D13','CAT_T1 CAT_T2 CAT_Q1 CAT_Q2','Task_F1 Task_CatalogResponse','F1_Correction F1_Result F1_Pending F1_PendingNotify',
 'F1 validation/certification handling', 'Current design keeps unavailable verification pending; automatic retry limits are not specified by the case.')
add('C01','Easy product/stock updates for producers with differing technical capability','Case Study: Producers',
 'D18','PRODUCER_G PRODUCER_T1 PRODUCER_T2 PRODUCER_T4 PRODUCER_Q CAT_T1 INV_T1','Task_F1 Task_F2','F1_Submit F1_Edit F2_EnterStockChange',
 'Three task forms', 'Forms support this quality, but usability has not been measured or user-tested.')
add('C02','Convenient local shopping, reliable institutional supply and less restaurant supplier administration','Case Study: three customer segments',
 'D08 D09 D19','ORD_G ORD_Q1 CUSTOMER_G CUSTOMER_T1 CUSTOMER_T3 CUSTOMER_Q CUSTOMER_Q_SUPPLY CUSTOMER_Q_ADMIN CUSTOMER_R','Task_Order Task_Fulfil Task_Complete','',
 'Enterprise context', 'The three segments are aggregated into one actor; this records their distinct needs without inventing three systems.')
add('C03','Product browsing/search/categories and transparent multi-vendor responsibilities','Case Study: Customers / Core functionality',
 'D08 D09 D10 D19','ORD_T1 ORD_T3 CUSTOMER_T1 CUSTOMER_T3 CUSTOMER_R','Task_Order Task_Fulfil Task_Complete','',
 'Enterprise context', 'Strategic activities cover these at a high level. Search/checkout are not claimed as F1/F2 operational implementations.')
add('C04','At least 48 hours producer preparation lead time and clear delivery/collection arrangements','Case Study: Producers / Customers',
 'D05 D08','PRODUCER_G_ORDER PRODUCER_T3 ORD_T1 ORD_T3','Task_Order Task_Fulfil Task_Complete','',
 'Enterprise context', 'Lead-time validation belongs to order handling, not product listing or inventory updates.')
add('C05','Weekly settlements, 5% commission and transparent accounting trail','Case Study: Producers / Core functionality',
 'D06 D14 D15 D16','PRODUCER_Q_INCOME FIN_G FIN_T1 FIN_T2 FIN_T3 FIN_Q1 PAYMENTS_T1 PAYMENTS_T2','Task_Payment Task_Reconcile Task_Settle Task_Audit','',
 'Enterprise context; sandbox/simulation only', 'No real payment execution or payment compliance result is asserted.')
add('C06','Link customers, products and producers to respond rapidly to safety concerns','Case Study: Quality assurance',
 'D07 D11 D17','CUSTOMER_G_CONCERN CUSTOMER_T2 QLT_G QLT_R QLT_T1 QLT_T2 QLT_T3 QLT_Q1','Task_Trace Task_Investigate Task_Respond Task_Review','',
 'Enterprise context', 'Modelled response context does not constitute a working incident-management service.')
add('C07','Postcode-based food miles, surplus discounts, recipes, storage guidance and farm stories','Case Study: Community features',
 'D12','COM_G COM_R COM_T1 COM_T2 COM_T3 COM_Q1','Task_Surplus Task_Content Task_Miles','',
 'Enterprise context', 'No geography API, discount engine or community publishing service is claimed.')
add('A01','Preserve accuracy under stale, duplicate and concurrent updates','Existing F2 design proposal; not an additional case requirement',
 'D04 D09','INV_T1 INV_T2 INV_T3 INV_Q1 INV_Q2','Task_F2 Task_Visibility','F2_Load F2_Order F2_OrderValid F2_RejectOrder F2_Save F2_Saved F2_Failed',
 'Versioned inventory and processed change IDs', 'The model says version/atomic commit; actual persistence and concurrent-instance evidence are required to substantiate this.')
add('A02','Trade trust against shortest listing time','Reasoned SR contribution judgement',
 'D02 D09 D13','CAT_T_VERIFY CAT_Q1 CAT_Q2','Task_F1','F1_Verify F1_Result F1_Pending',
 'Certification-check and pending path', 'help/hurt indicates expected direction of effect, not a measured latency or quality score.')
add('A03','Respect separate organisations and internal responsibilities','Teacher feedback supplied in screenshots plus current BPMN design',
 'D01 D02 D03 D04 D13','PRODUCER_T1 PRODUCER_T2 CAT_T1 INV_T1 VERIFIER_T1','Task_F1 Task_F2','F1_Submit F1_Edit F1_Validate F1_Verify F2_EnterStockChange F2_Producer',
 'Producer/marketplace pools, platform lanes and message exchanges', 'The teacher requested correct task ownership. The exact five-actor iStar decomposition is the model design, not a quoted tutor instruction.')
doc={
 'status':'Draft for group review', 'date':'2026-11-17',
 'meaning':'This is evidence of requirements/model coverage and exact reference checks. It is not evidence that every referenced functionality has executed.',
 'model':'models/istar/enterprise-model.json',
 'source_register':[
  {'id':'UC1','path':'docs/Use-Case-1-Requirements.xlsm','evidence':'R1-R10 read directly; original use-case reference retained'},
  {'id':'CASE','path':'review-evidence/requirements-2026-11-18/case-study-preview.txt','url':'https://blackboard.uwe.ac.uk/ultra/courses/_385767_1/document/_13162411_1?view=content&state=view','evidence':'Direct reading of saved Blackboard-visible two-page case text'},
  {'id':'STRATEGIC','path':'models/strategic/Strategic-BPMN.bpmn','evidence':'Existing strategic process baseline'},
  {'id':'F1','path':'review-evidence/responsibilities-2026-11-17/F1-saved.bpmn','evidence':'Responsibility revision'},
  {'id':'F2','path':'review-evidence/responsibilities-2026-11-17/F2-saved.bpmn','evidence':'Responsibility revision'}],
 'rows':rows}
(ROOT/'docs/sprint-2/traceability.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Sprint 2 model traceability','', '**Draft for group review — 17 November 2026.** This register checks what each model represents. Referenced code, a BPMN node or a form is not by itself evidence of an executed Camunda process.','',
 'The SD and SR files are two views of [one semantic model](../../models/istar/enterprise-model.json). Source text and IDs are preserved in [traceability.json](traceability.json).','',
 '| Requirement | SD dependency | SR rationale | Strategic BPMN | F1/F2 operational nodes |','|---|---|---|---|---|']
for r in rows:
 lines.append('| **'+r['id']+'** '+r['requirement']+' | '+', '.join(r['sd'])+' | '+', '.join(r['sr'])+' | '+', '.join(r['strategic'])+' | '+(', '.join(r['operational']) or 'Enterprise context; outside detailed F1/F2')+' |')
lines+=['','## Interpretation and remaining evidence','']
for r in rows:lines.append('- **'+r['id']+'** — '+r['qualification'])
lines+=['','## Sources and status','',
 '- R1–R10: the project requirements workbook, retaining its Use Case 1 references. BR1–BR6 remain proposals until a decision is recorded.',
 '- C01–C07: the [Blackboard Case Study](https://blackboard.uwe.ac.uk/ultra/courses/_385767_1/document/_13162411_1?view=content&state=view), read through the saved visible page text.',
 '- A01–A02: existing design choices and explicit rationale judgements, rather than new teacher requirements.',
 '- A03: teacher feedback supplied by the user about task ownership; the chosen pool/lane/actor arrangement is the implementation of that feedback.',
 '- Actual tutor scope approval, team review, personal contributions and successful runtime results must be recorded separately from this mapping.','']
(ROOT/'docs/sprint-2/traceability.md').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote',len(rows),'traceability rows.')
