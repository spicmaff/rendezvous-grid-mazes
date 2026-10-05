# Licensing notice

Copyright (c) 2026 Michael Fofonov and Artem Antonchikov.

New site, simulator and build/test code is MIT. New explanatory prose, authored metadata, diagrams and derived project data are CC BY 4.0. `site/index.html` and `site/app.mjs` each have one combined category: their HTML/JavaScript markup and behavior are MIT; their displayed explanatory prose is CC BY 4.0. This identifies separable subject matter without relicensing the manuscript.

The exact vendored manuscript, PDF, LaTeX, TikZ and bibliography in `research/paper/` retain the canonical author all-rights-reserved status. The paper build script remains MIT. Exact supplement software remains MIT, and exact project-authored data/certificates/non-paper documentation remain CC BY 4.0. Every copied canonical file retains the category in `research/LICENSES/LICENSE_MAP.json` and its unmodified notice. Third-party GUST, LPPL and OFL font notices remain exact; no new runtime font or image library is bundled.

The authoritative full license texts are [MIT](../research/LICENSES/CODE-MIT.txt), [CC BY 4.0](../research/LICENSES/DATA-DOCS-CC-BY-4.0.txt) and [paper rights](../research/LICENSES/PAPER-RIGHTS.txt). The CC legal text itself retains its public-domain dedication, separate from the data license. The canonical notice and text-origin records in `research/LICENSES/` are preserved.

`LICENSE_MAP.json` assigns every repository file to exactly one exact-path category. Build output inherits its input categories: site assets retain their site category, copied research retains its canonical category, public config/claims/citation retain CC BY 4.0, and the generated empty `.nojekyll` is CC BY 4.0 metadata. The provenance index is CC BY 4.0 project data, not a different grant for its referenced subjects.

Validate with `python3 -B scripts/licenses.py`. After adding a new public file, review its subject matter and regenerate with `python3 -B scripts/licenses.py --generate`. Do not modify canonical sources to insert headers. Canonical author confirmations and authority to grant the supplied licenses remain an author-side administrative requirement before actual submission, as recorded in the unmodified research notice/checklist.
