---
name: sgnergy-report-claim-validator
description: Builds local claim-register reports and applies R1-R6 numeric and wording gates before PDF rendering.
version: 1.0.0
---
# Report Claim Gate
NEW documentation written for this repository; no installed original skill found.

## Steps
1. Run the local audit, then python3 pipeline/make_report.py --client demo-office --month 2026-09. Rendering is blocked on validator nonzero exit.
2. Independently run python3 pipeline/validate_report.py --client demo-office --month 2026-09.
3. R1 checks allowed labels; R2 forbidden wording; R3 numeric mismatch with max(1% of truth, rounding precision tolerance); R4 required engineering flags; R5 known claim IDs; R6 numeric tokens in prose.
4. Run python3 eval/test_validator.py for in-memory clean/tamper checks. Tests are scoped; this is not a universal hallucination or safety guarantee.
5. Fresh truth recomputation reads raw CSV and reuses intake, benchmark, anomaly and proposal. It is independent of saved results, not independent algorithms. Claim source strings are not fully semantically authenticated, and numeric prose matching is value-based with broad allowances for small integers/config values.
6. Do not bypass on invalid data. The inherited null-truth tolerance calculation can fail before graceful rejection. Professional review and current source applicability checks remain required.

## Provenance
The repository report_content.py is a compact adaptation; report_pdf.py is a newly written portable minimal renderer. Neither reproduces original layout, charts or original 19-claim report exactly. Historical PDF evidence is not evidence of this renderer's output.
