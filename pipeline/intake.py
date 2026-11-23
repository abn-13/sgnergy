"""Skill 0 - Intake: validate AND repair the client's meter data.
pass: clean; partial: repairable or optional columns skipped; unusable: request re-export.
"""
import numpy as np
import pandas as pd
MAX_INTERPOLATE_H = 6

def run(df, gfa_m2):
    checks, critical, issues = [], [], []
    def check(name, ok, detail, severity="critical"):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        if not ok:
            (critical if severity == "critical" else issues).append(f"{name}: {detail}")
    required = ["Timestamp", "Total_Building_kWh", "ChillerPlant_kWh"]
    missing = [c for c in required if c not in df.columns]
    check("required_columns", not missing, f"missing {missing}" if missing else "all present")
    if missing:
        return {"status": "unusable", "checks": checks, "reasons": critical, "df_clean": None}
    n = len(df)
    span_h = (df.Timestamp.max() - df.Timestamp.min()).total_seconds() / 3600 + 1
    check("enough_data", n >= 0.5 * span_h, f"only {n} rows for a {span_h:.0f}-hour span")
    check("gfa_provided", gfa_m2 and gfa_m2 > 0, f"GFA = {gfa_m2} m2")
    if critical:
        return {"status": "unusable", "checks": checks, "reasons": critical, "df_clean": None}
    d = df.copy()
    num_cols = ["Total_Building_kWh", "ChillerPlant_kWh"]
    has_rt = "Cooling_Load_RT" in d.columns
    if has_rt:
        num_cols.append("Cooling_Load_RT")
    neg = int((d[num_cols] < 0).sum().sum())
    if neg:
        issues.append(f"negative_readings: {neg} sensor errors treated as missing")
        d[num_cols] = d[num_cols].mask(d[num_cols] < 0)
    over = d.ChillerPlant_kWh > d.Total_Building_kWh
    if over.any():
        issues.append(f"chiller_gt_total: {int(over.sum())} hours capped at building total (meter inconsistency, flagged)")
        d.loc[over, "ChillerPlant_kWh"] = d.loc[over, "Total_Building_kWh"]
    full_idx = pd.date_range(d.Timestamp.min(), d.Timestamp.max(), freq="h", tz=d.Timestamp.dt.tz)
    d = d.set_index("Timestamp").reindex(full_idx)
    miss = d.Total_Building_kWh.isna()
    runs = miss.groupby((~miss).cumsum()).transform("sum")
    small = miss & (runs <= MAX_INTERPOLATE_H)
    interp = d[num_cols].interpolate(method="time", limit_area="inside")
    d.loc[small, num_cols] = interp.loc[small, num_cols]
    hours_interp = int(small.sum())
    still_missing = d.Total_Building_kWh.isna()
    hours_excluded = int(still_missing.sum())
    if hours_interp:
        issues.append(f"gaps_interpolated: {hours_interp} hours filled (gaps up to {MAX_INTERPOLATE_H}h)")
    if hours_excluded:
        issues.append(f"hours_excluded: {hours_excluded} hours in gaps too large to fill - excluded, coverage stated")
    d = d.dropna(subset=["Total_Building_kWh"]).reset_index().rename(columns={"index": "Timestamp"})
    d["day"] = d.Timestamp.dt.day
    d["hour"] = d.Timestamp.dt.hour
    d["wd"] = d.Timestamp.dt.dayofweek
    coverage = round(len(d) / span_h * 100, 1)
    checks_skipped = []
    if not has_rt:
        checks_skipped.append("chiller_efficiency (Cooling_Load_RT column missing)")
        issues.append("cooling_load_missing: chiller efficiency check skipped, all other checks run")
    return {"status": "partial" if issues else "pass", "checks": checks, "reasons": critical + issues,
            "rows": len(d), "days": round(span_h / 24, 1), "start": str(d.Timestamp.min()), "end": str(d.Timestamp.max()),
            "cooling_load_rt_present": has_rt,
            "data_quality": {"coverage_pct": coverage, "hours_interpolated": hours_interp, "hours_excluded": hours_excluded,
                             "checks_skipped": checks_skipped, "issues": issues}, "df_clean": d}
