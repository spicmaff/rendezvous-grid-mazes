#!/usr/bin/env python3
"""Derive showcase assets solely from exact vendored research. Standard library only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,re,importlib.util
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'research';D=ROOT/'site/data'
def read(p):return json.loads((R/p).read_text())
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,R/p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
G=module('canonical_grid','supplement/common/grid.py');P=module('canonical_paths','supplement/paths/check.py')
sys.path.insert(0,str(R/'supplement/realization/scripts'))
V=module('validate_evidence','supplement/realization/scripts/validate_evidence.py')
C=module('consequence_replay','supplement/realization/scripts/consequence_replay.py')
provenance=[]
def write(name,obj,sources):
 data=(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode();p=D/name;p.write_bytes(data)
 provenance.append(dict(asset='site/data/'+name,source_files=[dict(path='research/'+s,sha256=hashlib.sha256((R/s).read_bytes()).hexdigest()) for s in sources],conversion_script='scripts/derive.py',derived_sha256=hashlib.sha256(data).hexdigest()))
def table(T,states):return [[[d,r] for m in range(1,16) for d,r in [T[q,m]]] for q in range(states)]
def from_entries(obj):return table({(e['state'],e['mask']):('NESW'.index(e['direction']),e['next_state']) for e in obj['entries']},obj.get('states',2))
astar=read('supplement/obstructions/universal_lower_bound/astar.json');atex=(R/'paper/sections/core_extremal.tex').read_text();block=atex.split('V_U=',1)[1].split('\\]',1)[0]
u=[list(map(int,p)) for p in re.findall(r'\((-?\d+),(-?\d+)\)',block)];assert len(u)==7
pathT=G.make_table({''.join(d for d in 'NESW' if d in m):[P.TABLE[m,q] for q in range(2)] for m,q in P.TABLE if q==0})
cert=read('supplement/expected/path_certificate.json');fail=cert['sample_failures'][0]
rotor={(q,m):(next(d for d in [(q+i)%4 for i in range(1,5)] if m>>d&1),0) for q in range(4) for m in range(1,16)};rotor={k:(d,(d+2)%4) for k,(d,_) in rotor.items()}
# Extract all five basin-table columns directly from the manuscript.
btex=(R/'paper/appendices/structural_consequences.tex').read_text().split('State 0, good',1)[1].split('\\end{tabular}',1)[0]
for a,b in [(r'\Sdir','S'),(r'\N','N'),(r'\E','E'),(r'\W','W')]:btex=btex.replace(a,b)
basins=[]
for good in (True,False):
 T=G.make_table({},states=3)
 for row in btex.splitlines():
  fields=row.split('&')
  if len(fields)!=5:continue
  ms=re.search(r'\$([NESW]+)\$',fields[0]);acts=[re.search(r'\(([NESW]),([012])\)',col) for col in fields[1:]]
  if not ms or not all(acts):continue
  for q,a in [(1,acts[0]),(2,acts[1]),(0,acts[2 if good else 3])]:T[q,G.mask(ms.group(1))]=('NESW'.index(a.group(1)),int(a.group(2)))
 basins.append(table(T,3))
examples={'presets':[
 dict(id='astar-u',label='A-star · exact seven-cell trap',claim='preset-astar',states=2,cells=u,starts=[[0,0],[2,0]],table=from_entries(astar),kind='Exact released witness'),
 dict(id='path8',label='Path survivor · exact eight-cell failure',claim='preset-path8',states=2,cells=fail['shape'],starts=fail['start'],table=table(pathT,2),kind='Exact released path witness; off-path rows legally completed'),
 dict(id='rotor',label='Four-state rotor · exact controller on a toy path',claim='four-state',states=4,cells=[[0,0],[1,0],[2,0],[2,1],[2,2],[3,2]],starts=[[0,0],[3,2]],table=table(rotor,4),kind='Exact paper controller; illustrative path geometry'),
 dict(id='toy-line',label='Compass priority · illustrative line',claim='toy',states=2,cells=[[i,0] for i in range(6)],starts=[[0,0],[5,0]],table=table(G.make_table({}),2),kind='Illustrative toy'),
 dict(id='basin-good',label='State-0 basin · exact accessible completion',claim='basin',states=3,cells=[[0,0],[1,0],[1,1],[2,1]],starts=[[0,0],[1,1]],table=basins[0],kind='Exact paper completion'),
 dict(id='basin-bad',label='State-0 basin · exact inaccessible completion',claim='basin',states=3,cells=[[0,0],[1,0],[1,1],[2,1]],starts=[[0,0],[1,1]],table=basins[1],kind='Exact paper completion')], 'path_certificate':{k:cert[k] for k in ['path_shape_counts','far_pairs_through_7','all_paths_through_7_succeed']}}
write('examples.json',examples,['paper/sections/core_extremal.tex','paper/sections/paths.tex','paper/appendices/structural_consequences.tex','supplement/obstructions/universal_lower_bound/astar.json','supplement/expected/path_certificate.json','supplement/paths/check.py','supplement/common/grid.py'])
family=read('supplement/obstructions/basis144/family.json');selected=read('supplement/obstructions/selected44/family.json');pack=read('supplement/obstructions/selected44/packing.json');sel={x['id'] for x in selected['instances']}
assert len(sel)==44 and sel<={x['id'] for x in family['instances']}
for i,x in zip(selected['selected_candidate_indices_zero_based'],selected['instances']):assert family['instances'][i]==x
write('family.json',dict(counts=family['counts'],instances=[dict(**{k:x[k] for k in ['id','cells','starts','size','geometry_id','orbit_id','schemas','graph_type','provenance']},selected=x['id'] in sel) for x in family['instances']],packing=[dict(id=w['id'],trapped=w['trapped_candidate_ids']) for w in pack['witnesses']]),['supplement/obstructions/basis144/family.json','supplement/obstructions/selected44/family.json','supplement/obstructions/selected44/packing.json'])
h=read('supplement/obstructions/universal_host/host.json');cells=h['cells'];ss={tuple(v) for v in cells};mm=G.masks(tuple(ss));edges=sum(m.bit_count() for m in mm)//2;seen={next(iter(ss))};pending=list(seen)
while pending:
 v=pending.pop()
 for d in G.DIRS:
  w=G.add(v,d)
  if w in ss and w not in seen:seen.add(w);pending.append(w)
assert len(cells)==len(ss)==5212 and edges==5211 and seen==ss and max(m.bit_count() for m in mm)==3
write('host.json',dict(cells=cells,stats=dict(vertices=len(ss),edges=edges,max_degree=3,connected=True,tree=True,fragments=len(h['pieces']),fragment_cells=2792,stalk_cells=990,rail_cells=1430),layout=h['layout'],pieces=[dict(id=p['id'],instance_id=p['instance_id'],cells=[[x+p['global_offset'][0],y+p['global_offset'][1]] for x,y in p['local_cells']],original_images=[[a['image'][0]+p['global_offset'][0],a['image'][1]+p['global_offset'][1]] for a in p['original_to_local']],starts=p['global_starts'],port=p['global_port'],method=p['method'],provenance=p['provenance']) for p in h['pieces']]),['supplement/obstructions/universal_host/host.json'])
real=[]
for name in ['saturated_nand8','staircase6']:
 path=f'supplement/realization/data/probe_{name}.json';r=read(path);w,M,out,vis=V.build(r['directions'],r['phases']);xy=[(0,0)]
 for ch in r['directions']:xy.append(G.add(xy[-1],G.DIRS['NESW'.index(ch)]))
 witnesses={}
 for q in r['witnesses']:
  V.controller_check(r['directions'],w,M,out,q)
  # x: NW west pair, y: ES east pair; probe uses these temporal paired roles.
  bits=''.join(str(int(q[a]!=q[b])) for mask,a,b in __import__('seam_probes').correspondence_pairs(w,M,out,vis))
  witnesses.setdefault(bits,q)
 real.append(dict(id=name,cells=xy,directions=r['directions'],phases=r['phases'],word=w,projection=r['projection'],witnesses=witnesses,solutions=r['solutions']))
write('realization.json',dict(examples=real),['supplement/realization/data/probe_saturated_nand8.json','supplement/realization/data/probe_staircase6.json','supplement/realization/scripts/validate_evidence.py','supplement/realization/scripts/seam_probes.py'])
# Cross-language vectors: every initially-far start pair through size seven.
vectors=[]
for n,shapes in P.generate_paths(7).items():
 for shape in sorted(shapes):
  if n<2:continue
  F=G.phi(shape,pathT)
  for i in range(n):
   for j in range(i+1,n):
    if P.manhattan(shape[i],shape[j])<=1:continue
    result=G.pair_run(shape,F,i,j,trace=True);assert result['success']
    if len(vectors)>=64:result.pop('trace')
    vectors.append(dict(cells=shape,starts=[shape[i],shape[j]],expected=result))
assert len(vectors)==4042
for p in examples['presets']:
 T={(q,m):tuple(p['table'][q][m-1]) for q in range(p['states']) for m in range(1,16)};shape=tuple(map(tuple,p['cells']));idx={v:i for i,v in enumerate(shape)}
 p['replay']=G.pair_run(shape,G.phi(shape,T,p['states']),*[idx[tuple(x)] for x in p['starts']],states=p['states'],trace=True)
# Update examples with source-checked initial-state replays.
provenance.pop(0);write('examples.json',examples,['paper/sections/core_extremal.tex','paper/sections/paths.tex','paper/appendices/structural_consequences.tex','supplement/obstructions/universal_lower_bound/astar.json','supplement/expected/path_certificate.json','supplement/paths/check.py','supplement/common/grid.py'])
write('vectors.json',dict(controller=table(pathT,2),cases=vectors),['supplement/paths/check.py','supplement/common/grid.py'])
(D/'provenance.json').write_text(json.dumps(dict(schema_version=1,assets=provenance),indent=2)+'\n')
print(f'Derived {len(provenance)} assets, {len(vectors)} canonical product vectors; host structural checks PASS.')
