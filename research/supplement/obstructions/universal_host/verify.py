#!/usr/bin/env python3
"""Independent extraction/counting and complete-transient portability check.
Uses primary JSON coordinates and fresh upper-proof predicates, not old checkers.
Every inverse-D4 source provenance is rebuilt from its matrix; states are untouched.
"""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,sys,hashlib,argparse
sys.dont_write_bytecode=True
if not __debug__:raise SystemExit('Assertions must be enabled; do not use -O')
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from common.grid import DIRS,masks,add,norm
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();O=a.output.resolve()
if O.is_relative_to(ROOT.parent):raise ValueError('Output must be outside the release')
O.mkdir(parents=True,exist_ok=True)
H=json.loads((ROOT/'obstructions/basis144/family.json').read_text())
U=json.loads((Path(__file__).parent/'host.json').read_text())
C=json.loads((O/'upper_symbolic_cases.json').read_text())

def tup(V):return tuple(map(tuple,V))
def minus(a,b):return (a[0]-b[0],a[1]-b[1])
def md(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])
def mm(A,x):return (A[0][0]*x[0]+A[0][1]*x[1],A[1][0]*x[0]+A[1][1]*x[1])
def norminst(V,S):
    V=tup(V);S=tup(S);off=(min(x for x,y in V),min(y for x,y in V))
    return tuple(sorted(minus(x,off) for x in V)),tuple(sorted(minus(x,off) for x in S))
def edges(V):
    v=set(V);return {tuple(sorted((p,add(p,d)))) for p in v for d in DIRS if add(p,d) in v}
def graphcheck(V):
    V=set(V);es=edges(V);todo=[next(iter(V))];seen=set(todo);deg=Counter()
    for a,b in es:deg[a]+=1;deg[b]+=1
    while todo:
        a=todo.pop()
        for d in DIRS:
            b=add(a,d)
            if b in V and b not in seen:seen.add(b);todo.append(b)
    assert seen==V
    return len(es),max(deg.values(),default=0)
leaves={x['id']:x for x in H['source_leaves']};instances={x['id']:x for x in H['instances']};transforms={x['name']:x for x in H['d4']}
assert len(leaves)==34 and len(instances)==144
for leaf in leaves.values():
    path,label=leaf['source'].split('#')
    source=ROOT.parent/path
    assert source.resolve().is_relative_to(ROOT.parent) and source.is_file()
    assert '\\label{'+label+'}' in source.read_text()
for path in U['proof_files']:
    assert (ROOT.parent/path).is_file()
allkeys={};source_maps={}
for leaf in leaves.values():
    assert leaf['initial_states']==[0,0]
    for g in transforms.values():
        A=g['inverse_matrix'];V=[mm(A,v) for v in leaf['cells']];S=[mm(A,s) for s in leaf['starts']]
        key=norminst(V,S);allkeys.setdefault(key,[]).append((leaf['id'],g['name']))
        off=(min(x for x,y in V),min(y for x,y in V))
        source_maps[leaf['id'],g['name']]={tuple(v):minus(mm(A,v),off) for v in leaf['cells']}
actual={norminst(x['cells'],x['starts']):x['id'] for x in instances.values()}
assert len(actual)==144 and set(actual)==set(allkeys)
for key,pr in allkeys.items():
    i=instances[actual[key]]
    assert i['initial_states']==[0,0] and len(set(i['start']))==2
    assert md(*tup(i['starts']))>=2
    assert sorted(pr)==sorted((x['leaf_id'],x['normalizer']) for x in i['provenance'])
    assert all(x['inverse_transform_matrix']==transforms[x['normalizer']]['inverse_matrix'] for x in i['provenance'])
    assert [tuple(i['cells'][j]) for j in i['start']]==list(tup(i['starts']))
    E,D=graphcheck(tup(i['cells']));assert E==len(i['cells'])-1 and D<=3
orbit=lambda V,S:min(norminst([mm(g['matrix'],x) for x in V],[mm(g['matrix'],x) for x in S]) for g in transforms.values())
geometries={k[0] for k in actual};orbits={orbit(*k) for k in actual}
geo_orbits={min(norm([mm(g['matrix'],x) for x in v]) for g in transforms.values()) for v in geometries}
counts=dict(source_records=len(leaves),distinct_normalized_instances=len({norminst(x['cells'],x['starts']) for x in leaves.values()}),before_dedup=len(leaves)*8,oriented_instances=len(actual),fixed_geometries=len(geometries),instance_orbits=len(orbits),geometry_orbits=len(geo_orbits),by_size=dict(Counter(len(k[0]) for k in actual)))
assert (counts['oriented_instances'],counts['fixed_geometries'],counts['instance_orbits'],counts['geometry_orbits'])==(144,76,22,13)

# Explicit correspondence from source leaves to the independently transcribed proof predicates.
correspondence={
'AX_EQUAL_S':['axis_equal_S'],'AX_EQUAL_N':['axis_equal_N'],'AX_TOGGLE':['axis_toggle'],
'AX_C0_RIGHT':['axis_C0_R0'],'AX_C1_LEFT':['axis_C1_L1'],
'AX_LEFT_CLONE':[x['name'] for x in C if x['name'].startswith('axis_negative_')],
'AX_RIGHT_CLONE':[x['name'] for x in C if x['name'].startswith('axis_positive_')],
'Z1_E':['mixed0_ES0_east'],'Z1_S1':['mixed0_ES0_wrongbit'],'Z2':['mixed0_SW0_south'],
'Z3_W':['mixed0_SW1_west'],'Z3_S1':['mixed0_SW1_wrongbit'],'Z4':['mixed0_final'],
'O1_W':['mixed1_NW1_west'],'O1_N0':['mixed1_NW1_wrongbit'],'O2':['mixed1_NE1_north'],
'O3_E':['mixed1_NE0_east'],'O3_N0':['mixed1_NE0_wrongbit'],'O4_S0':['mixed1_final_s1_0'],'O4_S1':['mixed1_final_s1_1'],
'LOCK_H_EW':['locked_SW1'],'LOCK_H_EE':['locked_ES0'],'LOCK_V_SS':['locked_ES1'],
'B_ES0':['bit_ES0'],'B_ES1':['bit_ES1'],'B_NE0':['bit_NE0'],'B_SW1':['bit_SW1'],
'W9_TAIL':[x['name'] for x in C if x['name'].startswith('tail_')],
'G1':[x['name'] for x in C if x['name'].endswith('_G1')],
'G2':[x['name'] for x in C if x['name'].endswith('_G2')]}
for v in range(2):
    for h in range(2):correspondence[f'RP_C{v}_C{h}']=[f'both_reset_{v}{h}']
assert set(correspondence)==set(leaves)
casebyname={x['name']:x for x in C};proof_cases=[];cutproof=[]
for lid,names in correspondence.items():
    L=leaves[lid];V=tup(L['cells']);lmin=(min(x for x,y in V),min(y for x,y in V))
    for name in names:
        c=casebyname[name];assert norminst(V,L['starts'])==norminst(c['cells'],c['starts']),(lid,name)
        w=tup(c['cells']);wmin=(min(x for x,y in w),min(y for x,y in w));shift=minus(lmin,wmin)
        visited={add(v,shift) for v in tup(c['possibly_visited_cells'])}
        used={tuple(sorted((add(tuple(e[0]),shift),add(tuple(e[1]),shift)))) for e in c['possibly_used_edges']}
        if lid not in ('G1','G2'):
            cut=U['source_cut_table'][lid];axis,k=cut['axis'],cut['k']
            cross={e for e in edges(V) if (e[0][axis]<=k)!=(e[1][axis]<=k)}
            assert len(cross)==1 and not cross&used,(lid,name,'cut used')
        else:
            gate=(2,2);JB=tuple(sorted(((1,1),(1,0))))
            if lid=='G2':assert gate not in visited
            else:assert gate not in visited or JB not in used
        proof_cases.append((lid,name,visited,used))
    if lid not in ('G1','G2'):cutproof.append(dict(leaf=lid,cut=U['source_cut_table'][lid],fresh_predicates=names,full_execution_unused=True))

# Validate each local fragment without trusting its recorded graph statistics.
pieces={x['id']:x for x in U['pieces']};source_piece=defaultdict(list);piece_results=[]
assert len(pieces)==len(U['pieces'])==172
assert U['piece_count']==172 and U['size']==5212 and U['edge_count']==5211
all_piece_cells=set();all_images=set();stalk=set();lastmax=None
for piece in U['pieces']:
    i=instances[piece['instance_id']];V=tup(i['cells']);assert tuple(tup(piece['original_cells']))==V
    local=set(tup(piece['local_cells']));assert len(local)==len(piece['local_cells'])
    e,d=graphcheck(local);assert e==len(local)-1 and d<=3
    tr=tuple(piece['local_origin_translation']);method=piece['method']
    image={tuple(x['original']):tuple(x['image']) for x in piece['original_to_local']}
    assert set(image)==set(V) and len(set(image.values()))==len(V)
    if method['kind']=='cut':
        axis,k=method['axis'],method['k'];assert method['width']==4
        expected={}
        for v in V:
            a=list(v);a[axis]+=4*(v[axis]>k);expected[v]=add(a,tr)
        assert image==expected
        cross={e for e in edges(V) if (e[0][axis]<=k)!=(e[1][axis]<=k)};assert len(cross)==1
        a,b=sorted(next(iter(cross)),key=lambda x:x[axis]);corridor=set()
        for j in range(1,5):
            v=list(a);v[axis]+=j;corridor.add(add(v,tr))
        assert corridor<=local
        extra=local-set(image.values())-corridor
        assert all(min(md(c,v) for v in image.values())>=2 for c in extra)
        exception=None
    else:
        assert method['kind']=='clean_boundary'
        assert image=={v:add(v,tr) for v in V}
        exception=tuple(method['gate']);assert exception in V
        assert tuple(piece['exceptional_unvisited_gate_image'])==image[exception]
        extra=local-set(image.values())
        assert all(min(md(c,image[v]) for v in V if v!=exception)>=2 for c in extra)
    local_masks=dict(zip(local,masks(tuple(local))))
    for v,m in zip(V,masks(V)):
        if v!=exception:assert local_masks[image[v]]==m,(piece['id'],v)
    assert tuple(map(image.get,tup(i['starts'])))==tup(piece['local_starts'])
    assert all(p in local for p in tup(piece['local_starts'])) and md(*tup(piece['local_starts']))>=2
    port=tuple(piece['local_port']);assert port in local
    offset=tuple(piece['global_offset']);glob={add(v,offset) for v in local}
    xmin,xmax=min(x for x,y in glob),max(x for x,y in glob)
    if lastmax is not None:assert xmin-lastmax==3
    lastmax=xmax
    assert not glob&all_piece_cells;all_piece_cells|=glob
    all_images|={add(v,offset) for v in image.values()}
    gport=add(port,offset);assert list(gport)==piece['global_port']
    assert [list(add(v,offset)) for v in tup(piece['local_starts'])]==piece['global_starts']
    assert all(p in glob for p in tup(piece['global_starts'])) and md(*tup(piece['global_starts']))>=2
    stalk|={(gport[0],y) for y in range(gport[1]+1,U['layout']['rail_y'])}
    for pr in piece['provenance']:
        assert pr in i['provenance']
        lid,g=pr['leaf_id'],pr['normalizer'];A=transforms[g]['inverse_matrix'];sm=source_maps[lid,g]
        if method['kind']=='cut':
            cut=U['source_cut_table'][lid];oldcross={e for e in edges(tup(leaves[lid]['cells'])) if (e[0][cut['axis']]<=cut['k'])!=(e[1][cut['axis']]<=cut['k'])}
            assert {tuple(sorted((sm[a],sm[b]))) for a,b in oldcross}==cross
        else:
            assert lid in ('G1','G2') and sm[(2,2)]==exception
            assert tuple(method['direction'])==mm(A,(0,1))
        source_piece[lid,g].append(piece['id'])
    piece_results.append(dict(id=piece['id'],kind=method['kind'],cells=len(local),edges=e,max_degree=d,provenances=len(piece['provenance']),all_original_masks_preserved=exception is None))
rail={(x,U['layout']['rail_y']) for x in range(U['layout']['rail_xmin'],U['layout']['rail_xmax']+1)}
assert not rail&stalk and not rail&all_piece_cells and not stalk&all_piece_cells
computed=all_piece_cells|stalk|rail;stored=set(tup(U['cells']))
assert computed==stored and len(stored)==len(U['cells'])
E,D=graphcheck(computed);assert (len(computed),E,D)==(5212,5211,3)
assert (len(all_piece_cells),len(stalk),len(rail))==(2792,990,1430)
# Only one stalk-neighbor at each port, and no other foreign-fragment contacts.
for piece in U['pieces']:
    off=tuple(piece['global_offset']);local={add(v,off) for v in tup(piece['local_cells'])};port=tuple(piece['global_port'])
    foreign={(a,add(a,d)) for a in local for d in DIRS if add(a,d) in computed-local}
    assert foreign=={(port,add(port,(0,1)))},(piece['id'],foreign)

# For every predicate and inverse compass transport, one fixed fragment protects
# the entire (union of all legal completions') transient and recurrent execution.
gmask=dict(zip(computed,masks(tuple(computed))));transport_results=[]
for lid,name,visited,used in proof_cases:
    for g in transforms:
        sm=source_maps[lid,g];protected=[]
        for pid in source_piece[lid,g]:
            piece=pieces[pid];method=piece['method'];off=tuple(piece['global_offset'])
            im={tuple(a['original']):add(tuple(a['image']),off) for a in piece['original_to_local']}
            V=tup(instances[piece['instance_id']]['cells']);vm=dict(zip(V,masks(V)))
            if method['kind']=='clean_boundary' and tuple(method['gate']) in {sm[v] for v in visited}:continue
            if method['kind']=='cut':
                ax,k=method['axis'],method['k']
                if any((sm[a][ax]<=k)!=(sm[b][ax]<=k) for a,b in used):continue
            assert all(gmask[im[sm[v]]]==vm[sm[v]] for v in visited)
            assert all(minus(im[sm[b]],im[sm[a]])==minus(sm[b],sm[a]) for a,b in used)
            assert all(md(im[sm[a]],im[sm[b]])>=md(a,b) for a,b in combinations(visited,2))
            protected.append(pid)
        assert protected,(lid,name,g,'no protected fixed fragment')
        transport_results.append(dict(leaf=lid,predicate=name,normalizer=g,protected_piece_ids=protected))

first=(U['layout']['rail_xmax']+1,U['layout']['rail_y']);assert min(md(first,v) for v in all_images)==8
assert {add(first,d) for d in DIRS}&computed=={(first[0]-1,first[1])}
assert all(v[0]<first[0] for v in all_images) # all further ray distances increase by length.
for length in [1,2,8,100,1000]:
    ext=computed|{(first[0]+j,first[1]) for j in range(length)};ee,dd=graphcheck(ext)
    assert len(ext)==5212+length and ee==len(ext)-1 and dd==3
out=dict(status='PASS',all_saved_starts_far=True,source_provenance_links_checked=34,basis_counts=counts,primitive_predicates=30,source_case_links={k:v for k,v in correspondence.items()},source_cuts=cutproof,pieces=piece_results,fragments=len(pieces),fragment_kinds=dict(Counter(x['kind'] for x in piece_results)),host=dict(vertices=len(computed),edges=E,max_degree=D,connected=True,acyclic=True,fragment_cells=len(all_piece_cells),stalk_cells=len(stalk),rail_cells=len(rail)),transport_cases=len(transport_results),complete_transients_protected=True,first_extension_cell=first,first_extension_clearance=8,extension_samples=[1,2,8,100,1000])
(O/'host_summary.json').write_text(json.dumps(out,indent=2))
(O/'portability_transport_cases.json').write_text(json.dumps(transport_results,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ('source_case_links','source_cuts','pieces')},indent=2))
