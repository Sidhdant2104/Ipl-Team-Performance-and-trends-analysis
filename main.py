"""Run the IPL Team Performance and Trends Analysis from the project root."""
from pathlib import Path
import sys
import pandas as pd
from src.data_loader import ROOT, load_matches, load_deliveries
from src.data_cleaning import clean_matches, clean_deliveries
from src.analysis import run_analysis


def main():
    try:
        matches = clean_matches(load_matches())
        deliveries = clean_deliveries(load_deliveries())
    except (FileNotFoundError, ValueError, pd.errors.ParserError) as exc:
        print(f"Data setup problem: {exc}", file=sys.stderr); return 1
    print("IPL Team Performance and Trends Analysis")
    print(f"Matches: {len(matches):,} rows, {len(matches.columns)} columns; deliveries: {len(deliveries):,} rows" if deliveries is not None else f"Matches: {len(matches):,} rows; deliveries.csv not found, so innings analyses are skipped.")
    print("Missing-value counts in matches:"); print(matches.isnull().sum().to_string())
    results = run_analysis(matches, deliveries)
    print("\nTop teams by wins:"); print(results["overall"].head(10).to_string(index=False))
    if "numpy_stats" in results:
        print("\nSeason average-innings-score statistics (NumPy):", results["numpy_stats"])
        print("Highest-scoring innings:"); print(results["highest_innings"].to_string(index=False))
        if "scores_by_outcome" in results: print("\nAverage innings runs by outcome:"); print(results["scores_by_outcome"].to_string(index=False))
    reports = ROOT / "outputs" / "reports"; reports.mkdir(parents=True, exist_ok=True)
    for key, filename in [("overall", "team_performance.csv"), ("season_team", "season_performance.csv"), ("season_matches", "season_match_counts.csv")]:
        results[key].to_csv(reports / filename, index=False)
    if not results["innings"].empty:
        results["innings"].to_csv(reports / "innings_scores.csv", index=False)
        results["season_scores"].to_csv(reports / "season_scoring_summary.csv", index=False)
    try:
        from src.visualization import create_charts
        chart_files = create_charts(results, ROOT / "outputs" / "charts")
    except ImportError as exc:
        chart_files = []
        print(f"Charts skipped because a plotting dependency is unavailable ({exc}). Install project dependencies with: python -m pip install -r requirements.txt")
    lines = ["# IPL analysis run summary", "", f"- Match records analyzed: {len(matches):,}", f"- Delivery records analyzed: {len(deliveries):,}" if deliveries is not None else "- Delivery records: unavailable; innings analysis skipped.", "", "## Leading teams by wins", "", results["overall"].head(10).to_string(index=False), "", "## Interpretation notes", "", "Win percentage uses decided matches as its denominator. Matches without a winner and ties are not counted as losses or decided matches. Innings totals add runs_off_bat and extras once per delivery. The data shows association and historical patterns; it does not establish that higher scores cause wins.", ""]
    if "numpy_stats" in results: lines += ["## Season average innings score statistics", "", "```text", str(results["numpy_stats"]), "```", ""]
    (reports / "analysis_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nGenerated files:")
    for path in sorted(list(reports.iterdir()) + chart_files): print(f"- {path.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
