---
name: sgnergy-meter-validation
description: Validates hourly meter input before local SGnergy analysis.
version: 1.0.0
---
# Meter Validation
NEW documentation written for this repository. No corresponding installed sgnergy-* original was found in the inspected skill glob.

## Steps
1. Work from the repository root. Inspect Python before execution; never run source containing delete operations. Never modify original client data.
2. Run python3 ops/sgnergy-automation/helper.py validate-csv --csv clients/demo-office/2026-09/meter_data.csv --gfa 10000.
3. Require explicit positive finite GFA, required columns Timestamp,Total_Building_kWh,ChillerPlant_kWh, at least 720 consecutive hourly timestamps, no duplicates, finite nonnegative readings and chiller <= total.
4. Missing Cooling_Load_RT skips efficiency; never fabricate it. The strict helper differs from pipeline/intake.py, which repairs small gaps up to six hours, caps inconsistent chiller values and excludes larger gaps. Report repairs, coverage and skipped checks.
5. Run python3 eval/test_intake.py for no-delete in-memory tests. Do not claim these tests cover malformed timestamps, infinite GFA or all boundary cases of the original intake implementation.

## Safety
Synthetic examples only. Keep source provenance, units and timezone. Never treat a partial period as measured annual consumption. No mailbox access, payment or sends.
