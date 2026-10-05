#!/usr/bin/env python3
"""Regenerate the exact fixed-geometry conjugate coverage through seven cells.

Every connected induced grid set is generated up to translation only. For each
set, all eligible unordered state-zero start pairs are tested against each of
eight simultaneous compass conjugates. Stopping uses contact or a repeated full
product state, never a time cutoff. Agent exchange gives the ordered-pair case.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from common.grid import DIRS, norm, masks, phi, pair_run, polyominoes, conjugate
import argparse,json,hashlib,re
from collections import Counter
from itertools import combinations

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve()
    if out.is_relative_to(ROOT.parent):raise ValueError('Output must be outside the release')
    out.mkdir(parents=True,exist_ok=True)
    data=json.loads((Path(__file__).parent/'astar.json').read_text())
    T={}
    for e in data['entries']:
        key=e['state'],e['mask'];act='NESW'.index(e['direction']),e['next_state']
        assert key not in T and key[0] in (0,1) and 1<=key[1]<=15
        assert 0<=act[1]<2 and (key[1]>>act[0])&1
        T[key]=act
    assert len(T)==30 and data['initial_state']==0 and data['states']==2
    # Check the frozen controller against all thirty rows of the included paper.
    tex=(ROOT.parent/'paper/sections/core_extremal.tex').read_text()
    tex=tex.split(r'\begin{tabular}',1)[1].split(r'\end{tabular}',1)[0]
    replacements={r'\Sdir':'S',r'\N':'N',r'\E':'E',r'\W':'W'}
    for k,v in replacements.items():tex=tex.replace(k,v)
    paper_table={}
    for row in tex.splitlines():
        fields=row.split('&')
        if len(fields)!=4:continue
        ms=re.fullmatch(r'\s*\$([NESW]+)\$\s*',fields[1])
        if ms is None:continue
        m=sum(1<<'NESW'.index(d) for d in ms.group(1))
        for q,col in enumerate(fields[2:]):
            act=re.search(r'\(([NESW]),([01])\)',col)
            assert act is not None
            paper_table[q,m]=('NESW'.index(act.group(1)),int(act.group(2)))
    assert paper_table==T,'A-star data differs from manuscript controller table'
    Ts=[conjugate(T,g) for g in range(8)]
    assert len({tuple(sorted(t.items())) for t in Ts})==8
    levels=polyominoes(7)
    expected=[1,2,6,19,63,216,760]
    assert [len(levels[n]) for n in range(1,8)]==expected
    hist=Counter();stats=[];total_pairs=total_runs=0;cyclic_astar_traps=0
    output=out/'all_geometries.jsonl'
    with output.open('w',encoding='utf-8',newline='\n') as stream:
        for n in range(1,8):
            pairs_n=runs_n=astar_fail_n=0
            for number,V in enumerate(sorted(levels[n]),1):
                eligible=[(i,j) for i,j in combinations(range(n),2)
                          if sum(abs(x-y) for x,y in zip(V[i],V[j]))>1]
                functions=[phi(V,t) for t in Ts] if eligible else []
                pair_results=[];covered=set();counts=[0]*8;first={}
                for i,j in eligible:
                    trap_mask=0
                    for g,F in enumerate(functions):
                        success=pair_run(V,F,i,j)
                        runs_n+=1
                        if not success:
                            trap_mask|=1<<g;counts[g]+=1;covered.add(g);first.setdefault(g,[i,j])
                    pair_results.append([i,j,trap_mask])
                pairs_n+=len(eligible);astar_fail_n+=counts[0]
                if n<7:assert not covered,(n,V,'Unexpected sub-seven failure')
                if n==7:
                    hist[len(covered)]+=1
                    if counts[0] and sum(m.bit_count() for m in masks(V))>2*(n-1):cyclic_astar_traps+=1
                record=dict(n=n,index=number,cells=V,eligible_pair_count=len(eligible),
                            pair_trap_bitmasks=pair_results,conjugates_trapped=sorted(covered),
                            trapping_pair_counts=counts,first_trapping_pairs={str(g):first[g] for g in sorted(first)})
                stream.write(json.dumps(record,separators=(',',':'),sort_keys=True)+'\n')
            stats.append(dict(n=n,fixed_geometries=len(levels[n]),eligible_unordered_pairs=pairs_n,
                              exact_product_runs=runs_n,astar_trapping_pairs=astar_fail_n))
            total_pairs+=pairs_n;total_runs+=runs_n
    assert dict(hist)=={0:594,1:112,2:52,4:2}
    assert max(hist)==4 and stats[-1]['astar_trapping_pairs']==152
    assert cyclic_astar_traps>0
    result=dict(status='PASS',fixed_connected_counts=expected,conjugates=8,initial_state=0,
                complete_product_recurrence=True,all_eligible_pairs_tested=True,
                seven_cell_coverage_histogram={str(k):hist[k] for k in sorted(hist)},
                max_coverage=4,all_smaller_failures=0,by_size=stats,
                total_geometries=sum(expected),total_eligible_unordered_pairs=total_pairs,
                total_exact_product_runs=total_runs,seven_cell_cyclic_astar_trap_geometries=cyclic_astar_traps,
                coverage_file='all_geometries.jsonl',coverage_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                astar_matches_paper=True)
    (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':
    if not __debug__:raise SystemExit('Assertions must be enabled; do not use -O')
    main()
