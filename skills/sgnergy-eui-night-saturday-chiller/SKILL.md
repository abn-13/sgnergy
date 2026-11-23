---
name: sgnergy-eui-night-saturday-chiller
description: Runs deterministic EUI, night, Saturday and chiller indicators on synthetic hourly meter data.
version: 1.0.0
---
# Energy Indicators
NEW documentation written for this repository, not an installed original export.

## Steps
1. Validate input and explicit GFA first. Run python3 pipeline/run_audit.py --client demo-office --month 2026-09 from the repository root.
2. EUI is sum(kWh) x 365 / period days / GFA, ESTIMATED from a short period. Benchmark/regulatory config values are inherited demonstration constants, not verified current applicability.
3. Night flag uses weekday minimum of hours 00-05 and 22-23 divided by maximum of hours 08-18, above 0.5. Excess uses all weekday after-hours load above its tenth percentile, including pre-onset baseline excess. Do not call this exact fault attribution.
4. Saturday flag compares daily energy with weekday daily mean, above 60%. Excess is clipped positive relative to Sunday mean; if no Sunday, baseline is 40% of weekday mean.
5. Chiller ratio uses energy divided by RT-hours where RT exceeds 30% of peak; missing days carry last valid value. Drift is an indicator with required professional-review text, not a diagnosis. Zero qualifying RT can fail the inherited implementation; hold such input instead of claiming a pass.
6. Proposal chiller potential uses endpoint drift multiplied by retained RT-hours, unlike integrated detector excess. Annualized upper-bound potential is not realized savings. Per-night cost divides full-period excess cost by affected weekday calendar dates, not overnight intervals.

## Verification
September seed 42 expects three faults, EUI 195, onset day 8 and actual threshold crossing day 23. Second seed 207 expects no Saturday fault, EUI 185, onset day 15 and crossing day 17. October is a 30-day window, not a full calendar month.
