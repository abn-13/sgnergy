#!/usr/bin/env python3
"""Adapted original numeric check, without private backup dependency."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT / 'pipeline'))
import common
import intake
import anomaly
import proposal
path = ROOT / 'clients/demo-office/2026-09/meter_data.csv'
raw = common.load_csv(path)
cfg = common.load_config()
clean = intake.run(raw,10000)['df_clean']
a = anomaly.run(clean,cfg)
p = proposal.run(clean,a,cfg,raw_df=raw)
f = p['night_waste_sgd_per_affected_night']
assert f['excess_kwh'] == 30426
assert f['denominator']['count'] == 17
assert f['denominator']['raw_after_hours_rows'] == 221
assert f['value'] == 519.03
assert f['period_cost_sgd_before_gst'] == 8823.54
assert f['label'] == 'ESTIMATED'
assert 'night_waste_sgd_per_affected_night' not in proposal.run(clean,{'findings':[]},cfg,raw_df=raw)
print('PASS: 30426 kWh x 0.29 / 17 affected weekday dates = S$519.03; not isolated fault savings')
