#!/usr/bin/env python3
"""Deterministic, offline static-site build. Never writes into research/."""
from pathlib import Path
import shutil,subprocess,sys,json,hashlib
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
def build():
 subprocess.run([sys.executable,'-B',str(ROOT/'scripts/derive.py')],check=True)
 subprocess.run([sys.executable,'-B',str(ROOT/'scripts/visual_assets.py')],check=True)
 output=ROOT/'dist'
 if output.exists():shutil.rmtree(output)
 shutil.copytree(ROOT/'site',output)
 # Content versions survive normal reloads when Pages/CDN or browser caches are warm.
 # Keep file paths stable and relative; scientific sources are copied without edits.
 def version(name):return hashlib.sha256((output/name).read_bytes()).hexdigest()[:16]
 app=(output/'app.mjs').read_text()
 for name in ['model.mjs','motion.mjs']:
  app=app.replace("'./"+name+"'", "'./"+name+'?v='+version(name)+"'")
 (output/'app.mjs').write_text(app)
 html=(output/'index.html').read_text()
 html=html.replace('href="style.css"','href="style.css?v='+version('style.css')+'"')
 html=html.replace('src="app.mjs"','src="app.mjs?v='+version('app.mjs')+'"')
 (output/'index.html').write_text(html)
 for path in ['research','LICENSES']:shutil.copytree(ROOT/path,output/path)
 for path in ['CITATION.cff','citation.bib']:shutil.copy2(ROOT/path,output/path)
 for p in (ROOT/'public').iterdir():shutil.copy2(p,output/p.name)
 (output/'.nojekyll').write_text('')
 print('Built dist/ with only relative links; no network or installed packages required.')
if __name__=='__main__':build()
