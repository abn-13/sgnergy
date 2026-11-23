#!/usr/bin/env python3
"""NEW portable no-writing sanity check, inspired by inspected original harness.
Original chart output and independently coded heuristic implementation omitted.
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT / 'pipeline'))
import common
import benchmark
import anomaly
path = ROOT / 'clients/demo-office/2026-09/meter_data.csv'
df = common.load_csv(path)
cfg = common.load_config()
key = json.loads((ROOT / 'eval/answer_key_2026-09.json').read_text())
b = benchmark.run(df,10000,cfg)
a = anomaly.run(df,cfg)
assert abs(b['eui_kwh_m2_yr']['value']-key['true_totals']['eui_kwh_m2_yr'])/key['true_totals']['eui_kwh_m2_yr'] <= .02
assert {f['id'] for f in a['findings']} == {'night_waste','weekend_waste','chiller_drift'}
print('PASS: EUI and three expected fault identities; this uses pipeline algorithms, not an independent detector')
