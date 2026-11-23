#!/usr/bin/env python3
"""NEW portable adaptation of original second demo. Analysis/evaluation only.
Uses exported fixture, never generates or overwrites source data. No mail or
PDF skill dependency, no deletion, backups, host paths or native scripts.
"""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / 'pipeline'))
import common
import intake
import benchmark
import anomaly
import proposal
import report_content
import validate_report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv',type=Path,default=Path(__file__).parent / '2026-09/meter_data.csv')
    ap.add_argument('--output',type=Path,required=True,help='New isolated evidence folder; must not exist')
    args = ap.parse_args()
    cfg = common.load_config()
    client = common.load_client(Path(__file__).parent)
    key = json.loads((Path(__file__).parent / '2026-09/answer_key.json').read_text())
    raw = common.load_csv(args.csv)
    ir = intake.run(raw,client['gfa_m2'])
    clean = ir.pop('df_clean')
    assert ir['status'] == 'pass' and ir['rows'] == 720
    a = anomaly.run(clean,cfg)
    b = benchmark.run(clean,client['gfa_m2'],cfg)
    p = proposal.run(clean,a,cfg,raw_df=raw)
    results = {'benchmark':b,'anomaly':a,'proposal':p,'intake':ir}
    f = {x['id']:x for x in a['findings']}
    checks = {'two_faults_no_weekend_false_positive':set(f) == {'night_waste','chiller_drift'},
              'EUI_within_2_percent':abs(b['eui_kwh_m2_yr']['value']-key['true_totals']['eui_kwh_m2_yr'])/key['true_totals']['eui_kwh_m2_yr'] <= .02,
              'night_onset':f.get('night_waste',{}).get('start_day') == 15,
              'crossing':f.get('chiller_drift',{}).get('crosses_limit_day') == key['kwrt_crosses_0.80_day']}
    errors = {}
    for fid,kid in [('night_waste','A_night_waste'),('chiller_drift','C_chiller_drift')]:
        det = f.get(fid,{}).get('excess_kwh',{}).get('value',0)
        truth = key['faults'][kid]['extra_kwh']
        errors[fid] = abs(det-truth)/truth
        checks[fid+'_within_10_percent'] = errors[fid] <= .10
    content = report_content.build_content(results,cfg,client,'2026-09')
    violations = validate_report.validate(content,raw,client['gfa_m2'],cfg,args.csv)
    checks['report_gate'] = not violations
    evidence = {'pass':all(checks.values()),'checks':checks,'relative_errors':errors,'violations':violations,
                'provenance':'New repository evaluation; distinct from archived original evidence'}
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in [('results.json',results),('report_content.json',content),('eval_results.json',evidence)]:
        (args.output / name).write_text(json.dumps(value,indent=2))
    print(json.dumps(evidence,indent=2))
    return 0 if evidence['pass'] else 1
if __name__ == '__main__':
    sys.exit(main())
