#!/usr/bin/env python3
"""Run every declared finite proof chain and validation in the standalone release.

Default is the full submission-level run; there is no silent quick/scoped mode.
Python >=3.10 and a GCC-compatible C++17 compiler are required. All products,
logs, temporary files and locally compiled code go to --output, never the release.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
if not __debug__:
    raise SystemExit('VERIFICATION_FAILED: assertions must be enabled; do not use python -O')
from pathlib import Path
import argparse,json,os,shutil,subprocess,platform
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from common.integrity import digest,snapshot,verify as verify_integrity,safe_file,require
from common.lrat_rup import self_test

STAGES=('integrity','rup_parser_selftest','path_certificate','upper_predicates',
        'basis_fragments_host','selected44_semantic_lrat_packing','universal_lower_bound',
        'realization_compile','realization_corpus','realization_witnesses',
        'staircase_certificates','realization_examples','construction_examples',
        'expected_outputs','frozen_inputs')

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True,help='New or empty directory outside the release')
    ap.add_argument('--cxx',default=os.environ.get('CXX','g++'),help='GCC-compatible C++17 compiler executable')
    a=ap.parse_args();out=a.output.resolve()
    if out.is_relative_to(ROOT.parent):raise ValueError('Output must be outside the release')
    if out.exists() and any(out.iterdir()):raise ValueError('Output must be new or empty; refusing stale outputs')
    out.mkdir(parents=True,exist_ok=True)
    report=dict(status='INCOMPLETE',completed_stages=[],missing_stages=list(STAGES),checks={})
    result=out/'verification.json'
    def save() -> None:
        result.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    def complete(name: str,details=None) -> None:
        require(name in STAGES and name not in report['completed_stages'],'Duplicate/unknown stage')
        report['completed_stages'].append(name);report['missing_stages'].remove(name)
        if details is not None:report['checks'][name]=details
        save();print(name+': PASS',flush=True)
    save()
    try:
        initial=verify_integrity(ROOT.parent);before=snapshot(ROOT.parent)
        artifact_map=json.loads((ROOT.parent/'manifests/PROOF_ARTIFACTS.json').read_text())
        required={'PATH_LOWER','SELECTED44','PACKING44','BASIS144','HOST172','U2_LOWER',
                  'REALIZATION_CORPUS','REALIZATION_WITNESSES','STAIRCASE_NAND','CONSTRUCTION_EXAMPLES'}
        require({x['id'] for x in artifact_map['claims']}==required,'Incomplete proof-artifact map')
        for c in artifact_map['claims']:
            require(c['checkers'] and c['artifacts'] and c['required_full_stage'],'Blank artifact-map chain')
            for name in c['checkers']+c['artifacts']:safe_file(ROOT.parent,name)
        complete('integrity',initial)
        test=self_test();(out/'rup_selftest.json').write_text(json.dumps(test,indent=2,sort_keys=True)+'\n')
        complete('rup_parser_selftest',test)
        logs=out/'logs';logs.mkdir()
        env=os.environ.copy();env.pop('PYTHONOPTIMIZE',None)
        env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',LC_ALL='C.UTF-8',TZ='UTC')
        for key,leaf in [('TMPDIR','tmp'),('HOME','home'),('XDG_CACHE_HOME','cache')]:
            path=out/leaf;path.mkdir();env[key]=str(path)
        def run(name: str,command: list[str]) -> None:
            with (logs/(name+'.log')).open('w') as stream:
                proc=subprocess.run(command,cwd=out,env=env,stdout=stream,stderr=subprocess.STDOUT)
            if proc.returncode:raise RuntimeError(name+' failed; see logs/'+name+'.log')
        py=sys.executable
        run('path_certificate',[py,'-B',str(ROOT/'paths/check.py'),str(out/'path_certificate.json')])
        p=json.loads((out/'path_certificate.json').read_text())
        require(p['far_pairs_through_7']==4042 and p['all_paths_through_7_succeed'],'Path count/result mismatch')
        require([p['path_shape_counts'][str(i)] for i in range(1,8)]==[1,2,6,14,34,82,198],'Path inventory mismatch')
        complete('path_certificate',dict(unordered_far_pairs=4042,failures=0,two_generators_equal=True))
        run('upper_predicates',[py,'-B',str(ROOT/'obstructions/basis144/upper_predicates.py'),'--output',str(out/'host')])
        pred=json.loads((out/'host/upper_symbolic_output.json').read_text())
        require(pred['local_predicates_checked']==116 and pred['counterexamples']==0,'Predicate coverage mismatch')
        complete('upper_predicates',pred)
        run('basis_fragments_host',[py,'-B',str(ROOT/'obstructions/universal_host/verify.py'),'--output',str(out/'host')])
        host=json.loads((out/'host/host_summary.json').read_text())
        require((host['fragments'],host['host']['vertices'],host['host']['edges'],host['host']['max_degree'])==(172,5212,5211,3),'Host counts differ')
        require(host['complete_transients_protected'] and host['all_saved_starts_far'] and host['first_extension_clearance']==8,'Host protection failed')
        complete('basis_fragments_host',dict(inventory=host['basis_counts'],fragments=172,host=host['host'],
                 all_saved_starts_far=True,complete_transients_protected=True,transport_cases=host['transport_cases'],extension_clearance=8))
        run('selected44_semantic_lrat_packing',[py,'-B',str(ROOT/'obstructions/selected44/verify.py'),'--output',str(out/'selected44')])
        cert=json.loads((out/'selected44/summary.json').read_text())
        require((cert['cnf_variables'],cert['cnf_clauses'],cert['selected_count'])==(21049,146795,44),'Certificate counts mismatch')
        require(len(cert['physical_functions'])==144 and cert['normalized_candidates_checked']==144,'Missing physical functions')
        require(cert['semantic_cnf_byte_identity'] and cert['packing_pairwise_disjoint'] and len(cert['packing_witnesses'])==44,'Semantic or packing replay incomplete')
        require(cert['lrat']['empty_clause'] and cert['lrat']['rat_steps']==0 and cert['lrat']['additions']==1414,'LRAT result mismatch')
        complete('selected44_semantic_lrat_packing',{k:v for k,v in cert.items() if k not in ('physical_functions','packing_witnesses')})
        run('universal_lower_bound',[py,'-B',str(ROOT/'obstructions/universal_lower_bound/verify.py'),'--output',str(out/'u2')])
        u=json.loads((out/'u2/summary.json').read_text())
        require(u['seven_cell_coverage_histogram']=={'0':594,'1':112,'2':52,'4':2} and u['max_coverage']==4 and u['all_smaller_failures']==0,'Universal lower bound mismatch')
        require(u['total_geometries']==1067 and u['all_eligible_pairs_tested'] and u['astar_matches_paper'],'Incomplete geometry replay')
        complete('universal_lower_bound',u)
        compiler=shutil.which(a.cxx)
        if compiler is None:raise RuntimeError('A GCC-compatible C++17 compiler is required')
        r=out/'realization';data=r/'data';binary=r/'bin/fresh_audit';data.mkdir(parents=True);binary.parent.mkdir()
        run('realization_compile',[compiler,'-std=c++17','-O3','-Wall','-Wextra','-Wpedantic',
                                  str(ROOT/'realization/scripts/fresh_audit.cpp'),'-o',str(binary)])
        complete('realization_compile',dict(source_included=True,standard='C++17'))
        run('realization_corpus',[str(binary),'8',str(data)])
        summary=json.loads((data/'fresh_summary.json').read_text())
        totals={k:sum(s[k] for s in summary['sizes']) for k in ('specifications','realizable','direction_rejections','residual_rejections','mismatches')}
        require(totals==dict(specifications=203260,realizable=94852,direction_rejections=105128,residual_rejections=3280,mismatches=0),'Realization corpus totals mismatch')
        require([s['n'] for s in summary['sizes']]==list(range(2,9)),'Realization horizon mismatch')
        for name in [f'fresh_n{i}.jsonl' for i in range(2,9)]+['fresh_summary.json']:
            require(digest(data/name)==digest(ROOT/'realization/data'/name),'Regenerated corpus differs: '+name)
        complete('realization_corpus',totals)
        run('realization_witnesses',[py,'-B',str(ROOT/'realization/scripts/validate_evidence.py'),str(data)])
        v=json.loads((data/'python_validation.json').read_text())
        require((v['specifications'],v['full_controllers'],v['profile_checks'],v['mismatches'])==(203260,189704,94852,0),'Witness validation totals mismatch')
        complete('realization_witnesses',v)
        run('staircase_certificates',[py,'-B',str(ROOT/'realization/scripts/negative_certificates.py'),str(data)])
        neg=json.loads((data/'fresh_staircase_certificates.json').read_text())
        require(len(neg['profiles'])==243,'Incomplete staircase profile enumeration')
        complete('staircase_certificates',dict(profiles=243,valid_xor_certificates=243))
        run('realization_examples',[py,'-B',str(ROOT/'realization/scripts/seam_probes.py'),str(data),str(binary)])
        nand=json.loads((data/'probe_saturated_nand8.json').read_text())
        require(nand['solutions']==20 and nand['projection']=={'00':12,'01':4,'10':4},'NAND validation mismatch')
        complete('realization_examples',dict(saturated_nand_solutions=20,projection={'00':12,'01':4,'10':4,'11':0},status='PASS'))
        run('construction_examples',[py,'-B',str(ROOT/'realization/scripts/consequence_replay.py'),str(data),str(binary)])
        cons=json.loads((data/'consequence_replay.json').read_text())
        complete('construction_examples',cons)
        expectations=json.loads((ROOT/'expected/replay_files.json').read_text())
        require(len(expectations['files'])>=30,'Incomplete frozen output expectations')
        comparisons=[]
        for e in expectations['files']:
            p=safe_file(out,e['output'])
            require(p.stat().st_size==e['bytes'] and digest(p)==e['sha256'],'Deterministic output mismatch: '+e['output'])
            if 'frozen' in e:
                require(digest(safe_file(ROOT.parent,e['frozen']))==e['sha256'],'Frozen expectation mismatch: '+e['frozen'])
            comparisons.append(dict(path=e['output'],sha256=e['sha256'],bytes=e['bytes']))
        (out/'output_comparison.json').write_text(json.dumps(dict(files=comparisons,status='PASS'),indent=2,sort_keys=True)+'\n')
        complete('expected_outputs',dict(byte_identical_files=len(comparisons)))
        require(snapshot(ROOT.parent)==before,'Frozen input files were modified')
        verify_integrity(ROOT.parent)
        complete('frozen_inputs',dict(unchanged=True))
        require(not report['missing_stages'] and tuple(report['completed_stages'])==STAGES,'Incomplete full verification')
        report['proof_claim_ids']=sorted(required)
        report['status']='PASS_FULL_REPRODUCIBILITY';save()
        environment=dict(python=platform.python_version(),platform=platform.system(),machine=platform.machine(),
                         compiler=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0])
        (out/'environment.json').write_text(json.dumps(environment,indent=2,sort_keys=True)+'\n')
        print('PASS_FULL_REPRODUCIBILITY',flush=True)
    except BaseException as exc:
        report['status']='FAILED'
        report['error']=str(exc).replace(str(ROOT.parent),'<release>').replace(str(out),'<output>')
        save();print('VERIFICATION_FAILED; missing stages: '+', '.join(report['missing_stages']),file=sys.stderr)
        raise

if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        print(str(exc),file=sys.stderr);sys.exit(1)
