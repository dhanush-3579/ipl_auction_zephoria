"""
IPL Analytics Pro — Full App (Bug-Fixed & Enhanced)
Requires:
  - IPL_Stat_2008_2025.json
  - player_team_season_mapping_info_and_images.json
  - short_name_to_full_name.json
Run:  streamlit run app.py
"""

import base64
import math
import math
import re

import streamlit as st
import json, os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL Analytics Pro",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.stApp { background: #0A0E1A; color: #E8EAF0; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0D1220 0%,#111827 100%) !important;
    border-right: 1px solid #1F2937;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }

.ipl-hero { text-align:center; padding: 24px 0 8px; }
.ipl-hero h1 {
    font-family:'Bebas Neue',cursive;
    font-size:3.6rem;
    letter-spacing:5px;
    background:linear-gradient(90deg,#F97316,#FBBF24,#F97316);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin:0;
}
.ipl-hero p {
    color:#64748B; font-size:.85rem;
    letter-spacing:3px; text-transform:uppercase; margin-top:-4px;
}

.stat-card {
    background:linear-gradient(135deg,#111827,#1E2A3B);
    border:1px solid #1F2937; border-radius:14px;
    padding:18px 20px; text-align:center;
    transition: transform .2s, box-shadow .2s;
}
.stat-card:hover {
    transform:translateY(-3px);
    box-shadow:0 8px 28px rgba(249,115,22,.18);
}
.stat-val {
    font-family:'Bebas Neue',cursive;
    font-size:2.6rem; color:#F97316;
    letter-spacing:2px; line-height:1;
}
.stat-lbl {
    font-size:.68rem; color:#64748B;
    text-transform:uppercase; letter-spacing:2px; margin-top:4px;
}

.sec-hdr {
    font-family:'Bebas Neue',cursive;
    font-size:1.7rem; color:#F97316;
    letter-spacing:3px;
    border-bottom:2px solid #F97316;
    padding-bottom:6px; margin: 24px 0 16px;
}

.pchip {
    display:inline-block; padding:4px 14px;
    border-radius:20px; font-size:.75rem;
    font-weight:600; letter-spacing:1px; margin:2px;
}
.bat  { background:rgba(249,115,22,.18); color:#FB923C; }
.bowl { background:rgba(59,130,246,.18); color:#60A5FA; }
.ar   { background:rgba(16,185,129,.18); color:#34D399; }
.wk   { background:rgba(167,139,250,.18); color:#A78BFA; }

.d11card {
    background:linear-gradient(135deg,#141E2F,#1C2840);
    border:1px solid #FFD700; border-radius:16px;
    padding:14px 10px; text-align:center;
    transition:all .2s; height:100%;
}
.d11card:hover {
    box-shadow:0 6px 22px rgba(255,215,0,.2);
    transform:translateY(-3px);
}
.d11name {
    font-family:'Bebas Neue',cursive;
    font-size:1.05rem; color:#E8EAF0; letter-spacing:1px;
}
.cbadge {
    background:linear-gradient(135deg,#FFD700,#F97316);
    color:#000; font-weight:800; font-size:.65rem;
    padding:2px 8px; border-radius:10px; letter-spacing:1px;
}
.vcbadge {
    background:linear-gradient(135deg,#9CA3AF,#6B7280);
    color:#000; font-weight:800; font-size:.65rem;
    padding:2px 8px; border-radius:10px; letter-spacing:1px;
}

[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }
div[data-testid="stTabs"] button {
    font-family:'Outfit',sans-serif !important;
    font-weight:600 !important;
}
hr { border-color:#1F2937 !important; }

/* ── Winner banner ── */
.winner-banner {
    text-align:center; padding:32px;
    background:linear-gradient(135deg,#111827,#1E2A3B);
    border-radius:16px;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  ROLE MAP  (defined here — was missing, causing NameError)
# ═══════════════════════════════════════════════════════════════

ROLE_MAP = {
    "WK-Batter": "WK", "Wicket Keeper": "WK", "Wicketkeeper": "WK",
    "WK Batter":  "WK", "wk-batter": "WK",
    "Batter":     "BAT", "Batsman": "BAT", "bat": "BAT",
    "Bowler":     "BOWL", "bowl": "BOWL",
    "All-Rounder":"AR", "Allrounder": "AR", "AR": "AR", "all-rounder": "AR",
}

def classify_role(player: str) -> str:
    """Fallback role classifier based on available stat keys."""
    has_bat  = bool(stat_data.get(player, {}).get("op_Bowler"))
    has_bowl = bool(stat_data.get(player, {}).get("op_Batter"))
    if has_bat and has_bowl: return "AR"
    if has_bowl:             return "BOWL"
    return "BAT"


# ═══════════════════════════════════════════════════════════════
#  DATA LOADING
# ═══════════════════════════════════════════════════════════════

@st.cache_data
def load_stat_data() -> dict:
    path = "IPL_Stat_2008_2025.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

@st.cache_data
def load_player_names() -> dict:
    path = "short_name_to_full_name.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

@st.cache_data
def load_squad_data() -> dict:
    path = "player_team_season_mapping_info_and_images.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
@st.cache_data
def get_teams_playing_recently():
    path = "teams_playing_11_players.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
    
# def update_teams_playing_recently(team1, team2, selected_players1, selected_players2):
#     path = "teams_playing_11_players.json"
#     if team_playing11_recently.get(str(team1)) == []:
#        team_playing11_recently[str(team1)] = selected_players1
#     if team_playing11_recently.get(str(team2)) == []:
#         team_playing11_recently[str(team2)] = selected_players2

    

#     if os.path.exists(path):
#         with open(path, "r") as f:
#             old_data = json.load(f)
#     else:
#         old_data = {}

#     if old_data != team_playing11_recently:
#         with open(path, "w") as f:
#             json.dump(team_playing11_recently, f)

def get_player_image(player):
    def get_base64_image(path):
            try : 
                with open(path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except Exception as e:
                default_path = os.path.join("ipl_player_images", "Aakash Chopra.png")
                with open(default_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()

    img_path = os.path.join("ipl_player_images", f"{player}.png")
    return get_base64_image(img_path)
stat_data  = load_stat_data()
squad_data = load_squad_data()
playerNames = load_player_names()
PN_L_to_S = {playerNames[i]:i for i in playerNames}
team_playing11_recently = get_teams_playing_recently()
stat_data  = load_stat_data()
squad_data = load_squad_data()
playerNames = load_player_names()
PN_L_to_S = {v: k for k, v in playerNames.items()}  # long_name → short_name

# ─── Data-missing guard ──────────────────────────────────────────────────────
if not stat_data or not squad_data:
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1></div>', unsafe_allow_html=True)
    missing = []
    if not stat_data:  missing.append("`IPL_Stat_2008_2025.json`")
    if not squad_data: missing.append("`player_team_season_mapping_info_and_images.json`")
    st.error(f"⚠️  Missing data files: {', '.join(missing)}")
    st.info("Place both JSON files in the **same folder** as `app.py`, then refresh.")
    st.stop()

# ═══════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════

def safe_max(lst, default=0):
    """max() that returns default for empty lists."""
    return max(lst) if lst else default

def safe_min(lst, default=0):
    return min(lst) if lst else default

def role_chip_Batter(player):
    return "Batter" if stat_data.get(player, {}).get("op_Bowler") else ""

def role_chip_Bowler(player):
    return "Bowler" if stat_data.get(player, {}).get("op_Batter") else ""

def get_teams():
    return sorted(squad_data.keys())

def get_seasons(team):
    return sorted(squad_data[team].keys(), reverse=True)

def get_squad(team, season):
    return squad_data.get(team, {}).get(season, {}).get("Players_Detail", {})

def get_common_seasons(t1, t2):
    s1 = set(squad_data.get(t1, {}).keys())
    s2 = set(squad_data.get(t2, {}).keys())
    return sorted(s1 & s2, reverse=True)

def get_team_players(team,season=None):
    if season:
        return sorted(squad_data.get(team, {}).get(season, {}).get("Players_Detail", {}).keys())
    else:
        players = set()
        for s in squad_data.get(team, {}):
            players.update(squad_data[team][s].get("Players_Detail", {}).keys())
    return sorted(players)

# ── Stat lookups ─────────────────────────────────────────────────────────────

def stat_vs_team(player, opp_team):
    return stat_data.get(PN_L_to_S.get(player, player), {}).get("op_team", {}).get(opp_team, {})

def stat_vs_bowler(player, bowler):
    key = PN_L_to_S.get(bowler, bowler)
    return stat_data.get(PN_L_to_S.get(player, player), {}).get("op_Bowler", {}).get(key, {})

def stat_vs_batter(player, batter):
    key = PN_L_to_S.get(batter, batter)
    return stat_data.get(PN_L_to_S.get(player, player), {}).get("op_Batter", {}).get(key, {})

def recent_form(player):
    return stat_data.get(PN_L_to_S.get(player, player), {}).get("Last_recent_matches", {})

def all_teams_stats(player):
    return stat_data.get(PN_L_to_S.get(player, player), {}).get("op_team", {})

# ── Career summaries ─────────────────────────────────────────────────────────

def career_summary_Batter(player):
    td = all_teams_stats(player)
    if not td:
        return {"matches":0,"runs":0,"sr":0,"avg":0,"wickets":0,
                "50s":0,"100s":0,"matches_played":0,"highest_score":0}

    total_runs   = sum(v.get("Bt_Runs", 0)      for v in td.values())
    total_balls  = sum(v.get("Bt_Balls", 0)     for v in td.values())
    total_wkts   = sum(v.get("Lose_Wicket", 0)  for v in td.values())
    total_m      = sum(v.get("Matches", 0)      for v in td.values())

    all_run_lists  = [x for v in td.values() for x in v.get("Bt_Runs_list", [])]
    all_ball_lists = [x for v in td.values() for x in v.get("Bt_Balls_list", [])]

    matches_played = sum(1 for x in all_ball_lists if x > 0)
    total_50s  = sum(1 for x in all_run_lists if 50 <= x < 100)
    total_100s = sum(1 for x in all_run_lists if x >= 100)
    highest    = safe_max(all_run_lists, 0)

    return {
        "matches":        total_m,
        "runs":           total_runs,
        "sr":             round(total_runs / total_balls * 100, 2) if total_balls > 0 else 0,
        "avg":            round(total_runs / max(matches_played, 1), 2),
        "wickets":        total_wkts,
        "50s":            total_50s,
        "100s":           total_100s,
        "matches_played": matches_played,
        "highest_score":  highest,
    }

def career_summary_Bowler(player):
    td = all_teams_stats(player)
    if not td:
        return {"matches":0,"matches_played":0,"wickets":0,"economy":0,
                "bwballs":0,"best3":0,"best4":0,"best5":0,"highwicket":0}

    total_wkts = sum(v.get("Gain_Wicket", 0) for v in td.values())
    total_bwb  = sum(v.get("Bw_Balls", 0)    for v in td.values())
    total_bwr  = sum(v.get("Bw_Runs", 0)     for v in td.values())
    total_m    = sum(v.get("Matches", 0)     for v in td.values())

    all_bw_ball_lists = [x for v in td.values() for x in v.get("Bw_Balls_list", [])]
    all_w_lists       = [x for v in td.values() for x in v.get("Bw_W_list", [])]

    matches_played = sum(1 for x in all_bw_ball_lists if x > 0) or total_m
    best3      = sum(1 for x in all_w_lists if x == 3)
    best4      = sum(1 for x in all_w_lists if x == 4)
    best5      = sum(1 for x in all_w_lists if x >= 5)
    highwicket = safe_max(all_w_lists, 0)

    return {
        "matches":        total_m,
        "matches_played": matches_played,
        "wickets":        total_wkts,
        "economy":        round((total_bwr / total_bwb) * 6, 2) if total_bwb > 0 else 0,
        "bwballs":        total_bwb,
        "best3":          best3,
        "best4":          best4,
        "best5":          best5,
        "highwicket":     highwicket,
    }

def career_summary_team(player, t):
    """Per-team career summary. Safe against empty lists."""
    td   = all_teams_stats(player)
    team = td.get(t, {})
    if not team:
        return {k: 0 for k in [
            "matches","total_bt_matches_played","total_bw_matches_played",
            "btruns","total_btW","total_bwW","economy","sr","avg",
            "50s","100s","3W","4W","5W+","highest_bt_score","highest_wicket"
        ]}

    bt_runs_list = team.get("Bt_Runs_list", [])
    bt_balls_list= team.get("Bt_Balls_list", [])
    bw_balls_list= team.get("Bw_Balls_list", [])
    bw_w_list    = team.get("Bw_W_list", [])

    total_btruns = team.get("Bt_Runs", 0)
    total_btballs= team.get("Bt_Balls", 0)
    total_bwruns = team.get("Bw_Runs", 0)
    total_bwballs= team.get("Bw_Balls", 0)
    total_bt_W   = team.get("Lose_Wicket", 0)
    total_bw_W   = team.get("Gain_Wicket", 0)
    total_m      = team.get("Matches", 0)

    bt_matches   = sum(1 for x in bt_balls_list if x > 0)
    bw_matches   = sum(1 for x in bw_balls_list if x > 0)
    total_50s    = sum(1 for x in bt_runs_list if 50 <= x < 100)
    total_100s   = sum(1 for x in bt_runs_list if x >= 100)
    highest_bt   = safe_max(bt_runs_list, 0)
    best3        = sum(1 for x in bw_w_list if x == 3)
    best4        = sum(1 for x in bw_w_list if x == 4)
    best5        = sum(1 for x in bw_w_list if x >= 5)
    highest_wkt  = safe_max(bw_w_list, 0)

    return {
        "matches":                total_m,
        "total_bt_matches_played":bt_matches,
        "total_bw_matches_played":bw_matches,
        "btruns":                 total_btruns,
        "total_btW":              total_bt_W,
        "total_bwW":              total_bw_W,
        "economy":                round((total_bwruns / total_bwballs) * 6, 2) if total_bwballs > 0 else 0,
        "sr":                     round(total_btruns / total_btballs * 100, 2) if total_btballs > 0 else 0,
        "avg":                    round(total_btruns / max(total_bt_W, 1), 2),
        "50s":                    total_50s,
        "100s":                   total_100s,
        "3W":                     best3,
        "4W":                     best4,
        "5W+":                    best5,
        "highest_bt_score":       highest_bt,
        "highest_wicket":         highest_wkt,
    }

# ─── Shared chart helpers ────────────────────────────────────────────────────

PLOTLY_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font_color="#CBD5E1", margin=dict(l=10, r=10, t=40, b=30),
)

def dark_fig_layout(fig, title="", height=320, title_color="#F97316", **kwargs):
    fig.update_layout(
        title=title, title_font_color=title_color,
        height=height,
        xaxis=dict(gridcolor="#1F2937"),
        yaxis=dict(gridcolor="#1F2937"),
        **PLOTLY_BASE, **kwargs
    )
    return fig

def runs_wicket_chart(runs_list, w_list, title=""):
    """Reusable runs-bar + wicket-star chart."""
    x_vals = list(range(1, len(runs_list) + 1))
    fig = go.Figure(go.Bar(
        x=x_vals, y=runs_list,
        marker_color=['#F97316' if r >= 50 else '#FBBF24' if r >= 30 else '#374151' for r in runs_list],
        name="Runs",
    ))
    # ── FIX: safe wicket marker logic ──────────────────────────────────────
    first_wkt_added = False
    for i, (runs, wkts) in enumerate(zip(runs_list, w_list)):
        if wkts > 0:
            fig.add_trace(go.Scatter(
                x=[x_vals[i]], y=[runs],
                mode='markers',
                marker=dict(size=14, color='#EF4444', symbol='star',
                            line=dict(color='#FCA5A5', width=2)),
                name='Wicket' if not first_wkt_added else None,
                showlegend=not first_wkt_added,
                hovertemplate=f'Match {x_vals[i]}<br>Runs: {runs}<br>W: {int(wkts)}<extra></extra>',
            ))
            first_wkt_added = True
    dark_fig_layout(fig, title=title, height=320)
    fig.update_layout(xaxis_title="Match", yaxis_title="Runs", hovermode='x unified')
    return fig

# ═══════════════════════════════════════════════════════════════
#  DREAM11 SCORING ENGINE
# ═══════════════════════════════════════════════════════════════

def dream11_score(player, squad_role, opp_team):
    sc  = 0.0
    vs  = stat_vs_team(player, opp_team)
    rec = recent_form(player)

    h2h_m   = max(vs.get("Matches", 1), 1)
    h2h_avg = vs.get("Bt_Avg", vs.get("Bt_Runs", 0) / h2h_m)
    h2h_sr  = vs.get("Bt_Strike_rate", 0)
    sc += h2h_avg * 1.2
    sc += max(h2h_sr - 100, 0) * 0.15

    h2h_wkts = vs.get("Gain_Wicket", 0)
    h2h_econ = vs.get("Bw_economy", 10)
    sc += (h2h_wkts / h2h_m) * 20
    sc += max(9 - h2h_econ, 0) * 2

    rec_avg  = rec.get("Bt_Avg", 0)
    rec_sr   = rec.get("Bt_Strike_rate", 0)
    rec_bw_e = rec.get("Bw_economy", 10)
    rec_bw_w = rec.get("Bw_Avg_Wickets", 0)
    sc += rec_avg * 0.9
    sc += max(rec_sr - 100, 0) * 0.1
    sc += rec_bw_w * 15
    sc += max(9 - rec_bw_e, 0) * 1.5

    r = ROLE_MAP.get(squad_role, classify_role(player))
    if r == "WK": sc += 10
    if r == "AR": sc += 8
    return round(sc, 2)

def pick_dream11(squad1, squad2, team1_name, team2_name):
    all_players = []
    for p, info in squad1.items():
        role = ROLE_MAP.get(info.get("role", "Batter"), classify_role(p))
        sc   = dream11_score(p, info.get("role", "Batter"), team2_name)
        all_players.append({"player": p, "role": role, "team": team1_name, "score": sc, "img": info.get("img", "")})
    for p, info in squad2.items():
        role = ROLE_MAP.get(info.get("role", "Batter"), classify_role(p))
        sc   = dream11_score(p, info.get("role", "Batter"), team1_name)
        all_players.append({"player": p, "role": role, "team": team2_name, "score": sc, "img": info.get("img", "")})

    all_players.sort(key=lambda x: x["score"], reverse=True)

    limits  = {"WK": 1, "BAT": 4, "AR": 3, "BOWL": 3}
    counts  = defaultdict(int)
    t_count = defaultdict(int)
    selected = []

    for p in all_players:
        if len(selected) >= 11: break
        r, t = p["role"], p["team"]
        if counts[r] < limits.get(r, 4) and t_count[t] < 7:
            selected.append(p)
            counts[r] += 1
            t_count[t] += 1

    # Fill remaining if still < 11
    for p in all_players:
        if len(selected) >= 11: break
        if p not in selected:
            selected.append(p)

    return selected

# ═══════════════════════════════════════════════════════════════
#  PREDICTION ENGINE
# ═══════════════════════════════════════════════════════════════

def predict_performance(player, opp_team):
    vs  = stat_vs_team(player, opp_team)
    rec = recent_form(player)

    h2h_m = max(vs.get("Matches", 0), 1)
    w_h2h = min(h2h_m / 15, 0.7)
    w_rec = 1 - w_h2h

    h2h_avg = vs.get("Bt_Avg", 0)
    h2h_sr  = vs.get("Bt_Strike_rate", 0)
    rec_avg = rec.get("Bt_Avg", 0)
    rec_sr  = rec.get("Bt_Strike_rate", 0)

    pred_runs = round(h2h_avg * w_h2h + rec_avg * w_rec, 0)
    pred_sr   = round(h2h_sr  * w_h2h + rec_sr  * w_rec, 0)

    h2h_wkts  = vs.get("Gain_Wicket", 0)
    rec_wpm   = rec.get("Bw_Avg_Wickets", 0)
    pred_wkts = (h2h_wkts / h2h_m) * w_h2h + rec_wpm * w_rec
    pred_wkts = math.floor(pred_wkts + 0.5)

    h2h_econ  = vs.get("Bw_economy", 0)
    rec_econ  = rec.get("Bw_economy", 0)
    pred_econ = round(h2h_econ * w_h2h + rec_econ * w_rec, 2)

    six_list  = vs.get("Six_list", [])
    four_list = vs.get("four_list", [])
    pred_4s   = round(sum(four_list) / max(len(four_list), 1), 0)
    pred_6s   = round(sum(six_list)  / max(len(six_list), 1), 0)
    pred_4s   = math.floor(pred_4s + 0.5)
    pred_6s   = math.floor(pred_6s + 0.5)

    return {
        "runs": pred_runs, "sr": pred_sr,
        "wickets": pred_wkts, "economy": pred_econ,
        "fours": pred_4s, "sixes": pred_6s,
        "h2h_matches": h2h_m - 1,
    }

# ═══════════════════════════════════════════════════════════════
#  WIN PROBABILITY ENGINE
# ═══════════════════════════════════════════════════════════════

def team_strength_score(squad, opp_team):
    """Compute aggregate team strength vs opponent."""
    total = 0.0
    for p, info in squad.items():
        pred = predict_performance(p, opp_team)
        role = ROLE_MAP.get(info.get("role", "Batter"), classify_role(p))
        bat_contrib  = pred["runs"] * (1 + (pred["sr"] - 100) / 1000 if pred["sr"] > 0 else 1)
        bowl_contrib = pred["wickets"] * 20 + max(8 - pred["economy"], 0) * 3 if pred["economy"] > 0 else pred["wickets"] * 20
        if role == "BAT":  total += bat_contrib * 1.0
        elif role == "BOWL": total += bowl_contrib * 1.0
        elif role == "AR":   total += bat_contrib * 0.7 + bowl_contrib * 0.7
        else:                total += bat_contrib * 0.9
    return round(total, 2)

def win_probability(squad1, squad2, team1_name, team2_name):
    s1 = team_strength_score(squad1, team2_name)
    s2 = team_strength_score(squad2, team1_name)
    total = s1 + s2 if (s1 + s2) > 0 else 1
    p1 = round(s1 / total * 100, 1)
    p2 = round(100 - p1, 1)
    return p1, p2, s1, s2

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════

teams = get_teams()

with st.sidebar:
    st.markdown("""
    <div style="font-family:'Bebas Neue',cursive;font-size:1.6rem;color:#F97316;
                letter-spacing:3px;text-align:center;padding:12px 0;
                border-bottom:1px solid #1F2937;margin-bottom:16px">
        🏏 IPL PRO
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("📊 Features", [
        "🏟️  All Player Stats",
        "👤  Prediction Match Wins",
        "⭐  Dream11 Predictor",
        "🔮  Match Scorecard Prediction",
    ], label_visibility="collapsed")

    # ── Global team/season pickers (used by pages 2-4) ──
    if page != "🏟️  All Player Stats":
        st.markdown("---")
        st.markdown("**⚙️ Match Setup**")

        team1 = st.selectbox("🔴 Team 1", teams, key="g_t1")
        team2_options = [t for t in teams if t != team1]
        team2 = st.selectbox("🔵 Team 2", team2_options, key="g_t2")

        # common = get_common_seasons(team1, team2)
        # if common:
        #     season = st.selectbox("📅 Season", common, key="g_season")
        # else:
        #     st.warning("No common seasons found.")
        #     season = None
        season = "2026"

# ═══════════════════════════════════════════════════════════════
#  PAGE 1 — ALL PLAYER STATS
# ═══════════════════════════════════════════════════════════════

if page == "🏟️  All Player Stats":
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1><p>Player Intelligence Platform · 2008–2025</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">📊 PLAYER STATISTICS</div>', unsafe_allow_html=True)

    all_players = sorted(list(PN_L_to_S.keys()))
    selected_player = st.selectbox("Select Player", all_players, key="player_select")

    if selected_player:
        short_name  = PN_L_to_S.get(selected_player, selected_player)
        player_info = stat_data.get(short_name, {})
        img_base64 = get_player_image(selected_player)
        # Player header with role classification
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
            <img src="data:image/png;base64,{img_base64}"
                style="width:200px;height:200px;border-radius:40px;object-fit:cover;border:2px solid #F97316;">
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                <div style="font-size:1.8rem;color:#E8EAF0;"> {   selected_player}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        is_batter = role_chip_Batter(short_name) == "Batter"
        is_bowler = role_chip_Bowler(short_name) == "Bowler"

        # ── Batting summary header ──
        if is_batter:
            cs = career_summary_Batter(short_name)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                <div>
                    <span class="pchip bat">Batter</span>
                    <span style="color:#64748B;font-size:.8rem;margin-left:8px">Career Statistics</span>
                </div>
            </div>""", unsafe_allow_html=True)

            cols = st.columns(6)
            for c, (lbl, val, col) in zip(cols, [
                ("INNINGS",    cs["matches_played"],              "#F97316"),
                ("RUNS",       cs["runs"],                        "#FBBF24"),
                ("BAT AVG",    f"{cs['avg']}",                    "#34D399"),
                ("STRIKE RT",  f"{cs['sr']}",                     "#60A5FA"),
                ("50s / 100s", f"{cs['50s']} / {cs['100s']}",    "#A78BFA"),
                ("BEST SCORE", cs["highest_score"],               "#FA908B"),
            ]):
                c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.divider()

        # ── Bowling summary header ──
        if is_bowler:
            cs = career_summary_Bowler(short_name)
            st.markdown(f'<span class="pchip bowl">Bowler</span><span style="color:#64748B;font-size:.8rem;margin-left:8px">Career Statistics</span>', unsafe_allow_html=True)

            cols = st.columns(6)
            for c, (lbl, val, col) in zip(cols, [
                ("INNINGS",      cs["matches_played"],         "#F97316"),
                ("WICKETS",      cs["wickets"],                "#FBBF24"),
                ("ECONOMY",      cs["economy"],                "#34D399"),
                ("3W / 4W",      f"{cs['best3']} / {cs['best4']}", "#60A5FA"),
                ("5W+",          cs["best5"],                  "#A78BFA"),
                ("BEST FIGURES", cs["highwicket"],             "#FA908B"),
            ]):
                c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.divider()

        # ── Tabs ──
        tab_career, tab_vs_teams, tab_vs_bowlers, tab_vs_batters, tab_vs_team_players, tab_recent = st.tabs([
            "📈 Career Overview", "🆚 vs Teams", "⚾ vs Bowlers", "🏏 vs Batters", "👥 vs Team Players", "📊 Recent Form"
        ])

        # ── Career Overview ──────────────────────────────────────────
        with tab_career:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🏏 Batting Statistics")
                cs = career_summary_Batter(short_name)
                for stat, value in [
                    ("Total Matches",    cs["matches"]),
                    ("Innings Played",   cs["matches_played"]),
                    ("Total Runs",       cs["runs"]),
                    ("Batting Average",  f"{cs['avg']:.2f}"),
                    ("Strike Rate",      f"{cs['sr']:.2f}"),
                    ("50s / 100s",       f"{cs['50s']} / {cs['100s']}"),
                    ("Times Out",        cs["wickets"]),
                    ("Best Score",       cs["highest_score"]),
                ]:
                    st.markdown(f"**{stat}:** {value}")

            with col2:
                st.markdown("### ⚾ Bowling Statistics")
                cs = career_summary_Bowler(short_name)
                for stat, value in [
                    ("Total Matches",  cs["matches"]),
                    ("Innings Bowled", cs["matches_played"]),
                    ("Total Wickets",  cs["wickets"]),
                    ("Economy Rate",   f"{cs['economy']:.2f}"),
                    ("3W hauls",       cs["best3"]),
                    ("4W hauls",       cs["best4"]),
                    ("5W+ hauls",      cs["best5"]),
                    ("Best Figures",   cs["highwicket"]),
                ]:
                    st.markdown(f"**{stat}:** {value}")

            # Radar comparison
            st.markdown("---")
            st.markdown("**🕸️ Skill Radar**")
            cs_bat = career_summary_Batter(short_name)
            cs_bwl = career_summary_Bowler(short_name)
            cats   = ["Runs (norm)", "Bat Avg", "Strike Rate", "Wickets (norm)", "Economy (inv)"]
            def n(v, mx): return min(v / mx * 100, 100) if mx > 0 else 0
            vals = [
                n(cs_bat["runs"], 4000),
                n(cs_bat["avg"],  80),
                n(cs_bat["sr"],   200),
                n(cs_bwl["wickets"], 200),
                n(max(0, 12 - cs_bwl["economy"]), 12),
            ]
            fig_r = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill='toself', line_color='#F97316', fillcolor='rgba(249,115,22,.15)',
                name=selected_player,
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(range=[0, 100], gridcolor='#1F2937', color='#64748B'),
                    angularaxis=dict(gridcolor='#1F2937', color='#64748B'),
                    bgcolor='rgba(0,0,0,0)',
                ),
                paper_bgcolor='rgba(0,0,0,0)', font_color='#CBD5E1',
                legend=dict(bgcolor='rgba(0,0,0,0)'), height=380,
            )
            st.plotly_chart(fig_r, use_container_width=True)

        # ── vs Teams ─────────────────────────────────────────────────
        with tab_vs_teams:
            team_stats = all_teams_stats(short_name)
            team_list  = sorted(team_stats.keys())

            if team_list:
                selected_team = st.selectbox("Select team", team_list, key="vs_team_select")
                if selected_team:
                    st.markdown(f"### {selected_player} vs {selected_team}")
                    ts = career_summary_team(short_name, selected_team)

                    if ts["total_bt_matches_played"] > 0:
                        st.markdown("**🏏 Batting vs this team**")
                        bcols = st.columns(6)
                        for c, (lbl, val, col) in zip(bcols, [
                            ("INNINGS",     ts["total_bt_matches_played"], "#F97316"),
                            ("RUNS",        ts["btruns"],                  "#FBBF24"),
                            ("AVERAGE",     f"{ts['avg']:.2f}",            "#34D399"),
                            ("STRIKE RATE", f"{ts['sr']:.1f}",             "#60A5FA"),
                            ("50s / 100s",  f"{ts['50s']} / {ts['100s']}", "#A78BFA"),
                            ("BEST SCORE",  ts["highest_bt_score"],        "#FA908B"),
                        ]):
                            c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

                    if ts["total_bw_matches_played"] > 0:
                        st.markdown("**⚾ Bowling vs this team**")
                        bcols = st.columns(6)
                        for c, (lbl, val, col) in zip(bcols, [
                            ("INNINGS",       ts["total_bw_matches_played"],   "#F97316"),
                            ("WICKETS",       ts["total_bwW"],                 "#FBBF24"),
                            ("ECONOMY",       f"{ts['economy']:.2f}",          "#34D399"),
                            ("3W / 4W",       f"{ts['3W']} / {ts['4W']}",     "#60A5FA"),
                            ("5W+",           ts["5W+"],                       "#A78BFA"),
                            ("BEST WICKET",   ts["highest_wicket"],            "#FA908B"),
                        ]):
                            c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

                # ── Team-wise comparison table ──
                rows = []
                for t_name, _stat in team_stats.items():
                    s = career_summary_team(short_name, t_name)
                    rows.append({
                        "Team":        t_name,
                        "Bt Innings":  s["total_bt_matches_played"],
                        "Runs":        s["btruns"],
                        "Avg":         round(s["avg"], 2),
                        "SR":          round(s["sr"], 2),
                        "Wickets":     s["total_bwW"],
                        "Economy":     round(s["economy"], 2),
                    })
                df_teams = pd.DataFrame(rows).sort_values("Runs", ascending=False)
                st.markdown("**📊 All-Teams Summary**")
                st.dataframe(
                    df_teams.style.background_gradient(subset=["Runs"], cmap="Oranges")
                                  .background_gradient(subset=["Wickets"], cmap="Blues"),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("No team-wise statistics available.")

        # ── vs Team Players ──────────────────────────────────────────
        with tab_vs_team_players:
            team_stats = all_teams_stats(short_name)
            team_list  = sorted(team_stats.keys())
            if team_list:
                selected_opp_team = st.selectbox("Select opponent team", team_list, key="vs_team_players_select")
                selected_season = st.selectbox("Select season", squad_data.get(selected_opp_team, {}).keys(), key="vs_team_players_season_select")
                if selected_opp_team:
                    st.markdown(f"### 👥 {selected_player} vs {selected_opp_team} Players")
                    opp_team_players = get_team_players(selected_opp_team, selected_season)

                    if opp_team_players:
                        st.markdown(f"**Batting record vs {selected_opp_team} bowlers**")
                        batting_rows = []
                        for opp_player in opp_team_players:
                            stat = stat_vs_bowler(short_name, opp_player)
                            if stat.get("Matches", 0) > 0:
                                batting_rows.append({
                                    "Bowler": opp_player,
                                    "Matches": stat.get("Matches", 0),
                                    "Runs": stat.get("Runs", 0),
                                    "Balls": stat.get("Balls", 0),
                                    "SR": round(stat.get("Strike_rate", 0), 1),
                                    "Avg": round(stat.get("Runs", 0) / stat.get("Matches", 1), 1),
                                    "Dismissed": stat.get("T_Wicket", 0),
                                    "Fours": sum(stat.get("four_list", [])),
                                    "Sixes": sum(stat.get("Six_list", [])),
                                })
                        if batting_rows:
                            df_bat = pd.DataFrame(batting_rows).sort_values("Runs", ascending=False)
                            st.dataframe(df_bat, use_container_width=True, hide_index=True)
                        else:
                            st.info("No batting records found for this team's bowlers.")

                        st.markdown(f"**Bowling record vs {selected_opp_team} batters**")
                        bowling_rows = []
                        for opp_player in opp_team_players:
                            stat = stat_vs_batter(short_name, opp_player)
                            if stat.get("Matches", 0) > 0:
                                balls = stat.get("Balls", 0)
                                econ = (stat.get("Runs", 0) / balls * 6) if balls else 0
                                bowling_rows.append({
                                    "Batter": opp_player,
                                    "Matches": stat.get("Matches", 0),
                                    "Runs Conceded": stat.get("Runs", 0),
                                    "Balls": balls,
                                    "Economy": round(econ, 2),
                                    "Wickets": stat.get("T_Wicket", 0),
                                    "Avg/Wkts": round(stat.get("T_Wicket", 0) / stat.get("Matches", 1), 2),
                                    "Success": f"{(stat.get('T_Wicket', 0) / stat.get('Matches', 1) * 100):.1f}%",
                                })
                        if bowling_rows:
                            df_bowl = pd.DataFrame(bowling_rows).sort_values("Wickets", ascending=False)
                            st.dataframe(df_bowl, use_container_width=True, hide_index=True)
                        else:
                            st.info("No bowling records found for this team's batters.")
                    else:
                        st.info(f"No player list available for {selected_opp_team}.")
            else:
                st.info("No team statistics available.")

        # ── vs Specific Bowlers ──────────────────────────────────────
        with tab_vs_bowlers:
            bowlers_list = [playerNames.get(p, p) for p in player_info.get("op_Bowler", {}).keys()]
            if bowlers_list:
                selected_bowler = st.selectbox("Select Bowler", sorted(bowlers_list), key="vs_bowler_select")
                if selected_bowler:
                    selected_player_img = get_player_image(selected_player)
                    selected_bowler_img = get_player_image(selected_bowler)
        # Player header with role classification
        
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                        <img src="data:image/png;base64,{selected_player_img}"
                            style="width:200px;height:200px;border-radius:40px;object-fit:cover;border:2px solid #F97316;">
                        <div style="font-size:1.8rem;color:#E8EAF0;"> VS </div>
                        <img src="data:image/png;base64,{selected_bowler_img}"
                            style="width:200px;height:200px;border-radius:40px;object-fit:cover;border:2px solid #F97316;">
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                            <div style="font-size:1.8rem;color:#E8EAF0;margin:0 20px">🏏 {selected_player}</div>
                            <div style="font-size:1.8rem;color:#E8EAF0;margin:0 20px"> ⚾ {selected_bowler}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    bs = stat_vs_bowler(short_name, selected_bowler)

                    bcols = st.columns(6)
                    for c, (lbl, val, col) in zip(bcols, [
                        ("RUNS",       bs.get("Runs", 0),                                           "#F97316"),
                        ("BALLS",      bs.get("Balls", 0),                                          "#FBBF24"),
                        ("STRIKE RT",  f"{bs.get('Strike_rate', 0):.1f}",                           "#34D399"),
                        ("DISMISSED",  bs.get("T_Wicket", 0),                                       "#60A5FA"),
                        ("FOURS",      sum(bs.get("four_list", [])),                                          "#A78BFA"),
                        ("SIXES",      sum(bs.get("Six_list", [])),                                          "#FA908B"),
                    ]):
                        c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

                    a1, a2 = st.columns(2)
                    runs_v  = bs.get("Runs", 0)
                    balls_v = bs.get("Balls", 0)
                    wkts_v  = bs.get("T_Wicket", 0)
                    mtchs   = bs.get("Matches", 1)
                    with a1:
                        st.markdown("**Detailed Batting vs Bowler**")
                        st.markdown(f"- Runs: **{runs_v}**")
                        st.markdown(f"- Balls Faced: **{balls_v}**")
                        st.markdown(f"- Average: **{runs_v / mtchs:.2f}**")
                        st.markdown(f"- Strike Rate: **{(runs_v / balls_v * 100) if balls_v else 0:.2f}**")
                        st.markdown(f"- Matches: **{mtchs}**")
                    with a2:
                        st.markdown("**Dismissal Analysis**")
                        st.markdown(f"- Times Dismissed: **{wkts_v}**")
                        st.markdown(f"- Dismissal Rate: **{(wkts_v / mtchs * 100) if mtchs else 0:.1f}%**")
                        st.markdown(f"- Fours: **{ sum(bs.get('four_list', [])) }**")
                        st.markdown(f"- Sixes: **{ sum(bs.get('Six_list', [])) }**")

                    run_list = bs.get("Runs_list", []) 
                    w_list   = bs.get("W_list", []) or [0] * len(run_list)
                    if run_list:
                        st.plotly_chart(
                            runs_wicket_chart(run_list, w_list, f"{selected_player} vs {selected_bowler}"),
                            use_container_width=True
                        )
            else:
                st.info("No bowler-vs stats available.")

        # ── vs Specific Batters ──────────────────────────────────────
        with tab_vs_batters:
            batters_list = [playerNames.get(p, p) for p in player_info.get("op_Batter", {}).keys()]
            if batters_list:
                selected_batter = st.selectbox("Select Batter", sorted(batters_list), key="vs_batter_select")
                if selected_batter:
                    selected_player_img = get_player_image(selected_player)
                    selected_batter_img = get_player_image(selected_batter)
        # Player header with role classification
        
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                        <img src="data:image/png;base64,{selected_player_img}"
                            style="width:200px;height:200px;border-radius:40px;object-fit:cover;border:2px solid #F97316;">
                        <div style="font-size:1.8rem;color:#E8EAF0;"> VS </div>
                        <img src="data:image/png;base64,{selected_batter_img}"
                            style="width:200px;height:200px;border-radius:40px;object-fit:cover;border:2px solid #F97316;">
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                            <div style="font-size:1.8rem;color:#E8EAF0;margin:0 10px">⚾ {selected_player}</div>
                            <div style="font-size:1.8rem;color:#E8EAF0;margin:0 20px"> 🏏 {selected_batter}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    bs2 = stat_vs_batter(short_name, selected_batter)

                    runs_c   = bs2.get("Runs", 0)
                    balls_b  = bs2.get("Balls", 0)
                    wkts_t   = bs2.get("T_Wicket", 0)
                    mtchs2   = bs2.get("Matches", 1)
                    econ     = (runs_c / balls_b * 6) if balls_b else 0

                    bat_cols = st.columns(5)
                    for c, (lbl, val, col) in zip(bat_cols, [
                        ("RUNS CONCEDED", runs_c,                              "#F97316"),
                        ("BALLS BOWLED",  balls_b,                             "#FBBF24"),
                        ("WICKETS",       wkts_t,                              "#34D399"),
                        ("ECONOMY",       f"{econ:.2f}",                       "#60A5FA"),
                        ("SUCCESS RATE",  f"{(wkts_t/mtchs2*100):.1f}%",      "#A78BFA"),
                    ]):
                        c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

                    a1, a2 = st.columns(2)
                    with a1:
                        st.markdown("**Bowling Detail vs Batter**")
                        st.markdown(f"- Runs Conceded: **{runs_c}**")
                        st.markdown(f"- Balls Bowled: **{balls_b}**")
                        st.markdown(f"- Wickets: **{wkts_t}**")
                        st.markdown(f"- Economy: **{econ:.2f}**")
                        st.markdown(f"- Balls/Wicket: **{balls_b / max(wkts_t, 1):.1f}**")
                    with a2:
                        st.markdown("**Match Analysis**")
                        st.markdown(f"- Matches: **{mtchs2}**")
                        st.markdown(f"- Avg Wkts/Match: **{wkts_t / mtchs2:.2f}**")
                        st.markdown(f"- Success Rate: **{(wkts_t/mtchs2*100):.1f}%**")
                        raw_d = stat_data.get(short_name, {}).get("op_Batter", {}).get(
                            PN_L_to_S.get(selected_batter, selected_batter), {})
                        fours_c = sum(raw_d.get("four_list", [0]))
                        sixes_c = sum(raw_d.get("Six_list", [0]))
                        st.markdown(f"- Fours Conceded: **{fours_c}**")
                        st.markdown(f"- Sixes Conceded: **{sixes_c}**")

                    run_list2 = bs2.get("Runs_list", [])
                    w_list2   = bs2.get("W_list", []) or [0] * len(run_list2)
                    if run_list2:
                        # ── FIX: title now correctly references selected_batter ──
                        st.plotly_chart(
                            runs_wicket_chart(run_list2, w_list2, f"{selected_player} bowling vs {selected_batter}"),
                            use_container_width=True
                        )

                    # All-batters table
                    all_bat = player_info.get("op_Batter", {})
                    if all_bat:
                        rows_all = []
                        for bat_key, s in all_bat.items():
                            name = playerNames.get(bat_key, bat_key)
                            r2, b2 = s.get("Runs", 0), s.get("Balls", 0)
                            w2, m2 = s.get("T_Wicket", 0), s.get("Matches", 1)
                            rows_all.append({
                                "Batter":  name,
                                "Matches": m2,
                                "Runs":    r2,
                                "Balls":   b2,
                                "SR":      round(s.get("Strike_rate", 0), 1),
                                "Avg":     round(r2 / m2, 1) if m2 else 0,
                                "Wkts":    w2,
                            })
                        df_all = pd.DataFrame(rows_all).sort_values("Runs", ascending=False)
                        st.markdown("**All Batters Faced**")
                        st.dataframe(df_all, use_container_width=True, hide_index=True)
            else:
                st.info("No batter-vs stats available.")

        # ── Recent Form ──────────────────────────────────────────────
        with tab_recent:
            rec = recent_form(short_name)
            if rec:
                rc1, rc2, rc3, rc4 = st.columns(4)
                for c, (lbl, val, col) in zip([rc1, rc2, rc3, rc4], [
                    ("REC BAT AVG",   f"{rec.get('Bt_Avg', 0):.1f}",          "#F97316"),
                    ("REC STRIKE RT", f"{rec.get('Bt_Strike_rate', 0):.1f}",  "#FBBF24"),
                    ("REC BW ECON",   f"{rec.get('Bw_economy', 0):.2f}",      "#60A5FA"),
                    ("REC WKT/GM",    f"{rec.get('Bw_Avg_Wickets', 0):.2f}",  "#A78BFA"),
                ]):
                    c.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{col};font-size:2rem">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

                recent_runs_all  = rec.get("Bt_Runs", [])
                recent_balls_all = rec.get("Bt_Balls", [])
                recent_years_all = rec.get("year", [])
                recent_inng_all = rec.get("inning", [])
                recent_wick_all = rec.get("Bt_Wickets", [])
                recent_runs  = []
                recent_balls = []
                recent_years = []
                recent_inng = []
                recent_wick = []
                

                for i in range(len(recent_balls_all)):
                    if recent_balls_all[i] != 0:
                        recent_runs.append(recent_runs_all[i])
                        recent_balls.append(recent_balls_all[i])
                        recent_years.append(recent_years_all[i])
                        recent_inng.append(recent_inng_all[i])
                        recent_wick.append(recent_wick_all[i])

                if isinstance(recent_runs, list) and recent_runs:
                    match_options = [5, 10, 15, 20, "All"]
                    sel_m = st.selectbox(
                        "Show previous matches", match_options,
                        format_func=lambda x: f"Last {x} matches" if isinstance(x, int) else "All matches",
                        key="recent_matches_count"
                    )
                    size_arr = len(recent_runs)
                    n_show = len(recent_runs) if sel_m == "All" else min(len(recent_runs), sel_m)
                    runs_s  = recent_runs[size_arr-n_show:]
                    inn  = recent_inng[size_arr-n_show:]
                    wicket  = recent_wick[size_arr-n_show:]
                    years_s = (recent_years[size_arr-n_show:] if isinstance(recent_years, list) and recent_years
                               else list(range(1, n_show + 1)))
                    
                    # fig = go.Figure(go.Bar(
                    #     x=[years_s,inn,wicket],
                    #     # x=list((f"{y}|{n}|{c}") for c, (y,n ) in enumerate(zip(years_s, inn))),
                    #     y=runs_s,
                    #     marker_color=['#F97316' if r >= 50 else '#FBBF24' if r >= 30 else '#374151' for r in runs_s],
                    # ))
                    x_vals = list(range(1, len(runs_s) + 1))

                    out_status = ["Out" if b > 0 else "Not Out" for b in recent_balls[size_arr-n_show:]]

                    fig = go.Figure(go.Bar(
                        x=x_vals,
                        y=runs_s,
                        marker_color=[
                            '#F97316' if r >= 50 else '#FBBF24' if r >= 30 else '#374151'
                            for r in runs_s
                        ],
                        customdata=list(zip(years_s, inn, out_status)),
                        hovertemplate=(
                            "Match %{x}<br>"
                            "Year: %{customdata[0]}<br>"
                            "Inning: %{customdata[1]}<br>"
                            "Status: %{customdata[2]}<br>"
                            "Runs: %{y}<extra></extra>"
                        )
                    ))
                    dark_fig_layout(fig, title=f"Recent Innings — Last {n_show} Matches",
                                    height=360, title_color="#FBBF24")
                    x_title = "Year/Innings/Wickets" if isinstance(recent_years, list) and recent_years else "Match Number"
                    fig.update_layout(xaxis_title=x_title, yaxis_title="Runs")
                    st.plotly_chart(fig, use_container_width=True)

                    # Yearly summary
                    if isinstance(recent_years, list) and recent_years:
                        df_y = pd.DataFrame({"year": [str(y) for y in recent_years], "runs": recent_runs})
                        df_sum = df_y.groupby("year", as_index=False).agg(
                            Matches=("runs","size"), Total=("runs","sum"), Avg=("runs","mean")
                        ).sort_values("year")

                        fig2 = go.Figure()
                        fig2.add_trace(go.Bar(x=df_sum["year"], y=df_sum["Total"],
                                              name="Total Runs", marker_color="#F97316"))
                        fig2.add_trace(go.Scatter(x=df_sum["year"], y=df_sum["Avg"],
                                                  name="Avg Runs", mode='lines+markers',
                                                  line=dict(color='#60A5FA', width=2)))
                        dark_fig_layout(fig2, title="Yearly Performance Summary",
                                        height=360, title_color="#F97316",
                                        legend=dict(orientation='h', y=-0.2))
                        fig2.update_layout(xaxis_title="Year", yaxis_title="Runs")
                        st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No recent form data available.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — WIN PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

elif page == "👤  Prediction Match Wins":
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">📊 WIN PROBABILITY PREDICTOR</div>', unsafe_allow_html=True)

    if not season:
        st.warning("Please select teams with a common season in the sidebar.")
        st.stop()

    squad1 = get_squad(team1, season)
    squad2 = get_squad(team2, season)

    # Player selection for each team
    st.markdown("**Select Playing XI for each team:**")
    col1, col2 = st.columns(2)
    with col1:
        selected_players1 = st.multiselect(f"🔴 Select players for {team1}", list(squad1.keys()), default=team_playing11_recently.get(team1, []), key=f"sel_p1_{team1}", max_selections=11)
    with col2:
        selected_players2 = st.multiselect(f"🔵 Select players for {team2}", list(squad2.keys()), default=team_playing11_recently.get(team2, []), key=f"sel_p2_{team2}", max_selections=11)

    # Filter squads to selected players
    if  len(selected_players1) < 11 or len(selected_players2) < 11:
        st.error(f"Please select players for both teams.")
        st.stop()
    

  
    if st.button("Predict Match Outcome", key="predict_button"):
        selected_squad1 = {p: squad1[p] for p in selected_players1 if p in squad1}
        selected_squad2 = {p: squad2[p] for p in selected_players2 if p in squad2}


       

        # if selected_squad1 and  selected_squad2:
        #     update_teams_playing_recently(team1, team2, selected_players1, selected_players2)

            

        p1, p2, s1, s2 = win_probability(selected_squad1, selected_squad2, team1, team2)

        # ── Win-probability display ──
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-around;
                    background:linear-gradient(135deg,#111827,#1E2A3B);
                    border-radius:20px;padding:30px;border:1px solid #1F2937;margin-bottom:24px">
            <div style="text-align:center">
                <div style="font-family:'Bebas Neue';font-size:3rem;color:#F97316">{team1}</div>
                <div style="font-family:'Bebas Neue';font-size:4rem;color:#FBBF24">{p1}%</div>
                <div style="color:#64748B;font-size:.8rem;letter-spacing:2px">WIN PROBABILITY</div>
            </div>
            <div style="font-family:'Bebas Neue';font-size:2rem;color:#374151">VS</div>
            <div style="text-align:center">
                <div style="font-family:'Bebas Neue';font-size:3rem;color:#60A5FA">{team2}</div>
                <div style="font-family:'Bebas Neue';font-size:4rem;color:#FBBF24">{p2}%</div>
                <div style="color:#64748B;font-size:.8rem;letter-spacing:2px">WIN PROBABILITY</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Probability bar
        fig_prob = go.Figure(go.Bar(
            x=[p1, p2], y=[team1, team2],
            orientation='h',
            marker_color=["#F97316", "#60A5FA"],
            text=[f"{p1}%", f"{p2}%"], textposition='inside',
        ))
        dark_fig_layout(fig_prob, title=f"{team1} vs {team2} — Win Probability ({season})", height=220)
        fig_prob.update_layout(xaxis=dict(range=[0, 100], gridcolor="#1F2937"))
        st.plotly_chart(fig_prob, use_container_width=True)

        st.divider()

        # ── Player-level predictions ──
        st.markdown("**🔍 Player Contribution Scores (vs Opponent)**")
        tab_t1, tab_t2 = st.tabs([f"🔴 {team1}", f"🔵 {team2}"])

        def player_contribution_df(squad, opp):
            rows = []
            for p, info in squad.items():
                pred = predict_performance(p, opp)
                role = ROLE_MAP.get(info.get("role", "Batter"), classify_role(p))
                rows.append({
                    "Player":     playerNames.get(p, p),
                    "Role":       role,
                    "Pred Runs":  pred["runs"],
                    "Pred SR":    pred["sr"],
                    "Pred Wkts":  pred["wickets"],
                    "Pred Econ":  pred["economy"],
                })
            return pd.DataFrame(rows).sort_values("Pred Runs", ascending=False)

        with tab_t1:
            df1 = player_contribution_df(selected_squad1, team2)
            fig1 = go.Figure(go.Bar(
                x=df1["Player"], y=df1["Pred Runs"],
                marker_color="#F97316", text=df1["Pred Runs"].astype(str), textposition='outside',
            ))
            dark_fig_layout(fig1, title=f"{team1} — Predicted Runs vs {team2}", height=300)
            fig1.update_layout(xaxis=dict(tickangle=-35, gridcolor="#1F2937"))
            st.plotly_chart(fig1, use_container_width=True)
            st.dataframe(df1, use_container_width=True, hide_index=True)

        with tab_t2:
            df2 = player_contribution_df(selected_squad2, team1)
            fig2 = go.Figure(go.Bar(
                x=df2["Player"], y=df2["Pred Runs"],
                marker_color="#60A5FA", text=df2["Pred Runs"].astype(str), textposition='outside',
            ))
            dark_fig_layout(fig2, title=f"{team2} — Predicted Runs vs {team1}", height=300)
            fig2.update_layout(xaxis=dict(tickangle=-35, gridcolor="#1F2937"))
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df2, use_container_width=True, hide_index=True)

        # ── Team radar ──
        st.divider()
        st.markdown("**🕸️ Team Strength Radar**")
        def team_radar_vals(squad, opp):
            preds = [predict_performance(p, opp) for p in squad]
            if not preds: return [0]*5
            avg_runs  = np.mean([x["runs"] for x in preds])
            avg_sr    = np.mean([x["sr"]   for x in preds])
            tot_wkts  = sum(x["wickets"] for x in preds)
            avg_econ  = np.mean([x["economy"] for x in preds if x["economy"] > 0]) if any(x["economy"] > 0 for x in preds) else 10
            depth     = sum(1 for x in preds if x["runs"] >= 20)
            return [avg_runs, avg_sr, tot_wkts, max(0, 10 - avg_econ), depth]

        rv1 = team_radar_vals(squad1, team2)
        rv2 = team_radar_vals(squad2, team1)
        mx  = [max(a, b, 0.01) for a, b in zip(rv1, rv2)]
        rv1n = [min(v/m*100, 100) for v, m in zip(rv1, mx)]
        rv2n = [min(v/m*100, 100) for v, m in zip(rv2, mx)]
        cats = ["Avg Runs", "Avg SR", "Total Wkts", "Econ (inv)", "Depth (20+)"]

        fig_rad = go.Figure()
        fig_rad.add_trace(go.Scatterpolar(r=rv1n + [rv1n[0]], theta=cats + [cats[0]],
            fill='toself', name=team1, line_color='#F97316', fillcolor='rgba(249,115,22,.2)'))
        fig_rad.add_trace(go.Scatterpolar(r=rv2n + [rv2n[0]], theta=cats + [cats[0]],
            fill='toself', name=team2, line_color='#60A5FA', fillcolor='rgba(96,165,250,.15)'))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100], gridcolor='#1F2937', color='#64748B'),
                    angularaxis=dict(gridcolor='#1F2937', color='#64748B'),
                    bgcolor='rgba(0,0,0,0)'),
            paper_bgcolor='rgba(0,0,0,0)', font_color='#CBD5E1',
            legend=dict(bgcolor='rgba(0,0,0,0)'), height=400,
        )
        st.plotly_chart(fig_rad, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — DREAM11 PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════

elif page == "⭐  Dream11 Predictor":
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">⭐ DREAM11 BEST XI</div>', unsafe_allow_html=True)

    if not season:
        st.warning("Please select teams with a common season in the sidebar.")
        st.stop()

    squad1 = get_squad(team1, season)
    squad2 = get_squad(team2, season)

    # Player selection for each team
    st.markdown("**Select Playing XI for each team:**")
    col1, col2 = st.columns(2)
    with col1:
        selected_players1 = st.multiselect(f"🔴 Select players for {team1}", list(squad1.keys()), default=team_playing11_recently.get(team1, []), key=f"sel_p1_{team1}", max_selections=11)
    with col2:
        selected_players2 = st.multiselect(f"🔵 Select players for {team2}", list(squad2.keys()), default=team_playing11_recently.get(team2, []), key=f"sel_p2_{team2}", max_selections=11)

    # Filter squads to selected players
    if  len(selected_players1) < 11 or len(selected_players2) < 11:
        st.error(f"Please select at most 11 players for {team1} and {team2}.")
        st.stop()

    if st.button("Dream11 Predictor", key="Dream11predict_button"):
        selected_squad1 = {p: squad1[p] for p in selected_players1 if p in squad1}
        selected_squad2 = {p: squad2[p] for p in selected_players2 if p in squad2}

    

        if not selected_squad1 or not selected_squad2:
            st.error(f"Please select players for both teams.")
            st.stop()

    

        st.markdown(f'<p style="color:#64748B;margin-bottom:20px">{team1} vs {team2} — {season} · AI-powered pick</p>', unsafe_allow_html=True)

        selected = pick_dream11(selected_squad1, selected_squad2, team1, team2)
        captain  = selected[0] if selected else None
        vc       = selected[1] if len(selected) > 1 else None

        # Summary row
        t1c = sum(1 for p in selected if p["team"] == team1)
        t2c = len(selected) - t1c
        role_cnt = defaultdict(int)
        for p in selected: role_cnt[p["role"]] += 1

        c1, c2, c3, c4 = st.columns(4)
        for col, (val, lbl, clr) in zip([c1, c2, c3, c4], [
            (t1c, f"from {team1[:10]}", "#F97316"),
            (t2c, f"from {team2[:10]}", "#60A5FA"),
            (11,  "Total Players",      "#34D399"),
            (f"{role_cnt['AR']} AR · {role_cnt['WK']} WK", "Balance", "#FBBF24"),
        ]):
            col.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{clr}">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.divider()

        ROLE_ICONS = {"WK": "🧤", "BAT": "🏏", "AR": "🔀", "BOWL": "⚾"}
        ROLE_FULL  = {"WK": "WK-Batter", "BAT": "Batsman", "AR": "All-Rounder", "BOWL": "Bowler"}
        CSS_R      = {"WK": "wk", "BAT": "bat", "AR": "ar", "BOWL": "bowl"}

        for role_grp, grp_label in [("WK","🧤 WICKET-KEEPER"), ("BAT","🏏 BATSMEN"),
                                    ("AR","🔀 ALL-ROUNDERS"), ("BOWL","⚾ BOWLERS")]:
            grp_players = [p for p in selected if p["role"] == role_grp]
            if not grp_players: continue

            st.markdown(f'<div style="font-family:Bebas Neue;font-size:1rem;color:#64748B;letter-spacing:3px;margin:16px 0 8px">{grp_label}</div>', unsafe_allow_html=True)
            cols = st.columns(max(len(grp_players), 1))

            for col, p in zip(cols, grp_players):
                is_c  = (p == captain)
                is_vc = (p == vc)
                border = "#FFD700" if is_c else "#9CA3AF" if is_vc else "#1F2937"
                t_col  = "#F97316" if p["team"] == team1 else "#60A5FA"
                badge  = '<span class="cbadge">C</span>'  if is_c  else \
                        '<span class="vcbadge">VC</span>' if is_vc else '<span class="vcbadge">P</span>'
                css_r  = CSS_R.get(p["role"], "bat")
                disp_name = playerNames.get(p["player"], p["player"])
                img = get_player_image(p["player"])
                with col:
                    st.markdown(f"""
                    <div class="d11card" style="border-color:{border}">
                        <img src="data:image/png;base64,{img}"
                            style="width:40%;height:50%;object-fit:cover;border-radius:8px">
                        <div style="font-size:1.8rem">{ROLE_ICONS.get(p['role'],'🏏')}</div>
                        <div class="d11name">{disp_name[:16]}</div>
                        <div style="color:{t_col};font-size:.7rem;font-weight:600;margin:3px 0">{p['team'][:14]}</div>
                        {badge}
                        <div style="margin-top:8px">
                            <span class="pchip {css_r}">{ROLE_FULL.get(p['role'],'BAT')}</span>
                        </div>
                        <p style="margin-top:8px;font-size:.78rem;color:#64748B">
                            Score: <span style="color:#FFD700;font-weight:700">{p['score']}</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Score bar ──
        st.divider()
        st.markdown('<div class="sec-hdr" style="font-size:1.2rem">📊 SCORE BREAKDOWN</div>', unsafe_allow_html=True)
        disp_names = [playerNames.get(p["player"], p["player"])[:12] for p in selected]
        fig_d11 = go.Figure(go.Bar(
            x=disp_names, y=[p["score"] for p in selected],
            marker_color=[
                "#FFD700" if p == captain else "#9CA3AF" if p == vc else
                "#F97316" if p["team"] == team1 else "#60A5FA"
                for p in selected
            ],
            text=[str(p["score"]) for p in selected], textposition='outside',
        ))
        dark_fig_layout(fig_d11, height=320)
        fig_d11.update_layout(xaxis=dict(tickangle=-35, gridcolor="#1F2937"))
        st.plotly_chart(fig_d11, use_container_width=True)

        df_d11 = pd.DataFrame([{
            "Player": playerNames.get(p["player"], p["player"]),
            "Team":   p["team"],
            "Role":   ROLE_FULL.get(p["role"], "BAT"),
            "Score":  p["score"],
            "Tag":    "C" if p == captain else "VC" if p == vc else "",
        } for p in selected])
        st.dataframe(df_d11.sort_values("Score", ascending=False), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MATCH SCORECARD PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🔮  Match Scorecard Prediction":
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">🔮 PREDICTED MATCH SCORECARD</div>', unsafe_allow_html=True)

    if not season:
        st.warning("Please select teams with a common season in the sidebar.")
        st.stop()

    squad1 = get_squad(team1, season)
    squad2 = get_squad(team2, season)

    # Player selection for each team
    st.markdown("**Select Playing XI for each team:**")
    col1, col2 = st.columns(2)
    with col1:
        selected_players1 = st.multiselect(f"🔴 Select players for {team1}", list(squad1.keys()), default=team_playing11_recently.get(team1, []), key=f"sel_p1_{team1}", max_selections=11)
    with col2:
        selected_players2 = st.multiselect(f"🔵 Select players for {team2}", list(squad2.keys()), default=team_playing11_recently.get(team2, []), key=f"sel_p2_{team2}", max_selections=11)

    # Filter squads to selected players
    if  len(selected_players1) < 11 or len(selected_players2) < 11:
        st.error(f"Please select at most 11 players for {team1} and {team2}.")
        st.stop()
    

    if st.button("Match Score Predictor", key="Match_scorepredict_button"):
        selected_squad1 = {p: squad1[p] for p in selected_players1 if p in squad1}
        selected_squad2 = {p: squad2[p] for p in selected_players2 if p in squad2}

    

        if not selected_squad1 or not selected_squad2:
            st.error(f"Please select players for both teams.")
            st.stop()

    

        st.markdown(f'<p style="color:#64748B;margin-bottom:20px">{team1} vs {team2} · {season} — Statistical model (H2H × Recent form blend)</p>', unsafe_allow_html=True)

        ROLE_FULL2 = {"WK": "🧤WK", "BAT": "🏏Bat", "AR": "🔀AR", "BOWL": "⚾Bowl"}

        def build_scorecard(squad, opp_team):
            rows = []
            for p, info in squad.items():
                pred = predict_performance(p, opp_team)
                role = ROLE_MAP.get(info.get("role", "Batter"), classify_role(p))
                rows.append({
                    "Player":    playerNames.get(p, p),
                    "Role":      role,
                    "Pred Runs": pred["runs"],
                    "Pred SR":   pred["sr"],
                    "Pred 4s":   pred["fours"],
                    "Pred 6s":   pred["sixes"],
                    "Pred Wkts": pred["wickets"],
                    "Pred Econ": pred["economy"],
                    "H2H Games": pred["h2h_matches"],
                })
            return sorted(rows, key=lambda x: x["Pred Runs"], reverse=True)

        def render_scorecard(squad, opp_team, team_name, color):
            rows = build_scorecard(squad, opp_team)
            top5 = rows[:5]
            cols = st.columns(5)
            for col, r in zip(cols, top5):
                conf = "🔥" if r["Pred Runs"] >= 35 else "✅" if r["Pred Runs"] >= 20 else "📉"
                col.markdown(f"""
                <div class="stat-card" style="border-left:3px solid {color}">
                    <div style="font-size:.7rem;color:#64748B;margin-bottom:2px">{conf} {r['Player'][:14]}</div>
                    <div class="stat-val" style="color:{color};font-size:2rem">{r['Pred Runs']}</div>
                    <div class="stat-lbl">PRED RUNS</div>
                    <div style="color:#64748B;font-size:.7rem;margin-top:4px">
                        SR {r['Pred SR']:.0f} · {r['Pred 4s']}×4 · {r['Pred 6s']}×6
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            fig = go.Figure(go.Bar(
                x=[r["Player"][:12] for r in rows], y=[r["Pred Runs"] for r in rows],
                marker_color=color, opacity=.85,
                text=[str(r["Pred Runs"]) for r in rows], textposition='outside',
            ))
            dark_fig_layout(fig, title=f"Predicted Batting — {team_name}", height=300, title_color=color)
            fig.update_layout(xaxis=dict(tickangle=-40, gridcolor="#1F2937"))
            st.plotly_chart(fig, use_container_width=True)

            bowl_rows = sorted([r for r in rows if r["Pred Wkts"] > 0],
                            key=lambda x: x["Pred Wkts"], reverse=True)
            if bowl_rows:
                fig2 = go.Figure(go.Bar(
                    x=[r["Player"][:12] for r in bowl_rows], y=[r["Pred Wkts"] for r in bowl_rows],
                    marker_color="#60A5FA",
                    text=[f"{r['Pred Wkts']:.2f}" for r in bowl_rows], textposition='outside',
                ))
                dark_fig_layout(fig2, title=f"Predicted Wickets — {team_name}", height=280, title_color="#60A5FA")
                fig2.update_layout(xaxis=dict(tickangle=-40, gridcolor="#1F2937"))
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("**Full Prediction Table**")
            df = pd.DataFrame([{
                "Player":   r["Player"],
                "Role":     ROLE_FULL2.get(r["Role"], "🏏Bat"),
                "Pred Runs":r["Pred Runs"],
                "Pred SR":  r["Pred SR"],
                "4s":       r["Pred 4s"],
                "6s":       r["Pred 6s"],
                "Wkts":     f"{r['Pred Wkts']:.2f}",
                "Economy":  f"{r['Pred Econ']:.2f}" if r["Pred Econ"] > 0 else "—",
                "H2H M":    r["H2H Games"],
            } for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True, height=380)
            return sum(r["Pred Runs"] for r in rows), rows

        tab_t1, tab_t2, tab_sum = st.tabs([f"🔴 {team1}", f"🔵 {team2}", "🏆 Match Summary"])

        with tab_t1:
            t1_total, t1_rows = render_scorecard(selected_squad1, team2, team1, "#F97316")
        with tab_t2:
            t2_total, t2_rows = render_scorecard(selected_squad2, team1, team2, "#60A5FA")
        with tab_sum:
            st.markdown('<div class="sec-hdr" style="font-size:1.4rem">🏆 PREDICTED MATCH SUMMARY</div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"""
                <div class="stat-card" style="border-left:4px solid #F97316;padding:28px">
                    <div style="font-family:'Bebas Neue';font-size:1.4rem;color:#F97316;letter-spacing:2px">{team1}</div>
                    <div style="font-family:'Bebas Neue';font-size:3.5rem;color:#E8EAF0;margin:8px 0">{int(t1_total)}</div>
                    <div style="color:#64748B;font-size:.8rem">PREDICTED TEAM RUNS</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:100%;font-family:\'Bebas Neue\';font-size:2rem;color:#64748B;letter-spacing:3px">VS</div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="stat-card" style="border-left:4px solid #60A5FA;padding:28px">
                    <div style="font-family:'Bebas Neue';font-size:1.4rem;color:#60A5FA;letter-spacing:2px">{team2}</div>
                    <div style="font-family:'Bebas Neue';font-size:3.5rem;color:#E8EAF0;margin:8px 0">{int(t2_total)}</div>
                    <div style="color:#64748B;font-size:.8rem">PREDICTED TEAM RUNS</div>
                </div>""", unsafe_allow_html=True)

            st.divider()

            winner  = team1 if t1_total >= t2_total else team2
            margin  = abs(t1_total - t2_total)
            w_col   = "#F97316" if winner == team1 else "#60A5FA"
            conf    = "HIGH" if margin > 30 else "MEDIUM" if margin > 15 else "LOW"
            conf_c  = "#34D399" if conf == "HIGH" else "#FBBF24" if conf == "MEDIUM" else "#EF4444"

            st.markdown(f"""
            <div style="text-align:center;padding:32px;background:linear-gradient(135deg,#111827,#1E2A3B);
                        border-radius:16px;border:1px solid {w_col}">
                <div style="color:#64748B;font-size:.8rem;letter-spacing:3px;text-transform:uppercase">Predicted Winner</div>
                <div style="font-family:'Bebas Neue';font-size:3rem;color:{w_col};letter-spacing:4px;margin:8px 0">{winner}</div>
                <div style="color:#64748B;font-size:.85rem">
                    by ~{int(margin)} runs &nbsp;|&nbsp;
                    Confidence: <span style="color:{conf_c};font-weight:700">{conf}</span>
                </div>
            </div>""", unsafe_allow_html=True)

            st.divider()

            # Key players
            st.markdown("**🌟 Key Players to Watch**")
            all_rows = [(r, team1) for r in t1_rows] + [(r, team2) for r in t2_rows]
            all_rows.sort(key=lambda x: x[0]["Pred Runs"], reverse=True)
            top_watch = all_rows[:6]
            cols = st.columns(3)
            for i, (r, t) in enumerate(top_watch):
                col = "#F97316" if t == team1 else "#60A5FA"
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="stat-card" style="border-left:3px solid {col};margin-bottom:12px">
                        <div style="color:{col};font-size:.72rem;font-weight:600">{t[:14]}</div>
                        <div style="font-family:'Bebas Neue';font-size:1.3rem;color:#E8EAF0">{r['Player'][:18]}</div>
                        <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:.78rem">
                            <span style="color:#FBBF24">🏏 {r['Pred Runs']} runs</span>
                            <span style="color:#60A5FA">⚾ {r['Pred Wkts']:.1f} wkts</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

            # Team radar
            st.divider()
            st.markdown("**Team Strength Comparison**")
            def tr_vals_rows(rows):
                if not rows: return [0]*5
                return [
                    np.mean([r["Pred Runs"] for r in rows]),
                    np.mean([r["Pred SR"]   for r in rows]),
                    sum(r["Pred Wkts"]       for r in rows),
                    max(r["Pred Runs"]       for r in rows),
                    sum(1 for r in rows if r["Pred Runs"] >= 20),
                ]

            rv1, rv2 = tr_vals_rows(t1_rows), tr_vals_rows(t2_rows)
            mx = [max(a, b, 0.01) for a, b in zip(rv1, rv2)]
            rv1n = [min(v/m*100, 100) for v, m in zip(rv1, mx)]
            rv2n = [min(v/m*100, 100) for v, m in zip(rv2, mx)]
            cats = ["Team Runs", "Avg SR", "Wickets", "Top Score", "Depth"]

            fig_r2 = go.Figure()
            fig_r2.add_trace(go.Scatterpolar(r=rv1n+[rv1n[0]], theta=cats+[cats[0]],
                fill='toself', name=team1, line_color='#F97316', fillcolor='rgba(249,115,22,.2)'))
            fig_r2.add_trace(go.Scatterpolar(r=rv2n+[rv2n[0]], theta=cats+[cats[0]],
                fill='toself', name=team2, line_color='#60A5FA', fillcolor='rgba(96,165,250,.15)'))
            fig_r2.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], gridcolor='#1F2937', color='#64748B'),
                        angularaxis=dict(gridcolor='#1F2937', color='#64748B'),
                        bgcolor='rgba(0,0,0,0)'),
                paper_bgcolor='rgba(0,0,0,0)', font_color='#CBD5E1',
                legend=dict(bgcolor='rgba(0,0,0,0)'), height=400,
            )
            st.plotly_chart(fig_r2, use_container_width=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#374151;font-size:.75rem;padding:16px">
    🏏 IPL Analytics Pro &nbsp;·&nbsp; Data: IPL 2008–2025
    &nbsp;·&nbsp; Predictions are statistical estimates, not guarantees
</div>
""", unsafe_allow_html=True)