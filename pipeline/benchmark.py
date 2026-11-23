"""Skill 1 - Benchmark: EUI vs Singapore office benchmarks and the MEI line."""

def run(df, gfa_m2, cfg):
    days = (df.Timestamp.max() - df.Timestamp.min()).total_seconds() / 86400 + 1 / 24
    total = float(df.Total_Building_kWh.sum())
    annual = total * 365 / days
    eui = annual / gfa_m2
    b, r = cfg["benchmarks"], cfg["regulatory"]
    median, p75 = b["office_eui_median_kwh_m2_yr"], b["office_eui_p75_kwh_m2_yr"]
    mei = r["mei_office_threshold_kwh_m2_yr"]
    if eui <= median:
        position = "at or below the office median"
    elif eui <= p75:
        position = "above the office median, below the 75th percentile"
    else:
        position = "in the worst quarter of offices"
    return {
        "month_kwh": round(total, 1), "days_of_data": round(days, 1),
        "annual_kwh": {"value": round(annual, 0), "label": "ESTIMATED", "basis": f"extrapolated from {days:.0f} days"},
        "eui_kwh_m2_yr": {"value": round(eui, 1), "label": "ESTIMATED"},
        "benchmarks": {"median": median, "p75": p75, "mei_threshold": mei, "label": "BENCHMARK / REGULATORY"},
        "position": position, "mei_risk": bool(eui > mei),
        "mei_note": (f"EUI {eui:.0f} is above the MEI office threshold of {mei} - mandatory improvement regime may apply [REGULATORY]" if eui > mei else
                     f"EUI {eui:.0f} is {mei - eui:.0f} below the MEI office threshold of {mei}" +
                     (" - one bad year could cross it [REGULATORY]" if mei - eui <= 20 else " - comfortably below the line [REGULATORY]")),
    }
