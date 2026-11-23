---
name: sgnergy-evaluation
description: Evaluates disclosed synthetic energy fixtures against planted-fault answer keys without using keys for detection.
version: 1.0.0
---
# Synthetic Evaluation
NEW documentation written for this repository, not an installed original export.

## Steps
1. Inspect every execution target for deletion first. The original eval/test_intake.py contains unlink calls and was not executed. The repository replacement is in-memory and non-destructive.
2. After September audit run python3 eval/score_results.py. Original tolerances: three findings, night onset, crossing near day 22, EUI within 2%, excess per fault within 10%, chiller engineer flag and savings labels.
3. Run python3 clients/demo-office-2/run_demo.py --output eval/demo-two-new-run with a new output directory after the second fixture is available. It recomputes using pipeline algorithms before comparing to the key. Archived eval_results.json and run_summary.json remain historical evidence, not current execution output.
4. Run python3 eval/test_intake.py, python3 eval/test_validator.py and python3 eval/test_nightly_cost.py only after required CSVs exist.
5. Do not extrapolate two seeded fictional buildings to field accuracy. Synthetic faults were deliberately tailored so the planned heuristics fire; October before/after is a simulated scenario, not verified customer savings.

## Evidence
Archived second-demo original evidence reports 11 passing checks: night relative error 4.37%, chiller relative error 0.51%, EUI 185, no Saturday false positive, onset day 15, crossing day 17. Original gate had 19 claims; original PDF three pages; tampered EUI blocked while original PDF hash stayed unchanged. These are selected sanitized historical claims, not new runtime verification.
