#!/usr/bin/env python3
"""Independent replay of explicit manuscript constructions and incidence fallback.
All transition tables below are transcribed from the mathematical statements,
not loaded from previous computational outputs.
"""
from __future__ import annotations
from collections import Counter
import itertools,json,subprocess,sys
from pathlib import Path
from validate_evidence import D,build
ROOT=Path(__file__).resolve().parents[1]

def total_table(s):
    return {(q,m):(next(d for d in range(4) if m>>d&1),0) for q in range(s) for m in range(1,16)}

def masks_of(d):return build(d,'-'*len(d))[1]

def next_tag(d,M,F,tag):
    v,q=tag;out,r=F[q,M[v]]
    if v<len(d) and D.index(d[v])==out:return v+1,r
    if v and (D.index(d[v-1])+2)%4==out:return v-1,r
    raise AssertionError(('illegal row',d,tag,F[q,M[v]]))

def orbit(d,F,start):
    M=masks_of(d);path=[];at={};tag=start
    while tag not in at:
        at[tag]=len(path);path.append(tag);tag=next_tag(d,M,F,tag)
    return path,at[tag]

def cycles(d,F,s):
    M=masks_of(d);done=set();result=[]
    for start in itertools.product(range(len(d)+1),range(s)):
        if start in done:continue
        path=[];at={};tag=start
        while tag not in at and tag not in done:
            at[tag]=len(path);path.append(tag);tag=next_tag(d,M,F,tag)
        if tag in at:result.append(path[at[tag]:])
        done.update(path)
    return result

def sharp_table(s):
    p=s-1;F=total_table(s)
    F[0,9]=(3,p);F[0,6]=(1,1)
    for i in range(1,p):F[i,9]=(0,i);F[i,6]=(2,i+1)
    F[p,9]=(0,0);F[p,6]=(2,0)
    if p==1:F[0,1]=(0,0)
    else:
        F[0,1]=(0,1)
        for i in range(2,p):F[i,1]=(0,i)
        F[p,1]=(0,0)
    F[0,4]=(2,0)
    for i in range(1,p):F[i,4]=(2,i+1)
    F[1,8]=(3,p)
    return F

def phase_table(phase):
    F=total_table(3)
    nw=[(2,2),(1,1),(1,0)] if phase==0 else [(2,2),(1,0),(1,1)]
    es=[(0,1),(3,2),(3,0)] if phase==0 else [(0,1),(3,0),(3,2)]
    for q in range(3):F[q,6]=nw[q];F[q,9]=es[q]
    F[1,5]=(0,1);F[2,5]=(2,2);F[2,1]=(0,1);F[1,4]=(2,2)
    return F

def brute(eq,n=4):
    return any(all((a&z).bit_count()%2==b for a,b in eq) for z in range(1<<n))

def gaussian(eq):
    basis={}
    for a,b in eq:
        while a:
            i=a.bit_length()-1
            if i not in basis:basis[i]=(a,b);break
            c,d=basis[i];a^=c;b^=d
        else:
            if b:return False
    return True

def pseudoforest(eq,n=4):
    adj=[set() for _ in range(n+len(eq))]
    for j,(a,b) in enumerate(eq):
        for v in range(n):
            if a>>v&1:adj[v].add(n+j);adj[n+j].add(v)
    seen=set();forest=True
    for v in range(len(adj)):
        if v in seen:continue
        stack=[v];seen.add(v);vertices=degree=0
        while stack:
            u=stack.pop();vertices+=1;degree+=len(adj[u])
            for w in adj[u]:
                if w not in seen:seen.add(w);stack.append(w)
        rank=degree//2-vertices+1
        if rank>1:return False,False
        if rank:forest=False
    return True,forest

def peel(eq,n=4):
    eq=[(set(i for i in range(n) if a>>i&1),b) for a,b in eq]
    while True:
        if any(not A and b for A,b in eq):return False
        eq=[(A,b) for A,b in eq if A]
        if not eq:return True
        unary=next(((next(iter(A)),b) for A,b in eq if len(A)==1),None)
        if unary:
            v,x=unary;eq=[(A-{v},b^x) if v in A else (A,b) for A,b in eq];continue
        count=Counter(v for A,b in eq for v in A)
        leaf=next((v for v,c in count.items() if c==1),None)
        if leaf is not None:
            eq=[(A,b) for A,b in eq if leaf not in A];continue
        # Every remaining component of a pseudoforest is a single cycle.
        assert all(len(A)==2 for A,b in eq) and all(c==2 for c in count.values())
        remaining=set(range(len(eq)))
        while remaining:
            seed=remaining.pop();stack=[seed];total=0
            while stack:
                i=stack.pop();A,b=eq[i];total^=b
                linked=[j for j in remaining if eq[j][0]&A]
                for j in linked:remaining.remove(j);stack.append(j)
            if total:return False
        return True

def main(data, exe):
    results={}
    sharp=[]
    for s in range(2,13):
        F=sharp_table(s)
        for n in range(3,71):
            d=''.join('EN'[j%2] for j in range(n-1));path,start=orbit(d,F,(0,0))
            expected=s*n-2 if n%2==0 else s*(n-1)
            assert start==0 and len(path)==expected
            load=Counter(v for v,q in path);assert all(load[v]==s for v in range(1,n-1))
            edge=Counter(min(path[i][0],path[(i+1)%len(path)][0]) for i in range(len(path)))
            assert all(edge[j]==2*(s-1 if d[j]=='E' else 1) for j in range(n-1))
            assert len(cycles(d,F,s))==1
            sharp.append({'s':s,'n':n,'period':len(path)})
    (data/'fresh_sharp_family.json').write_text(json.dumps(sharp,separators=(',',':'))+'\n')
    results['sharp_family']={'pairs':len(sharp),'s_range':[2,12],'n_range':[3,70],'mismatches':0}
    # Four incoming-port states; simultaneous absolute compass labels retained.
    F4={(q,m):(next(d for d in ((q+i)%4 for i in range(1,5)) if m>>d&1),0) for q in range(4) for m in range(1,16)}
    F4={key:(d,(d+2)%4) for key,(d,_) in F4.items()}
    count=0
    for n in range(2,9):
        for line in (data/f'fresh_n{n}.jsonl').open():
            r=json.loads(line)
            if set(r['p'])!={'-'}:continue
            cs=cycles(r['d'],F4,4);assert len(cs)==1 and len(cs[0])==2*(n-1)
            M=masks_of(r['d']);cset=set(cs[0])
            assert all(next_tag(r['d'],M,F4,tag) in cset for tag in itertools.product(range(n),range(4)))
            count+=1
    results['four_state_contours']={'geometries':count,'mismatches':0}
    phase_records=[]
    for lengths in itertools.product(range(1,5),repeat=3):
        d='N'.join('E'*l for l in lengths)
        for eta in itertools.product(range(2),repeat=2):
            p=list('-'*len(d))
            for j,e in enumerate(i for i,c in enumerate(d) if c=='N'):p[e]=str(eta[j])
            p=''.join(p)
            run=subprocess.run([str(exe),'--case',d,p],capture_output=True,text=True,check=True)
            record=json.loads(run.stdout);expected=eta[0]==eta[1]
            assert bool(record['exact'])==expected==bool(record['affine'])
            if expected:
                path,start=orbit(d,phase_table(eta[0]),(0,2));word=build(d,p)[0]
                assert start==0 and [v for v,q in path]==word
            phase_records.append({'d':d,'p':p,'realizable':expected})
    (data/'fresh_phase_family.json').write_text(json.dumps(phase_records,separators=(',',':'))+'\n')
    results['phase_locking_family']={'specifications':len(phase_records),'mismatches':0}
    U=total_table(3)
    for m,assign in {5:{0:(0,0),1:(2,1)},10:{1:(3,1),2:(1,2)},6:{0:(1,2),1:(2,1)},12:{0:(3,1),2:(2,1)},1:{1:(0,0)}}.items():
        for q,y in assign.items():U[q,m]=y
    count=0
    for a,b,c in itertools.product(range(2,6),range(3,7),range(2,6)):
        d='E'*a+'N'*b+'W'*c;path,start=orbit(d,U,(0,1));assert start==0 and [v for v,q in path]==build(d,'-'*len(d))[0];count+=1
    results['U_family']={'positive_cases':count,'mismatches':0}
    good=total_table(3);bad=total_table(3)
    for F in (good,bad):
        for m,values in {1:[(0,1),(0,1)],6:[(1,1),(2,2)],9:[(0,1),(3,2)],4:[(2,2),(2,2)]}.items():
            F[1,m],F[2,m]=values
    for m,y in {1:(0,1),6:(1,1),9:(0,1),4:(2,2)}.items():good[0,m]=y
    for m,y in {1:(0,0),6:(2,0),9:(0,0),4:(2,0)}.items():bad[0,m]=y
    cs_good=cycles('ENE',good,3);cs_bad=cycles('ENE',bad,3);assert len(cs_good)==1 and sorted(map(len,cs_bad))==[2,2,6]
    results['basin_separation']={'good_cycles':cs_good,'bad_cycles':cs_bad,'bad_pair_positions':[[0,2],[1,3]],'both_distances':2}
    num=ps=forest=0
    universe=list(itertools.product(range(16),range(2)))
    for k in range(5):
        for eq in itertools.combinations(universe,k):
            num+=1;fits,isforest=pseudoforest(eq)
            if not fits:continue
            ps+=1;forest+=isforest;assert peel(eq)==gaussian(eq)==brute(eq)
    assert (num,ps,forest)==(41449,23361,11714)
    results['forest_unicycle']={'all_systems':num,'pseudoforests':ps,'forests':forest,'mismatches':0}
    (data/'consequence_replay.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__ == '__main__':
    if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
    if len(sys.argv) != 3: raise SystemExit('Expected external data directory'+" and compiled oracle")
    data=Path(sys.argv[1]).resolve()
    if data.is_relative_to(ROOT.parents[1]): raise ValueError('Output must be outside the release')
    main(data, Path(sys.argv[2]).resolve())
