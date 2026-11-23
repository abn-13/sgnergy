#!/usr/bin/env python3
"""Adapted from original synthetic generator; formatting condensed.
Disclosed fictional 10,000 m2 office. Seed 42. September faults; October
30-day fixed window. Night fault extended through 06:00 so MIN-ratio fires.
Exact decomposition: total=base+A+B+C; A/B cooling at baseline efficiency.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
SEED = 42
GFA_M2 = 10000.0
DAYS = 30
HOURS = DAYS * 24
TARGET_EUI = 195.0
NIGHT_NC, NIGHT_RT = 52.0, 11.0
WEEKEND_NC, WEEKEND_RT = 72.0, 26.0
OCC_NC_VAR, OCC_RT_BASE, OCC_RT_VAR = 35.0, 200.0, 90.0
FAULT_A_NC, FAULT_A_RT = 128.0, 42.0
EFF_START, EFF_END, EFF_FIXED = 0.68, 0.84, 0.66
FAULT_A_START_DAY = 8
ROOT = Path(__file__).resolve().parent

def temp_factor(h):
    return (1.0 + np.cos(2.0 * np.pi * (h - 15.0) / 24.0)) / 2.0

def build(start, scenario, plug_base):
    rng = np.random.default_rng(SEED)
    n_nc = rng.uniform(-0.03, 0.03, HOURS)
    n_rt = rng.uniform(-0.03, 0.03, HOURS)
    n_ch = rng.uniform(-0.01, 0.01, HOURS)
    ts = pd.date_range(start=start, periods=HOURS, freq='h', tz='Asia/Singapore')
    day = np.arange(HOURS) // 24 + 1
    hour = np.arange(HOURS) % 24
    wd = ts.dayofweek.to_numpy()
    tf = temp_factor(hour)
    occupied = ((wd < 5) & (hour >= 8) & (hour < 19))
    weekday, saturday = wd < 5, wd == 5
    nc_base = np.where(occupied, plug_base + OCC_NC_VAR * tf, NIGHT_NC)
    rt_base = np.where(occupied, OCC_RT_BASE + OCC_RT_VAR * tf, NIGHT_RT)
    weekend_mask = ~weekday & ~occupied
    nc_base[weekend_mask], rt_base[weekend_mask] = WEEKEND_NC, WEEKEND_RT
    a_mask = ((scenario == 'faults') & weekday & (day >= FAULT_A_START_DAY) & ((hour >= 19) | (hour < 6)))
    nc_a, rt_a = np.where(a_mask, FAULT_A_NC, 0.0), np.where(a_mask, FAULT_A_RT, 0.0)
    b_mask = (scenario == "faults") & saturday
    nc_b = np.where(b_mask & (hour >= 8) & (hour < 19), plug_base + OCC_NC_VAR * tf - WEEKEND_NC, 0.0)
    rt_b = np.where(b_mask & (hour >= 8) & (hour < 19), OCC_RT_BASE + OCC_RT_VAR * tf - WEEKEND_RT, 0.0)
    nc_b = np.where(b_mask & ~((hour >= 8) & (hour < 19)), NIGHT_NC - WEEKEND_NC, nc_b)
    rt_b = np.where(b_mask & ~((hour >= 8) & (hour < 19)), NIGHT_RT - WEEKEND_RT, rt_b)
    eff = EFF_START + (EFF_END - EFF_START) * (day - 1) / (DAYS - 1) if scenario == 'faults' else np.full(HOURS, EFF_FIXED)
    nc = (nc_base + nc_a + nc_b) * (1 + n_nc)
    rt = (rt_base + rt_a + rt_b) * (1 + n_rt)
    chiller = rt * eff * (1 + n_ch)
    total = nc + chiller
    extra_a = float(np.sum(nc_a * (1 + n_nc) + rt_a * (1 + n_rt) * EFF_START * (1 + n_ch)))
    extra_b = float(np.sum(nc_b * (1 + n_nc) + rt_b * (1 + n_rt) * EFF_START * (1 + n_ch)))
    extra_c = float(np.sum((rt_base + rt_a + rt_b) * (1 + n_rt) * (eff - EFF_START) * (1 + n_ch)))
    df = pd.DataFrame({'Timestamp':ts.strftime('%Y-%m-%dT%H:%M:%S+08:00'), 'Total_Building_kWh':total.round(2),
                       'ChillerPlant_kWh':chiller.round(2), 'Cooling_Load_RT':rt.round(2)})
    meta = {'day':day,'hour':hour,'wd':wd,'eff':eff,'extra_a':extra_a,'extra_b':extra_b,'extra_c':extra_c,'rt_base':rt_base,'occupied':occupied}
    return df, meta

def calibrate(start):
    lo, hi = 50.0, 400.0
    for _ in range(50):
        mid = (lo + hi) / 2
        df, _ = build(start, 'faults', mid)
        eui = df.Total_Building_kWh.sum() * 365 / DAYS / GFA_M2
        if eui < TARGET_EUI:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def daily_kwrt(df, meta):
    rt, ch = df.Cooling_Load_RT.to_numpy(), df.ChillerPlant_kWh.to_numpy()
    keep = rt > 0.30 * rt.max()
    out = []
    for d in range(1, DAYS + 1):
        m = keep & (meta['day'] == d)
        out.append(round(float(ch[m].sum() / rt[m].sum()), 4) if m.any() else None)
    return out

def make_key(df, meta, scenario, start, plug_base):
    total = float(df.Total_Building_kWh.sum())
    kwrt = daily_kwrt(df, meta)
    crossing = next((i + 1 for i,v in enumerate(kwrt) if v is not None and v > 0.80), None)
    key = {'disclosed_synthetic':True,'seed':SEED,'gfa_m2':GFA_M2,'days':DAYS,'start':start,'scenario':scenario,
           'calibration':{'plug_load_base_kw':round(plug_base,2),'target_eui':TARGET_EUI},
           'true_totals':{'month_kwh':round(total,1),'daily_avg_kwh':round(total/DAYS,1),
                          'annualized_kwh_estimated':round(total*365/DAYS,0),'eui_kwh_m2_yr':round(total*365/DAYS/GFA_M2,2)},
           'daily_kwrt_series':kwrt,'kwrt_crosses_0.80_day':crossing}
    if scenario == 'faults':
        key['faults'] = {
            'A_night_waste':{'start_day':FAULT_A_START_DAY,'window':"19:00-06:00 weekdays (extended from plan's 02:00 so the min-load night/day ratio heuristic fires)",
                             'extra_kwh':round(meta['extra_a'],1),'expected_night_day_ratio_from_day8':'> 0.5'},
            'B_weekend_waste':{'start_day':1,'pattern':'Saturdays run weekday schedule','extra_kwh':round(meta['extra_b'],1),
                              'expected_saturday_vs_weekday_pct':'~75-85% of faulted weekday average (flag > 60%)'},
            'C_chiller_drift':{'eff_start_kwrt':EFF_START,'eff_end_kwrt':EFF_END,'extra_kwh':round(meta['extra_c'],1),'expected_crossing_day':'~22'}}
        key['attribution_note'] = 'total = base + A + B + C exactly; A/B extra cooling priced at baseline 0.68 kW/RT; drift C applies to all cooling load.'
    else:
        key['fixed_scenario'] = {'eff_kwrt_constant':EFF_FIXED,'faults_removed':['A','B','C']}
    return key

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', choices=['faults','fixed','both'], default='both')
    ap.add_argument('--gaps', action='store_true')
    args = ap.parse_args()
    plug_base = calibrate('2026-09-01')
    jobs = []
    if args.scenario in ('faults','both'):
        jobs.append(('faults','2026-09-01','2026-09'))
    if args.scenario in ('fixed','both'):
        jobs.append(('fixed','2026-10-01','2026-10'))
    for scenario,start,month in jobs:
        df,meta = build(start,scenario,plug_base)
        cdir = ROOT / 'clients/demo-office' / month
        cdir.mkdir(parents=True,exist_ok=True)
        df.to_csv(cdir / 'meter_data.csv',index=False)
        key = make_key(df,meta,scenario,start,plug_base)
        (ROOT / 'eval').mkdir(exist_ok=True)
        (ROOT / 'eval' / f'answer_key_{month}.json').write_text(json.dumps(key,indent=2))
        print(month, key['true_totals'])
        if args.gaps and scenario == 'faults':
            singles = np.random.default_rng(SEED+1).choice(HOURS,2,replace=False)
            gap_idx = np.concatenate([np.arange(300,303),singles])
            df.drop(index=gap_idx).to_csv(cdir / 'meter_data_gaps.csv',index=False)
if __name__ == '__main__':
    main()
