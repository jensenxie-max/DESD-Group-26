"""Check semantic constraints, SD/SR agreement and referenced BPMN IDs."""
from pathlib import Path
import json, xml.etree.ElementTree as E

P=Path(__file__).parent; ROOT=P.parents[1]
m=json.loads((P/'enterprise-model.json').read_text(encoding='utf-8'))
actors={a['id'] for a in m['actors']};nodes={n['id']:n for n in m['nodes']}
assert len(actors)==len(m['actors']);assert len(nodes)==len(m['nodes'])
allids=[n['id'] for k in ['actors','nodes','links','dependencies'] for n in m[k]]
assert len(allids)==len(set(allids)), 'IDs must be unique'
parents={};adj={};checks=[]
for l in m['links']:
 s,t=nodes[l['source']],nodes[l['target']]
 assert s['actor']==t['actor'], 'Intentional-element links cannot cross actor boundaries'
 typ=l['type']
 if typ=='refinement':
  assert s['type'] in ['goal','task'] and t['type'] in ['goal','task']
  assert l['value'] in ['AND','OR']
  parents.setdefault(l['target'],[]).append(l)
  adj.setdefault(l['source'],[]).append(l['target'])
 elif typ=='neededBy': assert s['type']=='resource' and t['type']=='task'
 elif typ=='contribution':assert t['type']=='quality' and l['value'] in ['make','help','hurt','break']
 elif typ=='qualification':assert s['type']=='quality' and t['type']!='quality'
 else:raise AssertionError('Unsupported relationship')
for ls in parents.values():
 assert len({l['value'] for l in ls})==1, 'One parent cannot combine AND and OR refinement'
 if ls[0]['value']=='AND':assert len(ls)>=2
def walk(n,stack):
 assert n not in stack,'Refinement cycle'
 for child in adj.get(n,[]):walk(child,stack|{n})
for n in adj:walk(n,set())
def reaches(source,target):
 return any(n==target or reaches(n,target) for n in adj.get(source,[]))
assert not reaches('CUSTOMER_T2','CUSTOMER_G'), 'Reporting a concern cannot be required for ordinary shopping'
assert not reaches('PRODUCER_T3','PRODUCER_G'), 'Accepted-order preparation is a separate conditional goal'
assert {l['source'] for l in parents['CAT_T2']}=={'CAT_T_NO_CLAIM','CAT_T_VERIFY'}
assert all(l['value']=='OR' for l in parents['CAT_T2'])
for d in m['dependencies']:
 assert d['depender'] in actors and d['dependee'] in actors and d['depender']!=d['dependee']
 assert d['type'] in ['goal','task','quality','resource']
 for end in ['depender','dependee']:
  nid=d[end+'_element']
  if nid:assert nodes[nid]['actor']==d[end]
 if d['depender_element']:
  assert not any(l['target']==d['depender_element'] and l['type'] in ['refinement','contribution'] for l in m['links'])
checks.extend(['Unique IDs','Same-actor intentional links','Link endpoint types','AND/OR arity and exclusivity','No refinement cycles','Distinct dependency actors','Optional dependency endpoints valid'])
checks.append('Concern/order conditions separated; certification has explicit no-claim/verification alternatives')
for name in ['SD','SR']:
 r=E.parse(P/f'{name}.svg').getroot();ids={x.get('id') for x in r.iter()}
 assert actors<=ids and {d['id'] for d in m['dependencies']}<=ids
 if name=='SR':assert set(nodes)<=ids
checks.append('Both SVG views contain the same actors/dependencies; SR includes every intentional element')
drawio=E.parse(P/'SD-SR.drawio').getroot()
assert len(drawio.findall('diagram'))==2
for page in drawio.findall('diagram'):
 cells=page.findall('.//mxCell');ids={x.get('id') for x in cells}
 assert len(cells)==len(ids)
 for cell in cells:
  for side in ['source','target']:
   if cell.get(side):assert cell.get(side) in ids
checks.append('Editable drawio pages have unique native cells and resolvable edge endpoints')
strategic=E.parse(ROOT/'models/strategic/Strategic-BPMN.bpmn').getroot();sids={x.get('id') for x in strategic.iter()}
for section in m['sections']:assert set(section['strategy'])<=sids
checks.append('All strategic activity references resolve')
trace=json.loads((ROOT/'docs/sprint-2/traceability.json').read_text(encoding='utf-8'))
bpmn_ids={}
for f in ['F1','F2']:
 r=E.parse(ROOT/f'review-evidence/responsibilities-2026-11-17/{f}-saved.bpmn').getroot();bpmn_ids[f]={x.get('id') for x in r.iter()}
for row in trace['rows']:
 assert set(row['sd'])<={d['id'] for d in m['dependencies']}
 assert set(row['sr'])<=set(nodes)
 assert set(row['strategic'])<=sids
 for id in row['operational']:assert id in bpmn_ids[id[:2]]
checks.append('Traceability references resolve across iStar, strategic and F1/F2 models')
report={'status':'PASS','scope':'Static semantic/reference checks, not tutor review or Camunda runtime validation','actors':len(actors),'intentional_elements':len(nodes),'dependencies':len(m['dependencies']),'intentional_links':len(m['links']),'checks':checks}
(P/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
