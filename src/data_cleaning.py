"""Conservative in-memory cleaning; source CSVs are never modified."""
import pandas as pd

TEAM_NAMES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
}


def clean_matches(matches):
    df = matches.copy()
    df = df.drop_duplicates(subset="match_id", keep="first")
    df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce")
    df = df.dropna(subset=["match_id", "season", "team1", "team2"]).copy()
    df["match_id"] = df["match_id"].astype("int64")
    df["season"] = df["season"].astype(str).str.strip()
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["team1", "team2", "winner"]:
        if col in df:
            df[col] = df[col].replace(TEAM_NAMES)
    # Missing winner is retained: abandoned/no-result matches are not losses.
    return df.reset_index(drop=True)


def clean_deliveries(deliveries):
    if deliveries is None:
        return None
    df = deliveries.copy()
    df = df.drop_duplicates()
    df["match_id"] = pd.to_numeric(df["match_id"], errors="coerce")
    df["innings"] = pd.to_numeric(df["innings"], errors="coerce")
    df = df.dropna(subset=["match_id", "innings", "batting_team"]).copy()
    for col in ["runs_off_bat", "extras"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["match_id"] = df["match_id"].astype("int64")
    df["innings"] = df["innings"].astype("int64")
    df["batting_team"] = df["batting_team"].replace(TEAM_NAMES)
    return df.reset_index(drop=True)
