"""Save clear PNG charts for the analyses supported by the supplied files."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="viridis")


def create_charts(results, output_dir):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    files = []
    def save(name):
        path = out / name
        plt.tight_layout(); plt.savefig(path, dpi=160, bbox_inches="tight"); plt.close(); files.append(path)
    overall = results["overall"]
    top = overall.nlargest(10, "matches_won").sort_values("matches_won")
    plt.figure(figsize=(10, 6)); plt.barh(top.team, top.matches_won, color="#167d8d")
    plt.xlabel("Matches won"); plt.ylabel("Team"); plt.title("Top 10 IPL Teams by Matches Won"); plt.grid(axis="x", alpha=.25); save("top_10_matches_won.png")
    wp = overall.dropna(subset=["win_percentage"]).sort_values("win_percentage")
    plt.figure(figsize=(10, max(5, len(wp)*.35))); sns.barplot(data=wp, x="win_percentage", y="team", color="#d89b2b")
    plt.xlabel("Win percentage (%) among decided matches"); plt.ylabel("Team"); plt.title("IPL Team Win Percentage"); save("team_win_percentage.png")
    season = results["season_team"]
    selected = overall.nlargest(6, "matches_won").team
    plot_data = season[season.team.isin(selected)]
    plt.figure(figsize=(12, 6)); sns.lineplot(data=plot_data, x="season", y="matches_won", hue="team", marker="o")
    plt.xlabel("Season"); plt.ylabel("Matches won"); plt.title("Season-wise Matches Won by Selected Teams"); plt.xticks(rotation=45); plt.legend(title="Team", bbox_to_anchor=(1.02, 1), loc="upper left"); save("season_wins_selected_teams.png")
    scores = results.get("innings")
    if scores is not None and not scores.empty:
        ss = results["season_scores"]
        plt.figure(figsize=(12, 5)); sns.lineplot(data=ss, x="season", y="average_innings_score", marker="o", color="#167d8d")
        plt.xlabel("Season"); plt.ylabel("Average innings runs"); plt.title("Average Innings Score by IPL Season"); plt.xticks(rotation=45); save("average_runs_by_season.png")
        plt.figure(figsize=(9, 5)); sns.histplot(data=scores, x="runs", bins=25, kde=True, color="#167d8d")
        plt.xlabel("Innings total (runs)"); plt.ylabel("Number of innings"); plt.title("Distribution of IPL Innings Scores"); save("innings_score_histogram.png")
        topteams = overall.nlargest(8, "matches_played").team
        plt.figure(figsize=(12, 6)); sns.boxplot(data=scores[scores.batting_team.isin(topteams)], x="batting_team", y="runs")
        plt.xlabel("Team"); plt.ylabel("Innings runs"); plt.title("Innings Score Distribution for Most Frequent Teams"); plt.xticks(rotation=35, ha="right"); save("innings_scores_by_team.png")
        comp = results.get("comparable")
        if comp is not None and not comp.empty:
            plt.figure(figsize=(7, 6)); sns.scatterplot(data=comp, x=1, y=2, hue="first_innings_won", palette={0:"#c45b4d",1:"#167d8d"}, alpha=.6)
            plt.xlabel("First innings runs"); plt.ylabel("Second innings runs"); plt.title("First vs Second Innings Runs (Comparable Matches)"); plt.legend(title="First innings won", labels=["No", "Yes"]); save("first_vs_second_innings.png")
        corr = results.get("correlation")
        if corr is not None:
            plt.figure(figsize=(6, 5)); sns.heatmap(corr, annot=True, cmap="vlag", center=0, fmt=".2f")
            plt.title("Correlation Between Season Scoring Summaries"); save("scoring_correlation_heatmap.png")
    return files
