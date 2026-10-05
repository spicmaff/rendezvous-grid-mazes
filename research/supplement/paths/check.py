#!/usr/bin/env python3
"""Fresh frozen checker for G1. No imports from frozen.
Generates induced grid paths by recursive endpoint walk with a no-touch rule,
normalizes only by translation (absolute compass orientation is retained),
and exactly simulates the explicit two-state survivor controller.
"""
import json, sys
from pathlib import Path

DIRS = {"N":(0,1), "E":(1,0), "S":(0,-1), "W":(-1,0)}
DELTA_TO_NAME = {v:k for k,v in DIRS.items()}

def add(a,b): return (a[0]+b[0], a[1]+b[1])
def manhattan(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def norm_shape(points):
    minx=min(x for x,y in points); miny=min(y for x,y in points)
    return tuple(sorted((x-minx,y-miny) for x,y in points))

def generate_paths(max_n):
    # Every induced path has an endpoint ordering. Starting one endpoint at (0,0)
    # and extending without touching any earlier non-predecessor vertex enumerates it.
    shapes={1:{((0,0),)}}
    seqs=[((0,0),)]
    for n in range(2,max_n+1):
        new_seqs=[]; out=set()
        for seq in seqs:
            last=seq[-1]
            used=set(seq)
            for dv in DIRS.values():
                w=add(last,dv)
                if w in used: continue
                # Inducedness: new endpoint may be adjacent only to its predecessor.
                if any(manhattan(w,u)==1 for u in seq[:-1]):
                    continue
                ns=seq+(w,)
                new_seqs.append(ns)
                out.add(norm_shape(ns))
        seqs=new_seqs
        shapes[n]=out
    return shapes


def generate_connected_sets(max_n):
    # A second, structurally different completeness check: grow arbitrary connected
    # cell sets by adding any boundary cell, then filter induced graphs to paths.
    levels={1:{((0,0),)}}
    for n in range(2,max_n+1):
        out=set()
        for sh in levels[n-1]:
            S=set(sh); boundary=set()
            for p in S:
                for dv in DIRS.values():
                    q=add(p,dv)
                    if q not in S: boundary.add(q)
            for q in boundary:
                out.add(norm_shape(S|{q}))
        levels[n]=out
    return levels

def is_induced_path_shape(sh):
    if len(sh)==1: return True
    S=set(sh); deg=[]; twice_edges=0
    for p in S:
        d=sum(1 for dv in DIRS.values() if add(p,dv) in S)
        deg.append(d); twice_edges+=d
    edges=twice_edges//2
    return edges==len(S)-1 and max(deg)<=2 and sum(d==1 for d in deg)==2

def mask(shape,p):
    S=set(shape); names=[]
    for name,dv in DIRS.items():
        if add(p,dv) in S: names.append(name)
    return frozenset(names)

# Explicit frozen lower-bound controller, (direction,next state).
TABLE = {
 (frozenset(["N"]),0):("N",1), (frozenset(["N"]),1):("N",0),
 (frozenset(["E"]),0):("E",1), (frozenset(["E"]),1):("E",0),
 (frozenset(["S"]),0):("S",0), (frozenset(["S"]),1):("S",0),
 (frozenset(["W"]),0):("W",0), (frozenset(["W"]),1):("W",1),
 (frozenset(["N","S"]),0):("S",0), (frozenset(["N","S"]),1):("N",1),
 (frozenset(["E","W"]),0):("W",0), (frozenset(["E","W"]),1):("E",1),
 (frozenset(["N","E"]),0):("E",1), (frozenset(["N","E"]),1):("N",1),
 (frozenset(["E","S"]),0):("S",0), (frozenset(["E","S"]),1):("E",1),
 (frozenset(["N","W"]),0):("W",0), (frozenset(["N","W"]),1):("N",1),
 (frozenset(["S","W"]),0):("S",0), (frozenset(["S","W"]),1):("S",0),
}

def step(shape, tag):
    p,q=tag; M=mask(shape,p)
    d,qn=TABLE[(M,q)]
    return (add(p,DIRS[d]), qn)

def pair_succeeds(shape,x,y,rho=1):
    a=(x,0); b=(y,0); seen=set()
    while True:
        if manhattan(a[0],b[0])<=rho: return True
        key=(a,b)
        if key in seen: return False
        seen.add(key)
        a2=step(shape,a); b2=step(shape,b)
        a,b=a2,b2

def verify_p8():
    P=((1,0),(1,1),(0,1),(0,2),(0,3),(1,3),(2,3),(2,2))
    S=tuple(P)
    expected=[frozenset(x) for x in [
        ["N"],["S","W"],["N","E"],["N","S"],
        ["E","S"],["E","W"],["S","W"],["N"]]]
    got=[mask(S,p) for p in P]
    if got!=expected: raise AssertionError((got,expected))
    # W9 rows used by the hand proof.
    w9={(frozenset(["N"]),0):("N",1),
        (frozenset(["S","W"]),1):("S",0)}
    def wstep(tag):
        p,q=tag; M=mask(S,p); d,qn=w9[(M,q)]; return (add(p,DIRS[d]),qn)
    a=(P[0],0); b=(P[-1],0); orbit=[]
    for _ in range(4):
        orbit.append({"a":a,"b":b,"distance":manhattan(a[0],b[0]),
                      "mask_a":"".join(sorted(mask(S,a[0]))),
                      "mask_b":"".join(sorted(mask(S,b[0])))})
        if manhattan(a[0],b[0])!=3: raise AssertionError("P8 distance")
        a,b=wstep(a),wstep(b)
    if a!=(P[0],0) or b!=(P[-1],0): raise AssertionError("P8 period")
    return orbit

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: python3 paths/check.py EXTERNAL_OUTPUT_JSON")
    outpath=Path(sys.argv[1]).resolve()
    release=Path(__file__).resolve().parents[2]
    if outpath.is_relative_to(release): raise ValueError("Output must be outside the release")
    shapes=generate_paths(8)
    connected=generate_connected_sets(7)
    connected_paths={n:{sh for sh in connected[n] if is_induced_path_shape(sh)} for n in range(1,8)}
    for n in range(1,8):
        if connected_paths[n] != shapes[n]:
            raise AssertionError(("generator disagreement",n,len(connected_paths[n]),len(shapes[n])))
    counts={str(n):len(shapes[n]) for n in sorted(shapes)}
    far_counts={}; fail_counts={}; first_fails=[]
    for n in range(1,9):
        far=fail=0
        for sh in sorted(shapes[n]):
            pts=list(sh)
            for i in range(len(pts)):
                for j in range(i+1,len(pts)):
                    if manhattan(pts[i],pts[j])<=1: continue
                    far+=1
                    if not pair_succeeds(sh,pts[i],pts[j]):
                        fail+=1
                        if len(first_fails)<20:
                            first_fails.append({"n":n,"shape":sh,"start":[pts[i],pts[j]]})
        far_counts[str(n)]=far; fail_counts[str(n)]=fail
    if sum(far_counts[str(n)] for n in range(1,8))!=4042: raise AssertionError(far_counts)
    if any(fail_counts[str(n)] for n in range(1,8)): raise AssertionError(fail_counts)
    if fail_counts["8"]==0: raise AssertionError("expected 8-cell failure")
    orbit=verify_p8()
    result={
      "generator":"recursive endpoint walk; new endpoint forbidden to touch older non-predecessor vertices; translation normalization only",
      "independent_generator_crosscheck":"arbitrary connected-set growth through size 7, filtered by induced edge/degree conditions; exact shape sets agree",
      "path_shape_counts":counts,
      "initially_far_unordered_pair_counts":far_counts,
      "failed_unordered_pair_counts":fail_counts,
      "far_pairs_through_7":sum(far_counts[str(n)] for n in range(1,8)),
      "all_paths_through_7_succeed":True,
      "least_failure_size_in_scan":8,
      "p8_w9_two_row_orbit":orbit,
      "sample_failures":first_fails,
      "status":"PASS"
    }
    outpath.parent.mkdir(parents=True,exist_ok=True)
    outpath.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":
    if not __debug__: raise SystemExit("Assertions must be enabled; do not use -O")
    main()
