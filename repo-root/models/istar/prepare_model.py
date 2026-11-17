"""Create the review baseline. Subsequent edits belong in enterprise-model.json."""
import json
from pathlib import Path

OUT = Path(__file__).parent
actors = [
    {"id":"producer","name":"Producer","type":"actor"},
    {"id":"marketplace","name":"Bristol Regional Food Network / Marketplace","type":"actor"},
    {"id":"customer","name":"Customer / community buyer","type":"actor"},
    {"id":"verifier","name":"Certification verification service","type":"actor"},
    {"id":"payments","name":"Payment / settlement service","type":"actor"},
]
nodes=[]; links=[]; sections=[]; link_serial=0
def node(id, actor, type, name, basis):
    nodes.append(dict(id=id,actor=actor,type=type,name=name,basis=basis)); return id
def link(source,target,type,value=None):
    global link_serial
    link_serial+=1
    links.append(dict(id=f'L{link_serial:03}',source=source,target=target,type=type,**({'value':value} if value else {})))
def section(id,title,goal,tasks,qualities,resource,basis,strategy):
    g=node(id+'_G','marketplace','goal',goal,basis)
    ts=[node(id+f'_T{i+1}','marketplace','task',s,basis) for i,s in enumerate(tasks)]
    qs=[node(id+f'_Q{i+1}','marketplace','quality',s,'Design rationale; qualitative assessment') for i,s in enumerate(qualities)]
    r=node(id+'_R','marketplace','resource',resource,basis)
    for t in ts: link(t,g,'refinement','AND')
    link(r,ts[0],'neededBy')
    link(ts[0],qs[0],'contribution','help')
    if len(qs)>1:
        link(ts[1],qs[0],'contribution','help')
        link(ts[1],qs[1],'contribution','hurt')
        link(ts[-1],qs[1],'contribution','help')
    else:
        link(ts[-1],qs[0],'contribution','help')
    sections.append(dict(id=id,title=title,goal=g,tasks=ts,qualities=qs,resource=r,strategy=strategy))

section('CAT','01  Catalogue / F1','Validated listings published',
    ['Validate details and request corrections','Check certification when claimed','Publish approved product and notify producer'],
    ['Trustworthy product information','Short time to listing'], 'Submitted product details',
    'Requirements R1-R6, R10; Strategic Task_F1', ['Task_F1','Task_CatalogResponse'])
section('INV','02  Inventory / F2','Stock and sale status consistent',
    ['Validate and apply stock/date changes','Check version and sale eligibility','Commit stock/status and synchronise availability'],
    ['Accurate sale availability','Prompt update completion'], 'Current product, stock and version',
    'Requirements R7-R9; version/atomic commit are existing design proposals', ['Task_F2','Task_Visibility'])
section('ORD','03  Orders and fulfilment','Accepted orders fulfilled',
    ['Check basket, availability and >=48h producer lead time','Obtain payment outcome','Coordinate producer fulfilment and customer outcome'],
    ['Dependable fulfilment'], 'Order and customer details',
    'Strategic order lane; Sprint 1 case-study mapping', ['Task_Order','Task_Payment','Task_Fulfil','Task_Complete'])
section('FIN','04  Finance and settlement','Producer sales settled and recorded',
    ['Reconcile sales and calculate 5% commission','Arrange weekly producer settlement','Maintain statements and audit trail'],
    ['Transparent financial accounting'], 'Sales and payment records',
    'Strategic finance lane; Sprint 1 case-study mapping', ['Task_Reconcile','Task_Settle','Task_Audit'])
section('QLT','05  Quality and traceability','Reported quality concern resolved',
    ['Identify affected products, producers and orders','Investigate and decide response','Notify affected customers and review follow-up'],
    ['Effective protection of customers'], 'Concern and traceability records',
    'Strategic quality lane; Sprint 1 case-study mapping', ['Task_Trace','Task_Investigate','Task_Respond','Task_Review'])
section('COM','06  Community and sustainability','Local-food information and offers shared',
    ['Coordinate surplus offers','Share recipes, storage advice and farm stories','Report food miles and sustainability information'],
    ['Less food waste; informed local choices'], 'Surplus, provenance and postcode information',
    'Strategic community lane; Sprint 1 case-study mapping', ['Task_Surplus','Task_Content','Task_Miles'])

# Other actors' internal rationale. Their services are not implemented by F1/F2.
external = {}
def ext(actor,goal,tasks,quality,resource):
    pre=actor.upper()
    g=node(pre+'_G',actor,'goal',goal,'Derived rationale for existing strategic participant')
    ts=[node(pre+f'_T{i+1}',actor,'task',s,'Strategic participant interaction') for i,s in enumerate(tasks)]
    q=node(pre+'_Q',actor,'quality',quality,'Design rationale; qualitative assessment')
    r=node(pre+'_R',actor,'resource',resource,'Strategic interaction / requirements')
    for t in ts: link(t,g,'refinement','AND' if len(ts)>1 else 'OR')
    link(r,ts[0],'neededBy'); link(ts[-1],q,'contribution','help')
    external[actor]=dict(goal=g,tasks=ts,quality=q,resource=r)
ext('producer','Producer obligations to marketplace fulfilled',
    ['Submit and correct product details','Maintain stock and sale dates','Prepare accepted producer orders'],
    'Reliable participation in local trade','Farm product and stock records')
ext('customer','Customer order and concern information supplied',
    ['Submit order and contact details','Report a quality concern when needed'],
    'Clear customer communication','Current offers and product provenance')
ext('verifier','Certification enquiry answered',
    ['Check certificate evidence and return result'],
    'Trustworthy verification','Certification reference and register')
ext('payments','Requested payment and settlement operations processed',
    ['Authorise requested payment','Execute requested producer settlement'],
    'Accurate transaction processing','Payment and settlement instructions')

# Refine conditional work separately from routine participation and express
# stakeholders' own interests rather than merely their platform obligations.
by_id={n['id']:n for n in nodes}
by_id['CAT_T2']['name']='Resolve certification requirement'
node('CAT_T_NO_CLAIM','marketplace','task','Confirm no organic claim','Use Case 1: certification is conditional')
node('CAT_T_VERIFY','marketplace','task','Verify claimed certificate','Use Case 1: certification is conditional')
link('CAT_T_NO_CLAIM','CAT_T2','refinement','OR')
link('CAT_T_VERIFY','CAT_T2','refinement','OR')
for l in links:
    if l['type']=='contribution' and l['source']=='CAT_T2':l['source']='CAT_T_VERIFY'
sections[0]['conditional_alternatives']=['CAT_T_NO_CLAIM','CAT_T_VERIFY']

for actor in ['producer','customer']:
    actor_ids={n['id'] for n in nodes if n['actor']==actor}
    links[:]=[l for l in links if l['source'] not in actor_ids]
by_id['PRODUCER_G']['name']='Products offered to regional customers'
by_id['PRODUCER_Q']['name']='Low learning and administration effort'
node('PRODUCER_G_ORDER','producer','goal','Accepted producer order prepared','Case Study: producer lead time; applies after order acceptance')
node('PRODUCER_T4','producer','task','Update stock and dates through a simple form','Existing F2 form design supporting producer usability')
node('PRODUCER_Q_INCOME','producer','quality','Timely, dependable sale income','Case Study: weekly producer settlement')
link('PRODUCER_T1','PRODUCER_G','refinement','AND')
link('PRODUCER_T2','PRODUCER_G','refinement','AND')
link('PRODUCER_T4','PRODUCER_T2','refinement','OR')
link('PRODUCER_T3','PRODUCER_G_ORDER','refinement','OR')
link('PRODUCER_T4','PRODUCER_Q','contribution','help')
link('PRODUCER_T3','PRODUCER_Q_INCOME','contribution','help')
link('PRODUCER_R','PRODUCER_T1','neededBy')
link('PRODUCER_R','PRODUCER_T2','neededBy')

by_id['CUSTOMER_G']['name']='Informed local purchase arranged'
by_id['CUSTOMER_T1']['name']='Submit one single- or multi-vendor order'
by_id['CUSTOMER_T2']['name']='Report a product or food-safety concern'
by_id['CUSTOMER_Q']['name']='Convenient access to local food'
node('CUSTOMER_G_CONCERN','customer','goal','Reported quality concern addressed','Case Study: applies only if a concern is reported; depends on marketplace response')
node('CUSTOMER_T3','customer','task','Review availability and supplier commitments','Case Study: customer browsing and fulfilment transparency')
node('CUSTOMER_Q_SUPPLY','customer','quality','Reliable and consistent supply','Case Study: community institutions')
node('CUSTOMER_Q_ADMIN','customer','quality','Low multi-supplier administration','Case Study: restaurants and cafes')
link('CUSTOMER_T1','CUSTOMER_G','refinement','AND')
link('CUSTOMER_T3','CUSTOMER_G','refinement','AND')
link('CUSTOMER_T2','CUSTOMER_G_CONCERN','refinement','OR')
link('CUSTOMER_R','CUSTOMER_T3','neededBy')
link('CUSTOMER_T1','CUSTOMER_Q','contribution','help')
link('CUSTOMER_T1','CUSTOMER_Q_ADMIN','contribution','help')
link('CUSTOMER_T3','CUSTOMER_Q_SUPPLY','contribution','help')

external['producer']['custom_positions']={
 'PRODUCER_G':[245,80,450,95], 'PRODUCER_T1':[250,280,420,100],
 'PRODUCER_T2':[250,460,420,100], 'PRODUCER_T4':[250,640,420,100],
 'PRODUCER_Q':[250,800,420,100], 'PRODUCER_G_ORDER':[250,970,420,95],
 'PRODUCER_T3':[250,1120,420,95], 'PRODUCER_Q_INCOME':[250,1280,420,95],
 'PRODUCER_R':[25,610,195,150]}
external['customer']['custom_positions']={
 'CUSTOMER_G':[245,80,450,100], 'CUSTOMER_T3':[250,300,420,100],
 'CUSTOMER_T1':[250,480,420,100], 'CUSTOMER_Q':[20,700,210,130],
 'CUSTOMER_Q_SUPPLY':[270,700,210,130], 'CUSTOMER_Q_ADMIN':[520,700,210,130],
 'CUSTOMER_G_CONCERN':[250,940,420,100], 'CUSTOMER_T2':[250,1120,420,100],
 'CUSTOMER_R':[25,350,190,170]}

deps=[]
def dep(id,der,dee,type,name,basis,why,condition=None):
    deps.append(dict(id=id,depender=der,dependee=dee,type=type,name=name,basis=basis,rationale=why,
        depender_element=None,dependee_element=None,**({'condition':condition} if condition else {})))
dep('D01','marketplace','producer','resource','Product details','R1-R4','The platform cannot validate facts the producer has not supplied.')
dep('D02','producer','marketplace','goal','Validated listing published','R6','The producer relies on the platform to publish only after its checks succeed.')
dep('D03','marketplace','producer','resource','Stock and seasonal dates','R7','The producer supplies current stock and availability information.')
dep('D04','producer','marketplace','goal','Sale availability maintained','R8-R9','The platform controls the sale status exposed to customers.')
dep('D05','marketplace','producer','task','Prepare producer-specific order','Strategic Task_Fulfil / Msg_Fulfil','The platform coordinates the order; the producer prepares the goods.')
dep('D06','producer','marketplace','goal','Sale proceeds settled','Strategic finance lane','The producer relies on marketplace reconciliation and settlement coordination.')
dep('D07','marketplace','producer','resource','Origin and traceability records','R2-R3; strategic quality lane','Investigation needs producer/product provenance.')
dep('D08','customer','marketplace','goal','Food order fulfilled','Strategic order lane','The buyer relies on the network to coordinate the accepted order.')
dep('D09','customer','marketplace','quality','Trustworthy product information','R2-R6; strategic catalogue lane','The buyer relies on adequate product checks and transparent information.')
dep('D10','marketplace','customer','resource','Order and contact details','Strategic Msg_Order','Checkout and outcome communication need buyer-supplied information.')
dep('D11','customer','marketplace','goal','Quality concern resolved','Strategic quality lane','The network can trace affected orders and coordinate a response.', 'A concern is reported')
dep('D12','customer','marketplace','resource','Community and sustainability information','Strategic community lane','The network supplies advice, offers, provenance and food-mile information.')
dep('D13','marketplace','verifier','resource','Certification check result','R5, R10','The platform relies on a provider result before accepting a claimed certificate.', 'Organic certification is claimed')
dep('D14','marketplace','payments','goal','Payment authorised','Strategic Task_Payment','The marketplace depends on the payment service rather than authorising money itself.')
dep('D15','marketplace','payments','goal','Producer settlement executed','Strategic Task_Settle','The marketplace calculates the amount; the service executes the payment.')
dep('D16','payments','marketplace','resource','Settlement instructions','Strategic Msg_Settle','The service needs the payee and amount produced by reconciliation.')
dep('D17','marketplace','customer','resource','Quality concern report','Strategic Msg_Incident','The buyer supplies the concern that triggers the investigation.', 'A concern is reported')
dep('D18','producer','marketplace','quality','Easy product and stock updates','Case Study: producer requirements','Producers have varying technical capability and need frequent updates without extensive training.')
dep('D19','customer','marketplace','quality','Convenient multi-vendor shopping','Case Study: customer segments and checkout','Families need convenient access, community institutions need consistent supply, and restaurants need less supplier administration.')

model = dict(schema='desd-group26-istar-1',language='iStar 2.0',status='Draft for group review',date='2026-11-17',
    scope='Whole enterprise; detailed operational traceability for Use Case 1 F1 and F2.',
    actors=actors,nodes=nodes,links=links,dependencies=deps,sections=sections,external_layout=external,
    dependency_endpoint_policy='SD and SR retain actor-level dependencies. Internal endpoints are intentionally unspecified; the rationale field explains the dependency. Internal relationships remain within one actor.',
    evidence=[
      {'path':'docs/Use-Case-1-Requirements.xlsm','status':'Read directly; R1-R10 and proposed BR1-BR6'},
      {'path':'docs/sprint-1/README.md','status':'Read directly; earlier scope and case-study mapping'},
      {'path':'review-evidence/requirements-2026-11-18/case-study-preview.txt','url':'https://blackboard.uwe.ac.uk/ultra/courses/_385767_1/document/_13162411_1?view=content&state=view','status':'Read directly from the saved Blackboard-visible Case Study text; includes both PDF pages'},
      {'path':'models/strategic/Strategic-BPMN.bpmn','status':'Read directly; six enterprise capability areas and five participants'},
      {'path':'review-evidence/responsibilities-2026-11-17/F1-saved.bpmn','status':'Read directly; current responsibility layout'},
      {'path':'review-evidence/responsibilities-2026-11-17/F2-saved.bpmn','status':'Read directly; current responsibility layout'},
      {'url':'https://arxiv.org/html/1605.07767v3','status':'Notation and relationship constraints checked against the language authors guide'}],
    assumptions=[
      'The five actors are the existing strategic model participants, not a teacher-mandated actor list.',
      'Qualities and help/hurt links are reasoned design judgements, not measured outcomes.',
      'Certification may be simulated; no real verification provider is asserted.',
      'Payment and settlement remain strategic context and sandbox scope; not F1/F2 implementation.',
      'Version checks, atomic persistence and scheduled season checks are existing design proposals, not separate confirmed case-study requirements.',
      'The six capability areas describe responsibilities inside the marketplace, not six new external actors.',
      'Customer / community buyer aggregates the three stated segments: individuals/families, community institutions, and independent restaurants/cafes. Their distinct expectations are retained in D19 and the traceability notes.',
      'No tutor approval, team review, student authorship or assessed completion is asserted by this draft.'],
    decisions_needed=[
      'Confirm whether the group already has SD/SR source files to preserve or merge.',
      'Confirm the tutor-agreed F1/F2 scope if this has been agreed since the recorded Sprint 1 baseline.',
      'Review the design trade-offs: certificate checking prioritises trust over shortest listing time; version checks prioritise correctness over immediate completion.',
      'Confirm stock units, date boundary/time zone policy and verification timeout follow-up in the operational design.'])
(OUT/'enterprise-model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared',len(actors),'actors,',len(nodes),'intentional elements,',len(deps),'dependencies.')
