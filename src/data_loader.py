"""Loading and validating the supplied IPL CSV files."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _find_column(frame, candidates, required=True):
    lookup = {str(c).strip().lower(): c for c in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    if required:
        raise ValueError(f"Missing required column. Expected one of: {', '.join(candidates)}. Found: {', '.join(map(str, frame.columns))}")
    return None


def load_matches(path=None):
    path = Path(path) if path else DATA_DIR / "matches.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}\nDownload an IPL matches CSV and place it at data/matches.csv. See README.md.")
    frame = pd.read_csv(path, low_memory=False)
    aliases = {
        "match_id": ["match_id", "id"], "season": ["season"], "date": ["date", "start_date"],
        "team1": ["team1", "team_1"], "team2": ["team2", "team_2"], "winner": ["winner"],
        "result": ["result", "result_type"],
    }
    for name, candidates in aliases.items():
        found = _find_column(frame, candidates, required=name not in {"result"})
        if found and found != name:
            frame = frame.rename(columns={found: name})
    return frame


def load_deliveries(path=None, required=False):
    path = Path(path) if path else DATA_DIR / "deliveries.csv"
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Optional file not found: {path}. Innings scoring analyses will be skipped.")
        return None
    frame = pd.read_csv(path, low_memory=False)
    aliases = {"match_id": ["match_id", "id"], "innings": ["innings"], "batting_team": ["batting_team"],
               "runs_off_bat": ["runs_off_bat", "batsman_runs"], "extras": ["extras", "extra_runs"]}
    for name, candidates in aliases.items():
        found = _find_column(frame, candidates)
        if found != name:
            frame = frame.rename(columns={found: name})
    return frame
