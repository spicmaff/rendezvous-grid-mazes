"""Strict release verifier for the supplied RUP-only ASCII LRAT trace.

This is not a general LRAT/RAT checker or a proof-assistant formalization. The
format prepass rejects RAT hints, invalid variables, missing terminators,
duplicate literals, nonmonotone/reused additions and invalid deletion records.
The semantic pass requires each cited clause to be unit, ending in conflict.
Even a reference after an earlier conflict is rejected, not silently skipped.
"""
from __future__ import annotations
from pathlib import Path
import re

class ProofError(ValueError):
    """The certificate is malformed or its derivation is invalid."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProofError(message)

def integer(token: str) -> int:
    require(re.fullmatch(r'-?[0-9]+', token) is not None, 'Invalid integer token')
    return int(token)

def literals(clause: list[int], nvars: int) -> None:
    require(all(1 <= abs(x) <= nvars for x in clause), 'Literal outside declared variables')
    require(len(set(clause)) == len(clause), 'Duplicate literal')
    require(not any(-x in set(clause) for x in clause), 'Tautological addition outside supported format')

def read_cnf(path: Path) -> tuple[int, list[list[int]]]:
    """Parse the shipped format: one terminated clause per noncomment line."""
    header = None
    clauses = []
    for number, line in enumerate(path.read_text(encoding='ascii').splitlines(), 1):
        t = line.split()
        if not t or t[0] == 'c':
            continue
        if t[0] == 'p':
            require(header is None and not clauses and len(t) == 4 and t[1] == 'cnf', 'Bad DIMACS header')
            header = integer(t[2]), integer(t[3])
            require(header[0] > 0 and header[1] >= 0, 'Invalid DIMACS counts')
            continue
        require(header is not None, 'DIMACS clause before header')
        row = [integer(x) for x in t]
        require(row[-1] == 0 and 0 not in row[:-1], f'Bad CNF terminator at line {number}')
        literals(row[:-1], header[0])
        clauses.append(row[:-1])
    require(header is not None and len(clauses) == header[1], 'DIMACS clause count mismatch')
    return header[0], clauses

def parse_rup_lrat(text: str, nvars: int, initial_count: int) -> list[tuple]:
    records = []
    last_add = initial_count
    empty_seen = False
    for number, line in enumerate(text.splitlines(), 1):
        t = line.split()
        require(bool(t), f'Blank LRAT record at line {number}')
        require(not empty_seen, 'Records after final empty clause')
        require(len(t) >= 3, 'Truncated LRAT record')
        cid = integer(t[0])
        require(cid > 0, 'Nonpositive clause identifier')
        if t[1] == 'd':
            ids = [integer(x) for x in t[2:]]
            require(cid == last_add, 'Deletion record must name the last addition identifier')
            require(ids[-1] == 0 and all(i > 0 for i in ids[:-1]), 'Malformed deletion list')
            require(len(set(ids[:-1])) == len(ids) - 1, 'Duplicate deletion identifier')
            records.append(('delete', number, cid, ids[:-1]))
            continue
        row = [integer(x) for x in t[1:]]
        require(row.count(0) == 2 and row[-1] == 0, 'Addition needs exactly two terminators')
        split = row.index(0)
        clause, hints = row[:split], row[split+1:-1]
        require(cid > last_add, 'Addition identifiers must increase, without reuse')
        literals(clause, nvars)
        require(hints and all(0 < h < cid for h in hints), 'RAT, absent, forward or malformed hint')
        require(len(set(hints)) == len(hints), 'Duplicate hint')
        records.append(('add', number, cid, clause, hints))
        last_add = cid
        empty_seen = not clause
    require(empty_seen, 'No final empty-clause addition')
    return records

def check_text(nvars: int, cnf: list[list[int]], text: str) -> dict:
    records = parse_rup_lrat(text, nvars, len(cnf))  # Explicit format prepass: no RAT steps.
    db = {i + 1: tuple(clause) for i, clause in enumerate(cnf)}
    for c in cnf:
        literals(c, nvars)
    additions = deleted = hint_uses = 0
    empty_id = None
    for record in records:
        kind, number, cid = record[:3]
        if kind == 'delete':
            for old in record[3]:
                require(old in db, f'Delete absent clause {old} at line {number}')
                del db[old]
                deleted += 1
            continue
        clause, hints = record[3:]
        require(cid not in db, 'Reused clause identifier')
        require(all(h in db for h in hints), f'Missing/deleted hint at line {number}')
        value = {abs(lit): lit < 0 for lit in clause}  # Assume target clause false.
        conflict = False
        for index, hid in enumerate(hints):
            require(not conflict, f'Unused hint after conflict at line {number}')
            hint_uses += 1
            unresolved = []
            satisfied = False
            for lit in db[hid]:
                if abs(lit) not in value:
                    unresolved.append(lit)
                elif value[abs(lit)] == (lit > 0):
                    satisfied = True
                    break
            require(not satisfied and len(unresolved) <= 1,
                    f'Nonunit or satisfied hint {hid} at line {number}')
            if not unresolved:
                conflict = True
                require(index == len(hints) - 1, f'Conflict before last hint at line {number}')
            else:
                lit = unresolved[0]
                value[abs(lit)] = lit > 0
        require(conflict, f'RUP did not derive conflict at line {number}')
        db[cid] = tuple(clause)
        additions += 1
        if not clause:
            empty_id = cid
    require(empty_id in db and db[empty_id] == (), 'Final empty clause is not active')
    return dict(format='ASCII LRAT with RUP-only additions',format_prepass_passed=True,
                additions=additions,deleted_clauses=deleted,hint_uses=hint_uses,
                final_empty_clause_id=empty_id,empty_clause=True,rat_steps=0)

def check(cnf_path: Path, proof_path: Path) -> dict:
    nvars, clauses = read_cnf(cnf_path)
    return check_text(nvars, clauses, proof_path.read_text(encoding='ascii'))

def self_test() -> dict:
    require(check_text(1, [[1], [-1]], '3 0 1 2 0\n')['empty_clause'], 'Positive control failed')
    cases = {
        'missing_hint': '3 0 1 99 0\n',
        'negative_RAT_hint': '3 0 1 -2 0\n',
        'forward_hint': '3 0 1 3 0\n',
        'nonconflicting_chain': '3 0 1 0\n',
        'duplicate_hint': '3 0 1 1 2 0\n',
        'missing_terminator': '3 0 1 2\n',
        'extra_terminator': '3 0 1 2 0 0\n',
        'unknown_deletion': '2 d 99 0\n3 0 1 2 0\n',
        'deleted_hint': '2 d 1 0\n3 0 1 2 0\n',
        'duplicate_deletion': '2 d 1 1 0\n3 0 1 2 0\n',
        'bad_deletion_identifier': '1 d 1 0\n3 0 1 2 0\n',
        'nonmonotone_addition': '2 0 1 2 0\n',
        'outside_variable': '3 2 0 1 2 0\n4 0 1 2 0\n',
        'duplicate_literal': '3 1 1 0 2 0\n4 0 1 2 0\n',
        'tautology': '3 1 -1 0 1 2 0\n4 0 1 2 0\n',
        'trailing_record': '3 0 1 2 0\n3 d 1 0\n',
        'no_empty_clause': '3 1 0 2 0\n',
        'nonnumeric_token': 'three 0 1 2 0\n',
    }
    for name, text in cases.items():
        try:
            check_text(1, [[1], [-1]], text)
        except ProofError:
            continue
        raise ProofError('Accepted malformed self-test: ' + name)
    other = [
        (2, [[1,2],[-1],[-2]], '4 0 1 2 3 0\n'),  # first hint is not unit
        (1, [[1],[-1],[1]], '4 0 1 2 3 0\n'),      # extra hint after conflict
        (1, [[1],[-1],[1]], '4 0 1 3 2 0\n'),      # satisfied rather than unit hint
    ]
    for n,c,t in other:
        try:
            check_text(n,c,t)
        except ProofError:
            continue
        raise ProofError('Accepted nonunit/trailing self-test')
    return dict(positive_controls=1,malformed_traces_rejected=len(cases)+len(other),status='PASS')
