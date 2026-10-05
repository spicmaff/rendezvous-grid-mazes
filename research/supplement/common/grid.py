#!/usr/bin/env python3
"""Exact induced-grid primitives used by independent release checks.
Coordinates and controller conventions agree with the frozen manuscript.
Enumeration keeps absolute orientation and quotients translation only.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
from itertools import combinations,product
import json
DIRS=((0,1),(1,0),(0,-1),(-1,0)); N,E,S,W=range(4)
LETTERS='NESW'

def add(a,b):return (a[0]+b[0],a[1]+b[1])
def norm(V):
    V=tuple(V); x=min(a for a,b in V);y=min(b for a,b in V)
    return tuple(sorted((a-x,b-y) for a,b in V))
def masks(V):
    ss=set(V)
    return tuple(sum(1<<d for d,v in enumerate(DIRS) if add(x,v) in ss) for x in V)
def mask(s):return sum(1<<LETTERS.index(a) for a in s)
def make_table(rows,states=2):
    T={(q,m):((m&-m).bit_length()-1,0) for q in range(states) for m in range(1,16)}
    for ms,actions in rows.items():
        for q,(d,r) in enumerate(actions):T[q,mask(ms)]=(LETTERS.index(d),r)
    return T

def phi(V,T,states=2):
    ix={x:i for i,x in enumerate(V)};mm=masks(V);out=[]
    for x,m in zip(V,mm):
        for q in range(states):
            d,r=T[q,m];assert m&(1<<d) and 0<=r<states
            out.append(states*ix[add(x,DIRS[d])]+r)
    return out

def pair_run(V,F,x,y,states=2,radius=1,qx=0,qy=0,trace=False):
    a=states*x+qx;b=states*y+qy;seen={};history=[]
    while (a,b) not in seen:
        va,vb=V[a//states],V[b//states]
        dist=abs(va[0]-vb[0])+abs(va[1]-vb[1])
        if dist<=radius:
            return {'success':True,'time':len(seen),'trace':history} if trace else True
        seen[a,b]=len(seen)
        if trace:history.append([a//states,a%states,b//states,b%states,dist])
        a,b=F[a],F[b]
    return {'success':False,'preperiod':seen[a,b],'period':len(seen)-seen[a,b], 'trace':history} if trace else False

def polyominoes(n):
    levels={1:{((0,0),)}}
    for k in range(2,n+1):
        new=set()
        for v in levels[k-1]:
            ss=set(v)
            for c in v:
                for d in DIRS:
                    x=add(c,d)
                    if x not in ss:new.add(norm((*v,x)))
        levels[k]=new
    return levels

def path_generator(n):
    """Second generator: extend only the end of a chordless self-avoiding walk."""
    ans={k:set() for k in range(1,n+1)}
    def rec(p,ss):
        ans[len(p)].add(norm(p))
        if len(p)==n:return
        for d in DIRS:
            x=add(p[-1],d)
            if x in ss:continue
            if sum(add(x,e) in ss for e in DIRS)!=1:continue
            rec(p+[x],ss|{x})
    rec([(0,0)],{(0,0)})
    return ans

def d4(g,x):
    a,b=x
    if g>=4:a=-a
    for _ in range(g%4):a,b=-b,a
    return a,b

def conjugate(T,g,states=2):
    dm=[DIRS.index(d4(g,d)) for d in DIRS]
    return {(q,sum(1<<dm[d] for d in range(4) if m&(1<<d))):(dm[d],r) for (q,m),(d,r) in T.items()}
