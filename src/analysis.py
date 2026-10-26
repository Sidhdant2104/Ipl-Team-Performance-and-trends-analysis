"""IPL summary calculations using Pandas and NumPy."""
import numpy as np
import pandas as pd


def match_table(matches):
    rows = []
    for _, m in matches.iterrows():
        teams = [m["team1"], m["team2"]]
        winner = m.get("winner")
        result = str(m.get("result", "")).strip().lower()
        no_result = pd.isna(winner) or "no result" in result or "abandon" in result or "cancel" in result
        tied = "tie" in result or result == "tied"
        for team in teams:
            rows.append({"match_id": m["match_id"], "season": m["season"], "team": team,
                         "win": int(pd.notna(winner) and team == winner),
                         "loss": int(not no_result and not tied and pd.notna(winner) and team != winner),
                         "no_result_or_tie": int(no_result or tied), "decided_match": int(not no_result and not tied and pd.notna(winner))})
    return pd.DataFrame(rows)


def innings_scores(deliveries):
    if deliveries is None or deliveries.empty:
        return pd.DataFrame()
    d = deliveries.copy()
    # Total innings runs = batter runs + all extras, each delivery counted once.
    d["total_runs"] = d["runs_off_bat"] + d["extras"]
    keys = ["match_id", "innings", "batting_team"]
    scores = d.groupby(keys, as_index=False).agg(runs=("total_runs", "sum"), season=("season", "first"))
    return scores


def overall_performance(matches, deliveries=None):
    participation = match_table(matches)
    out = participation.groupby("team").agg(matches_played=("match_id", "nunique"), matches_won=("win", "sum"),
        matches_lost=("loss", "sum"), no_result_or_tied=("no_result_or_tie", "sum"), decided_matches=("decided_match", "sum")).reset_index()
    out["win_percentage"] = np.where(out["decided_matches"] > 0, 100 * out["matches_won"] / out["decided_matches"], np.nan)
    scores = innings_scores(deliveries)
    if not scores.empty:
        totals = scores.groupby("batting_team").agg(total_runs_scored=("runs", "sum"), average_runs_per_innings=("runs", "mean")).reset_index().rename(columns={"batting_team": "team"})
        out = out.merge(totals, on="team", how="left")
    return out.sort_values(["matches_won", "win_percentage"], ascending=False).reset_index(drop=True)


def season_performance(matches):
    participation = match_table(matches)
    summary = participation.groupby(["season", "team"], as_index=False).agg(matches_played=("match_id", "nunique"), matches_won=("win", "sum"),
        matches_lost=("loss", "sum"), decided_matches=("decided_match", "sum"))
    summary["win_percentage"] = np.where(summary.decided_matches > 0, 100 * summary.matches_won / summary.decided_matches, np.nan)
    return summary.sort_values(["season", "matches_won"], ascending=[True, False]).reset_index(drop=True)


def season_match_counts(matches):
    return matches.groupby("season", as_index=False)["match_id"].nunique().rename(columns={"match_id": "matches"}).sort_values("season")


def run_analysis(matches, deliveries):
    scores = innings_scores(deliveries)
    result = {"matches": matches, "overall": overall_performance(matches, deliveries), "season_team": season_performance(matches),
              "season_matches": season_match_counts(matches), "innings": scores}
    if not scores.empty:
        result["season_scores"] = scores.groupby("season", as_index=False).agg(average_innings_score=("runs", "mean"), median_innings_score=("runs", "median"), innings=("runs", "size")).sort_values("season")
        result["highest_innings"] = scores.sort_values("runs", ascending=False).head(1)
        match_outcomes = matches[["match_id", "winner"]].drop_duplicates("match_id")
        scores["match_id"] = scores["match_id"].astype(int)
        comparable = scores[scores["innings"].isin([1, 2])].pivot_table(index="match_id", columns="innings", values="runs", aggfunc="sum").dropna(subset=[1, 2])
        comparable = comparable.reset_index().merge(match_outcomes, on="match_id", how="left")
        comparable["first_innings_won"] = comparable.apply(lambda r: int((r[1] > r[2] and r.winner == scores.loc[(scores.match_id == r.match_id) & (scores.innings == 1), "batting_team"].iloc[0]) or (r[2] > r[1] and r.winner == scores.loc[(scores.match_id == r.match_id) & (scores.innings == 2), "batting_team"].iloc[0])), axis=1)
        result["comparable"] = comparable
        winners = matches[["match_id", "winner"]].dropna(subset=["winner"])
        scores = scores.merge(winners, on="match_id", how="left")
        result["scores_by_outcome"] = scores.assign(outcome=np.where(scores.batting_team == scores.winner, "Winning innings", "Losing innings")).groupby("outcome", as_index=False).agg(average_runs=("runs", "mean"), innings=("runs", "size"))
        values = result["season_scores"]["average_innings_score"].dropna().to_numpy()
        if values.size:
            result["numpy_stats"] = {"mean": float(np.mean(values)), "median": float(np.median(values)), "std": float(np.std(values)), "min": float(np.min(values)), "max": float(np.max(values))}
        corr_data = result["season_scores"][["average_innings_score", "median_innings_score", "innings"]].dropna()
        if len(corr_data) >= 2:
            result["correlation"] = pd.DataFrame(np.corrcoef(corr_data.to_numpy(), rowvar=False), index=corr_data.columns, columns=corr_data.columns)
    return result
