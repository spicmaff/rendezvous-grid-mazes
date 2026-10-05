#!/usr/bin/env python3
"""Lazy universal-completion validation of the frozen upper-proof predicates.
Each test is transcribed directly from section 5 / appendix A. The checker
branches only on physical controller rows queried by the complete execution.
A repeated full product tag is exact; there is no timeout horizon.
"""
from __future__ import annotations
from pathlib import Path
import json,sys,argparse
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from itertools import product
from common.grid import DIRS,LETTERS,N,E,S,W,mask,masks,add

def row(ms,q,acts):return {(q,mask(ms)):tuple((LETTERS.index(d),r) for d,r in acts)}
def fixed(ms,q,d,r):return row(ms,q,[(d,r)])
def direction(ms,q,d):return row(ms,q,[(d,0),(d,1)])
def frame(v=(0,1),h=(0,1)):
    return fixed('NS',0,'S',v[0])|fixed('NS',1,'N',v[1])|fixed('EW',0,'W',h[0])|fixed('EW',1,'E',h[1])
def endpoint(ms,q,r):return fixed(ms,q,ms,r)
def sc(d,k):return (DIRS[d][0]*k,DIRS[d][1]*k)
def L(d,e,a,b):return [(0,0)]+[sc(d,k) for k in range(1,a+1)]+[sc(e,k) for k in range(1,b+1)]
def U(d,e):return [(0,0),sc(e,1),sc(e,2),sc(d,1),sc(d,2),add(sc(e,2),sc(d,1)),add(sc(e,2),sc(d,2))]

def universal(V,starts,domains):
    V=tuple(V);ix={v:i for i,v in enumerate(V)};mm=masks(V);n=len(V)
    assert len(ix)==n and sum(m.bit_count() for m in mm)==2*(n-1)
    D={(q,m):tuple((d,r) for d in range(4) if m&(1<<d) for r in range(2)) for q in range(2) for m in set(mm)}
    D.update({k:v for k,v in domains.items() if k[1] in mm})
    for (q,m),acts in D.items():assert acts and all(m&(1<<d) for d,r in acts)
    assigned={};counter={'leaves':0,'branches':0};used=set();vis=set();counterexample=None
    def walk(a,b,seen):
        nonlocal counterexample
        if counterexample is not None:return
        local=[]
        while True:
            x,y=a//2,b//2
            vis.update((x,y))
            if abs(V[x][0]-V[y][0])+abs(V[x][1]-V[y][1])<=1:
                counterexample={'reached_product':[a,b],'partial_rows':{f'{q}:{m}':v for (q,m),v in assigned.items()}};break
            if (a,b) in seen:counter['leaves']+=1;break
            ka=(a%2,mm[x]);kb=(b%2,mm[y])
            missing=ka if ka not in assigned else kb if kb not in assigned else None
            if missing is not None:
                for action in D[missing]:
                    counter['branches']+=1;assigned[missing]=action;walk(a,b,seen)
                    if counterexample is not None:break
                del assigned[missing];break
            seen.add((a,b));local.append((a,b))
            da,qa=assigned[ka];db,qb=assigned[kb];xa=ix[add(V[x],DIRS[da])];yb=ix[add(V[y],DIRS[db])]
            used.add(tuple(sorted((x,xa))));used.add(tuple(sorted((y,yb))))
            a,b=2*xa+qa,2*yb+qb
        for pair in reversed(local):seen.remove(pair)
    walk(2*ix[starts[0]],2*ix[starts[1]],set())
    edges={tuple(sorted((i,ix[add(v,d)]))) for i,v in enumerate(V) for d in DIRS if add(v,d) in ix}
    cuts=[]
    for axis in range(2):
        for k in range(min(x[axis] for x in V),max(x[axis] for x in V)):
            crossing={e for e in edges if (V[e[0]][axis]<=k)!=(V[e[1]][axis]<=k)}
            if len(crossing)==1 and not crossing&used:cuts.append({'axis':'xy'[axis],'k':k,'crossing_edge':[V[i] for i in next(iter(crossing))]})
    return counter|{'counterexample':counterexample,'universally_unused_single_edge_cuts':cuts,'possibly_visited_cells':[V[i] for i in sorted(vis)],'possibly_used_edges':[[V[i],V[j]] for i,j in sorted(used)]}

def tests():
    tt=[]
    def test(name,ref,V,a,b,dom):tt.append((name,ref,V,(a,b),dom))
    # Equal direction rows on a vertical axis; horizontal follows by simultaneous transport.
    for d in (N,S):
        test('axis_equal_'+LETTERS[d],'5.2',U(d,E),sc(d,1),add(sc(E,2),sc(d,1)),direction('NS',0,LETTERS[d])|direction('NS',1,LETTERS[d]))
    line=lambda n:[(0,j) for j in range(n)]
    test('axis_toggle','5.2',line(6),(0,2),(0,4),frame((1,0)))
    test('axis_C0_R0','5.2',line(5),(0,0),(0,4),frame((0,0))|endpoint('S',0,1))
    test('axis_C1_L1','5.2',line(5),(0,1),(0,3),frame((1,1))|endpoint('N',1,0))
    for f in [(0,0),(0,1),(1,1),(1,0)]:
        test('axis_negative_'+str(f),'5.2',U(S,E),sc(S,1),add(sc(E,2),sc(S,1)),frame(f)|endpoint('N',f[0],0))
        test('axis_positive_'+str(f),'5.2',U(N,E),sc(N,2),add(sc(E,2),sc(N,2)),frame(f)|endpoint('S',0,1)|endpoint('S',f[1],1))
    for v,h in product(range(2),repeat=2):
        dv=S if v==0 else N;dh=W if h==0 else E
        test(f'both_reset_{v}{h}','5.3–5.4',L(dv,dh,3,3),sc(dv,2),sc(dh,2),frame((v,v),(h,h)))
    # C0/I sequence. Deliberately retain all unneeded free endpoint bits.
    b0=frame((0,0))|endpoint('N',0,1)|endpoint('E',0,1)
    test('mixed0_ES0_east','A.1',L(S,E,3,2),sc(S,2),(0,0),b0|direction('ES',0,'E'))
    test('mixed0_ES0_wrongbit','A.1',L(S,E,4,1),sc(S,4),(0,0),b0|fixed('ES',0,'S',1))
    b0=b0|fixed('ES',0,'S',0)
    uv=[(0,0),(0,1),(0,2),(1,2),(2,2),(2,1),(2,0)]
    test('mixed0_SW0_south','A.1',uv,(0,1),(2,1),b0|direction('SW',0,'S'))
    b0=b0|direction('SW',0,'W')
    test('mixed0_SW1_west','A.1',L(S,W,3,2),sc(S,3),sc(W,1),b0|direction('SW',1,'W'))
    test('mixed0_SW1_wrongbit','A.1',L(S,W,4,2),sc(S,4),sc(W,2),b0|fixed('SW',1,'S',1))
    test('mixed0_final','A.1',uv[:-1],(0,1),(2,1),b0|fixed('SW',1,'S',0))
    # C1/I sequence.
    b1=frame((1,1))|endpoint('E',0,1)
    test('mixed1_NW1_west','A.2',L(N,W,3,2),sc(N,2),sc(W,2),b1|direction('NW',1,'W'))
    test('mixed1_NW1_wrongbit','A.2',L(N,W,4,1),sc(N,3),sc(W,1),b1|fixed('NW',1,'N',0))
    b1=b1|fixed('NW',1,'N',1)
    test('mixed1_NE1_north','A.2',U(N,E),(0,1),(2,1),b1|direction('NE',1,'N'))
    b1=b1|direction('NE',1,'E')
    test('mixed1_NE0_east','A.2',L(N,E,3,2),sc(N,2),sc(E,2),b1|direction('NE',0,'E'))
    test('mixed1_NE0_wrongbit','A.2',L(N,E,4,2),sc(N,4),sc(E,2),b1|fixed('NE',0,'N',0))
    b1=b1|fixed('NE',0,'N',1)
    test('mixed1_final_s1_0','A.2',[(0,1),(0,0),(1,0),(2,0),(2,1),(2,2)],(0,0),(2,2),b1|endpoint('S',1,0))
    test('mixed1_final_s1_1','A.2',U(N,E),(0,0),(2,1),b1|endpoint('S',1,1))
    # Corner locking and four independent output-bit failures.
    bb=frame()|endpoint('N',0,1)|endpoint('E',0,1)|direction('NE',0,'E')
    test('locked_SW1','5.6',[(0,0),(1,0),(2,0),(0,1),(0,2),(-1,2),(-2,2)],(1,0),(-1,2),bb|direction('SW',1,'W'))
    test('locked_ES0','5.6',[(0,0),(1,0),(2,0),(0,1),(0,2),(1,2),(2,2)],(1,0),(1,2),bb|direction('ES',0,'E'))
    test('locked_ES1','5.6',U(S,E),(0,-1),(2,-1),bb|direction('SW',1,'S')|direction('ES',1,'S'))
    bb=bb|direction('ES',0,'S')|direction('ES',1,'E')|direction('SW',1,'S')
    test('bit_ES0','A.3',[(1,2),(0,2),(0,1),(0,0),(1,0),(2,0)],(0,0),(0,2),bb|fixed('ES',0,'S',1))
    test('bit_ES1','A.3',[(0,1),(0,2),(1,2),(2,2),(2,1),(2,0)],(0,1),(2,1),bb|fixed('ES',1,'E',0))
    test('bit_NE0','A.3',[(0,3),(0,2),(1,2),(2,2),(2,1),(2,0)],(1,2),(2,1),bb|fixed('NE',0,'E',0))
    test('bit_SW1','A.3',[(0,2),(1,2),(1,1),(1,0),(2,0),(3,0)],(0,2),(2,0),bb|fixed('SW',1,'S',1))
    good=frame()|endpoint('N',0,1)|endpoint('E',0,1)|fixed('NE',0,'E',1)|fixed('ES',0,'S',0)|fixed('ES',1,'E',1)|fixed('SW',1,'S',0)
    tail=[(1,0),(0,0),(0,1),(0,2),(1,2),(2,2),(2,1)]
    for w1 in range(2):
        for d,r in product(('N','E'),range(2)):
            if w1==1 and (d,r)==('N',1):continue
            test(f'tail_{w1}_{d}{r}','5.7',tail,(0,0),(2,1),good|endpoint('W',1,w1)|fixed('NE',1,d,r))
    w9=endpoint('N',0,1)|endpoint('E',0,1)|endpoint('W',1,1)|fixed('EW',1,'E',1)|fixed('NE',0,'E',1)|fixed('NE',1,'N',1)|fixed('ES',0,'S',0)|fixed('ES',1,'E',1)|fixed('SW',1,'S',0)
    G1=[(0,1),(1,0),(1,1),(1,2),(2,2),(2,0),(3,0)]
    G2=[(0,1),(1,0),(1,1),(1,2),(2,2),(3,1),(3,2)]
    choices=list(product(('N','S','W'),range(2)))
    for u,v,eps in product(choices,choices,range(2)):
        g2=(v==('S',0) or u==('S',0) and v in [('N',0),('W',1)])
        dom=w9|fixed('NSW',0,*u)|fixed('NSW',1,*v)|endpoint('E',1,eps)
        test(f'junction_{u}_{v}_{eps}_G{2 if g2 else 1}','5.8',G2 if g2 else G1,(1,0) if g2 else (0,1),(3,1) if g2 else (1,0),dom)
    return tt

def main(out):
    res=[]
    for name,ref,V,starts,dom in tests():
        rr=universal(V,starts,dom)
        rec={'name':name,'reference':ref,'cells':V,'starts':starts,'hypotheses':{f'{q}:{m}':x for (q,m),x in dom.items()},**rr}
        res.append(rec)
        if rr['counterexample'] is not None:
            out.joinpath('upper_symbolic_failure.json').write_text(json.dumps(rec,indent=2));raise AssertionError(name)
    out.joinpath('upper_symbolic_cases.json').write_text(json.dumps(res,indent=2))
    summary={'local_predicates_checked':len(res),'completion_tree_leaves':sum(x['leaves'] for x in res),'queried_row_branches':sum(x['branches'] for x in res),'counterexamples':0,'path_cases_without_one_common_unused_cut':[x['name'] for x in res if x['reference']!='5.8' and not x['universally_unused_single_edge_cuts']],'junction_cases':sum(x['reference']=='5.8' for x in res)}
    out.joinpath('upper_symbolic_output.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':
    if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=args.output.resolve()
    if out.is_relative_to(ROOT.parent):raise ValueError('Output must be outside the release')
    out.mkdir(parents=True,exist_ok=True);main(out)
