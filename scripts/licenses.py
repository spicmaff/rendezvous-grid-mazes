#!/usr/bin/env python3
"""Generate/check an exhaustive exact-path map without touching canonical sources."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'LICENSES/LICENSE_MAP.json'
def public_files():return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and not any(x in ['dist','.git','__pycache__'] for x in p.relative_to(ROOT).parts))
def generate():
 canonical=json.loads((ROOT/'research/LICENSES/LICENSE_MAP.json').read_text());rules=[];covered=set()
 for r in canonical['rules']:
  rule=dict(r);rule['id']='vendored-'+r['id'];rule['paths']=['research/'+p for p in r['paths']];rule['provenance']='Exact bytes; research/LICENSES/LICENSE_MAP.json';rules.append(rule);covered.update(rule['paths'])
 # Central exact membership rather than precedence/glob rules.
 groups={k:[] for k in ['new-code','new-prose-data','html-code-and-prose','license-map-documentation']}
 paths=public_files()
 if 'LICENSES/LICENSE_MAP.json' not in paths:paths.append('LICENSES/LICENSE_MAP.json')
 for p in sorted(paths):
  if p in covered:continue
  if p in ['site/index.html','site/app.mjs']:groups['html-code-and-prose'].append(p)
  elif p.startswith('LICENSES/'):groups['license-map-documentation'].append(p)
  elif p.endswith(('.py','.mjs','.css','.yml')) or p=='.gitignore':groups['new-code'].append(p)
  else:groups['new-prose-data'].append(p)
 for k,ps in groups.items():
  rules.append(dict(id=k,category=k,paths=ps,spdx_id='MIT' if k=='new-code' else 'MIT AND CC-BY-4.0' if k=='html-code-and-prose' else 'CC-BY-4.0',scope='HTML/JavaScript markup and UI behavior MIT; explanatory prose CC BY 4.0' if k=='html-code-and-prose' else 'New project authored materials'))
 M.write_text(json.dumps(dict(schema_version=1,matching='Exact relative paths only; every repository file has exactly one category; generated dist files inherit the corresponding input category.',rules=rules),indent=2)+'\n')
def check():
 m=json.loads(M.read_text());counts={}
 for r in m['rules']:
  for p in r['paths']:
   assert not Path(p).is_absolute() and '..' not in Path(p).parts
   counts[p]=counts.get(p,0)+1
 actual=set(public_files());assert set(counts)==actual,{'unmapped':sorted(actual-set(counts)),'missing':sorted(set(counts)-actual)};assert all(v==1 for v in counts.values())
 print('PASS_LICENSE_MAP:',len(counts),'files, exactly one category each. dist inherits input categories; .nojekyll is CC BY 4.0 empty generated metadata.')
if __name__=='__main__':
 if '--generate' in sys.argv:generate()
 check()
