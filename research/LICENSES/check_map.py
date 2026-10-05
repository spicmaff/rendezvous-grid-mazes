#!/usr/bin/env python3
"""Validate exact-path license coverage; no writes, downloads or third-party modules.

Usage: python3 LICENSES/check_map.py [--path paper/main.pdf]
This administrative check does not replace the full scientific verifier.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, sys
from pathlib import Path, PurePosixPath
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(root: Path) -> tuple[dict, dict]:
    root = root.resolve()
    paths = {}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(), 'Symlinks are not permitted')
        if p.is_file():
            paths[p.relative_to(root).as_posix()] = p
    doc = json.loads((root/'LICENSES/LICENSE_MAP.json').read_text(encoding='utf-8'))
    require(doc['schema'] == 'rendezvous.license-map.v1', 'Unsupported schema')
    require(doc['release_id'] == 'rendezvous-submission-rc2-authors', 'Release identifier mismatch')
    assigned = {}
    rule_ids = []
    for rule in doc['rules']:
        rid = rule['id']; rule_ids.append(rid)
        require(isinstance(rule['paths'], list) and bool(rule['paths']), 'Empty rule')
        require(rule['paths'] == sorted(set(rule['paths'])), 'Rule paths not unique and sorted')
        for name in rule['paths']:
            p = PurePosixPath(name)
            require(not p.is_absolute() and '..' not in p.parts and str(p) == name,
                    'Unsafe or noncanonical license path')
            require(name not in assigned, 'Overlapping rules: ' + name)
            require(name in paths, 'Nonexistent mapped file: ' + name)
            assigned[name] = rule
    require(rule_ids == sorted(set(rule_ids)), 'Rule IDs not unique and sorted')
    require(set(assigned) == set(paths), 'Unclassified public release file')
    for name, p in paths.items():
        rule = assigned[name]
        if name.startswith('paper/') and p.suffix in ('.tex', '.bib', '.pdf'):
            require(rule['category'] == 'proprietary-author-copyright / all-rights-reserved'
                    and rule['spdx_id'] is None, 'Manuscript incorrectly licensed: ' + name)
        if p.suffix in ('.py', '.cpp', '.cc', '.c', '.h', '.hpp', '.sh'):
            require(rule['spdx_id'] == 'MIT' and rule['category'] == 'project-software',
                    'Source code lacks MIT assignment: ' + name)
        if name.startswith('supplement/') and p.suffix not in ('.py', '.cpp', '.cc', '.c', '.h', '.hpp', '.sh'):
            require(rule['spdx_id'] == 'CC-BY-4.0', 'Supplement data/docs not CC BY 4.0: ' + name)
        if name.startswith('manifests/'):
            require(rule['spdx_id'] == 'CC-BY-4.0', 'Manifest not CC BY 4.0: ' + name)
    preserved = {
        'LICENSES/GUST-FONT-LICENSE.txt': (None, 'LicenseRef-GUST-Font-1.0'),
        'LICENSES/LPPL-1.3c.txt': ('LPPL-1.3c', None),
        'LICENSES/OFL-1.1.txt': ('OFL-1.1', None),
    }
    for name, (spdx, ref) in preserved.items():
        rule = assigned[name]
        require(rule['category'] == 'third-party-font-notice' and rule['spdx_id'] == spdx
                and rule.get('license_ref') == ref, 'Font notice classification changed: ' + name)
    cc = assigned['LICENSES/DATA-DOCS-CC-BY-4.0.txt']
    require(cc['category'] == 'canonical-license-text' and cc['spdx_id'] == 'CC0-1.0'
            and cc['license_text_for'] == 'CC-BY-4.0', 'CC legal-text classification mismatch')
    origins = json.loads((root/'LICENSES/LICENSE_TEXT_ORIGINS.json').read_text(encoding='utf-8'))
    for record in origins['sources']:
        require(record['file'] in paths, 'Missing canonical license file')
        require(digest(paths[record['file']]) == record['release_sha256'], 'Canonical license hash mismatch')
    inventory = json.loads((root/'manifests/FILES.json').read_text(encoding='utf-8'))
    require(inventory['release_id'] == doc['release_id'], 'Manifest release identifier mismatch')
    excluded = set(inventory['excludes'])
    require(excluded == {'manifests/FILES.json', 'manifests/SHA256SUMS.txt'}, 'Unexpected digest exclusions')
    hashes = {name: digest(p) for name, p in paths.items() if name not in excluded}
    tree = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    require(tree == inventory['content_tree_sha256'], 'Content tree digest mismatch')
    counts = dict(sorted(collections.Counter(rule['id'] for rule in assigned.values()).items()))
    result = dict(status='PASS_LICENSE_MAP', release_files=len(paths), exactly_one_rule_per_file=True,
                  unclassified_files=[], overlapping_files=[], rules=len(rule_ids), counts_by_rule=counts,
                  canonical_license_text_hashes_match=True, content_tree_sha256=tree)
    return result, assigned

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', help='Public-release relative path to query after full validation')
    args = parser.parse_args()
    result, assigned = validate(ROOT)
    if args.path is not None:
        require(args.path in assigned, 'Unknown release path')
        result['query'] = {'path': args.path, **{k:v for k,v in assigned[args.path].items() if k != 'paths'}}
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print('LICENSE_MAP_FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
