# Realization data format

`fresh_nN.jsonl` contains one record per directed induced path and matching/phase specification. Directions `d` use the absolute order ENWS. Phases `p` use `-01`. `exact` is the congruence/partition oracle answer; `affine` is the independent profile compiler answer; `gate` is the doubled-side direction test, not an oracle premise. Answers are integers 0/1. `oracle_nodes` is a deterministic search-node count, not a mathematical invariant.

Positive rows contain both occurrence-state witnesses `q_exact` and `q_affine`, using actual states 0,1,2. Masks use E=1,N=2,W=4,S=8, unlike the NESW order in the obstruction checks. `singleton` uses ENWS indices. The vector code of actual state q is q+1. Vector addition is bitwise XOR, not addition modulo 3. `a` is nonzero and `kappa` can be zero at observationally unsaturated masks. `endpoint` contains occurrence assignments, with zero placeholders away from endpoints. `z` stores the internal role bits, with vertex v in bit v-1. State gauges are global, never independent across masks.

`probe_*.json` gives complete normalized local-injection solutions. `assignments` counts the full Cartesian search. For saturated NAND, the correspondence-mask order is NW=6 then ES=9; absence of key `11` means zero solutions. `relaxed_projection` is an explicitly weakened diagnostic, not realization.

`fresh_staircase_certificates.json` contains the binary equations and XOR row indices for each of 243 normalized profiles; the indicated XOR has zero left side and right side one. `fresh_sharp_family.json` and `fresh_phase_family.json` list finite checked family parameters; their controllers are the explicit functions in `scripts/consequence_replay.py`. `fresh_summary.json`, `python_validation.json`, `seam_summary.json` and `consequence_replay.json` are frozen expectations, never overwritten by verification.

The full verifier regenerates the corpus in the external output directory, compares the bytes, then reconstructs and simulates both complete legal controller tables per positive record. These finite checks validate the algorithms and examples, not the all-size theorem.
