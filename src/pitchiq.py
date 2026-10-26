"""PitchIQ match-state calculations and an empirical historical chase baseline.

There is no trained prediction model in this project. The fallback uses nearest
historical second-innings states from the supplied data and reports its sample.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

EXAMPLE_BATTER = "Example Batter (illustrative)"
EXAMPLE_BOWLER = "Example Bowler (illustrative)"

SCENARIOS = {
    "Last-Over Thriller": {
        "batting_team": "Chennai Super Kings", "bowling_team": "Mumbai Indians",
        "target": 177, "score": 157, "wickets": 6, "overs": 19, "balls": 0,
        "striker": "MS Dhoni", "non_striker": EXAMPLE_BATTER, "bowler": EXAMPLE_BOWLER,
        "purpose": "High-pressure final-over chase: 20 needed from 6 legal balls.",
    },
    "Comfortable Chase": {
        "batting_team": "Chennai Super Kings", "bowling_team": "Mumbai Indians",
        "target": 181, "score": 120, "wickets": 2, "overs": 14, "balls": 0,
        "striker": EXAMPLE_BATTER, "non_striker": EXAMPLE_BATTER, "bowler": EXAMPLE_BOWLER,
        "purpose": "A manageable chase rate with wickets in hand.",
    },
    "Difficult Chase": {
        "batting_team": "Mumbai Indians", "bowling_team": "Chennai Super Kings",
        "target": 205, "score": 115, "wickets": 5, "overs": 15, "balls": 0,
        "striker": EXAMPLE_BATTER, "non_striker": EXAMPLE_BATTER, "bowler": EXAMPLE_BOWLER,
        "purpose": "A demanding chase with limited wickets and 30 balls left.",
    },
    "Balanced Chase": {
        "batting_team": "Chennai Super Kings", "bowling_team": "Mumbai Indians",
        "target": 190, "score": 140, "wickets": 3, "overs": 16, "balls": 0,
        "striker": EXAMPLE_BATTER, "non_striker": EXAMPLE_BATTER, "bowler": EXAMPLE_BOWLER,
        "purpose": "A close finish with pressure and wickets still available.",
    },
}


def calculate_match_state(*, score, wickets, overs_completed, balls_completed, total_overs=20, target=None, innings="Second innings"):
    """Validate cricket inputs and calculate state using legal-ball notation."""
    fields = {"score": score, "wickets": wickets, "overs_completed": overs_completed,
              "balls_completed": balls_completed, "total_overs": total_overs}
    for name, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a whole number.")
    if score < 0:
        raise ValueError("Score cannot be negative.")
    if not 0 <= wickets <= 10:
        raise ValueError("Wickets lost must be between 0 and 10.")
    if not 1 <= total_overs <= 20:
        raise ValueError("Total innings overs must be between 1 and 20.")
    if not 0 <= overs_completed <= total_overs:
        raise ValueError("Completed overs must be between zero and the innings length.")
    if not 0 <= balls_completed <= 5:
        raise ValueError("Balls completed in the current over must be between zero and five.")
    if overs_completed == total_overs and balls_completed:
        raise ValueError("Balls completed cannot be added after the full innings length.")
    legal_balls_bowled = overs_completed * 6 + balls_completed
    total_legal_balls = total_overs * 6
    if legal_balls_bowled > total_legal_balls:
        raise ValueError("Legal balls bowled cannot exceed the innings length.")

    chase = innings == "Second innings"
    if chase and (target is None or isinstance(target, bool) or not isinstance(target, (int, np.integer)) or target < 1):
        raise ValueError("Enter a positive whole-number target for a chase.")
    if chase and target <= score and legal_balls_bowled == 0:
        raise ValueError("A target cannot already be reached before the innings starts.")

    balls_remaining = total_legal_balls - legal_balls_bowled
    runs_required = max(int(target) - score, 0) if chase else None
    status = "In progress"
    if chase and score >= target:
        status = "Chase complete"
    elif wickets >= 10:
        status = "Innings ended: all out"
    elif balls_remaining == 0:
        status = "Innings ended: overs completed"

    return {
        "innings": innings, "target": int(target) if chase else None,
        "score": int(score), "wickets_lost": int(wickets), "wickets_remaining": 10-int(wickets),
        "overs_completed": int(overs_completed), "balls_completed": int(balls_completed),
        "legal_balls_bowled": legal_balls_bowled, "legal_balls_remaining": balls_remaining,
        "runs_required": runs_required,
        "required_run_rate": (runs_required * 6 / balls_remaining if chase and balls_remaining > 0 else None),
        "current_run_rate": (score * 6 / legal_balls_bowled if legal_balls_bowled > 0 else None),
        "runs_per_remaining_ball": (runs_required / balls_remaining if chase and balls_remaining > 0 else None),
        "status": status,
    }


def _is_present(series):
    return series.notna() & series.astype(str).str.strip().ne("")


def build_historical_chase_states(matches, deliveries):
    """Make a small training reference of real mid-chase match states.

    Keeps states at 5, 10, 15, 16, 17, 18, and 19 completed overs, plus the
    terminal delivery if needed. A match contributes at most one state per
    checkpoint. A chase is a win when the match table's winner matches the
    second-innings batting team.
    """
    if deliveries is None or deliveries.empty or matches is None or matches.empty:
        return pd.DataFrame(columns=["match_id", "runs_required", "balls_remaining", "wickets_remaining", "won"])
    required = {"match_id", "innings", "batting_team", "runs_off_bat", "extras"}
    if not required.issubset(deliveries.columns):
        return pd.DataFrame(columns=["match_id", "runs_required", "balls_remaining", "wickets_remaining", "won"])
    outcomes = matches[["match_id", "winner"]].dropna(subset=["winner"]).drop_duplicates("match_id").set_index("match_id")["winner"]
    samples = []
    checkpoints = {5, 10, 15, 16, 17, 18, 19}
    d = deliveries.copy()
    # Source CSV order is delivery order. Keep it stable within each match/innings.
    if "actual_delivery" in d:
        d = d.sort_values(["match_id", "innings", "actual_delivery"], kind="stable")
    elif "ball" in d:
        d = d.sort_values(["match_id", "innings", "ball"], kind="stable")
    for match_id, group in d[d["innings"].isin([1, 2])].groupby("match_id", sort=False):
        first = group[group.innings == 1]
        second = group[group.innings == 2]
        if first.empty or second.empty or match_id not in outcomes.index:
            continue
        first_runs = int((first.runs_off_bat.fillna(0) + first.extras.fillna(0)).sum())
        target = first_runs + 1
        batting_team = str(second.iloc[0].batting_team)
        won = int(str(outcomes.loc[match_id]) == batting_team)
        score = 0
        wickets_lost = 0
        legal_balls = 0
        previous_overs = set()
        for _, delivery in second.iterrows():
            score += int(delivery.get("runs_off_bat", 0) or 0) + int(delivery.get("extras", 0) or 0)
            if pd.notna(delivery.get("wicket_type")):
                wickets_lost = min(10, wickets_lost + 1)
            wides = delivery.get("wides", 0)
            noballs = delivery.get("noballs", 0)
            is_legal = not ((pd.notna(wides) and float(wides) > 0) or (pd.notna(noballs) and float(noballs) > 0))
            if is_legal:
                legal_balls += 1
            completed = legal_balls // 6
            if legal_balls % 6 == 0 and completed in checkpoints and completed not in previous_overs:
                previous_overs.add(completed)
                balls_remaining = max(0, 120-legal_balls)
                if score < target and balls_remaining > 0 and wickets_lost < 10:
                    samples.append({"match_id": int(match_id), "runs_required": target-score,
                                    "balls_remaining": balls_remaining, "wickets_remaining": 10-wickets_lost, "won": won})
        # Short/abandoned innings and super-over states do not form standard T20 examples.
    return pd.DataFrame(samples)


def empirical_chase_estimate(state, historical_states, neighbors=25):
    """Estimate from nearest historical states, deduplicated to one row per match.

    Uses distance on required run rate, balls remaining, and wickets remaining.
    Laplace smoothing stabilizes small empirical samples. This is a descriptive
    baseline, not a fitted or calibrated prediction model.
    """
    if state["status"] != "In progress" or state["innings"] != "Second innings":
        return None
    samples = historical_states
    if samples is None or samples.empty or state["legal_balls_remaining"] <= 0:
        return None
    candidates = samples.copy()
    candidates["sample_rrr"] = candidates.runs_required * 6 / candidates.balls_remaining.clip(lower=1)
    candidates["query_rrr"] = state["required_run_rate"]
    candidates["distance"] = (
        (candidates.sample_rrr-candidates.query_rrr).abs()/6
        + (candidates.balls_remaining-state["legal_balls_remaining"]).abs()/120
        + (candidates.wickets_remaining-state["wickets_remaining"]).abs()/10
    )
    # Select the closest state from each historical match to avoid one match
    # dominating the estimate through multiple checkpoints.
    candidates = candidates.sort_values("distance").drop_duplicates("match_id").head(neighbors)
    count = len(candidates)
    if count < 5:
        return None
    wins = int(candidates.won.sum())
    probability = (wins + 1) / (count + 2)
    return {"batting_probability": probability, "bowling_probability": 1-probability,
            "sample_matches": count, "sample_wins": wins,
            "method": "Nearest comparable historical chase states (smoothed empirical baseline)",
            "note": "Descriptive estimate from this dataset; not a trained or calibrated model."}


def batting_recommendations(state):
    if state["status"] != "In progress" or state["innings"] != "Second innings":
        return ["No active chase to advise on; verify the innings state."] * 3
    rrr = state["required_run_rate"]
    wickets = state["wickets_remaining"]
    if rrr is None:
        return ["Keep wickets available while the innings gets underway.", "Build a scoring base through rotation.", "Reassess the required rate after a few legal balls."]
    level = "manageable" if rrr <= 9 else "building pressure" if rrr <= 12 else "demanding"
    items = [f"The required rate is {level} at {rrr:.2f} runs per over; compare it with the current rate before taking extra risk."]
    if wickets <= 3:
        items.append(f"Only {wickets} wicket{'s' if wickets != 1 else ''} remain; prioritize a batter staying in while targeting low-risk scoring options.")
    elif rrr >= 12:
        items.append("Boundary hitting is becoming important; identify a favorable matchup and avoid making every delivery a high-risk swing.")
    else:
        items.append("Use strike rotation to keep both batters involved and preserve boundary options for later overs.")
    if state["legal_balls_remaining"] <= 12 and state["runs_required"] > 12:
        items.append("With two overs or fewer and runs still required, plan for boundaries while keeping the strike with the set batter where possible.")
    elif state["legal_balls_remaining"] <= 30:
        items.append("Map the remaining runs over each over and look for a scoring option every few legal balls.")
    else:
        items.append("Avoid letting dot balls accumulate; reassess the plan at the next over break.")
    return items[:3]


def bowling_recommendations(state):
    if state["status"] != "In progress" or state["innings"] != "Second innings":
        return ["No active chase to advise on; verify the innings state."] * 3
    rrr = state["required_run_rate"]
    wickets = state["wickets_remaining"]
    if rrr is None:
        return ["Start with a disciplined line and length.", "Use the field to protect easy boundaries.", "Reassess after the first over."]
    if rrr >= 12:
        first = "The asking rate is high: protect the boundary while keeping a realistic wicket-taking option in the field."
    elif wickets <= 3:
        first = "Wickets are scarce; attack the new batter with a controlled catching option, while guarding the boundary."
    else:
        first = "Keep the scoring rate under pressure with disciplined lengths and a field that closes easy singles."
    if state["legal_balls_remaining"] <= 12:
        second = "At the death, use yorkers or well-executed slower balls, changing pace and length rather than repeating a predictable line."
    else:
        second = "Mix pace and length only when execution is reliable; avoid offering predictable slot balls."
    third = "Adjust the boundary riders and inner ring to the batter's scoring areas; no player-specific matchup evidence is available."
    return [first, second, third]
