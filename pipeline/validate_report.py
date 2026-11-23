#!/usr/bin/env python3
"""Adapted original R1-R6 validator. Fresh CSV recomputation reuses pipeline
algorithms: independent of results.json, NOT an independent algorithm.
"""
import argparse
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
import intake
import benchmark
import anomaly
import proposal
NUM_RE = re.compile(r'\d+(?:,\d{3})*(?:\.\d+)?')

def truth_map(df,gfa,cfg):
    ir = intake.run(df,gfa)
    dfc = ir['df_clean'] if ir['df_clean'] is not None else df
    b, a = benchmark.run(dfc,gfa,cfg), anomaly.run(dfc,cfg)
    p = proposal.run(dfc,a,cfg,raw_df=df)
    f = {x['id']:x for x in a['findings']}
    t = {'eui':b['eui_kwh_m2_yr']['value'],'annual_kwh':b['annual_kwh']['value'],'month_kwh':b['month_kwh'],
         'tariff':p['tariff_sgd_kwh']['value'],'total_savings_sgd_year':p['total_potential_savings_sgd_year']}
    dq = ir.get('data_quality') or {}
    if dq:
        for field in ('coverage_pct','hours_interpolated','hours_excluded'):
            t['data_coverage_pct' if field == 'coverage_pct' else field] = dq[field]
    for i,x in enumerate(p['top3_issues_sgd_year']):
        t[f'top3.{i}'] = x['sgd_year']
    if 'night_waste' in f:
        x = f['night_waste']
        t.update({'night_waste.ratio_before':x['night_day_ratio_before'],'night_waste.ratio_after':x['night_day_ratio_after'],
                  'night_waste.excess_kwh':x['excess_kwh']['value'],
                  'night_waste.sgd_per_affected_night':p['night_waste_sgd_per_affected_night']['value'],
                  'night_waste.affected_nights':p['night_waste_sgd_per_affected_night']['denominator']['count']})
    if 'weekend_waste' in f:
        x = f['weekend_waste']
        t['weekend_waste.excess_kwh'] = x['excess_kwh']['value']
        for d,v in x['saturday_vs_weekday_pct'].items():
            t[f'weekend_waste.sat_pct.{d}'] = v
    if 'chiller_drift' in f:
        x = f['chiller_drift']
        for field in ('kwrt_start','kwrt_end'):
            t[f'chiller_drift.{field}'] = x[field]
        t['chiller_drift.excess_kwh'] = x['excess_kwh']['value']
    for fx in p['fixes']:
        t[f"{fx['id']}.savings_sgd_year"] = fx['savings_sgd_year']['value']
        t[f"{fx['id']}.cost_sgd"] = fx['cost_sgd']['value']
        if fx['payback_years']['value'] is not None:
            t[f"{fx['id']}.payback_years"] = fx['payback_years']['value']
    return t,p,a

def config_numbers(cfg):
    out = set()
    def walk(x):
        if isinstance(x,(int,float)):
            out.add(float(x))
        elif isinstance(x,dict):
            for v in x.values():
                walk(v)
        elif isinstance(x,list):
            for v in x:
                walk(v)
    walk(cfg)
    out.add(cfg['heuristics']['weekend_vs_weekday_flag']*100)
    return out

def all_text(content):
    parts = [content.get('disclosure','')]
    for s in content['sections']:
        parts.append(s['heading'])
        parts.extend(s['paragraphs'])
    for e in content.get('engineer_items',[]):
        parts.extend([e['item'],e['flag']])
    return parts

def validate(content,df,gfa,cfg,csv_path):
    v = []
    truth,p,a = truth_map(df,gfa,cfg)
    src = f'{csv_path.name} ({len(df)} rows)'
    for c in content['claims']:
        if c.get('label') not in cfg['labels_allowed']:
            v.append(f"[R1 LABEL-MISSING] claim '{c['id']}' has label '{c.get('label')}'.")
    for text in all_text(content):
        low = text.lower()
        for w in cfg['forbidden_words']:
            hit = (w in low) if ' ' in w else re.search(rf'\b{re.escape(w)}\b',low)
            if hit:
                v.append(f"[R2 FORBIDDEN-WORD] '{w}' appears in: {text[:90]}")
    for c in content['claims']:
        if c['id'] not in truth:
            v.append(f"[R5 UNTRACEABLE-CLAIM] '{c['id']}' has no recomputable source in {src}.")
            continue
        tv = truth[c['id']]
        tol = max(0.01*abs(tv),0.5*10**-c.get('precision',2))+1e-9
        if tv is None or abs(c['value']-tv) > tol:
            v.append(f"[R3 NUMBER-MISMATCH] report says '{c['id']}' = {c['value']}; independent recomputation from {src} gives {tv} (tolerance {tol:.4g}). Evidence: {csv_path}")
    flagged = [fx['name'] for fx in p['fixes'] if fx['engineer_flag']] + [x['title'] for x in a['findings'] if x['engineer_flag']]
    have = {e['item']:e.get('flag','') for e in content.get('engineer_items',[])}
    for item in flagged:
        if item not in have or cfg['engineer_flag_text'] not in have[item]:
            v.append(f"[R4 ENGINEER-FLAG-MISSING] '{item}' omits required flag: {cfg['engineer_flag_text']}")
    allowed = {float(c['value']) for c in content['claims']}
    allowed |= config_numbers(cfg)
    allowed |= {float(i) for i in range(0,32)} | {2026.0,365.0}
    for text in all_text(content):
        for m in NUM_RE.finditer(text):
            raw = m.group().replace(',','')
            val = float(raw)
            dec = len(raw.split('.')[1]) if '.' in raw else 0
            tol = 0.5*10**-dec+1e-9
            if not any(abs(val-a_) <= tol for a_ in allowed):
                v.append(f"[R6 UNTRACKED-NUMBER] '{m.group()}' in {text[:70]} matches no claim, benchmark or config value.")
    return v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client',default='demo-office')
    ap.add_argument('--month',default='2026-09')
    ap.add_argument('--content',default=None)
    args = ap.parse_args()
    mdir = common.ROOT / 'clients' / args.client / args.month
    cpath = Path(args.content) if args.content else mdir / 'report_content.json'
    content = json.loads(cpath.read_text())
    cfg = common.load_config()
    client = common.load_client(mdir.parent)
    csv_path = mdir / 'meter_data.csv'
    violations = validate(content,common.load_csv(csv_path),client['gfa_m2'],cfg,csv_path)
    common.log_action(mdir / 'action_log.jsonl','validate_report',[cpath,csv_path],[], 'blocked' if violations else 'pass',f'{len(violations)} violations')
    if violations:
        print('REPORT BLOCKED')
        print('\n'.join(violations))
        sys.exit(2)
    print(f"REPORT VALIDATED - {len(content['claims'])} claims recomputed from {csv_path.name}, all match. Cleared for saving.")
if __name__ == '__main__':
    main()
