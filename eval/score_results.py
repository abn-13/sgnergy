#!/usr/bin/env python3
"""Adapted original scorer: September fixture only; not real-world accuracy."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
res = json.loads((ROOT / 'clients/demo-office/2026-09/results.json').read_text())
key = json.loads((ROOT / 'eval/answer_key_2026-09.json').read_text())
f = {x['id']:x for x in res['anomaly']['findings']}
fa,fb,fc = (key['faults'][k] for k in ('A_night_waste','B_weekend_waste','C_chiller_drift'))
def within(det,truth,tol):
    return abs(det-truth)/truth <= tol
checks = [
 ('3/3 faults found',len(f) == 3),
 ('A start day == 8',f.get('night_waste',{}).get('start_day') == fa['start_day']),
 ('C crosses near day 22',f.get('chiller_drift',{}).get('crosses_limit_day') is not None and abs(f['chiller_drift']['crosses_limit_day']-22) <= 2),
 ('EUI within 2%',within(res['benchmark']['eui_kwh_m2_yr']['value'],key['true_totals']['eui_kwh_m2_yr'],.02)),
 ('A extra kWh within 10%',within(f['night_waste']['excess_kwh']['value'],fa['extra_kwh'],.10)),
 ('B extra kWh within 10%',within(f['weekend_waste']['excess_kwh']['value'],fb['extra_kwh'],.10)),
 ('C extra kWh within 10%',within(f['chiller_drift']['excess_kwh']['value'],fc['extra_kwh'],.10)),
 ('engineer flag',f['chiller_drift']['engineer_flag'] is True),
 ('savings labelled',all('label' in x['savings_sgd_year'] for x in res['proposal']['fixes']))]
for name,ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
print(f'RESULT: {sum(ok for _,ok in checks)}/{len(checks)}')
sys.exit(0 if all(ok for _,ok in checks) else 1)
