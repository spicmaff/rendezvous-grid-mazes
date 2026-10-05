#!/usr/bin/env python3
"""Literal local-injection enumeration and adversarial seam regressions.
No previous-stage code is used. Imports only the independent validator.
"""
from __future__ import annotations
from collections import Counter
import itertools
import json
from pathlib import Path
import subprocess
import sys
from validate_evidence import D, build, rows, controller_check

ROOT = Path(__file__).resolve().parents[1]

def correspondence_pairs(w, masks, out, visits):
    by_mask = {}
    for v in range(1, len(visits) - 1):
        if len(visits[v]) == 3:
            doubled = next(d for d in range(4) if sum(out[i] == d for i in visits[v]) == 2)
            pair = [i for i in visits[v] if out[i] == doubled]
            by_mask.setdefault(masks[v], []).append(pair)
    return [(m, group[0][0], pair[0]) for m, group in sorted(by_mask.items()) for pair in group[1:]]

def relaxed(q, w, masks, out, visits):
    direction = {}
    sat_successor = {}
    for i, v in enumerate(w):
        key = q[i], masks[v]
        if key in direction and direction[key] != out[i]:
            return False
        direction[key] = out[i]
        if v not in (0, len(visits)-1) and len(visits[v]) == 3:
            y = q[(i+1) % len(w)]
            if key in sat_successor and sat_successor[key] != y:
                return False
            sat_successor[key] = y
    return True

def local_product(d, p, colors=3, collect=False, completion=False):
    w, masks, out, visits = build(d, p)
    if max(map(len, visits)) > colors:
        return dict(assignments=0, solutions=0, projection={}, relaxed_projection=[], witnesses=[])
    normal = 1 if len(visits)>2 else 0
    opts = [list(itertools.permutations(range(colors), len(ids))) for ids in visits]
    opts[normal] = [tuple(range(len(visits[normal])))]
    pairs = correspondence_pairs(w, masks, out, visits)
    checked = solutions = 0
    projection = Counter()
    relaxed_projection = set()
    witnesses = []
    for assignment in itertools.product(*opts):
        q = [0] * len(w)
        for ids, values in zip(visits, assignment):
            for i, x in zip(ids, values):
                q[i] = x
        checked += 1
        key = ''.join(str(int(q[a] != q[b])) for m, a, b in pairs)
        valid = rows(w, masks, out, q)[0] if colors==3 else generic_rows(w, masks, out, q, colors)
        if valid:
            solutions += 1
            projection[key] += 1
            if collect:
                witnesses.append(q)
        if completion and relaxed(q, w, masks, out, visits):
            relaxed_projection.add(key)
    return dict(assignments=checked, solutions=solutions, projection=dict(sorted(projection.items())), relaxed_projection=sorted(relaxed_projection), witnesses=witnesses,
                correspondence_masks=[m for m,a,b in pairs])

def generic_rows(w,masks,out,q,colors):
    if any(x not in range(colors) for x in q) or len(set(zip(w,q)))!=len(w):return False
    F={}
    for i,v in enumerate(w):
        key=(q[i],masks[v]);value=(out[i],q[(i+1)%len(w)])
        if key in F and F[key]!=value:return False
        F[key]=value
    return True

def two_state_criterion(d):
    w,M,out,visits=build(d,'-'*len(d));masks=sorted(set(M[1:-1]));idx={m:i for i,m in enumerate(masks)}
    for left,right in itertools.product(range(2),repeat=2):
        expr=[]
        for i,v in enumerate(w):
            if v==0:expr.append((0,left))
            elif v==len(M)-1:expr.append((0,right))
            else:
                ports=[j for j in range(4) if M[v]>>j&1]
                expr.append((1<<idx[M[v]],ports.index(out[i])))
        eq=[];anchors={}
        for i,v in enumerate(w):
            key=(M[v],out[i]) if v not in (0,len(M)-1) else (M[v],expr[i][1])
            if key in anchors:
                j=anchors[key];a,b=expr[(i+1)%len(w)];c,e=expr[(j+1)%len(w)];eq.append((a^c,b^e))
            else:anchors[key]=i
        basis={};ok=True
        for a,b in eq:
            while a:
                k=a.bit_length()-1
                if k not in basis:basis[k]=(a,b);break
                c,e=basis[k];a^=c;b^=e
            else:
                if b:ok=False;break
        if ok:return True
    return False

def main(data, exe):
    results={}
    # A third, literal product representation checks every specification below 6.
    totals=dict(specifications=0,assignments=0,mismatches=0,completion_projection_mismatches=0)
    for n in range(2,6):
        for line in (data/f'fresh_n{n}.jsonl').open():
            r=json.loads(line);b=local_product(r['d'],r['p'],completion=True)
            assert bool(b['solutions'])==bool(r['exact'])
            assert set(b['projection'])==set(b['relaxed_projection'])
            totals['specifications']+=1;totals['assignments']+=b['assignments']
    results['third_oracle_through_5']=totals
    for name,d,p in [('noncoset4','EEE','---'),('nand5','EEEE','----'),('completion6','ENENE','--0-0'),('staircase6','ENENE','-0-1-'),('one_double_unsat7','ENENEN','----0-'),('saturated_nand8','ENENNNE','0-0---0')]:
        r=local_product(d,p,collect=True,completion=name=='completion6')
        r['directions']=d;r['phases']=p
        if name in ('staircase6','one_double_unsat7'):assert r['solutions']==0
        if name=='saturated_nand8':assert r['projection']=={'00':12,'01':4,'10':4} and r['assignments']==279936
        if name=='completion6':assert set(r['projection'])=={'0'} and set(r['relaxed_projection'])=={'0','1'}
        if name=='nand5':
            w,M,out,vis=build(d,p);allowed=set()
            for q in r['witnesses']:
                if any(q[i]!=0 for i,v in enumerate(w) if v in (1,2,3) and out[i]==0):continue
                # Normal frame at vertex one fixes its W state to one.
                b=q[next(i for i in vis[2] if out[i]==2)]
                c=q[next(i for i in vis[3] if out[i]==2)]
                allowed.add(f'{b-1}{c-1}')
            assert allowed=={'00','01','10'};r['fixed_direction_projection']=sorted(allowed)
        if name=='noncoset4':
            w,M,out,vis=build(d,p);perms=set()
            for q in r['witnesses']:
                e=q[next(i for i in vis[2] if out[i]==0)];s=q[next(i for i in vis[2] if out[i]==2)]
                absent=next(x for x in range(3) if x not in (e,s));f=(e,s,absent)
                perms.add(tuple(f.index(x) for x in range(3)))
            assert perms=={(0,1,2),(0,2,1),(2,1,0)};r['relative_permutations']=sorted(perms)
        (data/f'probe_{name}.json').write_text(json.dumps(r,indent=2)+'\n')
        results[name]={k:v for k,v in r.items() if k!='witnesses'}
    # Endpoint-only successor conflict, while all internal constraints hold.
    d='ENNW';p='----';q=[0,0,0,0,0,1,1,1];w,M,out,vis=build(d,p)
    assert rows(w,M,out,q,True)[0] and not rows(w,M,out,q)[0]
    results['endpoint_omission']={'d':d,'p':p,'word':w,'q':q,'passes_without_endpoint_rows':True,'full_rows':False}
    # An excessive affine extension to an unobserved input produces zero.
    d='EEE';p='---';q=[1,0,0,0,1,1];w,M,out,vis=build(d,p);assert rows(w,M,out,q)[0]
    results['unused_output_zero_trap']={'d':d,'q':q,'Q_vectors':[x+1 for x in q],'singleton_E':1,'used_W_input':2,'used_W_output':2,'admissible_observational_kappa':2,'invented_unused_output':2^2,'legal_completion_exists':True}
    # Independent state renaming at one mask changes the constraints.
    d='EEEN';p='----';q=[1,0,0,0,1,1,1,1];w,M,out,vis=build(d,p);assert rows(w,M,out,q)[0]
    mutated=[(1-x if x in (0,1) else x) if M[v]==6 else x for v,x in zip(w,q)]
    assert not rows(w,M,out,mutated)[0]
    results['illegal_mask_state_gauge']={'d':d,'q':q,'mutated':mutated,'mask':6,'global_rows_after_local_rename':False}
    # Independent D4 standardization of each corner merges distinct inputs.
    d='ENE';p='---';q=[0,1,1,0,2,2];w,M,out,vis=build(d,p);assert rows(w,M,out,q)[0]
    normalized={};conflict=False
    for i,v in enumerate(w):
        if M[v] not in (6,9):continue
        rotation=-1 if M[v]==6 else 1;key=(q[i],3);direction=(out[i]+rotation)%4
        if key in normalized and normalized[key]!=direction:conflict=True
        normalized[key]=direction
    assert conflict
    results['illegal_independent_D4']={'d':d,'q':q,'actual_rows':True,'independently_rotated_corner_rows':False}
    # Matching is an explicit input requirement, not a solver convention.
    invalid=subprocess.run([str(exe),'--case','EN','00'],capture_output=True,text=True)
    assert invalid.returncode==1 and 'adjacent doubled' in invalid.stderr
    results['adjacent_doubles']={'d':'EN','p':'00','load_at_middle':4,'rejected_before_compilation':True,'message':invalid.stderr.strip()}
    # Spatially imprimitive, but tagged-simple: two distinct periods.
    d='E';p='0';q=[0,0,1,1];w,M,out,vis=build(d,p);controller_check(d,w,M,out,q)
    results['period_distinction']={'spatial_word':w,'states':q,'spatial_least_period':2,'tagged_least_period':4}
    # Shared global profile parameter: componentwise existential choice is invalid.
    candidates=(0,1);component1={t for t in candidates if t==0};component2={t for t in candidates if t==1}
    assert component1 and component2 and not component1&component2
    results['shared_profile_quantifier_test']={'type':'algebraic quantifier regression, not a newly claimed path counterexample','component1_profiles':sorted(component1),'component2_profiles':sorted(component2),'common_profiles':[]}
    # Direct finite replay of the two-state theorem on all absolute geometries.
    checked=0;negative=[]
    for n in range(2,9):
        for line in (data/f'fresh_n{n}.jsonl').open():
            r=json.loads(line)
            if set(r['p'])!={'-'}:continue
            result=bool(local_product(r['d'],r['p'],colors=2)['solutions'])
            assert result==two_state_criterion(r['d'])
            checked+=1
            if not result:negative.append(r['d'])
    assert checked==1612 and len(negative)==8 and all(len(d)==7 for d in negative)
    results['two_state_contours']={'geometries':checked,'negative':negative,'mismatches':0,'minimum_negative_vertices':8}
    (data/'seam_summary.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in results.items() if k in ('third_oracle_through_5','saturated_nand8','completion6','two_state_contours')},indent=2))

if __name__ == '__main__':
    if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
    if len(sys.argv) != 3: raise SystemExit('Expected external data directory'+" and compiled oracle")
    data=Path(sys.argv[1]).resolve()
    if data.is_relative_to(ROOT.parents[1]): raise ValueError('Output must be outside the release')
    main(data, Path(sys.argv[2]).resolve())
