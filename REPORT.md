# IPL Team Performance and Trends Analysis

## Title Page

**Project title:** IPL Team Performance and Trends Analysis  
**Student name:** [Enter student name]  
**Roll number:** [Enter roll number]  
**Class / semester:** [Enter class / semester]  
**Department:** [Enter department]  
**College:** [Enter college]  
**Academic year:** [Enter academic year]  

## Abstract

This project describes historical Indian Premier League match outcomes and scoring patterns using Python. Pandas is used to clean, group, and summarize CSV data; NumPy provides descriptive statistics; and Matplotlib and Seaborn create charts. The analysis covers team results, season-level performance, innings totals, and the relationship between innings scores and match outcomes when the supplied files support those calculations. The program generates results from the CSV files placed in `data/`; this report template contains no assumed or fabricated numerical findings.

## Introduction

The Indian Premier League has changed in team composition and format across seasons. A data analysis project can summarize historical outcomes and scoring while making the definitions and limitations clear. The project uses match-level records and optional ball-by-ball records to compare team performance and scoring trends.

## Problem Statement

The project examines how team wins and win percentages vary, how team results change by season, which teams and seasons have notable scoring totals, and how innings scores relate to winning outcomes in comparable matches.

## Objectives

- Summarize matches played, wins, losses, and no-result/tied matches by team.
- Compare team performance and participation across seasons.
- Calculate innings totals and season scoring summaries from delivery records when available.
- Visualize team results and innings scoring distributions.
- Interpret statistical association cautiously without claiming causation.

## Software and Hardware Requirements

- Python 3.9 or later
- Pandas, NumPy, Matplotlib, Seaborn, and Jupyter
- A computer capable of running Python and handling the included CSV data; no specialized hardware is required

## Dataset Description

The project uses `data/matches.csv` and optionally `data/deliveries.csv`. The supplied files have 1,243 match rows and 295,732 delivery rows before cleaning, as counted during project setup. Match data includes `match_id`, `season`, `team1`, `team2`, `winner`, and result fields. Delivery data includes `match_id`, `innings`, `batting_team`, `runs_off_bat`, and `extras`. The format resembles Cricsheet's documented IPL data, but the provenance of the supplied copies was not independently confirmed. See the Cricsheet downloads and terms at https://cricsheet.org/downloads/.

## Methodology

1. Load CSV files and inspect dimensions, columns, data types, and missing values.
2. Remove duplicate match IDs and exact duplicate delivery rows in memory.
3. Exclude match rows missing essential identifiers or participating teams, while retaining no-winner matches.
4. Group match participation by team and season to calculate outcomes.
5. Sum batter runs and extras within each match, innings, and batting team.
6. Join innings information to match outcomes using `match_id`, then create descriptive summaries and plots.

## Data Cleaning Techniques

Cleaning is performed on copies, leaving the input CSVs unchanged. Missing winners are retained and treated as undecided/no-result records rather than losses. Missing optional information such as city or player of the match does not invalidate a match. Three historical franchise labels are normalized for aggregation: Delhi Daredevils to Delhi Capitals, Kings XI Punjab to Punjab Kings, and Rising Pune Supergiant to Rising Pune Supergiants. The mapping is documented in `src/data_cleaning.py` and README.md.

## Statistical Techniques

- **Win percentage:** matches won divided by decided matches (wins plus losses), multiplied by 100. No-result and tied matches are excluded from the denominator.
- **Innings total:** sum of `runs_off_bat + extras` once per delivery. The dataset records extras as a separate total, so extras are added once rather than reconstructed from component columns.
- **Descriptive statistics:** mean, median, population standard deviation, minimum, and maximum of season average innings scores where available.
- **Correlation:** Pearson correlation among season scoring summary variables when enough observations exist. Correlation indicates co-variation and does not establish causation.

## Implementation Details

`main.py` loads and cleans the CSVs, prints the leading team summaries, writes CSV tables and a Markdown run summary to `outputs/reports/`, and saves supported charts to `outputs/charts/`. Reusable functions are in the `src/` package. `notebooks/ipl_analysis.ipynb` presents the analysis in an educational sequence and imports these same functions.

## Graphs and Their Interpretations

The application generates a top-ten wins bar chart, a team win-percentage bar chart, a season wins line chart, and—when delivery data is available—season average innings runs, innings score histogram, team innings score boxplot, first-versus-second innings scatter plot, and scoring-summary correlation heatmap. Interpretations must be made from the generated charts and actual run output; a chart indicates historical patterns and should not be treated as proof of cause.

## Results and Key Findings

Run `python main.py` to generate dataset-specific findings. The generated `outputs/reports/analysis_summary.md`, `team_performance.csv`, `season_performance.csv`, and scoring tables contain the numerical results for the local dataset. No unverified statistics are stated in this report template.

## Limitations

- The provenance of the supplied CSV copies has not been verified beyond their schema.
- Historical team names, tournament formats, and seasons vary; franchise-name normalization is an analytical convention.
- Match-level winner data may not describe ties, abandoned fixtures, or special match outcomes uniformly in all dataset versions.
- Innings scores do not control for venue, innings length, weather, or match conditions.
- Correlation and descriptive summaries do not prove causation.
- If the delivery file is missing, innings scoring analyses cannot be produced.

## Future Scope

Potential extensions include verifying and documenting a precise dataset release, carefully reconciling historical team identities, adding venue-level summaries, and comparing outcomes by toss decision. Any extension should preserve source attribution and avoid claims beyond the data.

## Conclusion

This project provides a reproducible descriptive workflow for IPL team performance and scoring patterns. Results are calculated from the available CSV data, with no-result handling and innings-run definitions documented so that students can explain the analysis and its limitations.

## References

1. Cricsheet, IPL data downloads and documentation, https://cricsheet.org/downloads/ (accessed for schema/source guidance; consult current terms and citation requirements).
2. pandas documentation, https://pandas.pydata.org/docs/.
3. NumPy documentation, https://numpy.org/doc/.
4. Matplotlib documentation, https://matplotlib.org/stable/.
5. Seaborn documentation, https://seaborn.pydata.org/.
