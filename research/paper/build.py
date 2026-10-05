#!/usr/bin/env python3
"""Build the frozen paper from source, writing only to an external directory.

Usage: python3 paper/build.py --output /absolute/new/directory --check-canonical
Requires Python >=3.10, pdfLaTeX and BibTeX8 (or BibTeX). No network is used.
The fixed source date, omitted PDF dates/trailer ID and fixed relative TeX input
paths make the PDF byte reproducible with the documented TeX toolchain.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot() -> dict:
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file()}

def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--check-canonical',action='store_true')
    args=ap.parse_args();out=args.output.resolve()
    if out.is_relative_to(ROOT.parent):raise ValueError('Build output must be outside the release')
    if out.exists() and any(out.iterdir()):raise ValueError('Build output must be new or empty')
    tools={}
    for name,choices in [('pdflatex',['pdflatex']),('bibtex',['bibtex8','bibtex','bibtex.original'])]:
        selected=next((shutil.which(c) for c in choices if shutil.which(c)),None)
        if selected is None:raise RuntimeError('Missing system tool: '+name)
        tools[name]=selected
    before=snapshot();out.mkdir(parents=True,exist_ok=True)
    src=out/'source';aux=out/'build';logs=out/'logs'
    src.mkdir();aux.mkdir();logs.mkdir()
    for p in sorted(ROOT.rglob('*')):
        if p.is_file() and p.suffix in ('.tex','.bib'):
            q=src/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    env=os.environ.copy();env.update(SOURCE_DATE_EPOCH='1790812800',FORCE_SOURCE_DATE='1',TZ='UTC',LC_ALL='C.UTF-8')
    env['TEXMFVAR']=str(out/'texmf-var');env['TEXMFCONFIG']=str(out/'texmf-config')
    env['HOME']=str(out/'home');Path(env['HOME']).mkdir()
    env['TMPDIR']=str(out/'tmp');Path(env['TMPDIR']).mkdir()
    passes=[]
    def run(cmd: list[str],cwd: Path,name: str) -> None:
        with (logs/name).open('w') as stream:
            proc=subprocess.run(cmd,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        if proc.returncode:raise RuntimeError('Paper build failed; inspect external log '+name)
    command=[tools['pdflatex'],'-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-file-line-error',
             '-jobname=main','-output-directory=../build',r'\pdfinfoomitdate=1\pdftrailerid{}\pdfsuppressptexinfo=-1\input{main.tex}']
    run(command,src,'latex1.log');passes.append('pdflatex')
    shutil.copyfile(src/'references.bib',aux/'references.bib')
    run([tools['bibtex'],'main'],aux,'bibliography.log');passes.append(Path(tools['bibtex']).name)
    run(command,src,'latex2.log');passes.append('pdflatex')
    run(command,src,'latex3.log');passes.append('pdflatex')
    log=(aux/'main.log').read_text(errors='replace')
    if 'Label(s) may have changed' in log or 'Rerun to get' in log:
        run(command,src,'latex4.log');passes.append('pdflatex');log=(aux/'main.log').read_text(errors='replace')
    fatal=[x for x in ['There were undefined references','undefined on input line','multiply defined','Citation `','Label(s) may have changed','Rerun to get'] if x in log]
    over=re.findall(r'Overfull \\[hv]box \(([\d.]+)pt too (?:wide|high)\)',log)
    if fatal or over:raise RuntimeError('Final LaTeX validation failed: '+repr((fatal,over)))
    page=re.search(r'Output written on .*?\((\d+) pages?[,\s]',log,re.S)
    if page is None:raise RuntimeError('Cannot determine page count from final LaTeX log')
    pdf=out/'main.pdf';shutil.copyfile(aux/'main.pdf',pdf)
    canonical=ROOT/'main.pdf';matches=canonical.is_file() and digest(canonical)==digest(pdf)
    if args.check_canonical and not matches:raise RuntimeError('Built PDF does not match canonical SHA-256; compare toolchain versions')
    if snapshot()!=before:raise RuntimeError('Frozen paper input was modified')
    result=dict(status='PASS_PAPER_BUILD',pages=int(page.group(1)),pdf_sha256=digest(pdf),
                canonical_sha256_match=matches,source_inputs_unchanged=True,passes=passes,
                undefined_references=False,undefined_citations=False,overfull_boxes=0,
                pdf_dates_omitted=True,pdf_trailer_id_omitted=True)
    (out/'build_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    versions={name:subprocess.check_output([exe,'--version'],text=True,stderr=subprocess.STDOUT).splitlines()[0] for name,exe in tools.items()}
    (out/'tool_versions.json').write_text(json.dumps(versions,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
        print('PAPER_BUILD_FAILED: '+str(exc),file=sys.stderr);sys.exit(1)
