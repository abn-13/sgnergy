"""Shared helpers for the audit pipeline. All numbers come from Python,
never from the model. Every action is logged (AvePoint-style audit trail)."""
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent.parent

def load_config():
    return json.loads((ROOT / "config.json").read_text())

def load_client(client_dir):
    return json.loads((Path(client_dir) / "client.json").read_text())

def load_csv(path):
    df = pd.read_csv(path, parse_dates=["Timestamp"])
    df["day"] = df.Timestamp.dt.day
    df["hour"] = df.Timestamp.dt.hour
    df["wd"] = df.Timestamp.dt.dayofweek
    return df

def log_action(log_path, step, files_read, files_written, outcome, note=""):
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "agent": "monthly-audit", "step": step,
             "files_read": [str(f) for f in files_read],
             "files_written": [str(f) for f in files_written],
             "outcome": outcome, "note": note}
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def sgd(x):
    return round(float(x), 2)
