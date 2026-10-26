# IPL Team Performance and Trends Analysis

A beginner-friendly Python mini-project that explores historical IPL team results, season trends, and innings scoring. It uses Pandas and NumPy for analysis and Matplotlib/Seaborn for saved charts. It is descriptive analysis, not a machine-learning project.

## Features

- Team wins, losses, no-result/tied counts, and win percentage
- Season-wise team results and match counts
- Innings totals built from ball-by-ball batter runs plus extras
- Winning and losing innings averages, score distribution, top innings, and season scoring summaries
- PNG charts, CSV tables, and a generated Markdown run summary
- Jupyter notebook using the same reusable `src/` functions as the command-line program

## Project structure

```text
 data/                 supplied CSV datasets
 notebooks/            educational analysis notebook
 src/                  loading, cleaning, analysis, and chart functions
 outputs/charts/       generated PNG visualizations
 outputs/reports/      generated CSV summaries and Markdown report
 main.py               command-line entry point
 REPORT.md             college mini-project report template
 requirements.txt      Python dependencies
```

## Requirements and setup

Use Python 3.9 or later. From the project root:

```bash
python3 -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Dataset source and placement

This project was supplied with `matches.csv` and `deliveries.csv`, placed in `data/`. The files use the Cricsheet IPL ball-by-ball dataset schema: match data with `match_id`, `season`, `team1`, `team2`, `winner`, and delivery data with `match_id`, `innings`, `batting_team`, `runs_off_bat`, and `extras`. The source is [Cricsheet IPL data](https://cricsheet.org/downloads/); please check its current terms and citation guidance when redistributing the files. The CSV files provided locally are included as analysis inputs; their provenance was not verified beyond the column structure.

If setting up from a clean copy, obtain the IPL match and delivery CSV exports from Cricsheet or another documented IPL dataset source, then place them at:

```text
data/matches.csv
data/deliveries.csv
```

The exact columns are validated. `deliveries.csv` is optional: without it, match and season analyses still run, while innings and scoring charts are skipped with a clear message. No dataset is downloaded by the application.

## Run the analysis

From the project root with the virtual environment active:

```bash
python main.py
```

Generated charts are saved in `outputs/charts/`. Summary CSVs and the run-specific Markdown summary are saved in `outputs/reports/`.

## Open the notebook

```bash
jupyter notebook notebooks/ipl_analysis.ipynb
```

Run notebook cells from top to bottom. It imports the same cleaning and analysis functions from `src/`.

## Cleaning and interpretation notes

- Duplicate matches are removed by `match_id`; duplicate delivery records are removed as exact duplicates.
- Rows missing a match identifier, season, or participating teams are excluded from match analysis. Missing winners remain as no-result/undecided matches.
- Historical franchise labels are grouped under later franchise names for three continuing teams: Delhi Daredevils → Delhi Capitals, Kings XI Punjab → Punjab Kings, and Rising Pune Supergiant → Rising Pune Supergiants. These are display/aggregation conventions; team identities and names changed historically.
- Win percentage is wins divided by decided matches (wins plus losses). No-result and tied matches are not losses.
- An innings total is the sum of `runs_off_bat + extras` for every delivery. Extras include the dataset's recorded wides, no-balls, byes, leg-byes, and penalties. Each delivery is counted once.
- Outcome comparison uses actual `match_id` plus innings and batting team. Matches without a reliable winner are excluded from winner-versus-loser summaries. Correlation describes association, not causation.

## Common issues

- **Missing `data/matches.csv`:** download a documented IPL matches CSV and put it at the path shown above.
- **Missing required columns:** compare the CSV headers with the schema listed above. The loader supports common alternatives such as `id`, `batsman_runs`, and `extra_runs`.
- **`ModuleNotFoundError`:** activate the virtual environment and run `python -m pip install -r requirements.txt`.
- **Charts not visible:** open the PNG files under `outputs/charts/`; the script saves charts rather than displaying interactive windows.

## Attribution

Cricsheet provides ball-by-ball cricket data and documents download formats at [cricsheet.org](https://cricsheet.org/). Dataset attribution and reuse terms belong to the upstream source; consult its current guidance before redistribution. Do not infer that a locally provided file is an untouched official export without checking its provenance.

## PitchIQ interactive match predictor

Launch the presentation-friendly Streamlit app from the project root:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\\Scripts\\Activate.ps1` first. PitchIQ provides four illustrative chase templates and a Custom Match form. Changing teams, player selections, score, wickets, overs, or target recalculates the situation automatically. The app is a manual-entry demo; **Live Score Feed Not Connected** is shown explicitly.

No trained model is included in this project. For active second-innings chases, PitchIQ uses a labeled empirical baseline that compares the entered situation with up to 25 nearest historical match states reconstructed from the supplied ball-by-ball data. It shows the number of distinct historical matches in that comparison and warns that the estimate is not calibrated. Player names do not affect it. First-innings and completed-innings states do not get an ordinary win estimate. Strategy advice is general cricket guidance, not player-specific analysis.
