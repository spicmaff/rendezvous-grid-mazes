"""Strict release inventory and checksum validation, with no self-hash cycle."""
from __future__ import annotations
import hashlib,json,sys
sys.dont_write_bytecode=True
from pathlib import Path,PurePosixPath

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()

def require(ok: bool,message: str) -> None:
    if not ok:raise ValueError(message)

def safe_file(root: Path,name: str) -> Path:
    rel=PurePosixPath(name)
    require(not rel.is_absolute() and '..' not in rel.parts and str(rel)==name,'Unsafe or noncanonical manifest path')
    p=root.joinpath(*rel.parts)
    require(p.resolve().is_relative_to(root.resolve()) and p.is_file() and not p.is_symlink(),'Missing/unsafe file: '+name)
    return p

def snapshot(root: Path) -> dict[str,str]:
    result={}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'Symlink in frozen release: '+str(p.relative_to(root)))
        if p.is_file():result[p.relative_to(root).as_posix()]=digest(p)
    return result

def verify(root: Path) -> dict:
    root=root.resolve();files=snapshot(root)
    checksum='manifests/SHA256SUMS.txt';inventory='manifests/FILES.json'
    expected={}
    for line in safe_file(root,checksum).read_text(encoding='utf-8').splitlines():
        require(len(line)>66 and line[64:66]=='  ','Malformed checksum record')
        h,name=line[:64],line[66:]
        require(len(h)==64 and all(c in '0123456789abcdef' for c in h),'Malformed SHA-256')
        require(name not in expected,'Duplicate checksum path')
        safe_file(root,name);expected[name]=h
    require(set(expected)==set(files)-{checksum},'Incomplete checksum inventory or untracked release file')
    for name,h in expected.items():require(files[name]==h,'SHA-256 mismatch: '+name)
    manifest=json.loads(safe_file(root,inventory).read_text())
    records=manifest['files'];indexed={r['path']:r for r in records}
    require(len(indexed)==len(records),'Duplicate FILES.json entry')
    require(set(indexed)==set(files)-{inventory,checksum},'FILES.json inventory mismatch')
    for name,r in indexed.items():
        p=safe_file(root,name)
        require(r['bytes']==p.stat().st_size and r['sha256']==files[name],'FILES.json mismatch: '+name)
    return dict(status='PASS_INTEGRITY_ONLY',release_files=len(files),checksum_entries=len(expected),inventory_entries=len(records),all_release_files_accounted=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    print(json.dumps(verify(root),indent=2,sort_keys=True))
