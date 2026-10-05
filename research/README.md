# Memory, Recurrent Geometry, and Rendezvous Traps in Induced Grid Mazes

Release identifier: `rendezvous-submission-rc2-authors`.

This package contains the frozen paper, one canonical PDF, and the complete source/data needed for every declared finite proof chain and implementation validation. The mathematical statements, hypotheses, constants, controller tables, quantifier order, open problems and proof statuses are not changed by this release.

## Verify the supplement

From the release directory, run:

```sh
python3 supplement/verify_all.py --output /tmp/rendezvous-replay
```

The output directory must be new or empty and outside this release. The same command works from any current directory when the script path is made absolute. All generated data, logs, temporary files, and the locally compiled executable are written below the requested output directory. Nothing is installed, downloaded, or written into the release. Invoking Python explicitly avoids dependence on ZIP executable permission bits.

The default run is the full run; there is no implicit quick or scoped mode. It first validates the complete inventory and checksums, executes all 15 required stages, regenerates and compares 30 deterministic output files, and rechecks that the input tree is unchanged. Only then can it print `PASS_FULL_REPRODUCIBILITY`. A failure is nonzero and records an explicit missing-stage list in `verification.json`. Do not use Python's `-O` option, which disables assertions.

Requirements: Python 3.10 or later, standard library only, and a GCC-compatible C++17 compiler (`g++` by default; `--cxx` selects another executable). The tested environment uses Python 3.13.5 and GCC 14.2.0 on x86-64 Linux. No SAT solver, external proof checker, Python package installation, historical archive or network access is required. See `supplement/README.md` for exact scopes and `manifests/PROOF_ARTIFACTS.json` for the claim-to-checker map.

## Build the paper

```sh
python3 paper/build.py --output /tmp/rendezvous-paper --check-canonical
```

The build requires pdfLaTeX, BibTeX8 (preferred; BibTeX is an available fallback), Latin Modern and AMS fonts, and the standard LaTeX packages listed in `paper/main.tex`. In distribution terms these are provided by a TeX Live installation with the LaTeX base/recommended/extra, pictures, recommended fonts and BibTeX tools collections. No packages are installed by the build script. It invokes no shell escape and puts all source copies, caches and intermediate files under the external output directory.

The canonical PDF was built with pdfTeX 1.40.26 (TeX Live 2025/dev/Debian), kpathsea 6.4.0/dev, and BibTeX8 0.99d-x4.02. Its hash is recorded in `manifests/FILES.json`. The build uses a fixed source epoch, omits PDF date fields and trailer IDs, and gives TeX fixed relative input paths. `--check-canonical` also requires byte equality with `paper/main.pdf`; a different TeX/font toolchain may typeset the same mathematics but fail this byte-equality check. Omitting that option permits a diagnostic local build; it does not assert canonical byte reproduction.

## Contents and trust boundary

`paper/` contains the LaTeX/TikZ sources, bibliography, build script and exactly one PDF. `supplement/` contains transparent checkers, physical decision DAGs, the exact CNF/LRAT proof, controller witnesses, host coordinates and the realization validation corpus. `manifests/` contains the complete inventory, checksums, provenance and proof-artifact map. The small RUP verifier is deliberately specialized to the checked format of this supplied proof; it is not advertised as a general LRAT/RAT implementation or proof-assistant verification.

The finite path lower bound, the selected 44-family certificate and packing lower bound, and the lower bound on a universal maze require computation. The inventory/host checks validate concrete data accompanying human construction theorems. The finite realization scans validate algorithms and examples, not the all-size realization theorem. No status in the paper is strengthened by finite agreement.

## Authors and licensing

The author order is **Michael Fofonov**, then **Artem Antonchikov**.

Michael Fofonov: Alferov University, 8/3 Khlopina Str., St. Petersburg 194021, Russia.

Artem Antonchikov: Moscow Institute of Physics and Technology (National Research University), 9 Institutskiy per., Dolgoprudny, Moscow Region 141700, Russian Federation.

Project software is licensed under MIT. Project-authored supplement data, certificates and non-paper documentation are licensed under CC BY 4.0. Copyright (c) 2026 Michael Fofonov and Artem Antonchikov. The manuscript/PDF and LaTeX/TikZ manuscript materials remain all rights reserved pending a publication agreement; journal/publication terms may later govern the accepted or published manuscript. Third-party font notices remain separate and unchanged. No journal acceptance of the selected licenses is implied.

The exact classification of every public file is in `LICENSES/LICENSE_MAP.json`; the central mapping avoids modifications to proof-critical source files merely to add license headers. Run `python3 LICENSES/check_map.py` to check the complete, non-overlapping assignment. This administrative check is separate from the 15-stage scientific verifier.

The corresponding author is not yet designated. Corresponding-author email, ORCIDs, funding/grant declarations, competing interests and contribution statements are not supplied in this artifact. The affiliation assignments follow the author-side decisions; official sources verify institutional names and addresses. See `AUTHOR_METADATA_24.md`, `AUTHOR_CONFIRMATION_CHECKLIST_24.md` and `LICENSES/NOTICE.md`. Both authors' final confirmations and authority to grant the selected licenses remain to be recorded before actual submission.

## Checksum convention

`manifests/FILES.json` lists the bytes and SHA-256 of every release file except itself and `manifests/SHA256SUMS.txt`. The latter lists every release file except itself, including `FILES.json`, `PROVENANCE.json`, the proof map and expected-output manifest. The `content_tree_sha256` field hashes the compact, key-sorted JSON path-to-SHA-256 mapping for exactly the entries in `FILES.json`; it has the same two exclusions. There is no circular self-hash. Run `python3 supplement/common/integrity.py` for an integrity-only check, which is not a proof replay. In the delivery envelope, the outer `SHA256SUMS.txt` covers all envelope files except itself, including the inner checksum manifest and the separate engineering reports. The enclosing ZIP's SHA-256 is recorded outside that ZIP.

Checksums detect alteration relative to this deposit; they are not an authorship signature. Provenance records original artifact identifiers and content hashes but is not a runtime dependency. No historical research directory is included or needed.
