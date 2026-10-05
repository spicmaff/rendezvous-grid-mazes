#!/usr/bin/env python3
"""Offline drift checks: claims, links, canonical labels, asset hashes, licenses."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote,parse_qs
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
class HTML(HTMLParser):
 def __init__(self):super().__init__();self.ids=set();self.claims=set();self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.add(a['id'])
  for k in ['data-claim','data-source']:
   if k in a:self.claims.add(a[k])
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
def main():
 p=HTML();p.feed((ROOT/'site/index.html').read_text());m=json.loads((ROOT/'public/claims.json').read_text());c={x['id']:x for x in m['components']}
 assert len(c)==len(m['components']);assert p.claims<=set(c),p.claims-set(c)
 app=(ROOT/'site/app.mjs').read_text()
 # Each runtime URL carries the content hash of its actual built bytes.
 built=(ROOT/'dist/index.html').read_text()
 for name in ['style.css','app.mjs']:
  url=re.search(r'(?:href|src)="('+re.escape(name)+r'\?v=[0-9a-f]+)"',built)
  assert url, 'Missing runtime version: '+name
  assert parse_qs(urlsplit(url[1]).query)['v']==[hashlib.sha256((ROOT/'dist'/name).read_bytes()).hexdigest()[:16]]
 for name in ['model.mjs','motion.mjs']:
  version=hashlib.sha256((ROOT/'dist'/name).read_bytes()).hexdigest()[:16]
  assert "'./"+name+'?v='+version+"'" in (ROOT/'dist/app.mjs').read_text()
 assert set(re.findall(r"sourceHTML\('([^']+)'\)",app))<=set(c)
 assert all(x['claim'] in c for x in json.loads((ROOT/'site/data/examples.json').read_text())['presets'])
 for x in c.values():
  for path in [x['paper_source'],*x['data_sources'],*x['semantic_sources']]:assert (ROOT/path).is_file(),path
 assert set(x['status'] for x in c.values())=={'DEDUCTIVE','COMPUTER_ASSISTED_CERTIFICATE','EXACT_FINITE_REPLAY','ILLUSTRATIVE_TOY','OPEN'}
 for link in p.links:
  u=urlsplit(link)
  if u.scheme:assert u.scheme=='https';continue
  if not u.path:
   target=u.fragment.split('?')[0];assert not target or target in p.ids,target
  else:assert not u.path.startswith('/');assert (ROOT/'dist'/unquote(u.path)).is_file(),link
 for a in json.loads((ROOT/'site/data/provenance.json').read_text())['assets']:
  assert hashlib.sha256((ROOT/a['asset']).read_bytes()).hexdigest()==a['derived_sha256'],a['asset']
  for s in a['source_files']:assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256'],s['path']
 config=json.loads((ROOT/'public/config.json').read_text());assert all(config[x]=='' or config[x].startswith('https://') for x in ['repository_url','arxiv_url','doi_url','journal_url'])
 for pth in ['site/index.html','site/app.mjs','site/style.css']:
  t=(ROOT/pth).read_text();assert 'ROUND' not in t and '/workspace/' not in t
 subprocess.run([sys.executable,'-B',str(ROOT/'scripts/licenses.py')],check=True)
 print('PASS_SHOWCASE_CHECKS: mapped claims, exact assets/source hashes, local links/fragments, central URLs and public copy.')
if __name__=='__main__':main()
