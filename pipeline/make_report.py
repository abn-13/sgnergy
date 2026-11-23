#!/usr/bin/env python3
"""Adapted original gate-before-PDF orchestrator; local files only."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common
import report_content
import report_pdf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--client',default='demo-office')
    ap.add_argument('--month',default='2026-09')
    ap.add_argument('--content',default=None)
    args = ap.parse_args()
    cdir = common.ROOT / 'clients' / args.client
    mdir = cdir / args.month
    cfg,client = common.load_config(),common.load_client(cdir)
    if args.content:
        cpath = Path(args.content)
    else:
        content = report_content.build_content(json.loads((mdir / 'results.json').read_text()),cfg,client,args.month)
        cpath = mdir / 'report_content.json'
        cpath.write_text(json.dumps(content,indent=2))
    gate = subprocess.run([sys.executable,str(Path(__file__).parent / 'validate_report.py'),'--client',args.client,'--month',args.month,'--content',str(cpath)],capture_output=True,text=True)
    print(gate.stdout,end='')
    if gate.returncode:
        print(gate.stderr,end='')
        print('GATE CLOSED - no PDF written.')
        sys.exit(2)
    df = common.load_csv(mdir / 'meter_data.csv')
    charts = report_pdf.make_charts(df,cfg,mdir / 'charts')
    out = mdir / 'report.pdf'
    report_pdf.render_pdf(json.loads(cpath.read_text()),charts,out)
    common.log_action(mdir / 'action_log.jsonl','report_saved',[cpath],[out],'ok','validator passed before save')
    print(f'PDF saved: {out}')
if __name__ == '__main__':
    main()
