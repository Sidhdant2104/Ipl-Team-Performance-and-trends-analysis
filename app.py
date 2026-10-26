"""PitchIQ — IPL Win Probability & Strategy Advisor."""
import html
import streamlit as st

from src.data_loader import ROOT, load_matches, load_deliveries
from src.data_cleaning import clean_matches, clean_deliveries
from src.pitchiq import (
    SCENARIOS, EXAMPLE_BATTER, EXAMPLE_BOWLER, calculate_match_state,
    build_historical_chase_states, empirical_chase_estimate,
    batting_recommendations, bowling_recommendations,
)

st.set_page_config(page_title="PitchIQ | IPL Strategy Advisor", page_icon="🏏", layout="wide")

st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background: #f4f7f4; color: #172320; }
[data-testid="stHeader"] { background: rgba(244,247,244,.92); }
.block-container { max-width: 1180px; padding-top: 1.6rem; padding-bottom: 3rem; }
.pitchiq-hero { background: linear-gradient(120deg,#103b2d,#1e5c45); color:#fff; padding:1.45rem 1.7rem; border-radius:16px; margin-bottom:1rem; }
.pitchiq-hero h1 { margin:0; color:#fff; font-size:2rem; }
.pitchiq-hero p { margin:.35rem 0 0; color:#d6e8df; font-size:1.02rem; }
.status-pill { display:inline-block; background:#e2eee7; color:#175239; border:1px solid #bdd6c6; border-radius:999px; padding:.32rem .72rem; font-weight:650; font-size:.82rem; margin:.2rem .35rem .5rem 0; }
.scoreboard { background:#172320; color:#fff; border-radius:14px; padding:1rem 1.2rem; text-align:center; }
.scoreboard .score { font-size:2rem; font-weight:750; letter-spacing:.02em; }
.scoreboard .sub { color:#c7d5ce; font-size:.92rem; }
.probability-bar { display:flex; height:18px; overflow:hidden; border-radius:999px; background:#dce5df; margin:.45rem 0 .25rem; }
.probability-bat { background:#27875b; height:100%; }
.probability-bowl { background:#384942; height:100%; }
.result-card { border:1px solid #dce6df; background:#fff; border-radius:14px; padding:1rem 1.2rem; min-height:100%; }
.result-card h3 { margin-top:0; color:#174d37; }
.demo-note { background:#fff8e7; border:1px solid #f0d99b; border-radius:10px; padding:.7rem .9rem; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e1e9e3; padding:.85rem 1rem; border-radius:12px; }
.stButton > button[kind="primary"] { background:#176b48; border-color:#176b48; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Preparing historical chase examples…")
def load_historical_states(matches, deliveries):
    return build_historical_chase_states(matches, deliveries)


def _default_teams(teams):
    first = teams[0] if teams else ""
    second = next((team for team in teams if team != first), "")
    return first, second


@st.cache_data(show_spinner="Loading the IPL dataset…")
def load_app_data():
    matches = clean_matches(load_matches())
    deliveries = clean_deliveries(load_deliveries())
    return matches, deliveries


def _set_initial_state(teams):
    first, second = _default_teams(teams)
    defaults = {
        "demo_scenario": "Custom Match", "batting_team": first, "bowling_team": second,
        "innings": "Second innings", "total_overs": 20, "score": 0, "wickets": 0,
        "overs": 0, "balls": 0, "target": 1,
        "striker": "Not specified", "non_striker": "Not specified", "bowler": "Not specified",
        "analyzed_state": None, "analyzed_scenario": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _players_for(deliveries, team, role):
    if deliveries is None or not team:
        return []
    col = "striker" if role == "batter" else "bowler"
    team_col = "batting_team" if role == "batter" else "bowling_team"
    if col not in deliveries or team_col not in deliveries:
        return []
    return sorted(deliveries.loc[deliveries[team_col] == team, col].dropna().astype(str).unique().tolist())


def _set_player(key, preferred, options):
    # Add the clearly labeled illustrative placeholder when no verified roster
    # entry matches a particular demo template selection.
    full = list(dict.fromkeys(options + [EXAMPLE_BATTER, EXAMPLE_BOWLER, "Not specified"]))
    st.session_state[key] = preferred if preferred in full else (full[0] if full else "Not specified")


def _apply_demo(teams, deliveries):
    scenario = st.session_state.get("demo_scenario", "Custom Match")
    if scenario == "Custom Match":
        first, second = _default_teams(teams)
        st.session_state.update({"batting_team": first, "bowling_team": second, "innings": "Second innings",
            "total_overs": 20, "score": 0, "wickets": 0, "overs": 0, "balls": 0, "target": 1,
            "analyzed_state": None, "analyzed_scenario": None})
        _set_player("striker", "Not specified", _players_for(deliveries, first, "batter"))
        _set_player("non_striker", "Not specified", _players_for(deliveries, first, "batter"))
        _set_player("bowler", "Not specified", _players_for(deliveries, second, "bowler"))
        return
    template = SCENARIOS[scenario]
    for key in ["batting_team", "bowling_team"]:
        value = template[key]
        st.session_state[key] = value if value in teams else _default_teams(teams)[0 if key == "batting_team" else 1]
    for key in ["target", "score", "wickets", "overs", "balls"]:
        st.session_state[key] = template[key]
    st.session_state.update({"innings": "Second innings", "total_overs": 20,
        "analyzed_state": None, "analyzed_scenario": scenario})
    st.session_state["striker"] = template["striker"]
    st.session_state["non_striker"] = template["non_striker"]
    st.session_state["bowler"] = template["bowler"]


def _clear_analysis():
    st.session_state["analyzed_state"] = None


def _overs_changed():
    st.session_state["analyzed_state"] = None
    total = int(st.session_state.get("total_overs", 20))
    if int(st.session_state.get("overs", 0)) > total:
        st.session_state["overs"] = total
        st.session_state["balls"] = 0


def _teams_changed(teams):
    batting = st.session_state.get("batting_team")
    bowling = st.session_state.get("bowling_team")
    if batting == bowling:
        st.session_state["bowling_team"] = next((team for team in teams if team != batting), "")
    # Player widget values are validated against fresh roster lists during render.
    st.session_state["analyzed_state"] = None


def _reset_match(teams, deliveries):
    st.session_state["demo_scenario"] = "Custom Match"
    _apply_demo(teams, deliveries)


def _formatted_rate(value):
    return "—" if value is None else f"{value:.2f}"


def _render_situation(state):
    st.markdown("### Calculated Match Situation")
    batting_team = html.escape(str(st.session_state.batting_team))
    bowling_team = html.escape(str(st.session_state.bowling_team))
    overs_label = f"{state['overs_completed']}.{state['balls_completed']} overs completed"
    if state["innings"] == "Second innings":
        summary = f"{state['score']}/{state['wickets_lost']} · Target {state['target']} · {state['runs_required']} needed"
    else:
        summary = f"{state['score']}/{state['wickets_lost']} · First innings"
    st.markdown(f'<div class="scoreboard"><div class="sub">{batting_team} batting · {bowling_team} bowling</div><div class="score">{summary}</div><div class="sub">{overs_label}</div></div>', unsafe_allow_html=True)
    if state["innings"] == "Second innings":
        metrics = [
            ("Target", str(state["target"])), ("Current score", f"{state['score']}/{state['wickets_lost']}"),
            ("Runs required", str(state["runs_required"])), ("Wickets remaining", str(state["wickets_remaining"])),
            ("Legal balls remaining", str(state["legal_balls_remaining"])), ("Required run rate", _formatted_rate(state["required_run_rate"])),
        ]
    else:
        metrics = [
            ("Current score", f"{state['score']}/{state['wickets_lost']}"), ("Wickets remaining", str(state["wickets_remaining"])),
            ("Legal balls bowled", str(state["legal_balls_bowled"])), ("Current run rate", _formatted_rate(state["current_run_rate"])),
        ]
    for start in range(0, len(metrics), 3):
        cols = st.columns(3)
        for col, (label, value) in zip(cols, metrics[start:start+3]):
            col.metric(label, value)
    st.caption(f"Current run rate: {_formatted_rate(state['current_run_rate'])}  ·  Runs per remaining ball: {_formatted_rate(state['runs_per_remaining_ball'])}")


def main():
    st.markdown('<div class="pitchiq-hero"><h1>🏏 PitchIQ</h1><p>IPL Win Probability &amp; Strategy Advisor</p></div>', unsafe_allow_html=True)
    st.markdown('<span class="status-pill">Manual Match Entry — Live Score Feed Not Connected</span><span class="status-pill">Historical dataset analysis</span>', unsafe_allow_html=True)
    demo_mode = st.toggle("Demo Mode", value=True, help="Keeps the four presentation scenarios prominent. You can still edit every match input.")

    try:
        matches, deliveries = load_app_data()
    except Exception as exc:
        st.error("IPL data could not be loaded. Check that data/matches.csv exists and has the expected columns.")
        with st.expander("Technical details"):
            st.code(str(exc))
        return
    teams = sorted(set(matches.team1.dropna().astype(str)) | set(matches.team2.dropna().astype(str)))
    _set_initial_state(teams)
    historical_states = load_historical_states(matches, deliveries)

    if demo_mode:
        st.markdown("## Quick Demo Scenarios")
        st.caption("Illustrative templates for a college presentation. These are not verified historical match states.")
    else:
        st.markdown("## Quick Demo Scenarios")
        st.caption("Select a presentation example or choose Custom Match to enter a situation.")
    scenario_names = ["Custom Match", *SCENARIOS.keys()]
    st.selectbox("Load a ready-made example", scenario_names, key="demo_scenario",
                 on_change=_apply_demo, args=(teams, deliveries), help="Choosing a template fills in teams, players, score, wickets, overs, and target.")
    scenario_name = st.session_state.demo_scenario
    if scenario_name in SCENARIOS:
        st.markdown(f'<div class="demo-note"><strong>Illustrative Scenario — Not a Live Match</strong><br>{SCENARIOS[scenario_name]["purpose"]}</div>', unsafe_allow_html=True)
    st.button("↺ Reset Match", on_click=_reset_match, args=(teams, deliveries), key="reset_match")

    st.markdown("## Match Setup")
    team_col1, team_col2 = st.columns(2)
    with team_col1:
        st.selectbox("Batting team", teams, key="batting_team", on_change=_teams_changed, args=(teams,))
    with team_col2:
        bowling_options = [team for team in teams if team != st.session_state.batting_team]
        if st.session_state.bowling_team not in bowling_options and bowling_options:
            st.session_state.bowling_team = bowling_options[0]
        st.selectbox("Bowling team", bowling_options, key="bowling_team", on_change=_teams_changed, args=(teams,))

    batter_options = _players_for(deliveries, st.session_state.batting_team, "batter")
    bowler_options = _players_for(deliveries, st.session_state.bowling_team, "bowler")
    for key, options in [("striker", batter_options), ("non_striker", batter_options), ("bowler", bowler_options)]:
        valid_options = list(dict.fromkeys(options + [EXAMPLE_BATTER, EXAMPLE_BOWLER, "Not specified"]))
        if st.session_state.get(key) not in valid_options:
            st.session_state[key] = "Not specified"
    st.caption("Player dropdowns list historical appearances associated with the selected franchise. They are not verified current rosters; player selection does not affect the estimate.")
    p1, p2, p3 = st.columns(3)
    with p1: st.selectbox("Striker", list(dict.fromkeys(batter_options + [EXAMPLE_BATTER, "Not specified"])), key="striker")
    with p2: st.selectbox("Non-striker", list(dict.fromkeys(batter_options + [EXAMPLE_BATTER, "Not specified"])), key="non_striker")
    with p3: st.selectbox("Current bowler", list(dict.fromkeys(bowler_options + [EXAMPLE_BOWLER, "Not specified"])), key="bowler")

    innings_col, overs_col = st.columns(2)
    with innings_col:
        st.selectbox("Innings", ["First innings", "Second innings"], key="innings", on_change=_clear_analysis)
    with overs_col:
        st.number_input("Total innings overs", min_value=1, max_value=20, step=1, key="total_overs", on_change=_overs_changed)
    s1, s2, s3, s4 = st.columns(4)
    with s1: st.number_input("Current runs", min_value=0, max_value=999, step=1, key="score", on_change=_clear_analysis)
    with s2: st.number_input("Wickets lost", min_value=0, max_value=10, step=1, key="wickets", on_change=_clear_analysis)
    with s3: st.number_input("Completed overs", min_value=0, max_value=int(st.session_state.total_overs), step=1, key="overs", on_change=_clear_analysis)
    with s4: st.number_input("Balls completed in current over", min_value=0, max_value=5, step=1, key="balls", on_change=_clear_analysis)
    if st.session_state.innings == "Second innings":
        st.number_input("Target score", min_value=1, max_value=999, step=1, key="target", on_change=_clear_analysis)
    else:
        st.caption("Target is used only for a second-innings chase.")
    recent_balls = st.text_input("Optional recent legal-ball sequence", placeholder="Example: 1, 0, 4, W, 2, 1", help="Optional context only. Wides and no-balls are not counted as legal balls; use the balls-completed control for the official legal-ball count.")

    try:
        state = calculate_match_state(score=int(st.session_state.score), wickets=int(st.session_state.wickets),
            overs_completed=int(st.session_state.overs), balls_completed=int(st.session_state.balls),
            total_overs=int(st.session_state.total_overs), target=int(st.session_state.target) if st.session_state.innings == "Second innings" else None,
            innings=st.session_state.innings)
        if recent_balls.strip():
            st.caption("Recent-ball sequence is presentation context only; score and legal-ball controls remain authoritative.")
        _render_situation(state)
    except ValueError as exc:
        state = None
        st.error(str(exc))

    analyze = st.button("Analyze Match", type="primary", use_container_width=True, disabled=state is None)
    if analyze and state:
        st.session_state.analyzed_state = state
        st.session_state.analyzed_scenario = scenario_name

    analyzed = st.session_state.get("analyzed_state")
    if analyzed:
        st.markdown("## Match Prediction")
        if analyzed["status"] == "Chase complete":
            st.success(f"Chase complete: {st.session_state.batting_team} reached the target. This is a match state, not a forecast.")
        elif analyzed["status"] != "In progress":
            st.info(f"{analyzed['status']}. No ordinary win estimate is shown for a completed innings.")
        elif analyzed["innings"] != "Second innings":
            st.info("The project has no trained first-innings prediction model. Historical chase estimates are only available for second-innings states.")
        else:
            estimate = empirical_chase_estimate(analyzed, historical_states)
            if estimate is None:
                st.warning("A historical estimate is unavailable: too few comparable completed chases are present in the supplied data.")
            else:
                batting_name = st.session_state.batting_team
                bowling_name = st.session_state.bowling_team
                batting_pct = 100 * estimate["batting_probability"]
                bowling_pct = 100 * estimate["bowling_probability"]
                st.caption("Empirical historical baseline — no trained model is included in this project. This estimate is not calibrated and cannot account for all match conditions.")
                c1, c2 = st.columns(2)
                c1.metric(f"{batting_name} · batting", f"{batting_pct:.1f}%")
                c2.metric(f"{bowling_name} · bowling", f"{bowling_pct:.1f}%")
                st.markdown(f'<div class="probability-bar" role="img" aria-label="Batting team {batting_pct:.1f} percent, bowling team {bowling_pct:.1f} percent"><div class="probability-bat" style="width:{batting_pct:.3f}%"></div><div class="probability-bowl" style="width:{bowling_pct:.3f}%"></div></div>', unsafe_allow_html=True)
                st.caption(f"{batting_name}: green · {bowling_name}: charcoal")
                st.markdown(f"**Method:** {estimate['method']} · **Comparable historical matches:** {estimate['sample_matches']} · **Chase wins in sample:** {estimate['sample_wins']}")
                st.info(estimate["note"] + " Outcomes remain uncertain; the estimate is descriptive and may be unreliable for a state unlike the historical sample.")
                with st.expander("Why this estimate?"):
                    st.write(f"It compares required rate ({analyzed['required_run_rate']:.2f}), legal balls remaining ({analyzed['legal_balls_remaining']}), and wickets remaining ({analyzed['wickets_remaining']}) with the nearest unique historical match states.")
                    st.write("Team identities, player names, current bowler, venue, weather, toss, and recent-ball text are not baseline features and do not affect this estimate.")

        st.markdown("### Tactical Recommendations")
        bat, bowl = st.columns(2)
        with bat:
            with st.container(border=True):
                st.markdown("### Batting strategy")
                st.caption("General tactical guidance based on the entered match state.")
                for item in batting_recommendations(analyzed): st.markdown(f"- {item}")
        with bowl:
            with st.container(border=True):
                st.markdown("### Bowling strategy")
                st.caption("General guidance; no player matchup advantage is assumed.")
                for item in bowling_recommendations(analyzed): st.markdown(f"- {item}")
        st.caption("Predictions are estimates, not guarantees. This app uses manual inputs and does not follow live matches.")


if __name__ == "__main__":
    main()
