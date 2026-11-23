#!/usr/bin/env python3
"""NEW no-delete replacement for original destructive fixture test.
In-memory repairs and missing optional-column regression only.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT / 'pipeline'))
import common
import intake
raw = common.load_csv(ROOT / 'clients/demo-office/2026-09/meter_data.csv')
r = intake.run(raw,10000)
assert r['status'] == 'pass' and r['rows'] == 720
r = intake.run(raw.drop(index=[300,301,302,500,600]),10000)
assert r['status'] == 'partial' and r['data_quality']['hours_interpolated'] == 5
r = intake.run(raw.drop(columns=['Cooling_Load_RT']),10000)
assert r['status'] == 'partial' and r['data_quality']['checks_skipped']
r = intake.run(raw.drop(index=range(200,212)),10000)
assert r['data_quality']['hours_excluded'] == 12
r = intake.run(raw.drop(columns=['Total_Building_kWh']),10000)
assert r['status'] == 'unusable'
print('PASS: clean, small gap, optional RT missing, large gap, missing required column')
