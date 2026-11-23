#!/usr/bin/env python3
"""NEW repository-written analysis-only helper. Not the installed Mail helper.
No subprocesses, Mail APIs, network, deletion or state database writes.
"""
import argparse
import math
from pathlib import Path
import pandas as pd

def validate_csv(path,gfa):
    if not math.isfinite(gfa) or gfa <= 0:
        raise ValueError('Explicit positive finite GFA required')
    df = pd.read_csv(path)
    required = ['Timestamp','Total_Building_kWh','ChillerPlant_kWh']
    if df.empty or any(c not in df for c in required):
        raise ValueError('Required columns missing or empty')
    df['Timestamp'] = pd.to_datetime(df.Timestamp,errors='raise')
    if df.Timestamp.isna().any() or df.Timestamp.duplicated().any():
        raise ValueError('Invalid or duplicate timestamps')
    df = df.sort_values('Timestamp')
    if len(df) < 720 or not df.Timestamp.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError('At least 720 continuous hourly readings required')
    for col in required[1:]+(['Cooling_Load_RT'] if 'Cooling_Load_RT' in df else []):
        df[col] = pd.to_numeric(df[col],errors='raise')
        if not df[col].map(math.isfinite).all() or (df[col] < 0).any():
            raise ValueError('Invalid readings')
    if (df.ChillerPlant_kWh > df.Total_Building_kWh).any():
        raise ValueError('Chiller exceeds building total')
    print(f'CSV valid: {len(df)} rows; optional cooling load present={"Cooling_Load_RT" in df}')
    return df

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Local validation only. Mail commands are disabled.')
    ap.add_argument('command',choices=['validate-csv'])
    ap.add_argument('--csv',type=Path,required=True)
    ap.add_argument('--gfa',type=float,required=True)
    args = ap.parse_args()
    validate_csv(args.csv,args.gfa)
