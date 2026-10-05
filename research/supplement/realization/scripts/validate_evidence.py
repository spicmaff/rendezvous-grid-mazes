#!/usr/bin/env python3
"""Independent Python audit of the fresh C++ corpus; imports no earlier checker.

Rebuilds walks from expanded edge lists, verifies every positive coloring and
its stored affine profile, completes and simulates both controller witnesses.
Also checks all simultaneous D4 images and path reversals in the finite corpus.
"""
from __future__ import annotations
import itertools
import json
from pathlib import Path
import sys

D = 'ENWS'
VEC = ((1, 0), (0, 1), (-1, 0), (0, -1))

def build(d: str, p: str) -> tuple[list[int], list[int], list[int], list[list[int]]]:
    n = len(d) + 1
    assert len(p) == n - 1 and set(p) <= set('-01')
    assert all(p[j] == '-' or p[j + 1] == '-' for j in range(n - 2))
    xy = [(0, 0)]
    for ch in d:
        x, y = xy[-1]
        dx, dy = VEC[D.index(ch)]
        xy.append((x + dx, y + dy))
    assert len(set(xy)) == n
    masks = [0] * n
    # Compute masks from the full geometric adjacency relation, not from indices.
    for i, (x, y) in enumerate(xy):
        neighbors = []
        for j, (u, v) in enumerate(xy):
            if abs(u - x) + abs(v - y) == 1:
                neighbors.append(j)
                masks[i] |= 1 << VEC.index((u - x, v - y))
        assert sorted(neighbors) == list(range(max(0, i - 1), i)) + list(range(i + 1, min(n, i + 2)))
    walk = [0]
    for j in range(n - 1):
        walk.append(j + 1)
        if p[j] == '0':
            walk.extend((j, j + 1))
    for j in range(n - 2, -1, -1):
        walk.append(j)
        if p[j] == '1':
            walk.extend((j + 1, j))
    assert walk[-1] == walk[0]
    w = walk[:-1]
    visits = [[i for i, v in enumerate(w) if v == j] for j in range(n)]
    for v, ids in enumerate(visits):
        expected = (1 if v in (0, n - 1) else 2) + sum(p[e] != '-' for e in (v - 1, v) if 0 <= e < n - 1)
        assert len(ids) == expected
    out = [VEC.index((xy[w[(i+1) % len(w)]][0] - xy[v][0], xy[w[(i+1) % len(w)]][1] - xy[v][1])) for i, v in enumerate(w)]
    return w, masks, out, visits

def rows(w: list[int], masks: list[int], out: list[int], q: list[int], ignore_endpoints: bool = False) -> tuple[bool, dict]:
    if len(q) != len(w) or any(x not in (0, 1, 2) for x in q):
        return False, {}
    if len(set(zip(w, q))) != len(w):
        return False, {}
    table = {}
    for i, v in enumerate(w):
        if ignore_endpoints and v in (0, len(masks) - 1):
            continue
        key, value = (q[i], masks[v]), (out[i], q[(i + 1) % len(q)])
        if key in table and table[key] != value:
            return False, table
        table[key] = value
    return True, table

def controller_check(d: str, w: list[int], masks: list[int], out: list[int], q: list[int]) -> None:
    good, table = rows(w, masks, out, q)
    assert good
    for state in range(3):
        for m in range(1, 16):
            table.setdefault((state, m), (next(i for i in range(4) if m >> i & 1), 0))
    assert len(table) == 45
    assert all(m & (1 << direction) and successor in range(3) for (state, m), (direction, successor) in table.items())
    tag = w[0], q[0]
    seen = set()
    for i in range(len(w)):
        assert tag == (w[i], q[i]) and tag not in seen
        seen.add(tag)
        v, state = tag
        direction, successor = table[state, masks[v]]
        nxt = None
        if v + 1 < len(masks) and D.index(d[v]) == direction:
            nxt = v + 1
        if v and (D.index(d[v - 1]) + 2) % 4 == direction:
            assert nxt is None
            nxt = v - 1
        assert nxt is not None
        tag = nxt, successor
    assert tag == (w[0], q[0])

def profile_check(r: dict, w: list[int], masks: list[int], out: list[int], visits: list[list[int]]) -> None:
    q = [x + 1 for x in r['q_affine']]
    n, L = len(masks), len(w)
    assert r['masks'] == sorted(set(masks[1:-1]))
    params = {m: (s, a, k) for m, s, a, k in zip(r['masks'], r['singleton'], r['a'], r['kappa'])}
    times = {}
    for v in range(1, n - 1):
        s, a, k = params[masks[v]]
        assert a in (1, 2, 3) and k in (0, 1, 2, 3) and masks[v] >> s & 1
        paired = [i for i in visits[v] if out[i] != s]
        single = [i for i in visits[v] if out[i] == s]
        assert len(single) == 1 and len(paired) in (1, 2)
        if len(paired) == 2:
            assert k != 0
        assert q[single[0]] == a
        b = next(x for x in (1, 2, 3) if x != a)
        for e, i in enumerate(paired):
            t = ((r['z'] >> (v - 1)) & 1) ^ e
            times[i] = t
            assert q[i] == b ^ (a if t else 0)
    for v in (0, n - 1):
        for i in visits[v]:
            assert q[i] == r['endpoint'][i]
    # All pair comparisons, instead of reusing the C++ anchor-star compiler.
    for i, v in enumerate(w):
        for j in range(i):
            u = w[j]
            if masks[v] != masks[u]:
                continue
            if v in (0, n - 1):
                if q[i] == q[j]:
                    assert q[(i + 1) % L] == q[(j + 1) % L]
            elif out[i] == out[j]:
                s, a, k = params[masks[v]]
                rhs = 0 if out[i] == s or times[i] == times[j] else k
                assert q[(i + 1) % L] ^ q[(j + 1) % L] == rhs

def main(root: Path) -> None:
    index = {}
    counts = dict(specifications=0, positives=0, full_controllers=0, profile_checks=0, d4_comparisons=0, reversal_comparisons=0, state_permutation_checks=0)
    for path in sorted(root.glob('fresh_n*.jsonl')):
        for line in path.open():
            r = json.loads(line)
            assert (r['d'], r['p']) not in index
            index[r['d'], r['p']] = bool(r['exact'])
            counts['specifications'] += 1
            w, masks, out, visits = build(r['d'], r['p'])
            assert r['affine'] == r['exact']
            doubled_sides = {}
            gate = True
            for v in range(1, len(masks) - 1):
                if len(visits[v]) == 3:
                    doubled = next(d for d in range(4) if sum(out[i] == d for i in visits[v]) == 2)
                    if masks[v] in doubled_sides and doubled_sides[masks[v]] != doubled:
                        gate = False
                    doubled_sides[masks[v]] = doubled
            assert gate == bool(r['gate'])
            if r['exact']:
                counts['positives'] += 1
                for name in ('q_exact', 'q_affine'):
                    controller_check(r['d'], w, masks, out, r[name])
                    counts['full_controllers'] += 1
                profile_check(r, w, masks, out, visits)
                counts['profile_checks'] += 1
                # Exhaust all S3 names on a deterministic subset, not an empirical invariance assumption.
                if counts['positives'] <= 256:
                    for perm in itertools.permutations(range(3)):
                        controller_check(r['d'], w, masks, out, [perm[x] for x in r['q_affine']])
                        counts['state_permutation_checks'] += 1
    for (d, p), result in index.items():
        for sign in (-1, 1):
            for rotation in range(4):
                image = ''.join(D[(sign * D.index(x) + rotation) % 4] for x in d)
                assert index[image, p] == result
                counts['d4_comparisons'] += 1
        reverse = ''.join(D[(D.index(x) + 2) % 4] for x in reversed(d))
        reverse_phase = ''.join('-' if x == '-' else str(1 - int(x)) for x in reversed(p))
        assert index[reverse, reverse_phase] == result
        counts['reversal_comparisons'] += 1
    counts['mismatches'] = 0
    (root / 'python_validation.json').write_text(json.dumps(counts, indent=2) + '\n')
    print(json.dumps(counts, indent=2))

if __name__ == '__main__':
    if not __debug__: raise SystemExit('Assertions must be enabled; do not use -O')
    if len(sys.argv) != 2: raise SystemExit('Expected external generated data directory')
    data=Path(sys.argv[1]).resolve()
    if data.is_relative_to(Path(__file__).resolve().parents[3]): raise ValueError('Output must be outside the release')
    main(data)
