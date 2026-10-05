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
 for path in ['research','LICENSES']:shutil.copytree(ROOT/path,output/path)
 for path in ['CITATION.cff','citation.bib']:shutil.copy2(ROOT/path,output/path)
 for p in (ROOT/'public').iterdir():shutil.copy2(p,output/p.name)
 (output/'.nojekyll').write_text('')
 print('Built dist/ with only relative links; no network or installed packages required.')
if __name__=='__main__':build()
