# Development and contributions

Treat `research/` as immutable, exact scientific input. Change UI or conversion code outside it. A new scientific statement needs a stable component ID in `public/claims.json`, an exact paper label and, if data-backed, the canonical data and semantic checker. Preserve every scope and proof-status qualifier. Any edited controller/maze in the browser becomes an illustrative toy.

Run `python3 -B scripts/build.py`, `python3 -B scripts/check.py`, and `node --test tests/*.test.mjs`. `scripts/derive.py` imports canonical Python semantics without writing bytecode into research. `site/data/` is committed and deterministically regenerated. Edit explanatory text in English and keep source links local/relative. No backend, telemetry, cookies or external runtime assets are needed. Do not add publication identifiers that the authors have not supplied.

Controls must remain keyboard operable and legible on mobile. The canvas has equivalent pan/zoom/fragment buttons and arrow-key support. Motion starts only on explicit Run; stepping is always available. Test both themes and a non-root server path after changes. Visual QA tooling is optional for local development and is not a build dependency.

To audit derived bytes, see `site/data/provenance.json`. To audit licensing, see `LICENSES/NOTICE.md` and run `scripts/licenses.py`. New files require reviewed exact-path license entries; the original research license map is never regenerated.
