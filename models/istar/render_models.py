"""Render the editable semantic JSON as SVG and native diagrams.net cells."""
from pathlib import Path
import json, math, textwrap, html, xml.etree.ElementTree as E

P=Path(__file__).parent
M=json.loads((P/'enterprise-model.json').read_text(encoding='utf-8'))
N={n['id']:n for n in M['nodes']}; A={a['id']:a for a in M['actors']}
D={d['id']:d for d in M['dependencies']}
COLOURS={'goal':('#e8f3ec','#245a3b'),'task':('#eaf1ff','#255ba2'),'quality':('#fff2d8','#916412'),'resource':('#fff','#546273'),'actor':('#edf0f5','#263852')}
def esc(v):return html.escape(str(v))

class Canvas:
 def __init__(self,w,h,name):
  self.w,self.h,self.name=w,h,name;self.shapes=[];self.edges=[];self.txt=[];self.svg=[]
 def text(self,x,y,s,size=20,colour='#223248',anchor='start',weight='normal'):
  self.txt.append(dict(x=x,y=y,s=s,size=size,colour=colour,anchor=anchor,weight=weight))
 def shape(self,id,type,label,x,y,w,h,fill=None,stroke=None):
  self.shapes.append(dict(id=id,type=type,label=label,x=x,y=y,w=w,h=h,fill=fill,stroke=stroke))
 def edge(self,id,points,type='dependency',label='',source=None,target=None,labelpos=None):
  self.edges.append(dict(id=id,points=points,type=type,label=label,source=source,target=target,labelpos=labelpos))
 def node(self,id,x,y,w=290,h=92):
  n=N[id];self.shape(id,n['type'],n['name'],x,y,w,h)
 def bbox(self,id):return next(s for s in self.shapes if s['id']==id)
 def point(self,id,side):
  n=self.bbox(id);x,y,w,h=[n[k] for k in ['x','y','w','h']]
  return {'top':(x+w/2,y),'bottom':(x+w/2,y+h),'left':(x,y+h/2),'right':(x+w,y+h/2)}[side]
 def write(self):
  head=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.name)}">'
  defs='''<defs>
   <marker id="dependency" markerWidth="18" markerHeight="18" refX="9" refY="9" orient="auto" markerUnits="userSpaceOnUse"><path d="M5,2 L5,16 C18,16 18,2 5,2" fill="white" stroke="#52667d" stroke-width="2"/></marker>
   <marker id="arrow" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto" markerUnits="userSpaceOnUse"><path d="M1,1 L12,7 L1,13 Z" fill="#52667d"/></marker>
   <marker id="and" markerWidth="16" markerHeight="16" refX="12" refY="8" orient="auto" markerUnits="userSpaceOnUse"><path d="M12,1 V15" stroke="#52667d" stroke-width="3"/></marker>
   <marker id="neededBy" markerWidth="16" markerHeight="16" refX="10" refY="8" orient="auto" markerUnits="userSpaceOnUse"><circle cx="9" cy="8" r="5" fill="white" stroke="#52667d" stroke-width="2"/></marker>
  </defs>'''
  parts=[head,defs,'<rect width="100%" height="100%" fill="#fff"/>']
  for s in self.shapes:
   if s['type']=='boundary':parts.append(self.svgshape(s))
  for e in self.edges:
   typ=e['type'];marker='dependency' if typ=='dependency' else 'and' if typ=='AND' else 'neededBy' if typ=='neededBy' else 'arrow'
   path='M '+' L '.join(f'{x},{y}' for x,y in e['points'])
   dash=' stroke-dasharray="4 5"' if typ=='qualification' else ''
   parts.append(f'<path id="{esc(e["id"])}" d="{path}" fill="none" stroke="#52667d" stroke-width="2.3"{dash} marker-end="url(#{marker})"/>')
   if e['label']:
    x,y=e['labelpos'] or e['points'][len(e['points'])//2]
    txt=esc(e['label']);ww=len(e['label'])*10+16
    parts.append(f'<rect x="{x-ww/2}" y="{y-17}" width="{ww}" height="23" fill="white"/>')
    parts.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="18" text-anchor="middle" fill="#42556b">{txt}</text>')
  for s in self.shapes:
   if s['type']!='boundary':parts.append(self.svgshape(s))
  for t in self.txt:
   parts.append(f'<text x="{t["x"]}" y="{t["y"]}" font-family="Arial, sans-serif" font-size="{t["size"]}" font-weight="{t["weight"]}" text-anchor="{t["anchor"]}" fill="{t["colour"]}">{esc(t["s"])}</text>')
  parts.append('</svg>');(P/f'{self.name}.svg').write_text('\n'.join(parts),encoding='utf-8')
 def svgshape(self,s):
  x,y,w,h=[s[k] for k in ['x','y','w','h']];typ=s['type'];label=s['label'];id=s['id']
  fill,stroke=COLOURS.get(typ,('#f8fafc','#8b9bad'));fill=s['fill'] or fill;stroke=s['stroke'] or stroke
  attrs=f'id="{esc(id)}" fill="{fill}" stroke="{stroke}" stroke-width="2.5"'
  if typ in ['goal','actor']:
   shape=f'<ellipse {attrs} cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}"/>'
  elif typ=='task':
   shape=f'<polygon {attrs} points="{x+22},{y} {x+w-22},{y} {x+w},{y+h/2} {x+w-22},{y+h} {x+22},{y+h} {x},{y+h/2}"/>'
  elif typ=='quality':
   shape=f'<path {attrs} d="M{x+w*.13},{y+h*.22} C{x-w*.03},{y+h*.08} {x-w*.06},{y+h*.72} {x+w*.12},{y+h*.78} C{x+w*.14},{y+h*1.05} {x+w*.39},{y+h*1.08} {x+w*.46},{y+h*.86} C{x+w*.7},{y+h*1.1} {x+w*.96},{y+h*.99} {x+w*.93},{y+h*.73} C{x+w*1.08},{y+h*.55} {x+w*1.04},{y+h*.12} {x+w*.87},{y+h*.22} C{x+w*.76},{y-h*.07} {x+w*.53},{y-h*.04} {x+w*.47},{y+h*.14} C{x+w*.32},{y-h*.1} {x+w*.13},{y-h*.01} {x+w*.13},{y+h*.22} Z"/>'
  else:
   shape=f'<rect {attrs} x="{x}" y="{y}" width="{w}" height="{h}" rx="{50 if typ=="boundary" else 0}"'+(' stroke-dasharray="12 9"' if typ=='boundary' else '')+'/>'
  if typ=='boundary':return shape
  size=22 if typ=='actor' else 21
  lines=textwrap.wrap(label,width=max(12,int((w-44)/(size*.53))),break_long_words=False)
  step=size*1.18;start=y+h/2-(len(lines)-1)*step/2+size*.33
  for i,l in enumerate(lines):shape+=f'<text x="{x+w/2}" y="{start+i*step}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size}" fill="#172a40">{esc(l)}</text>'
  if typ!='actor' and not id.startswith('key_'):shape+=f'<text x="{x+7}" y="{y-8}" font-family="Arial, sans-serif" font-size="15" fill="#65768a" stroke="white" stroke-width="3" paint-order="stroke">{esc(id)}</text>'
  return shape

def title(c,sub):
 c.text(55,65,'BRISTOL REGIONAL FOOD NETWORK',30,weight='bold')
 c.text(55,110,sub,27)
 c.text(55,150,'Sprint 2 • Draft for group review • 17 November 2026',19,colour='#66758a')
def legend(c,y):
 c.text(55,y,'READING KEY',22,weight='bold')
 for i,(typ,name) in enumerate([('actor','Actor'),('goal','Goal'),('task','Task'),('resource','Resource'),('quality','Quality / softgoal')]):
  c.shape('key_'+typ,typ,name,55+i*330,y+35,280,85)
 c.text(55,y+165,'D-shaped dependency markers point from the depender, through the dependum, to the dependee. This is dependency direction, not a message flow.',20)
 c.text(55,y+200,'SR: T-head = AND refinement; arrow = OR refinement; open circle = needed-by; help / hurt arrows express qualitative design judgements.',20)
 c.text(55,y+235,f'SD and SR use the same 5 actors and {len(D)} dependencies. F1/F2 are the operational focus; orders, finance, quality and community remain enterprise context.',20)

def sd():
 c=Canvas(2800,2500,'SD');title(c,'Strategic Dependency (SD) • Whole-enterprise relationships')
 positions={'producer':(70,570,220,220),'marketplace':(1270,900,260,260),'customer':(2510,570,220,220),'verifier':(70,1700,220,220),'payments':(2510,1700,220,220)}
 for a,p in positions.items():c.shape(a,'actor',A[a]['name'],*p)
 layout={}
 for i,d in enumerate(['D01','D02','D03','D04','D05','D06','D07','D18']):layout[d]=(630,280+i*145,340,88)
 for i,d in enumerate(['D08','D09','D10','D11','D12','D17','D19']):layout[d]=(1830,280+i*170,340,88)
 layout['D13']=(630,1730,340,100)
 for i,d in enumerate(['D14','D15','D16']):layout[d]=(1830,1580+i*170,340,100)
 def acentre(a):x,y,w,h=positions[a];return x+w/2,y+h/2,w/2,h/2
 def touch(a,pt):
  x,y,rx,ry=acentre(a);dx,dy=pt[0]-x,pt[1]-y;scale=math.sqrt((dx/rx)**2+(dy/ry)**2);return x+dx/scale,y+dy/scale
 for did,pos in layout.items():
  d=D[did];x,y,w,h=pos;c.shape(did,d['type'],d['name'],*pos)
  sc=acentre(d['depender']);tc=acentre(d['dependee']);left=(x,y+h/2);right=(x+w,y+h/2)
  ent=left if sc[0]<x else right;ext=left if tc[0]<x else right
  c.edge(did+'_a',[touch(d['depender'],ent),ent],source=d['depender'],target=did)
  c.edge(did+'_b',[ext,touch(d['dependee'],ext)],source=did,target=d['dependee'])
 c.text(1400,1770,'F1: D01 / D02 / D13',23,anchor='middle',weight='bold')
 c.text(1400,1810,'F2: D03 / D04 / D09',23,anchor='middle',weight='bold')
 c.text(1400,1860,'D13 applies when organic certification is claimed.',18,anchor='middle')
 c.text(1400,1890,'D11 / D17 apply when a concern is reported.',18,anchor='middle')
 legend(c,2140);c.write();return c

def sr():
 c=Canvas(5100,3570,'SR');title(c,'Strategic Rationale (SR) • Six enterprise capabilities and stakeholder rationale')
 bounds={'producer':(50,260,750,1420),'customer':(50,1810,750,1350),'marketplace':(1330,260,2440,2900),'verifier':(4300,260,750,1180),'payments':(4300,1850,750,1310)}
 for a,(x,y,w,h) in bounds.items():
  c.shape('boundary_'+a,'boundary','',x,y,w,h)
  c.shape(a,'actor',A[a]['name'],x+30,y+25,190,190)
 c.text(1660,345,'Marketplace rationale: each capability has its own achievement goal.',26,weight='bold')
 c.text(1660,389,'Actor-level dependencies retain the same meaning and IDs as the SD view.',22,colour='#66758a')
 # Six complete rationale groups in a two-column, three-row layout.
 for i,s in enumerate(M['sections']):
  ox=1420+(i%2)*1180;oy=510+(i//2)*850+(100 if i//2>0 else 0)
  c.text(ox,oy,s['title'],27,weight='bold')
  c.node(s['goal'],ox+340,oy+55,360,95)
  for j,t in enumerate(s['tasks']):c.node(t,ox+j*365,oy+255,315,105)
  alt=s.get('conditional_alternatives',[])
  for j,t in enumerate(alt):c.node(t,ox+285+j*275,oy+410,235,85)
  for j,q in enumerate(s['qualities']):c.node(q,ox+80+j*590,oy+(595 if alt else 500),370,95)
  c.node(s['resource'],ox+350,oy+(770 if alt else 690),350,88)
  ids={s['goal'],*s['tasks'],*s['qualities'],s['resource'],*alt}
  for l in M['links']:
   if l['source'] not in ids or l['target'] not in ids:continue
   typ=l['type'];source=l['source'];target=l['target']
   if typ=='refinement':
    p=c.point(source,'top');q=c.point(target,'bottom');mid=oy+(385 if source in alt else 192)
    points=[p,(p[0],mid),(q[0],mid),q];label=l['value'];labelpos=(q[0]+36,mid-13)
   elif typ=='neededBy':
    p=c.point(source,'left');q=c.point(target,'left');route=ox-28
    points=[p,(route,p[1]),(route,q[1]),q];label='needed-by';labelpos=(route+60,oy+640)
   else:
    p=c.point(source,'bottom');q=c.point(target,'top');points=[p,q];label=l['value'];labelpos=((p[0]+q[0])/2,(p[1]+q[1])/2)
   c.edge(l['id'],points,l.get('value') if typ=='refinement' else typ,label,source,target,labelpos)
  c.text(ox,oy+(895 if alt else 815),'Strategic: '+', '.join(s['strategy']),17,colour='#66758a')
 # Expanded rationale for every other actor.
 for a,layout in M['external_layout'].items():
  bx,by,bw,bh=bounds[a];g=layout['goal'];ts=layout['tasks'];q=layout['quality'];r=layout['resource']
  custom=layout.get('custom_positions')
  if custom:
   for nid,(x,y,w,h) in custom.items():c.node(nid,bx+x,by+y,w,h)
   ids=set(custom)
   for l in M['links']:
    if l['source'] not in ids or l['target'] not in ids:continue
    typ=l['type'];source=l['source'];target=l['target']
    if typ=='refinement':
     if source in ['PRODUCER_T4','PRODUCER_T3','CUSTOMER_T2']:
      pp=c.point(source,'top');qq=c.point(target,'bottom');pts=[pp,qq];lp=(pp[0]+34,(pp[1]+qq[1])/2)
     else:
      pp=c.point(source,'left');qq=c.point(target,'left');route=bx+231-(8 if source.endswith('T1') else 0)
      pts=[pp,(route,pp[1]),(route,qq[1]),qq];lp=(route-35,pp[1]-15)
     label=l['value']
    elif typ=='neededBy':
     pp=c.point(source,'top');qq=c.point(target,'left');route=pp[0]+(12 if target.endswith('T2') else 0)
     pts=[pp,(route,pp[1]),(route,qq[1]),qq];label='needed-by';lp=(route-8,(pp[1]+qq[1])/2-(30 if abs(pp[1]-qq[1])<40 else 0))
    else:
     pp=c.point(source,'bottom');qq=c.point(target,'top');label=l['value']
     if source=='CUSTOMER_T3':
      route=bx+710;mid=qq[1]-48
      pts=[pp,(route,pp[1]),(route,mid),(qq[0],mid),qq];lp=(route-27,mid-15)
     else:
      pts=[pp,qq];lp=((pp[0]+qq[0])/2+25,(pp[1]+qq[1])/2)
    c.edge(l['id'],pts,l.get('value') if typ=='refinement' else typ,label,source,target,lp)
   if a=='producer':c.text(bx+250,by+930,'Order branch: only after an order is accepted.',16,colour='#66758a')
   else:c.text(bx+250,by+900,'Concern branch: only when a concern is reported.',16,colour='#66758a')
   continue
  c.node(g,bx+245,by+90,450,110)
  starty=by+330;taskh=95;gap=165
  for j,t in enumerate(ts):c.node(t,bx+250,starty+j*gap,420,taskh)
  c.node(q,bx+250,by+bh-360,420,110)
  c.node(r,bx+250,by+bh-175,420,100)
  ids={g,*ts,q,r}
  for l in M['links']:
   if l['source'] not in ids or l['target'] not in ids:continue
   typ=l['type'];source=l['source'];target=l['target']
   if typ=='refinement':
    pp=c.point(source,'left');qq=c.point(target,'left');route=bx+238-7*ts.index(source)
    pts=[pp,(route,pp[1]),(route,qq[1]),qq];label=l['value'];lp=(route-36,pp[1]-15)
   elif typ=='neededBy':
    pp=c.point(source,'left');qq=c.point(target,'left');route=bx+70
    pts=[pp,(route,pp[1]),(route,qq[1]),qq];label='needed-by';lp=(route+80,(pp[1]+qq[1])/2)
   else:
    pp=c.point(source,'bottom');qq=c.point(target,'top');pts=[pp,qq];label=l['value'];lp=(pp[0]+35,(pp[1]+qq[1])/2)
   c.edge(l['id'],pts,l.get('value') if typ=='refinement' else typ,label,source,target,lp)
 # Actor-level dependencies are intentionally not assigned to an internal element.
 ypos={}
 for i,d in enumerate(['D01','D02','D03','D04','D05','D06','D07','D18']):ypos[d]=350+i*170
 for i,d in enumerate(['D08','D09','D10','D11','D12','D17','D19']):ypos[d]=1820+i*200
 ypos['D13']=720
 for i,d in enumerate(['D14','D15','D16']):ypos[d]=2100+i*260
 for did,y in ypos.items():
  d=D[did];other=d['depender'] if d['depender']!='marketplace' else d['dependee'];left=other in ['producer','customer']
  x=905 if left else 3870;w=320;h=100;c.shape(did,d['type'],d['name'],x,y,w,h)
  bound_outer=800 if left else 4300;bound_market=1330 if left else 3770
  outer=(bound_outer,y+h/2);market=(bound_market,y+h/2)
  a,b=(market,outer) if d['depender']=='marketplace' else (outer,market)
  entry=(x,y+h/2) if a[0]<x else (x+w,y+h/2);exit=(x,y+h/2) if b[0]<x else (x+w,y+h/2)
  c.edge(did+'_a',[a,entry],source='boundary_'+d['depender'],target=did)
  c.edge(did+'_b',[exit,b],source=did,target='boundary_'+d['dependee'])
 c.text(55,3220,'Boundary links intentionally refer to actors; no internal depender/dependee element is asserted. Rationale bindings are described in the model and traceability table.',21)
 legend(c,3280);c.write();return c

def drawio(canvases):
 root=E.Element('mxfile',host='app.diagrams.net',type='device')
 for c in canvases:
  page=E.SubElement(root,'diagram',id=c.name,name=c.name)
  model=E.SubElement(page,'mxGraphModel',dx='1000',dy='1000',grid='1',gridSize='10',guides='1',tooltips='1',connect='1',arrows='1',fold='1',page='1',pageScale='1',pageWidth=str(c.w),pageHeight=str(c.h))
  cells=E.SubElement(model,'root');E.SubElement(cells,'mxCell',id='0');E.SubElement(cells,'mxCell',id='1',parent='0')
  for s in c.shapes:
   typ=s['type'];fill,stroke=COLOURS.get(typ,('#f8fafc','#8b9bad'));shape={'goal':'ellipse','actor':'ellipse','task':'hexagon','quality':'cloud','resource':'rectangle','boundary':'rectangle'}[typ]
   style=f'shape={shape};whiteSpace=wrap;html=0;fillColor={s["fill"] or fill};strokeColor={s["stroke"] or stroke};fontSize=21;strokeWidth=2;fontFamily=Arial;'
   if typ=='boundary':style+='rounded=1;arcSize=10;dashed=1;fillOpacity=35;'
   label=s['label'] if typ in ['actor','boundary'] else s['id']+'\n'+s['label']
   cell=E.SubElement(cells,'mxCell',id=s['id'],value=label,style=style,vertex='1',parent='1')
   E.SubElement(cell,'mxGeometry',x=str(s['x']),y=str(s['y']),width=str(s['w']),height=str(s['h']),attrib={'as':'geometry'})
  for e in c.edges:
   marker={'dependency':'open','AND':'dash','neededBy':'oval'}.get(e['type'],'classic')
   style=f'edgeStyle=none;rounded=0;html=0;endArrow={marker};endFill=0;strokeColor=#52667d;strokeWidth=2;fontSize=17;labelBackgroundColor=#ffffff;'
   label=e['label'] if e['type']!='dependency' else 'D'
   attrs={}
   for end,ix,prop in [('source',0,'exit'),('target',-1,'entry')]:
    ref=e[end]
    if ref:
     box=c.bbox(ref);px,py=e['points'][ix]
     attrs[end]=ref
     style+=f'{prop}X={(px-box["x"])/box["w"]};{prop}Y={(py-box["y"])/box["h"]};{prop}Perimeter=0;'
   cell=E.SubElement(cells,'mxCell',id=e['id'],value=label,style=style,edge='1',parent='1',attrib=attrs)
   geo=E.SubElement(cell,'mxGeometry',relative='1',attrib={'as':'geometry'})
   p,q=e['points'][0],e['points'][-1]
   E.SubElement(geo,'mxPoint',x=str(p[0]),y=str(p[1]),attrib={'as':'sourcePoint'})
   E.SubElement(geo,'mxPoint',x=str(q[0]),y=str(q[1]),attrib={'as':'targetPoint'})
   if len(e['points'])>2:
    arr=E.SubElement(geo,'Array',attrib={'as':'points'})
    for x,y in e['points'][1:-1]:E.SubElement(arr,'mxPoint',x=str(x),y=str(y))
  for i,t in enumerate(c.txt):
   width=max(300,len(t['s'])*t['size']*.6);xx=t['x']-width/2 if t['anchor']=='middle' else t['x']
   cell=E.SubElement(cells,'mxCell',id=f'text_{i}',value=t['s'],style=f'text;html=0;whiteSpace=wrap;align=left;verticalAlign=middle;fontSize={t["size"]};fontColor={t["colour"]};fontFamily=Arial;fontStyle={1 if t["weight"]=="bold" else 0};',vertex='1',parent='1')
   E.SubElement(cell,'mxGeometry',x=str(xx),y=str(t['y']-t['size']),width=str(width),height=str(t['size']*1.4),attrib={'as':'geometry'})
 E.indent(root);E.ElementTree(root).write(P/'SD-SR.drawio',encoding='utf-8',xml_declaration=True)

if __name__=='__main__':
 canvases=[sd(),sr()];drawio(canvases)
 print('Rendered SD.svg, SR.svg and editable two-page SD-SR.drawio.')
