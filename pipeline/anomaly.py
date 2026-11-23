"""Adapted from original Skill 2. Same demo heuristics, compact formatting."""
import numpy as np
ENGINEER_FLAG = "Needs review by a PE (Mechanical) or BCA-registered Energy Auditor"

def run(df, cfg):
    h = cfg['heuristics']
    load = df.Total_Building_kWh.to_numpy()
    office = df.hour.between(8, 18)
    night = df.hour.isin([0, 1, 2, 3, 4, 5, 22, 23])
    findings, ratios = [], {}
    for d in sorted(df.day.unique()):
        m = df.day == d
        if df.loc[m, 'wd'].iloc[0] >= 5:
            continue
        n_arr, d_arr = load[(m & night).to_numpy()], load[(m & office).to_numpy()]
        if len(n_arr) and len(d_arr):
            ratios[int(d)] = float(n_arr.min() / d_arr.max())
    flagged = [d for d, r in ratios.items() if r > h['night_day_ratio_flag']]
    after_hours = df[(df.wd < 5) & ~office]
    baseline = float(np.percentile(after_hours.Total_Building_kWh, 10))
    night_excess = float((after_hours.Total_Building_kWh - baseline).clip(lower=0).sum())
    if flagged:
        start = min(flagged)
        pre = [r for d, r in ratios.items() if d < start]
        findings.append({'id':'night_waste', 'title':'After-hours load abnormally high',
            'start_day':start, 'start_date':str(df.Timestamp[df.day == start].iloc[0].date()),
            'night_day_ratio_before':round(float(np.mean(pre)), 2) if pre else None,
            'night_day_ratio_after':round(float(np.mean([r for d, r in ratios.items() if d >= start])), 2),
            'flag_threshold':h['night_day_ratio_flag'], 'label':'HEURISTIC',
            'excess_kwh':{'value':round(night_excess, 0), 'label':'ESTIMATED', 'basis':f'after-hours load above baseline {baseline:.0f} kW'},
            'possible_cause':'BMS night setback may be disabled or overridden', 'engineer_flag':False})
    daily = df.groupby('day').Total_Building_kWh.sum()
    wd_days = [d for d in daily.index if df.loc[df.day == d, 'wd'].iloc[0] < 5]
    wd_avg = float(daily[wd_days].mean())
    sat_days = [d for d in daily.index if df.loc[df.day == d, 'wd'].iloc[0] == 5]
    sun_days = [d for d in daily.index if df.loc[df.day == d, 'wd'].iloc[0] == 6]
    quiet_day = float(daily[sun_days].mean()) if sun_days else wd_avg * 0.4
    sat_pct = {int(d):float(daily[d] / wd_avg) for d in sat_days}
    sat_flagged = [d for d, p in sat_pct.items() if p > h['weekend_vs_weekday_flag']]
    if sat_flagged:
        weekend_excess = float(sum(max(daily[d] - quiet_day, 0) for d in sat_flagged))
        findings.append({'id':'weekend_waste', 'title':'Saturdays consuming like weekdays',
            'start_day':min(sat_flagged), 'start_date':str(df.Timestamp[df.day == min(sat_flagged)].iloc[0].date()),
            'saturday_vs_weekday_pct':{d:round(p * 100) for d,p in sat_pct.items()},
            'flag_threshold_pct':h['weekend_vs_weekday_flag'] * 100, 'label':'HEURISTIC',
            'excess_kwh':{'value':round(weekend_excess, 0), 'label':'ESTIMATED', 'basis':f'vs quiet-day baseline {quiet_day:.0f} kWh/day'},
            'possible_cause':'Weekday schedule may be running on Saturdays', 'engineer_flag':False})
    kwrt_series, crossing = {}, None
    if 'Cooling_Load_RT' in df.columns:
        rt, ch = df.Cooling_Load_RT.to_numpy(), df.ChillerPlant_kWh.to_numpy()
        keep = rt > h['chiller_low_load_filter_pct_of_peak'] * rt.max()
        for d in sorted(df.day.unique()):
            m = keep & (df.day == d).to_numpy()
            kwrt_series[int(d)] = float(ch[m].sum() / rt[m].sum()) if m.any() else None
        last = None
        for d in kwrt_series:
            if kwrt_series[d] is None:
                kwrt_series[d] = last
            else:
                last = kwrt_series[d]
        valid = {d:v for d,v in kwrt_series.items() if v is not None}
        limit = cfg['regulatory']['chiller_plant_efficiency_limit_kwrt_under_500RT']
        crossing = next((d for d,v in valid.items() if v > limit), None)
        first, lastv = valid[min(valid)], valid[max(valid)]
        if crossing is not None or lastv - first > 0.05:
            drift_kwh = float(sum(rt[(df.day == d).to_numpy()].sum() * (v-first) for d,v in valid.items()))
            findings.append({'id':'chiller_drift', 'title':'Chiller plant efficiency worsening through the month',
                'start_day':min(valid), 'start_date':str(df.Timestamp[df.day == min(valid)].iloc[0].date()),
                'kwrt_start':round(first,3), 'kwrt_end':round(lastv,3), 'kwrt_daily':{d:round(v,3) for d,v in valid.items()},
                'crosses_limit_day':crossing, 'limit_kwrt':limit, 'label':'MEASURED (trend), REGULATORY (limit)',
                'rt_hours_above_low_load_filter':round(float(rt[keep].sum()),0),
                'excess_kwh':{'value':round(drift_kwh,0), 'label':'ESTIMATED', 'basis':f'cooling load x efficiency drift from {first:.3f} kW/RT'},
                'possible_cause':'Possible tube fouling or setpoint drift - unconfirmed',
                'engineer_flag':True, 'engineer_flag_text':ENGINEER_FLAG})
    return {'findings':findings, 'night_day_ratio_daily':{d:round(r,2) for d,r in ratios.items()}, 'faults_found':len(findings)}
