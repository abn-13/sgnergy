#!/usr/bin/env python3
"""Adapted original orchestrator. Local artifacts only; no mail integration."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
import intake
import benchmark
import anomaly
import proposal

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client',default='demo-office')
    ap.add_argument('--month',default='2026-09')
    ap.add_argument('--csv',default='meter_data.csv')
    args = ap.parse_args()
    cdir = common.ROOT / 'clients' / args.client
    mdir = cdir / args.month
    csv_path = mdir / args.csv
    log_path = mdir / 'action_log.jsonl'
    cfg, client = common.load_config(), common.load_client(cdir)
    results = {'client':client['client_name'],'month':args.month,'generated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'data_file':args.csv,'disclosure':client['disclosure']}
    def save():
        (mdir / 'results.json').write_text(json.dumps(results,indent=2))
    common.log_action(log_path,'pipeline_start',[csv_path],[],'ok',f'client={args.client} month={args.month}')
    df_raw = common.load_csv(csv_path)
    ir = intake.run(df_raw,client['gfa_m2'])
    df = ir.pop('df_clean')
    results['intake'] = ir
    save()
    if ir['status'] == 'unusable':
        print('INTAKE UNUSABLE: request re-export; no report or delivery.')
        sys.exit(2)
    common.log_action(log_path,'intake',[csv_path],[mdir / 'results.json'],ir['status'],f"{ir['rows']} rows")
    results['benchmark'] = benchmark.run(df,client['gfa_m2'],cfg)
    results['anomaly'] = anomaly.run(df,cfg)
    results['proposal'] = proposal.run(df,results['anomaly'],cfg,raw_df=df_raw)
    save()
    for step in ('benchmark','anomaly','proposal'):
        common.log_action(log_path,step,[csv_path],[mdir / 'results.json'],'ok')
    print(f'AUDIT OK {args.client} {args.month}')
    print(json.dumps(results,indent=2))
if __name__ == '__main__':
    main()
