#!/usr/bin/env python3
"""Deterministic SVG diagrams from the project's own exact grid language."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];S=R/'site';p=json.loads((S/'data/examples.json').read_text())['presets'][0];xy=p['cells'];ss={tuple(v) for v in xy}
def diagram(ox,oy,z):
 out='<g>'
 for x,y in xy:
  for dx,dy in [(0,1),(1,0)]:
   if (x+dx,y+dy) in ss:out+=f'<path d="M{ox+x*z} {oy-y*z}l{dx*z} {-dy*z}" stroke="#4e6361" stroke-width="3"/>'
 for x,y in xy:out+=f'<rect x="{ox+x*z-20}" y="{oy-y*z-20}" width="40" height="40" rx="4" fill="#dfe8e1" stroke="#afbeb4"/>'
 out+=f'<circle cx="{ox}" cy="{oy}" r="24" fill="#126967"/><rect x="{ox+2*z-24}" y="{oy-24}" width="48" height="48" rx="4" fill="#a54425"/>'
 out+=f'<g font-family="sans-serif" font-size="18" fill="#fffefa" text-anchor="middle"><text x="{ox}" y="{oy+6}">A</text><text x="{ox+2*z}" y="{oy+6}">B</text></g></g>'
 return out
hero='<svg xmlns="http://www.w3.org/2000/svg" width="520" height="320" viewBox="0 0 520 320">'+diagram(180,240,80)+'</svg>\n'
social='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#f5f3ec"/><path d="M65 75h1070M65 550h1070" stroke="#cbd2c9"/><g font-family="sans-serif" fill="#a54425" font-size="17" letter-spacing="3"><text x="65" y="120">FINITE MEMORY / RECURRENT GEOMETRY</text></g><g font-family="Georgia,serif" font-size="64" fill="#192c2c"><text x="65" y="220">Memory, Recurrent</text><text x="65" y="298">Geometry, and</text><text x="65" y="376">Rendezvous Traps</text></g><g font-family="sans-serif" fill="#4e6361" font-size="22"><text x="65" y="460">Michael Fofonov · Artem Antonchikov</text><text x="65" y="590">Exact grid models · Interactive constructions · Reproducible artifacts</text></g><rect x="790" y="150" width="345" height="350" fill="#e8eeea" stroke="#cbd2c9"/>'+diagram(870,425,85)+'</svg>\n'
favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="5" fill="#192c2c"/><path d="M7 25V7h18v18" stroke="#f5f3ec" stroke-width="3" fill="none"/><circle cx="7" cy="25" r="4" fill="#81d1c3"/><rect x="21" y="21" width="8" height="8" fill="#ffb094"/></svg>\n'
manifest=[]
for name,text in [('hero.svg',hero),('social-preview.svg',social),('favicon.svg',favicon)]:
 (S/name).write_text(text);manifest.append(dict(asset='site/'+name,source_files=[dict(path='site/data/examples.json',sha256=hashlib.sha256((S/'data/examples.json').read_bytes()).hexdigest())],conversion_script='scripts/visual_assets.py',derived_sha256=hashlib.sha256(text.encode()).hexdigest()))
path=S/'data/provenance.json';prov=json.loads(path.read_text());prov['assets'].extend(manifest);path.write_text(json.dumps(prov,indent=2)+'\n');print('Built deterministic hero, social preview and favicon SVGs.')
