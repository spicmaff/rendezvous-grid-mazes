#!/usr/bin/env python3
"""Independent physical semantics, CNF and RUP/LRAT release check.
No historical checker is imported. Exhaustion branches only on an actual
unassigned controller row. At every physical terminal cube the supplied DAG
is proved constant under that cube, not sampled at a default completion.
"""
from pathlib import Path
from collections import Counter
from itertools import combinations
import json,sys,hashlib,argparse
sys.dont_write_bytecode=True
if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from common.grid import masks,DIRS,pair_run,phi,norm
from common.lrat_rup import check as lrat_check, read_cnf
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();O=a.output.resolve()
if O.is_relative_to(ROOT.parent):raise ValueError('Output must be outside the release')
O.mkdir(parents=True,exist_ok=True)
C=Path(__file__).resolve().parent
B=C.parent/'basis144'
family=json.loads((B/'family.json').read_text())
minimum=json.loads((C/'family.json').read_text())
manifest=json.loads((C/'encoding_manifest.json').read_text())
legal={(s,m):tuple((d,t) for t in range(2) for d in range(4) if m>>d&1) for s in range(2) for m in range(1,16)}
results=[]

# Check the complete physical-to-normalized instance correspondence before encoding.
normalized=json.loads((B/'normalized_candidates.json').read_text())
family_hash=hashlib.sha256((B/'family.json').read_bytes()).hexdigest()
assert normalized['source_sha256']==family_hash==minimum['candidate_family_sha256']
assert minimum['candidate_family']=='../basis144/family.json'
assert minimum['candidate_lower_bound_certificate']==minimum['packing_lower_bound_certificate']=='packing.json'
assert minimum['coverage_certificate']=='escaping.lrat'
assert len(family['instances'])==144
assert [x['id'] for x in family['instances']]==[f'H{i:03}' for i in range(1,145)]
expected_normalized=[]
for inst in family['instances']:
    V=tuple(map(tuple,inst['cells']));n=len(V)
    assert V==norm(V) and len(set(V))==n and 2<=n<=7
    assert inst['cells']==inst['shape'] and inst['n']==inst['size']==n
    assert inst['initial_states']==[0,0]
    i,j=inst['start'];assert 0<=i<j<n
    assert [inst['cells'][i],inst['cells'][j]]==inst['starts']
    assert sum(abs(x-y) for x,y in zip(V[i],V[j]))>=2
    seen={V[0]};pending=[V[0]]
    while pending:
        x,y=pending.pop()
        for dx,dy in DIRS:
            p=x+dx,y+dy
            if p in V and p not in seen:seen.add(p);pending.append(p)
    assert len(seen)==n
    expected_normalized.append(dict(id=inst['id'],n=n,schemas=inst['schemas'],shape=inst['shape'],start=inst['start'],start_convention='ordered'))
assert normalized['instances']==expected_normalized
assert minimum['instances']==[family['instances'][i] for i in minimum['selected_candidate_indices_zero_based']]
assert minimum['candidate_count']==144 and minimum['certified_candidate_lower_bound']==44
assert len(manifest['functions'])==144 and len({x['id'] for x in manifest['functions']})==144

def physical_semantics(inst,dag):
    V=tuple(map(tuple,inst['shape'])); M=masks(V); idx={p:i for i,p in enumerate(V)}
    nxt={(i,d):idx[(x+dx,y+dy)] for i,(x,y) in enumerate(V) for d,(dx,dy) in enumerate(DIRS) if (x+dx,y+dy) in idx}
    nodes={n['id']:n for n in dag['nodes']}; nd={}
    assert len(nodes)==len(dag['nodes'])
    assert [n['id'] for n in dag['nodes']]==list(range(len(nodes)))
    assert dag['root']==len(nodes)-1 and dag['stats']['dag_nodes']==len(nodes)
    assert nodes[0]['kind']=='SUCCESS' and nodes[1]['kind']=='TRAP'
    for i,n in nodes.items():
        if n['kind']=='QUERY':
            k=(n['entry']['state'],n['entry']['mask']);ar={('NESW'.index(a['direction']),a['next_state']):a['child'] for a in n['arcs']}
            assert len(ar)==len(n['arcs']) and set(ar)==set(legal[k])
            assert all(j<i for j in ar.values()),'Not an acyclic bottom-up DAG'
            nd[i]=(k,ar)
        else: assert n['kind'] in ('SUCCESS','TRAP')
    T={};stats=Counter();mass=Counter()
    # Verify the entire DAG cofactor, including rows skipped by physical execution.
    def constant(node,want):
        stats['dag_cofactor_visits']+=1
        n=nodes[node]
        if n['kind']!='QUERY':
            assert (n['kind']=='TRAP')==want,(inst['id'],'semantic mismatch',dict(T));return
        k,ar=nd[node]
        if k in T:constant(ar[T[k]],want)
        else:
            for a,j in ar.items():T[k]=a;constant(j,want)
            del T[k]
    def recurse(pair,seen,weight):
        stats['physical_symbolic_calls']+=1
        while True:
            a,b=pair;v,q=a//2,a%2;w,r=b//2,b%2
            if abs(V[v][0]-V[w][0])+abs(V[v][1]-V[w][1])<=1:
                stats['success_cubes']+=1;mass['success']+=weight;constant(dag['root'],False);return
            if pair in seen:
                stats['trap_cubes']+=1;mass['trap']+=weight;constant(dag['root'],True);return
            # Agent 2 is deliberately queried first, unlike the supplied DAG.
            keys=[(r,M[w]),(q,M[v])]
            missing=next((k for k in keys if k not in T),None)
            if missing is not None:
                for act in legal[missing]:
                    T[missing]=act;recurse(pair,seen,weight//len(legal[missing]))
                del T[missing];return
            seen=seen|{pair};d,t=T[(q,M[v])];e,u=T[(r,M[w])]
            pair=(2*nxt[v,d]+t,2*nxt[w,e]+u);stats['product_steps']+=1
    domain=1
    for acts in legal.values():domain*=len(acts)
    recurse(tuple(2*x for x in inst['start']),frozenset(),domain)
    assert sum(mass.values())==domain
    return dict(stats),dict(mass)

# Independent atom enumeration, followed by exact clause-by-clause regeneration.
atoms=[];amap={};clauses=[];counter=0
for q in range(2):
    for m in range(1,16):
        group=[]
        for d in range(4):
            if not (m>>d&1):continue
            for r in range(2):
                counter+=1;amap[q,m,d,r]=counter;group.append(counter)
                atoms.append((counter,q,m,'NESW'[d],r))
        clauses.append(group)
        clauses.extend([-a,-b] for a,b in combinations(group,2))
assert atoms==[(a['dimacs'],a['state'],a['mask'],a['direction'],a['next_state']) for a in manifest['atoms']['atoms']]
assert counter==128
counter+=1;TRUE=counter;clauses.append([TRUE]);intern={};roots={};mf={a['id']:a for a in manifest['functions']}
for n,inst in enumerate(family['instances'],1):
    f=B/'functions'/f"{inst['id']}.json";dag=json.loads(f.read_text())
    assert mf[inst['id']]['file']=='../basis144/functions/'+f.name
    assert (C/mf[inst['id']]['file']).resolve()==f.resolve()
    assert mf[inst['id']]['dag_nodes']==len(dag['nodes'])
    assert dag['instance']=={k:normalized['instances'][n-1][k] for k in ('id','n','shape','start','start_convention')}
    assert dag['instance']['shape']==inst['cells'] and dag['instance']['start']==inst['start']
    assert dag['instance']['id']==inst['id'] and dag['instance']['n']==len(inst['cells'])
    assert hashlib.sha256(json.dumps({'root':dag['root'],'nodes':dag['nodes']},sort_keys=True,separators=(',',':')).encode()).hexdigest()==mf[inst['id']]['function_sha256']
    st,mass=physical_semantics(dag['instance'],dag)
    assert mass['trap']==mf[inst['id']]['trapped_controllers'] and mass['success']==mf[inst['id']]['escaping_controllers']
    lits={}
    for node in dag['nodes']:
        if node['kind']=='SUCCESS':lit=-TRUE
        elif node['kind']=='TRAP':lit=TRUE
        else:
            q,m=node['entry']['state'],node['entry']['mask']
            arc=tuple((amap[q,m,'NESW'.index(a['direction']),a['next_state']],lits[a['child']]) for a in node['arcs'])
            key=(q,m,arc)
            if key not in intern:
                counter+=1;intern[key]=counter
                for a,ch in arc:clauses.extend([[-a,-counter,ch],[-a,counter,-ch]])
            lit=intern[key]
        lits[node['id']]=lit
    roots[inst['id']]=lits[dag['root']]
    assert roots[inst['id']]==mf[inst['id']]['root_literal']
    results.append(dict(id=inst['id'],**st,**mass,dag_nodes=len(dag['nodes'])))
    if n%24==0:print('physical functions',n,flush=True)
assert len(clauses)==manifest['base_clauses'] and counter==manifest['variables']
selected=[x['id'] for x in minimum['instances']];assert len(set(selected))==44
clauses.extend([[-roots[i]] for i in selected])
cnf=C/'escaping.cnf';actual=[]
for line in cnf.open():
    if line.startswith('p'):assert list(map(int,line.split()[2:]))==[counter,len(clauses)]
    elif not line.startswith('c'):
        a=list(map(int,line.split()));assert a[-1]==0;actual.append(a[:-1])
assert actual==clauses,'CNF does not match physically validated functions'
print('All physical functions and CNF agree',flush=True)

# Byte-identical semantic CNF reconstruction precedes the formal checker.
regenerated='p cnf '+str(counter)+' '+str(len(clauses))+'\n'
regenerated+=''.join(' '.join(map(str,c))+' 0\n' for c in clauses)
(O/'reconstructed.cnf').write_text(regenerated,encoding='ascii')
assert (O/'reconstructed.cnf').read_bytes()==cnf.read_bytes()
assert (counter,len(actual))==(21049,146795)
assert manifest['distinct_encoded_root_literals']==len(set(roots.values()))==144
lrat=lrat_check(O/'reconstructed.cnf',C/'escaping.lrat')
assert lrat['additions']==1414 and lrat['empty_clause'] and lrat['rat_steps']==0
print('Physical semantics, normalized candidates, byte-exact CNF and LRAT/RUP agree',flush=True)

packing=json.loads((C/'packing.json').read_text());wresults=[];covered=set()
assert packing['candidate_family_sha256']==family_hash
assert packing['candidate_count']==144 and packing['lower_bound']==44
assert len(packing['witnesses'])==44 and len({w['id'] for w in packing['witnesses']})==44
for w in packing['witnesses']:
    T={}
    for e in w['controller']['entries']:
        key=e['state'],e['mask'];act='NESW'.index(e['direction']),e['next_state']
        assert key not in T and act in legal[key];T[key]=act
    assert len(T)==30
    # The simulator uses the same explicit (state,mask) row keys.
    TT={(q,m):a for (q,m),a in T.items()};bad=[]
    for inst in family['instances']:
        V=tuple(map(tuple,inst['cells']))
        ans=pair_run(V,phi(V,TT),*inst['start'])
        if not ans:bad.append(inst['id'])
    assert bad==w['trapped_candidate_ids'] and bad and not (set(bad)&covered)
    covered.update(bad);wresults.append(dict(id=w['id'],trapped=bad))
assert len(wresults)==44
# Independently check the included irredundancy witnesses as well; no solver involved.
irredundant=[]
for w in minimum['inclusion_irredundancy_witnesses']:
    T={}
    for e in w['controller']['entries']:
        key=e['state'],e['mask'];act='NESW'.index(e['direction']),e['next_state']
        assert key not in T and act in legal[key];T[key]=act
    assert len(T)==30
    bad=[]
    for inst in family['instances']:
        V=tuple(map(tuple,inst['cells']))
        if not pair_run(V,phi(V,T),*inst['start']):bad.append(inst['id'])
    assert bad==w['trapped_candidate_ids']
    assert set(bad)&set(selected)=={w['instance_id']}
    assert sorted(w['deleted_family_successes'])==sorted(set(selected)-{w['instance_id']})
    irredundant.append(w['instance_id'])
assert sorted(irredundant)==sorted(selected)
out=dict(physical_functions=results,physical_domain=manifest['legal_controllers'],cnf_variables=counter,cnf_clauses=len(actual),cnf_exact_match=True,selected_count=len(selected),lrat=lrat,packing_witnesses=wresults,packing_pairwise_disjoint=True,normalized_candidates_checked=144,irreducibility_witnesses_checked=len(irredundant),semantic_cnf_byte_identity=True,cnf_sha256=hashlib.sha256(cnf.read_bytes()).hexdigest(),status='PASS')
(O/'summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('physical_functions','packing_witnesses')},indent=2))
