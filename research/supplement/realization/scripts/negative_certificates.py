#!/usr/bin/env python3
"""Recompile and certify every normalized staircase profile, independently.
Binary rows are represented as (coefficient bitmask, right hand bit).
"""
from __future__ import annotations
import itertools,json,sys
from pathlib import Path
from validate_evidence import build
ROOT=Path(__file__).resolve().parents[1]

def xor_expr(A,B):
    return (A[0]^B[0],A[1]^B[1],A[2]^B[2])

def compile_staircase(a_es,k_nw,k_es,left,right):
    w,M,out,vis=build('ENENE','-0-1-');L=len(w)
    params={6:(2,1,k_nw),9:(0,a_es,k_es)}
    X=[None]*L;t={};groups={};eq=[];descriptions=[]
    for v,ids in enumerate(vis):
        if v in (0,5):
            for i in ids:X[i]=(left if v==0 else right,0,0)
            continue
        s,a,k=params[M[v]];b=next(x for x in (1,2,3) if x!=a);eps=0
        for i in ids:
            if out[i]==s:X[i]=(a,0,0)
            else:
                X[i]=(b^(a if eps else 0), (1<<(v-1)) if a&1 else 0, (1<<(v-1)) if a&2 else 0)
                t[i]=(eps,1<<(v-1));eps+=1
            groups.setdefault((M[v],out[i]),[]).append(i)
    # Complete S3 gauge is justified by fixing the first saturated frame.
    eq.append((1,0));descriptions.append('global state gauge z_1=0')
    for (m,d),ids in sorted(groups.items()):
        j=ids[0];s,a,k=params[m]
        for i in ids[1:]:
            c,a0,a1=xor_expr(X[(i+1)%L],X[(j+1)%L])
            if d!=s:
                ec=t[i][0]^t[j][0];coef=t[i][1]^t[j][1]
                c^=k if ec else 0
                if k&1:a0^=coef
                if k&2:a1^=coef
            for bit,coef in enumerate((a0,a1)):
                eq.append((coef,(c>>bit)&1));descriptions.append(f'mask={m}, direction={d}, visits={j},{i}, bit={bit}')
    return eq,descriptions

def contradiction(eq):
    basis={}
    for number,(a,b) in enumerate(eq):
        combination=1<<number
        while a:
            pivot=a.bit_length()-1
            if pivot not in basis:
                basis[pivot]=(a,b,combination);break
            c,d,comb=basis[pivot];a^=c;b^=d;combination^=comb
        else:
            if b:return [j for j in range(len(eq)) if combination>>j&1]
    raise AssertionError('a staircase profile unexpectedly has a solution')

def main(data):
    records=[]
    for parameters in itertools.product((1,2,3),repeat=5):
        eq,descriptions=compile_staircase(*parameters);cert=contradiction(eq)
        a=b=0
        for j in cert:a^=eq[j][0];b^=eq[j][1]
        assert (a,b)==(0,1)
        records.append({'a_ES':parameters[0],'k_NW':parameters[1],'k_ES':parameters[2],'left':parameters[3],'right':parameters[4],
                        'rows':eq,'row_descriptions':descriptions,'xor_certificate_indices':cert})
    assert len(records)==243
    (data/'fresh_staircase_certificates.json').write_text(json.dumps({'d':'ENENE','p':'-0-1-','a_NW':1,'z_1':0,'profiles':records},indent=2)+'\n')
    print(json.dumps({'profiles':len(records),'valid_xor_certificates':len(records),'mismatches':0}))
if __name__ == '__main__':
    if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
    if len(sys.argv) != 2: raise SystemExit('Expected external data directory'+"")
    data=Path(sys.argv[1]).resolve()
    if data.is_relative_to(ROOT.parents[1]): raise ValueError('Output must be outside the release')
    main(data)
