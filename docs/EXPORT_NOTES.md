# Analysis Export Notes
NEW documentation written for this repository. No README was created.

## Scope and provenance
The parent directory was verified before files were created. Reads and writes used dedicated file tools. No Git commands, source execution, recursive private-folder copying or original modifications occurred.

The pipeline modules and generate_data.py are compact adaptations transcribed from inspected originals, NOT faithful file copies. Formatting/comments were condensed. run_audit.py removes assistance-email drafting. report_content.py is a compact adapted claim builder; report_pdf.py is a NEW minimal renderer without original charts. make_report.py retains an adapted gate-before-PDF flow. These deviations mean the requested original-module export is incomplete.

Answer keys preserve inspected original values in reformatted JSON. Second-demo eval_results.json preserves original evaluation values. run_summary.json is a selected sanitized historical-evidence extract. No original PDFs, charts, mail messages, drafts, logs, SQLite state, customer records or backups were exported.

skills/sgnergy-lead-intake and sgnergy-new-data are sanitized adaptations of installed originals. The inspected sgnergy-*/SKILL.md glob found only those two. Meter-validation, EUI/night/Saturday/chiller, report/claim-validator and evaluation skill folders are NEW documentation written for this repository, not installed originals. The helper and second run_demo.py are NEW analysis-only replacements/adaptations. Evaluation scripts are adapted or newly written and labelled in their headers, not exact original copies.

## Incomplete items
The three original 720-row meter CSVs were inspected but NOT exported. Audit/report and CSV-dependent evaluations are therefore not runnable as delivered. Do not mark this task complete or cite successful repository tests. eval/sanity_check.py is a new pipeline-based check, not an export of the original independent heuristic/chart harness. Original mail/invoice/research modules and their evaluations were excluded from the analysis-only boundary. The original test_intake.py contains unlink calls and was not executed; the replacement uses in-memory data only.

## Commands
Python 3.10+ recommended. From repository root:

```sh
python3 -m pip install -r requirements.txt
```

Only AFTER the missing meter CSVs are exported, the intended commands are:

```sh
python3 ops/sgnergy-automation/helper.py validate-csv --csv clients/demo-office/2026-09/meter_data.csv --gfa 10000
python3 pipeline/run_audit.py --client demo-office --month 2026-09
python3 pipeline/make_report.py --client demo-office --month 2026-09
python3 pipeline/validate_report.py --client demo-office --month 2026-09
python3 eval/score_results.py
python3 eval/sanity_check.py
python3 eval/test_intake.py
python3 eval/test_validator.py
python3 eval/test_nightly_cost.py
python3 clients/demo-office-2/run_demo.py --output eval/demo-two-new-run
```

No commands were executed here. Audit/report writes can overwrite repository artifacts; use isolated output directories. generate_data.py can regenerate first-demo scenarios but is NOT a substitute for the requested dedicated Read/Write CSV export. It can overwrite repository CSVs/keys. Original second runner's private backup and installed PDF-script dependencies were removed in the new analysis-only runner.

## Historical evidence
First original key: September 160274.0 kWh, EUI 195.0; A 29333.2 kWh from day 8, B 9070.1 kWh, C 7437.4 kWh; actual threshold crossing day 23. October 112982.8 kWh and EUI 137.46 over a 30-day window, not a full calendar month. These are synthetic key values, not a new scorer pass.

Second archived original evaluation: 11 checks passed, EUI 185, two faults and no Saturday false positive, night onset day 15, crossing day 17. Night detected 30930 vs 29635.1 kWh (4.37% error); chiller 7394 vs 7432 kWh (0.51%). Original report gate checked 19 claims; original PDF had three pages; tampered EUI was blocked and the clean PDF hash remained unchanged. Original PDF is not included, so hash and PDF checks are historical evidence only, not evidence for the new renderer.

## Limits and sanitization
Fresh validator recomputation reuses detector algorithms and is independent of saved results, not independent algorithms. Value-based prose checking has broad small-integer/config allowances. Null truth can fail tolerance arithmetic; all-zero cooling can fail valid-series lookup. Intake is graceful repair, not strict ingress. The new strict helper validates finite GFA/readings and continuity but is not automatically wired into run_audit. Savings are annualized upper-bound assumptions, not realized savings or compliance findings. Regulatory and tariff descriptions in config are explicitly unverified inherited demo references.

Private identities were replaced with example.invalid addresses. Host paths were replaced with portable repository-root/TEMP_DIR instructions; site/form/collection/Stripe references use placeholders. Native Mail helper was inspected but replaced with a no-mail local validation helper. No credentials, mail data, lead records or private state are included. Root config was read only for required analysis constants and rebuilt without secrets.

Final dedicated content scan found no private host root, original private email identities, Stripe URL, original site/collection IDs, unlink/rmtree/remove calls or shutil.copy in exported files. This targeted scan is not a comprehensive secret detector. No executions or runtime validation were performed.
