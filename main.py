"""
IPL Analytics Pro — Full App
Requires:
  - IPL_Stat_2008_2025.json      (player H2H stats)
  - player_team_season_mapping_info_and_images.json  (season squad + roles)
Run:  streamlit run app.py
"""

import base64
from itertools import count
from tkinter import Image

import streamlit as st
import json, os, copy, math
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
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.stApp {
    background: #0A0E1A;
    color: #E8EAF0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0D1220 0%,#111827 100%) !important;
    border-right: 1px solid #1F2937;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }

/* ── Title ── */
.ipl-hero {
    text-align:center;
    padding: 24px 0 8px;
}
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
    color:#64748B;
    font-size:.85rem;
    letter-spacing:3px;
    text-transform:uppercase;
    margin-top:-4px;
}

/* ── Cards ── */
.stat-card {
    background:linear-gradient(135deg,#111827,#1E2A3B);
    border:1px solid #1F2937;
    border-radius:14px;
    padding:18px 20px;
    text-align:center;
    transition: transform .2s, box-shadow .2s;
}
.stat-card:hover {
    transform:translateY(-3px);
    box-shadow:0 8px 28px rgba(249,115,22,.18);
}
.stat-val {
    font-family:'Bebas Neue',cursive;
    font-size:2.6rem;
    color:#F97316;
    letter-spacing:2px;
    line-height:1;
}
.stat-lbl {
    font-size:.68rem;
    color:#64748B;
    text-transform:uppercase;
    letter-spacing:2px;
    margin-top:4px;
}

/* ── Section headers ── */
.sec-hdr {
    font-family:'Bebas Neue',cursive;
    font-size:1.7rem;
    color:#F97316;
    letter-spacing:3px;
    border-bottom:2px solid #F97316;
    padding-bottom:6px;
    margin: 24px 0 16px;
}

/* ── Player chip ── */
.pchip {
    display:inline-block;
    padding:4px 14px;
    border-radius:20px;
    font-size:.75rem;
    font-weight:600;
    letter-spacing:1px;
    margin:2px;
}
.bat  { background:rgba(249,115,22,.18); color:#FB923C; }
.bowl { background:rgba(59,130,246,.18); color:#60A5FA; }
.ar   { background:rgba(16,185,129,.18); color:#34D399; }
.wk   { background:rgba(167,139,250,.18); color:#A78BFA; }

/* ── Dream11 card ── */
.d11card {
    background:linear-gradient(135deg,#141E2F,#1C2840);
    border:1px solid #FFD700;
    border-radius:16px;
    padding:14px 10px;
    text-align:center;
    transition:all .2s;
    height:100%;
}
.d11card:hover {
    box-shadow:0 6px 22px rgba(255,215,0,.2);
    transform:translateY(-3px);
}
.d11name {
    font-family:'Bebas Neue',cursive;
    font-size:1.05rem;
    color:#E8EAF0;
    letter-spacing:1px;
}
.cbadge {
    background:linear-gradient(135deg,#FFD700,#F97316);
    color:#000;font-weight:800;
    font-size:.65rem;padding:2px 8px;
    border-radius:10px;letter-spacing:1px;
}
.vcbadge {
    background:linear-gradient(135deg,#9CA3AF,#6B7280);
    color:#000;font-weight:800;
    font-size:.65rem;padding:2px 8px;
    border-radius:10px;letter-spacing:1px;
}

/* ── Prediction bars ── */
.pred-bar-wrap { background:#1F2937; border-radius:6px; height:10px; margin:4px 0; }
.pred-bar { height:10px; border-radius:6px; }

/* ── Table ── */
[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; }

div[data-testid="stTabs"] button { 
    font-family:'Outfit',sans-serif !important;
    font-weight:600 !important;
}

hr { border-color:#1F2937 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  DATA LOADING
# ═══════════════════════════════════════════════════════════════

@st.cache_data
def load_stat_data()->dict:
    path = r"IPL_Stat_2008_2025.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
@st.cache_data
def load_player_names()->dict:
    path = r"short_name_to_full_name.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

@st.cache_data
def load_squad_data()->dict:
    path = r"player_team_season_mapping_info_and_images.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def get_player_image(player):
    def get_base64_image(path):
            try : 
                with open(path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()
            except Exception as e:
                default_path = r'ipl_player_images\Aakash Chopra.png'
                with open(default_path, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode()

    img_path = os.path.join("ipl_player_images", f"{player}.png")
    return get_base64_image(img_path)
stat_data  = load_stat_data()
squad_data = load_squad_data()
playerNames = load_player_names()
PN_L_to_S = {playerNames[i]:i for i in playerNames}
default_image = r'C:\\Users\\WELCOME\\Desktop\\Cricket_\\PlayerPerformancePrediction_Main_folder\\ipl_player_images\\ipl_player_images\\Anshul Kamboj.png'


# ─── Data-missing guard ──────────────────────────────────────────────────────
if stat_data is None or squad_data is None:
    st.markdown('<div class="ipl-hero"><h1>🏏 IPL ANALYTICS PRO</h1></div>', unsafe_allow_html=True)
    missing = []
    if stat_data  is None: missing.append("`IPL_Stat_2008_2025.json`")
    if squad_data is None: missing.append("`player_team_season_mapping_info_and_images.json`")
    st.error(f"⚠️  Missing data files: {', '.join(missing)}")
    st.info("Place both JSON files in the **same folder** as `app.py`, then refresh.")
    st.markdown("""
**Expected squad JSON structure:**
```json
{
  "Chennai Super Kings": {
    "2024": {
      "Players_Detail": {
        "MS Dhoni": { "role": "WK-Batter", "img": "path/or/url" },
        ...
      }
    }
  }
}
```
**Expected stat JSON structure (IPL_Stat_2008_2025.json):**
```json
{
  "MS Dhoni": {
    "op_team":   { "Mumbai Indians": { "Bt_Runs":830, ... } },
    "op_Bowler": { "JJ Bumrah":      { "Runs":50, ... } },
    "op_Batter": { "RG Sharma":      { "Runs":41, ... } },
    "Last_recent_matches": { "Bt_Avg":35, "Bt_Strike_rate":132, ... }
  }
}
```
""")
    st.stop()

# ═══════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════


def role_chip_Batter(player):
    role = stat_data.get(player, {}).get("op_Bowler", {}).keys()
    if role:
        return "Batter"
   
    return ""
def role_chip_Bowler(player):
    role = stat_data.get(player, {}).get("op_Batter", {}).keys()
    if role:
        return "Bowler"
   
    return ""

def get_teams():
    return sorted(squad_data.keys())

def get_seasons(team):
    return sorted(squad_data[team].keys(), reverse=True)

def get_squad(team, season):
    return squad_data.get(team, {}).get(season, {}).get("Players_Detail", {})

def get_common_seasons(t1, t2):
    s1 = set(squad_data.get(t1, {}).keys())
    s2 = set(squad_data.get(t2, {}).keys())
    common = s1 & s2
    return sorted(common, reverse=True)

# ── Stat lookups ─────────────────────────────────────────────────────────────

def stat_vs_team(player, opp_team):
    return stat_data.get(player, {}).get("op_team", {}).get(opp_team, {})

def stat_vs_bowler(player, bowler):
    return stat_data.get(player, {}).get("op_Bowler", {}).get(PN_L_to_S.get(bowler, bowler), {})

def stat_vs_batter(player, batter):
    return stat_data.get(player, {}).get("op_Batter", {}).get(PN_L_to_S.get(batter,batter), {})

def recent_form(player):
    return stat_data.get(player, {}).get("Last_recent_matches", {})

def all_teams_stats(player):
    return stat_data.get(player, {}).get("op_team", {})
def current_teams_stats(player,team):
    return stat_data.get(player, {}).get("op_team", {}).get(team,{})

def career_summary_Batter(player):
    td = all_teams_stats(player)
    total_runs  = sum(v.get("Bt_Runs",0)        for v in td.values())
    total_balls = sum(v.get("Bt_Balls",0)        for v in td.values())
    total_wkts  = sum(v.get("Lose_Wicket",0)     for v in td.values())
    total_m     = sum(v.get("Matches",0)         for v in td.values())
    total_matches_played = sum( len([1 for x in lst if x > 0]) for lst in (v.get("Bt_Balls_list",[])   for v in td.values()))
    total_50s     = sum(len([x for x in lst if 50 <= x < 100]) for lst in (v.get("Bt_Runs_list", []) for v in td.values()))
    total_100s    = sum(len([x for x in lst if x >= 100]) for lst in (v.get("Bt_Runs_list", []) for v in td.values()))
    highest_score = max(
        x 
        for v in td.values() 
        for x in v.get("Bt_Runs_list", [])
    )

    return {
        "matches": total_m,
        "runs": total_runs,
        "sr": round(total_runs/total_balls*100,2) if total_balls>0 else 0,
        "avg": round(total_runs/max(total_matches_played,1),2),
        "wickets": total_wkts,
        "50s": total_50s,
        "100s": total_100s,
        "matches_played": total_matches_played,
        "highest_score": highest_score,
    }
def career_summary_team(player,t):
    td = all_teams_stats(player)
    team = td.get(t,{})
    total_btruns  = team.get("Bt_Runs",0)
    total_btballs = team.get("Bt_Balls",0)
    total_bwruns  = team.get("Bw_Runs",0)
    total_bwballs = team.get("Bw_Balls",0)
    total_bt_W  = team.get("Lose_Wicket",0)
    total_bw_W  = team.get("Gain_Wicket",0)
    total_m     = team.get("Matches",0)
    total_bt_matches_played = len([x for x in team.get("Bt_Balls_list", []) if x > 0])
    total_bw_matches_played = len([x for x in team.get("Bw_Balls_list", []) if x > 0])
    total_50s     = len([x for x in team.get("Bt_Runs_list", []) if 50 <= x < 100])
    total_100s    =  len([x for x in team.get("Bt_Runs_list", []) if x >= 100])
    highest_score = max(
        x 
        
        for x in team.get("Bt_Runs_list", [])
    )
    Best3     = len([x for x in team.get("Bw_W_list", []) if x==3])   
    Best4     = len([x for x in team.get("Bw_W_list", []) if x==4])   
    Best5     = len([x for x in team.get("Bw_W_list", []) if x>=5])  
    highest_wicket = max(
        x 
        for x in team.get("Bw_W_list", [])
    )

    return {
        "matches": total_m,
        "total_bt_matches_played": total_bt_matches_played,
        "total_bw_matches_played": total_bw_matches_played,
        "btruns": total_btruns,
        "total_btW": total_bt_W,
        "total_bwW": total_bw_W,
        "economy": round((total_bwruns/total_bwballs)*6,2) if total_bwballs>0 else 0,
        "sr": round(total_btruns/total_btballs*100,2) if total_btballs>0 else 0,
        "avg": round(total_btruns/max(total_bt_W,1),2),    
        "50s": total_50s,
        "100s": total_100s,
       "3W": Best3,
         "4W": Best4,
            "5W+": Best5,
        "highest_bt_score": highest_score,
        "highest_wicket": highest_wicket,
    }
def career_summary_Bowler(player):
    td = all_teams_stats(player)
    total_wkts  = sum(v.get("Gain_Wicket",0)     for v in td.values())
    total_bwb   = sum(v.get("Bw_Balls",0)        for v in td.values())
    total_bwr   = sum(v.get("Bw_Runs",0)         for v in td.values())
    total_m     = sum(v.get("Matches",0)         for v in td.values())
    total_matches_played = sum(
        len([1 for x in lst if x > 0])
        for lst in (v.get("Bw_Balls_list", []) for v in td.values())
    ) or total_m
    Best3     = sum(len([x for x in lst if x==3]) for lst in (v.get("Bw_W_list", []) for v in td.values()))
    Best4     = sum(len([x for x in lst if x==4]) for lst in (v.get("Bw_W_list", []) for v in td.values()))
    Best5     = sum(len([x for x in lst if x>=5]) for lst in (v.get("Bw_W_list", []) for v in td.values()))
    highest_wicket = max(
        x 
        for v in td.values() 
        for x in v.get("Bw_W_list", [])
    )
   
    return {
        "matches": total_m,
        "matches_played": total_matches_played,
        "wickets": total_wkts,
        "economy": round((total_bwr/total_bwb)*6,2) if total_bwb>0 else 0,
        "bwballs": total_bwb,
        "best3": Best3,
        "best4": Best4,
        "best5": Best5,
        "highwicket":highest_wicket,
    }



# ═══════════════════════════════════════════════════════════════
#  DREAM11 SCORING ENGINE
# ═══════════════════════════════════════════════════════════════

def dream11_score(player, squad_role, opp_team):
    """
    Score a player for Dream11 selection.
    Uses: H2H vs opp_team  +  recent form  +  role bonus
    """
    sc = 0.0
    vs  = stat_vs_team(player, opp_team)
    rec = recent_form(player)

    # ── H2H batting ──────────────────────────────
    h2h_runs = vs.get("Bt_Runs", 0)
    h2h_sr   = vs.get("Bt_Strike_rate", 0)
    h2h_m    = max(vs.get("Matches", 1), 1)
    h2h_avg  = vs.get("Bt_Avg", h2h_runs / h2h_m)

    sc += h2h_avg * 1.2
    sc += max(h2h_sr - 100, 0) * 0.15

    # ── H2H bowling ──────────────────────────────
    h2h_wkts = vs.get("Gain_Wicket", 0)
    h2h_econ = vs.get("Bw_economy", 10)
    sc += (h2h_wkts / h2h_m) * 20
    sc += max(9 - h2h_econ, 0) * 2

    # ── Recent form ──────────────────────────────
    rec_avg  = rec.get("Bt_Avg", 0)
    rec_sr   = rec.get("Bt_Strike_rate", 0)
    rec_bw_e = rec.get("Bw_economy", 10)
    rec_bw_w = rec.get("Bw_Avg_Wickets", 0)

    sc += rec_avg  * 0.9
    sc += max(rec_sr - 100, 0) * 0.1
    sc += rec_bw_w * 15
    sc += max(9 - rec_bw_e, 0) * 1.5

    # ── Role bonus ───────────────────────────────
    r = ROLE_MAP.get(squad_role, classify_role(player))
    if r == "WK": sc += 10
    if r == "AR": sc += 8

    return round(sc, 2)

def pick_dream11(squad1, squad2, team1_name, team2_name):
    """
    Pick balanced XI: 1 WK, 3-4 BAT, 2-3 AR, 3-4 BOWL
    from two squads of 11.
    """
    all_players = []
    for p, info in squad1.items():
        role = ROLE_MAP.get(info.get("role","Batter"), "BAT")
        sc   = dream11_score(p, info.get("role","Batter"), team2_name)
        all_players.append({"player":p,"role":role,"team":team1_name,"score":sc,"img":info.get("img","")})
    for p, info in squad2.items():
        role = ROLE_MAP.get(info.get("role","Batter"), "BAT")
        sc   = dream11_score(p, info.get("role","Batter"), team1_name)
        all_players.append({"player":p,"role":role,"team":team2_name,"score":sc,"img":info.get("img","")})

    all_players.sort(key=lambda x: x["score"], reverse=True)

    limits  = {"WK":1,"BAT":4,"AR":3,"BOWL":3}
    counts  = {"WK":0,"BAT":0,"AR":0,"BOWL":0}
    t_count = {team1_name:0, team2_name:0}
    selected = []

    # first pass – respect limits
    for p in all_players:
        if len(selected) >= 11: break
        r, t = p["role"], p["team"]
        if counts.get(r,0) < limits.get(r,4) and t_count.get(t,0) < 7:
            selected.append(p)
            counts[r] = counts.get(r,0) + 1
            t_count[t] = t_count.get(t,0) + 1

    # fill remaining (relax limits)
    if len(selected) < 11:
        for p in all_players:
            if len(selected) >= 11: break
            if p not in selected:
                selected.append(p)

    return selected

# ═══════════════════════════════════════════════════════════════
#  PREDICTION ENGINE  (simple weighted regression-like blending)
# ═══════════════════════════════════════════════════════════════

def predict_performance(player, opp_team):
    vs  = stat_vs_team(player, opp_team)
    rec = recent_form(player)

    h2h_m = max(vs.get("Matches",0), 1)

    # ── Batting ──────────────────────────────────
    h2h_avg  = vs.get("Bt_Avg", 0)
    h2h_sr   = vs.get("Bt_Strike_rate", 0)
    rec_avg  = rec.get("Bt_Avg", 0)
    rec_sr   = rec.get("Bt_Strike_rate", 0)

    # weight: more H2H games → trust H2H more
    w_h2h = min(h2h_m / 15, 0.7)
    w_rec = 1 - w_h2h

    pred_runs = round(h2h_avg * w_h2h + rec_avg * w_rec, 1)
    pred_sr   = round(h2h_sr  * w_h2h + rec_sr  * w_rec, 1)

    # ── Bowling ──────────────────────────────────
    h2h_wkts = vs.get("Gain_Wicket", 0)
    h2h_wpm  = h2h_wkts / h2h_m
    rec_wpm  = rec.get("Bw_Avg_Wickets", 0)
    pred_wkts = round(h2h_wpm * w_h2h + rec_wpm * w_rec, 2)

    h2h_econ = vs.get("Bw_economy", 0)
    rec_econ = rec.get("Bw_economy", 0)
    pred_econ = round(h2h_econ * w_h2h + rec_econ * w_rec, 2)

    # ── Boundary prediction ───────────────────────
    # Use stored run list if available
    run_list = vs.get("Bt_Runs_list", [])
    six_list = vs.get("Six_list", [])
    four_list= vs.get("four_list",[])
    pred_4s  = round(sum(four_list)/max(len(four_list),1), 1)
    pred_6s  = round(sum(six_list) /max(len(six_list), 1), 1)

    return {
        "runs": pred_runs, "sr": pred_sr,
        "wickets": pred_wkts, "economy": pred_econ,
        "fours": pred_4s, "sixes": pred_6s,
        "h2h_matches": h2h_m-1,
    }

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



# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — ALL PLAYER STATS
# ══════════════════════════════════════════════════════════════════════════════

if page == "🏟️  All Player Stats":
    st.markdown('<div class="sec-hdr">📊 PLAYER STATISTICS</div>', unsafe_allow_html=True)

    # Get all players from stat data
    all_players = sorted(list(PN_L_to_S.keys()))
    
    # Player selection
    
    selected_player = st.selectbox("Select Player", all_players, key="player_select",)

    if selected_player:
        player_info = stat_data.get(PN_L_to_S[selected_player], {})
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
        
        if role_chip_Batter(PN_L_to_S[selected_player]) == "Batter":
            cs = career_summary_Batter(PN_L_to_S[selected_player])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                <div>
                    Batter
                    <span style="color:#64748B;font-size:.8rem;margin-left:8px">
                        Career Statistics
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Career summary cards
            cols = st.columns(6)
            mets = [
                ("MATCHES",   cs["matches_played"],                  "#F97316"),
                ("RUNS",      cs["runs"],                     "#FBBF24"),
                ("BAT AVG",   f"{cs['avg']}",                 "#34D399"),
                ("STRIKE RT", f"{cs['sr']}",                  "#60A5FA"),
                ("50s/100s",   f"{cs['50s']}/{cs['100s']}",                  "#A78BFA"),
                ("Best Score",   f"{cs['highest_score']}",                  "#FA908B"),
               
            ]
            for c, (lbl, val, col) in zip(cols, mets):
                c.markdown(f"""<div class="stat-card">
                    <div class="stat-val" style="color:{col}">{val}</div>
                    <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

            st.divider()
        if role_chip_Bowler(PN_L_to_S[selected_player]) == "Bowler":
            cs = career_summary_Bowler(PN_L_to_S[selected_player])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
                <div>
                    Bowler
                    <span style="color:#64748B;font-size:.8rem;margin-left:8px">
                        Career Statistics
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Career summary cards
            cols = st.columns(6)
            mets = [
                ("MATCHES",   cs["matches_played"],                  "#F97316"),
                ("WICKETS",   cs["wickets"],                 "#FBBF24"),
                ("ECONOMY",    cs['economy'],              "#34D399"),
                ("3s/4s",   f"{cs['best3']}/{cs['best4']}",              "#60A5FA"),
                ("5s + ",   f"{cs['best5']}",             "#A78BFA"),
                ("Best Wicket",   f"{cs['highwicket']}",             "#FA908B"),

            ]
            for c, (lbl, val, col) in zip(cols, mets):
                c.markdown(f"""<div class="stat-card">
                    <div class="stat-val" style="color:{col}">{val}</div>
                    <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

            st.divider()

        # Tabs for different stat views
        tab_career, tab_vs_teams, tab_vs_bowlers, tab_vs_batters, tab_recent = st.tabs([
            "📈 Career Overview", "🆚 vs Teams", "⚾ vs Bowlers", "🏏 vs Batters", "📊 Recent Form"
        ])

        # ── Career Overview ──────────────────────────────────────────────────────
        with tab_career:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("# Batting Statistics ")
                cs = career_summary_Batter(PN_L_to_S[selected_player])
                batting_stats = [
                    ("TotalMatches", cs["matches"]),
                    ("Played Innings", cs["matches_played"]),
                    ("Total Runs", cs["runs"]),
                    ("Batting Average", f"{cs['avg']:.2f}"),
                    ("Strike Rate", f"{cs['sr']:.2f}"),
                    ("50S/100S", f"{cs['50s']}/{cs['100s']}"),
                    ("Wicket Lost", f"{cs['wickets']}"),
                    ("Best Score", f"{cs['highest_score']}"),
                ]

                for stat, value in batting_stats:
                    st.markdown(f"**{stat}:** {value}")

            with col2:
                st.markdown("# Bowling Statistics ")
                cs = career_summary_Bowler(PN_L_to_S[selected_player])
                bowling_stats = [
                    ("TotalMatches", cs["matches"]),
                    ("Played Innings", cs["matches_played"]),
                    ("Total Wickets", cs["wickets"]),
                    ("Economy Rate", f"{cs['economy']:.2f}"),
                    ("3W", f"{cs['best3']}"),
                    ("4W", f"{cs['best4']}"),
                    ("5W+", f"{cs['best5']}"),
                    ("Best Wicket", f"{cs['highwicket']}"),
                ]

                for stat, value in bowling_stats:
                    st.markdown(f"**{stat}:** {value}")

        # ── vs Teams ─────────────────────────────────────────────────────────────
        with tab_vs_teams:
            team_stats = all_teams_stats(PN_L_to_S[selected_player])
            team_list = list(stat_data.get(PN_L_to_S[selected_player],{}).get('op_team').keys())
            # st.write(team_stats)
            if team_list:
                selected_team = st.selectbox("Select team", sorted(team_list), key="vs_team_select")
                if selected_team:
                    st.markdown(f"### {selected_player} vs {selected_team}")
                    team_stat = career_summary_team(PN_L_to_S[selected_player], selected_team)
                    if team_stat.get("total_bt_matches_played", team_stat.get("total_balls", 0)) > 0:
                        st.markdown("**Batting Statistics**")
                        # Stats display
                        bcols = st.columns(6)
                        team_mets = [
                            ("Matches", team_stat.get("total_bt_matches_played", team_stat.get("total_balls", 0)), "#F97316"),
                            ("RUNS SCORED", team_stat.get("btruns", team_stat.get("total_runs", 0)), "#FBBF24"),
                            ("AVERAGE", f"{team_stat.get('avg', team_stat.get('bt_average', 0)):.2f}", "#34D399"),
                            ("STRIKE RATE", f"{team_stat.get('sr', team_stat.get('bt_strike_rate', 0)):.1f}", "#60A5FA"),
                            ("50s/100s", f"{team_stat.get('50s', 0)}/{team_stat.get('100s', 0)}", "#A78BFA"),
                            ("Best Score", f"{team_stat.get('highest_bt_score', 0)}", "#FA908B"),
                        ]
                        for c, (lbl, val, col) in zip(bcols, team_mets):
                            c.markdown(f"""<div class="stat-card">
                                <div class="stat-val" style="color:{col}">{val}</div>
                                <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)
                    if team_stat.get("total_bw_matches_played", 0) > 0:
                        st.markdown("**Bowling Statistics**")
                        # Stats display
                        bcols = st.columns(6)
                        team_mets = [
                            ("Matches", team_stat.get("total_bw_matches_played", team_stat.get("total_balls", 0)), "#F97316"),
                            ("Wickets", team_stat.get("total_bwW", team_stat.get("total_runs", 0)), "#FBBF24"),
                            ("ECONOMY", f"{team_stat.get('economy', team_stat.get('bt_average', 0)):.2f}", "#34D399"),
                            ("3w/4w", f"{team_stat.get('3W',0)}/{team_stat.get('4W', 0)}", "#60A5FA"),
                            ("5+", f"{team_stat.get('5W+', 0)}", "#A78BFA"),
                            ("Best Wicket", f"{team_stat.get('highest_wicket', 0)}", "#FA908B"),
                        ]
                        for c, (lbl, val, col) in zip(bcols, team_mets):
                            c.markdown(f"""<div class="stat-card">
                                <div class="stat-val" style="color:{col}">{val}</div>
                                <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

                    # # Detailed analysis
                    # st.markdown("**Detailed Batting Analysis vs Bowler**")
                    # analysis_cols = st.columns(2)
                    # with analysis_cols[0]:
                    #     runs_vs_bowler = bowler_stats.get("Runs", bowler_stats.get("total_runs", 0))
                    #     balls_vs_bowler = bowler_stats.get("Balls", bowler_stats.get("total_balls", 0))
                    #     avg_vs_bowler = runs_vs_bowler / max(bowler_stats.get("Matches", 1), 1)
                    #     sr_vs_bowler = (runs_vs_bowler / balls_vs_bowler * 100) if balls_vs_bowler > 0 else 0

                    #     st.markdown(f"**Runs Scored:** {runs_vs_bowler}")
                    #     st.markdown(f"**Balls Faced:** {balls_vs_bowler}")
                    #     st.markdown(f"**Average:** {avg_vs_bowler:.2f}")
                    #     st.markdown(f"**Strike Rate:** {sr_vs_bowler:.2f}")
                    #     st.markdown(f"**Matches Faced:** {bowler_stats.get('Matches', 1)}")

                    # with analysis_cols[1]:
                    #     wickets_by_bowler = bowler_stats.get("T_Wicket", bowler_stats.get("total_wicket", 0))
                    #     dismissal_rate = (wickets_by_bowler / bowler_stats.get("Matches", 1) * 100) if bowler_stats.get("Matches", 1) > 0 else 0

                    #     st.markdown(f"**Times Dismissed:** {wickets_by_bowler}")
                    #     st.markdown(f"**Dismissal Rate:** {dismissal_rate:.1f}%")

                    #     # Boundary stats
                    #     fours_vs_bowler = bowler_stats.get("fours", 0)
                    #     sixes_vs_bowler = bowler_stats.get("sixes", 0)
                    #     st.markdown(f"**Fours:** {fours_vs_bowler}")
                    #     st.markdown(f"**Sixes:** {sixes_vs_bowler}")
            if team_stats:
                rows = []
                for team, stat in team_stats.items():
                    stats = career_summary_team(PN_L_to_S[selected_player], team)
                    rows.append({
                        "Team": team,
                        "Matches": stats.get("matches", 0),
                        "Runs": stats.get("btruns", 0),
                        "Average": round(stats.get("avg", 0), 2),
                        "Strike Rate": round(stats.get("sr", 0), 2),
                        "Wickets": stats.get("total_bwW", 0),
                        "Economy": round(stats.get("economy", 0), 2),
                    })
                st.write("**Team-wise Statistics**")
                df_teams = pd.DataFrame(rows).sort_values("Runs", ascending=False)
                st.dataframe(df_teams.style.background_gradient(subset=["Runs"], cmap="Oranges")
                                   .background_gradient(subset=["Wickets"], cmap="Blues"),
                           use_container_width=True, hide_index=True)

                # Top performances
                st.markdown("**Top Batting Performances**")
                top_batting = df_teams.nlargest(5, "Runs")[["Team", "Runs", "Average", "Strike Rate"]]
                st.dataframe(top_batting, use_container_width=True, hide_index=True)

                st.markdown("**Top Bowling Performances**")
                top_bowling = df_teams.nlargest(5, "Wickets")[["Team", "Wickets", "Economy"]]
                st.dataframe(top_bowling, use_container_width=True, hide_index=True)
            else:
                st.info("No team-wise statistics available")

        # ── vs Specific Bowlers ─────────────────────────────────────────────────
        with tab_vs_bowlers:
            bowlers_list = [playerNames.get(p,p) for p in player_info.get("op_Bowler", {}).keys()]
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
                    
                    bowler_stats = stat_vs_bowler(PN_L_to_S[selected_player], selected_bowler)


                    # Stats display
                    bcols = st.columns(6)
                    bowler_mets = [
                        ("RUNS SCORED", bowler_stats.get("Runs", bowler_stats.get("total_runs", 0)), "#F97316"),
                        ("BALLS FACED", bowler_stats.get("Balls", bowler_stats.get("total_balls", 0)), "#FBBF24"),
                        ("STRIKE RATE", f"{bowler_stats.get('Strike_rate', bowler_stats.get('bt_strike_rate', 0)):.1f}", "#34D399"),
                        ("DISMISSALS", bowler_stats.get("T_Wicket", bowler_stats.get("total_wicket", 0)), "#60A5FA"),
                        ("FOURS", bowler_stats.get("fours", 0), "#A78BFA"),
                        ("SIXES", bowler_stats.get("sixes", 0), "#FA908B"),
                    ]
                    for c, (lbl, val, col) in zip(bcols, bowler_mets):
                        c.markdown(f"""<div class="stat-card">
                            <div class="stat-val" style="color:{col}">{val}</div>
                            <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

                    # Detailed analysis
                    st.markdown("**Detailed Batting Analysis vs Bowler**")
                    analysis_cols = st.columns(2)
                    with analysis_cols[0]:
                        runs_vs_bowler = bowler_stats.get("Runs", bowler_stats.get("total_runs", 0))
                        balls_vs_bowler = bowler_stats.get("Balls", bowler_stats.get("total_balls", 0))
                        avg_vs_bowler = runs_vs_bowler / max(bowler_stats.get("Matches", 1), 1)
                        sr_vs_bowler = (runs_vs_bowler / balls_vs_bowler * 100) if balls_vs_bowler > 0 else 0

                        st.markdown(f"**Runs Scored:** {runs_vs_bowler}")
                        st.markdown(f"**Balls Faced:** {balls_vs_bowler}")
                        st.markdown(f"**Average:** {avg_vs_bowler:.2f}")
                        st.markdown(f"**Strike Rate:** {sr_vs_bowler:.2f}")
                        st.markdown(f"**Matches Faced:** {bowler_stats.get('Matches', 1)}")

                    with analysis_cols[1]:
                        wickets_by_bowler = bowler_stats.get("T_Wicket", bowler_stats.get("total_wicket", 0))
                        dismissal_rate = (wickets_by_bowler / bowler_stats.get("Matches", 1) * 100) if bowler_stats.get("Matches", 1) > 0 else 0

                        st.markdown(f"**Times Dismissed:** {wickets_by_bowler}")
                        st.markdown(f"**Dismissal Rate:** {dismissal_rate:.1f}%")

                        # Boundary stats
                        fours_vs_bowler = bowler_stats.get("fours", 0)
                        sixes_vs_bowler = bowler_stats.get("sixes", 0)
                        st.markdown(f"**Fours:** {fours_vs_bowler}")
                        st.markdown(f"**Sixes:** {sixes_vs_bowler}")

                    # Performance trend
                    if bowler_stats.get("Runs_list"):
                        # Prepare data with wicket markers
                        runs_list = bowler_stats.get("Runs_list", [])
                        w_list = bowler_stats.get("W_list", [])
                        x_vals = list(range(len(runs_list)))
                        
                        # Create figure with runs line
                        fig_bowler = go.Figure(go.Scatter(
                            x=x_vals,
                            y=runs_list,
                            mode='lines+markers',
                            line=dict(color='#F97316', width=2),
                            marker=dict(size=8, color='#F97316'),
                            name='Runs Scored',
                        ))
                        
                        # Add wicket markers on the same plot
                        for i, (runs, wkts) in enumerate(zip(runs_list, w_list)):
                            if wkts > 0:  # Only mark if wicket occurred
                                fig_bowler.add_trace(go.Scatter(
                                    x=[i],
                                    y=[runs],
                                    mode='markers',
                                    marker=dict(size=15, color='#EF4444', symbol='star', 
                                              line=dict(color='#FCA5A5', width=2)),
                                    name=f'Wicket ({int(wkts)})',
                                    hovertemplate=f'<b>Match {i}</b><br>Runs: {runs}<br>Wickets: {int(wkts)}<extra></extra>',
                                    showlegend=(i == next(j for j, w in enumerate(w_list) if w > 0))  # Show legend only once
                                ))
                        
                        fig_bowler.update_layout(
                            title=f"Runs vs {selected_bowler} — Wicket Markers",
                            plot_bgcolor="rgba(0,0,0,0)", 
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#CBD5E1", 
                            height=320, 
                            title_font_color="#F97316",
                            margin=dict(l=10,r=10,t=40,b=30),
                            xaxis=dict(gridcolor="#1F2937", title="Match Number"),
                            yaxis=dict(gridcolor="#1F2937", title="Runs"),
                            hovermode='x unified',
                        )
                        st.plotly_chart(fig_bowler, use_container_width=True)
            else:
                st.info("No bowler statistics available")

        # ── vs Specific Batters ─────────────────────────────────────────────────
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

                    batter_stats = stat_vs_batter(PN_L_to_S.get(selected_player, selected_player), selected_batter)
                    


                    # Stats display
                    bat_cols = st.columns(6)
                    batter_mets = [
                        ("RUNS CONCEDED", batter_stats.get("Runs", batter_stats.get("total_runs", 0)), "#F97316"),
                        ("BALLS BOWLED", batter_stats.get("Balls", batter_stats.get("total_balls", 0)), "#FBBF24"),
                        ("WICKETS TAKEN", batter_stats.get("T_Wicket", batter_stats.get("total_wicket", 0)), "#34D399"),
                        ("ECONOMY", f"{(batter_stats.get('Runs', 0) / max(batter_stats.get('Balls', 1), 1) * 6):.2f}", "#60A5FA"),
                        ("Success Rate", f"{(batter_stats.get('T_Wicket', 0) / max(batter_stats.get('Matches', 1), 1) * 100):.1f}%", "#A78BFA"),
                        
                    ]
                    for c, (lbl, val, col) in zip(bat_cols, batter_mets):
                        c.markdown(f"""<div class="stat-card">
                            <div class="stat-val" style="color:{col}">{val}</div>
                            <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

                    # Detailed bowling analysis
                    st.markdown("**Detailed Bowling Analysis vs Batter**")
                    bowl_analysis_cols = st.columns(2)
                    with bowl_analysis_cols[0]:
                        runs_conceded = batter_stats.get("Runs", batter_stats.get("total_runs", 0))
                        balls_bowled = batter_stats.get("Balls", batter_stats.get("total_balls", 0))
                        wickets_taken = batter_stats.get("T_Wicket", batter_stats.get("total_wicket", 0))
                        economy = (runs_conceded / balls_bowled * 6) if balls_bowled > 0 else 0
                        avg_balls_per_wicket = balls_bowled / max(wickets_taken, 1)

                        st.markdown(f"**Runs Conceded:** {runs_conceded}")
                        st.markdown(f"**Balls Bowled:** {balls_bowled}")
                        st.markdown(f"**Wickets Taken:** {wickets_taken}")
                        st.markdown(f"**Economy Rate:** {economy:.2f}")
                        st.markdown(f"**Avg Balls/Wicket:** {avg_balls_per_wicket:.1f}")

                    with bowl_analysis_cols[1]:
                        matches_vs_batter = batter_stats.get("Matches", 1)
                        avg_wickets = wickets_taken / matches_vs_batter
                        success_rate = (wickets_taken / matches_vs_batter * 100) if matches_vs_batter > 0 else 0

                        st.markdown(f"**Matches:** {matches_vs_batter}")
                        st.markdown(f"**Avg Wickets/Match:** {avg_wickets:.2f}")
                        st.markdown(f"**Success Rate:** {success_rate:.1f}%")

                        # Boundary stats
                        fours_conceded = sum(stat_data.get(PN_L_to_S.get(selected_player, selected_player), {}).get("op_Batter", {}).get(selected_batter, {}).get("four_list", [0]))
                        sixes_conceded = sum(stat_data.get(PN_L_to_S.get(selected_player, selected_player), {}).get("op_Batter", {}).get(selected_batter, {}).get("Six_list", [0]))
                        st.markdown(f"**Fours Conceded:** {fours_conceded}")
                        st.markdown(f"**Sixes Conceded:** {sixes_conceded}")

                    # Wickets trend
                    if batter_stats.get("Runs_list"):
                        # Prepare data with wicket markers
                        runs_list = batter_stats.get("Runs_list", [])
                        w_list = batter_stats.get("W_list", [])
                        x_vals = list(range(len(runs_list)))
                        
                        # Create figure with runs line
                        fig_bowler = go.Figure(go.Scatter(
                            x=x_vals,
                            y=runs_list,
                            mode='lines+markers',
                            line=dict(color='#F97316', width=2),
                            marker=dict(size=8, color='#F97316'),
                            name='Runs Scored',
                        ))
                        
                        # Add wicket markers on the same plot
                        for i, (runs, wkts) in enumerate(zip(runs_list, w_list)):
                            if wkts > 0:  # Only mark if wicket occurred
                                fig_bowler.add_trace(go.Scatter(
                                    x=[i],
                                    y=[runs],
                                    mode='markers',
                                    marker=dict(size=15, color='#EF4444', symbol='star', 
                                              line=dict(color='#FCA5A5', width=2)),
                                    name=f'Wicket ({int(wkts)})',
                                    hovertemplate=f'<b>Match {i}</b><br>Runs: {runs}<br>Wickets: {int(wkts)}<extra></extra>',
                                    showlegend=(i == next(j for j, w in enumerate(w_list) if w > 0))  # Show legend only once
                                ))
                        
                        fig_bowler.update_layout(
                            title=f"Runs vs {selected_bowler} — Wicket Markers",
                            plot_bgcolor="rgba(0,0,0,0)", 
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#CBD5E1", 
                            height=320, 
                            title_font_color="#F97316",
                            margin=dict(l=10,r=10,t=40,b=30),
                            xaxis=dict(gridcolor="#1F2937", title="Match Number"),
                            yaxis=dict(gridcolor="#1F2937", title="Runs"),
                            hovermode='x unified',
                        )
                        st.plotly_chart(fig_bowler, use_container_width=True)

                    # All batters performance vs this player
                    all_batters = player_info.get("op_Batter", {})
                    if all_batters:
                        rows_all = []
                        for bat, stats in all_batters.items():
                            name = playerNames.get(bat, bat)
                            runs = stats.get("Runs", stats.get("total_runs", 0))
                            balls = stats.get("Balls", stats.get("total_balls", 0))
                            wickets = stats.get("T_Wicket", stats.get("total_wicket", 0))
                            sr = stats.get("Strike_rate", stats.get("bt_strike_rate", 0))
                            matches = stats.get("Matches", 1)
                            avg = stats.get("Avg", runs / matches if matches else 0)
                            rows_all.append({
                                "Batter": name,
                                "Matches": matches,
                                "Runs": runs,
                                "Balls": balls,
                                "SR": round(sr, 1),
                                "Avg": round(avg, 1),
                                "Wkts": wickets,
                            })

                        df_all_batters = pd.DataFrame(rows_all).sort_values("Runs", ascending=False)
                        st.markdown("**All Batters Faced — Performance Summary**")
                        st.dataframe(df_all_batters, use_container_width=True, hide_index=True)

                        st.markdown("**Best 5 Batters Faced**")
                        st.dataframe(df_all_batters.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("No batter statistics available")

        # ── Recent Form ─────────────────────────────────────────────────────────
        with tab_recent:
            rec = recent_form(PN_L_to_S.get(selected_player, selected_player))
            if rec:
                rc1, rc2, rc3, rc4 = st.columns(4)
                mets_rec = [
                    ("REC BAT AVG",  f"{rec.get('Bt_Avg',0):.1f}",         "#F97316"),
                    ("REC STRIKE RT",f"{rec.get('Bt_Strike_rate',0):.1f}", "#FBBF24"),
                    ("REC BW ECON",  f"{rec.get('Bw_economy',0):.2f}",     "#60A5FA"),
                    ("REC WKT/GM",   f"{rec.get('Bw_Avg_Wickets',0):.2f}", "#A78BFA"),
                ]
                for c, (lbl, val, col) in zip([rc1,rc2,rc3,rc4], mets_rec):
                    c.markdown(f"""<div class="stat-card">
                        <div class="stat-val" style="color:{col};font-size:2rem">{val}</div>
                        <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

                # Recent runs chart
                recent_runs  = rec.get("Bt_Runs", [])
                recent_years = rec.get("year", [])
                if isinstance(recent_runs, list) and recent_runs:
                    match_options = [5, 10, 15, 20, "All"]
                    selected_matches = st.selectbox(
                        "Show previous matches", match_options,
                        format_func=lambda x: f"{x} matches" if isinstance(x, int) else "All matches",
                        key="recent_matches_count"
                    )
                    if selected_matches == "All":
                        slice_count = len(recent_runs)
                    else:
                        slice_count = min(len(recent_runs), selected_matches)

                    recent_runs_slice = recent_runs[:slice_count]
                    if isinstance(recent_years, list) and recent_years:
                        recent_years_slice = recent_years[:slice_count]
                    else:
                        recent_years_slice = list(range(1, slice_count + 1))

                    match_numbers = list(range(1, slice_count + 1))
                    status_keys = ["not_out", "out", "dismissed", "status"]
                    status_list = None
                    for key in status_keys:
                        raw_list = rec.get(key)
                        if isinstance(raw_list, list) and len(raw_list) >= slice_count:
                            status_list = raw_list[:slice_count]
                            break

                    if status_list is not None:
                        status_labels = []
                        for raw in status_list:
                            if isinstance(raw, bool):
                                status_labels.append("Not Out" if raw is False else "Out")
                            elif isinstance(raw, (int, float)):
                                status_labels.append("Out" if raw else "Not Out")
                            else:
                                status_labels.append(str(raw))
                    else:
                        status_labels = ["Status unavailable"] * slice_count

                    fig = go.Figure(go.Bar(
                        x=match_numbers,
                        y=recent_runs_slice,
                        marker_color=[
                            '#F97316' if r >= 50 else '#FBBF24' if r >= 30 else '#374151'
                            for r in recent_runs_slice
                        ],
                        hovertemplate=
                            'Match %{x}<br>Runs: %{y}<br>Status: %{customdata}<extra></extra>',
                        customdata=status_labels,
                    ))
                    fig.update_layout(
                        title=f"Recent Innings — Last {slice_count} Matches",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#CBD5E1", height=360, title_font_color="#FBBF24",
                        margin=dict(l=10,r=10,t=40,b=30),
                        xaxis=dict(gridcolor="#1F2937", title="Match Number"),
                        yaxis=dict(gridcolor="#1F2937", title="Runs"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Yearly summary graph
                    if isinstance(recent_years, list) and recent_years:
                        df_year = pd.DataFrame({
                            "year": [str(y) for y in recent_years],
                            "runs": recent_runs,
                        })
                        df_summary = df_year.groupby("year", as_index=False).agg(
                            Matches=("runs", "size"),
                            Total_Runs=("runs", "sum"),
                            Avg_Runs=("runs", "mean"),
                        ).sort_values("year")

                        fig2 = go.Figure()
                        fig2.add_trace(go.Bar(
                            x=df_summary["year"],
                            y=df_summary["Total_Runs"],
                            name="Total Runs",
                            marker_color="#F97316",
                        ))
                        fig2.add_trace(go.Scatter(
                            x=df_summary["year"],
                            y=df_summary["Avg_Runs"],
                            name="Avg Runs",
                            mode='lines+markers',
                            line=dict(color='#60A5FA', width=2),
                            marker=dict(size=8, color='#60A5FA'),
                        ))
                        fig2.update_layout(
                            title="Yearly Performance Summary",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#CBD5E1", height=360, title_font_color="#F97316",
                            margin=dict(l=10,r=10,t=40,b=30),
                            xaxis=dict(gridcolor="#1F2937", tickangle=-45, title="Year"),
                            yaxis=dict(gridcolor="#1F2937", title="Runs"),
                            legend=dict(orientation='h', y=-0.2, x=0.02),
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No recent batting data available")
            else:
                st.info("No recent form data available")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — PLAYER DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════

elif page == "👤  Prediction Match Wins":

    st.markdown(f'<div class="sec-hdr">Working on It {page}</div>', unsafe_allow_html=True)
    if 0:
        st.markdown('<div class="sec-hdr">👤 PLAYER DEEP DIVE</div>', unsafe_allow_html=True)

        all_squad = {**squad1, **squad2}
        all_names = sorted(all_squad.keys())

        col_sel, col_opp = st.columns([2,1])
        with col_sel:
            player = st.selectbox("Select Player", all_names)
            player = PN_L_to_S[player]
        with col_opp:
            opp = st.selectbox("vs Team", [team1, team2])

        info   = all_squad.get(player, {})
        role   = ROLE_MAP.get(info.get("role","Batter"), "BAT")
        cs     = career_summary(player)
        vs_opp = stat_vs_team(player, opp)
        rec    = recent_form(player)

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin:12px 0 20px">
            <div>
                <div style="font-family:'Bebas Neue',cursive;font-size:2rem;color:#E8EAF0;letter-spacing:2px">{player}</div>
                {role_chip(info.get("role","Batter"))}
                <span style="color:#64748B;font-size:.8rem;margin-left:8px">
                    {'🔴 ' + team1 if player in squad1 else '🔵 ' + team2}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Career summary cards
        cols = st.columns(6)
        mets = [
            ("MATCHES",   cs["matches"],                  "#F97316"),
            ("RUNS",      cs["runs"],                     "#FBBF24"),
            ("BAT AVG",   f"{cs['avg']}",                 "#34D399"),
            ("STRIKE RT", f"{cs['sr']}",                  "#60A5FA"),
            ("WICKETS",   cs["wickets"],                  "#A78BFA"),
            ("ECONOMY",   f"{cs['economy']}",             "#F472B6"),
        ]
        for c, (lbl, val, col) in zip(cols, mets):
            c.markdown(f"""<div class="stat-card">
                <div class="stat-val" style="color:{col}">{val}</div>
                <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

        st.divider()

        tab_h2h, tab_bowler, tab_batter, tab_form = st.tabs([
            f"🆚 vs {opp}", "⚾ vs Specific Bowlers", "🏏 vs Specific Batters", "📈 Form"
        ])

        # ── H2H vs Team ──────────────────────────────────────────────────────────
        with tab_h2h:
            if not vs_opp:
                st.info(f"No H2H data for {player} vs {opp}")
            else:
                c1,c2,c3,c4,c5,c6 = st.columns(6)
                h_mets = [
                    ("RUNS",     vs_opp.get("Bt_Runs",0),                  "#F97316"),
                    ("AVG",      f"{vs_opp.get('Bt_Avg',0):.1f}",          "#FBBF24"),
                    ("SR",       f"{vs_opp.get('Bt_Strike_rate',0):.1f}",  "#34D399"),
                    ("MATCHES",  vs_opp.get("Matches",0),                  "#60A5FA"),
                    ("WICKETS",  vs_opp.get("Gain_Wicket",0),              "#A78BFA"),
                    ("ECONOMY",  f"{vs_opp.get('Bw_economy',0):.2f}",      "#F472B6"),
                ]
                for c, (lbl, val, col) in zip([c1,c2,c3,c4,c5,c6], h_mets):
                    c.markdown(f"""<div class="stat-card">
                        <div class="stat-val" style="color:{col};font-size:2rem">{val}</div>
                        <div class="stat-lbl">{lbl}<br><span style="color:#374151;font-size:.6rem">vs {opp[:12]}</span></div>
                    </div>""", unsafe_allow_html=True)

                run_list  = vs_opp.get("Bt_Runs_list", [])
                year_list = vs_opp.get("year", [])
                if run_list:
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_chart, col_pie = st.columns([2,1])
                    with col_chart:
                        colors_bar = ['#F97316' if r >= 50 else '#FBBF24' if r >= 30 else '#374151' for r in run_list]
                        fig = go.Figure(go.Bar(
                            x=year_list if year_list else list(range(len(run_list))),
                            y=run_list,
                            marker_color=colors_bar,
                            text=run_list, textposition='outside',
                        ))
                        fig.update_layout(
                            title=f"{player} — Innings vs {opp}",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font_color="#CBD5E1", height=320,
                            margin=dict(l=10,r=10,t=40,b=30),
                            xaxis=dict(gridcolor="#1F2937", tickangle=-45),
                            yaxis=dict(gridcolor="#1F2937"),
                            title_font_color="#F97316",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_pie:
                        # Milestone breakdown
                        ducks  = sum(1 for r in run_list if r == 0)
                        low    = sum(1 for r in run_list if 1  <= r < 20)
                        mid    = sum(1 for r in run_list if 20 <= r < 50)
                        fifties= sum(1 for r in run_list if r >= 50)
                        fig2 = go.Figure(go.Pie(
                            labels=["Duck","<20","20-49","50+"],
                            values=[ducks, low, mid, fifties],
                            hole=0.4,
                            marker_colors=["#EF4444","#374151","#FBBF24","#F97316"],
                        ))
                        fig2.update_layout(
                            title="Score Range", height=320,
                            paper_bgcolor="rgba(0,0,0,0)", font_color="#CBD5E1",
                            title_font_color="#FBBF24",
                            legend=dict(bgcolor="rgba(0,0,0,0)"),
                        )
                        st.plotly_chart(fig2, use_container_width=True)

                # Radar vs career
                st.divider()
                st.markdown("**Performance Radar — H2H vs Career**")
                cats = ["Runs","Strike Rate","Avg","Wickets","Economy (inv)"]

                def norm(v, mx): return min(v/mx*100, 100) if mx > 0 else 0
                h2h_vals = [
                    norm(vs_opp.get("Bt_Runs",0), 600),
                    norm(vs_opp.get("Bt_Strike_rate",0), 200),
                    norm(vs_opp.get("Bt_Avg",0), 80),
                    norm(vs_opp.get("Gain_Wicket",0), 20),
                    norm(max(0, 12-vs_opp.get("Bw_economy",10)), 12),
                ]
                car_vals = [
                    norm(cs["runs"], 3000),
                    norm(cs["sr"], 200),
                    norm(cs["avg"], 80),
                    norm(cs["wickets"], 100),
                    norm(max(0, 12-cs["economy"]), 12),
                ]
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(r=h2h_vals+[h2h_vals[0]], theta=cats+[cats[0]],
                    fill='toself', name=f'vs {opp[:12]}', line_color='#F97316', fillcolor='rgba(249,115,22,.2)'))
                fig_r.add_trace(go.Scatterpolar(r=car_vals+[car_vals[0]], theta=cats+[cats[0]],
                    fill='toself', name='Career', line_color='#60A5FA', fillcolor='rgba(96,165,250,.15)'))
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(range=[0,100], gridcolor='#1F2937', color='#64748B'),
                            angularaxis=dict(gridcolor='#1F2937', color='#64748B'),
                            bgcolor='rgba(0,0,0,0)'),
                    paper_bgcolor='rgba(0,0,0,0)', font_color='#CBD5E1',
                    legend=dict(bgcolor='rgba(0,0,0,0)'), height=380,
                )
                st.plotly_chart(fig_r, use_container_width=True)

    # ── vs Specific Bowlers ───────────────────────────────────────────────────
        with tab_bowler:
            opp_squad = squad2 if player in squad1 else squad1
            rows = []
            for bowler in opp_squad:
                sv = stat_vs_bowler(player, bowler)
                if sv and sv.get("Runs", sv.get("total_runs", 0)) > 0:
                    rows.append({
                        "Bowler": bowler,
                        "Runs":   sv.get("Runs", sv.get("total_runs", 0)),
                        "Balls":  sv.get("Balls", sv.get("total_balls", 0)),
                        "Wkts":   sv.get("T_Wicket", sv.get("total_wicket", 0)),
                        "SR":     round(sv.get("Strike_rate", sv.get("bt_strike_rate", 0)), 1),
                        "Avg":    round(sv.get("Avg", sv.get("Avg", 0)), 1),
                        "Matches":sv.get("Matches", 1),
                    })
            if rows:
                df_b = pd.DataFrame(rows).sort_values("Runs", ascending=False)
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.bar(df_b.head(10), x="Bowler", y="Runs",
                                color="Runs", color_continuous_scale="Oranges", text="Runs")
                    fig.update_traces(textposition='outside')
                    fig.update_xaxes(tickangle=-40)
                    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    font_color="#CBD5E1", height=320, title=f"Runs vs bowlers (top 10)",
                                    title_font_color="#F97316", margin=dict(t=40,b=60))
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    dismissed = df_b[df_b["Wkts"]>0].sort_values("Wkts", ascending=False)
                    if not dismissed.empty:
                        fig2 = px.pie(dismissed, values="Wkts", names="Bowler", hole=0.4,
                                    color_discrete_sequence=px.colors.qualitative.Set3)
                        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#CBD5E1",
                                        height=320, title="Dismissed by", title_font_color="#EF4444",
                                        legend=dict(bgcolor="rgba(0,0,0,0)"))
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("No dismissals recorded vs these bowlers")
                st.dataframe(df_b.style.background_gradient(subset=["Runs"], cmap="Oranges")
                                .background_gradient(subset=["Wkts"], cmap="Reds"),
                            use_container_width=True, hide_index=True)
            else:
                st.info("No matchup data available")

        # ── vs Specific Batters ───────────────────────────────────────────────────
        with tab_batter:
            opp_squad_b = squad2 if player in squad1 else squad1
            rows = []
            for batter in opp_squad_b:
                sv = stat_vs_batter(player, batter)
                if sv and sv.get("Runs", sv.get("total_runs", 0)) > 0:
                    rows.append({
                        "Batter": batter,
                        "Runs":   sv.get("Runs", sv.get("total_runs", 0)),
                        "Balls":  sv.get("Balls", sv.get("total_balls", 0)),
                        "Wkts":   sv.get("T_Wicket", sv.get("total_wicket", 0)),
                        "SR":     round(sv.get("Strike_rate", sv.get("bt_strike_rate", 0)), 1),
                        "Matches":sv.get("Matches", 1),
                    })
            if rows:
                df_bat = pd.DataFrame(rows).sort_values("Runs", ascending=False)
                c1, c2 = st.columns(2)
                with c1:
                    fig = px.bar(df_bat.head(10), x="Batter", y="Runs",
                                color="Runs", color_continuous_scale="Blues", text="Runs")
                    fig.update_traces(textposition='outside')
                    fig.update_xaxes(tickangle=-40)
                    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    font_color="#CBD5E1", height=320, title="Runs conceded (top 10)",
                                    title_font_color="#60A5FA", margin=dict(t=40,b=60))
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    fig2 = px.scatter(df_bat, x="Runs", y="SR", size="Balls", color="Wkts",
                                    hover_name="Batter", color_continuous_scale="Reds")
                    fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                    font_color="#CBD5E1", height=320,
                                    title="SR vs Runs (bubble=balls)", title_font_color="#34D399")
                    st.plotly_chart(fig2, use_container_width=True)
                st.dataframe(df_bat.style.background_gradient(subset=["Runs"], cmap="Blues")
                                .background_gradient(subset=["Wkts"], cmap="Greens"),
                            use_container_width=True, hide_index=True)
            else:
                st.info("No matchup data available")

        # ── Recent Form ───────────────────────────────────────────────────────────
        with tab_form:
            if not rec:
                st.info("No recent form data available.")
            else:
                rc1, rc2, rc3, rc4 = st.columns(4)
                mets_rec = [
                    ("REC BAT AVG",  f"{rec.get('Bt_Avg',0):.1f}",         "#F97316"),
                    ("REC STRIKE RT",f"{rec.get('Bt_Strike_rate',0):.1f}", "#FBBF24"),
                    ("REC BW ECON",  f"{rec.get('Bw_economy',0):.2f}",     "#60A5FA"),
                    ("REC WKT/GM",   f"{rec.get('Bw_Avg_Wickets',0):.2f}", "#A78BFA"),
                ]
                for c, (lbl, val, col) in zip([rc1,rc2,rc3,rc4], mets_rec):
                    c.markdown(f"""<div class="stat-card">
                        <div class="stat-val" style="color:{col};font-size:2rem">{val}</div>
                        <div class="stat-lbl">{lbl}</div></div>""", unsafe_allow_html=True)

                # Recent runs chart
                recent_runs  = rec.get("Bt_Runs", [])
                recent_years = rec.get("year", [])
                if isinstance(recent_runs, list) and recent_runs:
                    fig = go.Figure(go.Scatter(
                        x=recent_years if recent_years else list(range(len(recent_runs))),
                        y=recent_runs, mode='lines+markers',
                        line=dict(color='#F97316', width=2),
                        marker=dict(color=['#F97316' if r>=50 else '#FBBF24' if r>=30 else '#374151' for r in recent_runs],
                                    size=8),
                        fill='tozeroy', fillcolor='rgba(249,115,22,0.1)',
                    ))
                    fig.update_layout(
                        title="Recent Innings — Run Trend",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#CBD5E1", height=320, title_font_color="#FBBF24",
                        margin=dict(l=10,r=10,t=40,b=30),
                        xaxis=dict(gridcolor="#1F2937", tickangle=-45),
                        yaxis=dict(gridcolor="#1F2937"),
                    )
                    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — DREAM11 PREDICTOR
# ══════════════════════════════════════════════════════════════════════════════

elif page == "⭐  Dream11 Predictor":
    
    st.markdown(f'<div class="sec-hdr">Working on It — {page}</div>', unsafe_allow_html=True)
    if 0:
        st.markdown('<div class="sec-hdr">⭐ DREAM11 BEST XI</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#64748B;margin-bottom:20px">{team1} vs {team2} — {season} | AI-powered pick</p>', unsafe_allow_html=True)

        if not squad1 or not squad2:
            st.warning("Squad data not available for one or both teams.")
            st.stop()

        selected = pick_dream11(squad1, squad2, team1, team2)

        captain = selected[0]
        vc      = selected[1] if len(selected) > 1 else None

        # Summary row
        t1c = sum(1 for p in selected if p["team"] == team1)
        t2c = len(selected) - t1c
        c1,c2,c3,c4 = st.columns(4)
        mcard = lambda col, val, lbl, col2="#F97316": col.markdown(
            f'<div class="stat-card"><div class="stat-val" style="color:{col2}">{val}</div>'
            f'<div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)
        mcard(c1, t1c, f"from {team1[:10]}")
        mcard(c2, t2c, f"from {team2[:10]}", "#60A5FA")
        mcard(c3, 11,  "Total Players", "#34D399")
        role_cnt = defaultdict(int)
        for p in selected: role_cnt[p["role"]] += 1
        mcard(c4, f"{role_cnt['AR']} AR · {role_cnt['WK']} WK", "Balance", "#FBBF24")

        st.divider()

        ROLE_ICONS = {"WK":"🧤","BAT":"🏏","AR":"🔀","BOWL":"⚾"}
        ROLE_FULL  = {"WK":"WK-Batter","BAT":"Batsman","AR":"All-Rounder","BOWL":"Bowler"}
        CSS_R = {"WK":"wk","BAT":"bat","AR":"ar","BOWL":"bowl"}

        for role_grp, grp_label in [("WK","🧤 WICKET-KEEPER"), ("BAT","🏏 BATSMEN"),
                                    ("AR","🔀 ALL-ROUNDERS"), ("BOWL","⚾ BOWLERS")]:
            grp_players = [p for p in selected if p["role"] == role_grp]
            if not grp_players: continue

            st.markdown(f'<div style="font-family:Bebas Neue;font-size:1rem;color:#64748B;letter-spacing:3px;margin:16px 0 8px">{grp_label}</div>', unsafe_allow_html=True)
            cols = st.columns(len(grp_players))

            for col, p in zip(cols, grp_players):
                is_c  = (p == captain)
                is_vc = (p == vc)
                border = "#FFD700" if is_c else "#9CA3AF" if is_vc else "#1F2937"
                t_col  = "#F97316" if p["team"] == team1 else "#60A5FA"
                badge  = '<span class="cbadge">C</span>' if is_c else '<span class="vcbadge">VC</span>' if is_vc else ''
                css_r  = CSS_R.get(p["role"], "bat")

                col.markdown(f"""
                <div class="d11card" style="border-color:{border}">
                    <div style="font-size:1.8rem">{ROLE_ICONS.get(p['role'],'🏏')}</div>
                    <div class="d11name">{p['player'][:16]}</div>
                    <div style="color:{t_col};font-size:.7rem;font-weight:600;margin:3px 0">{p['team'][:12]}</div>
                    {badge}
                    <div style="margin-top:8px"><span class="pchip {css_r}">{ROLE_FULL.get(p['role'],'BAT')}</span></div>
                    <div style="margin-top:8px;font-size:.78rem;color:#64748B">
                        Score: <span style="color:#FFD700;font-weight:700">{p['score']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        st.markdown('<div class="sec-hdr" style="font-size:1.2rem">📊 SCORE BREAKDOWN</div>', unsafe_allow_html=True)

        fig = go.Figure(go.Bar(
            x=[p["player"][:12] for p in selected],
            y=[p["score"]       for p in selected],
            marker_color=[
                "#FFD700" if p == captain else "#9CA3AF" if p == vc else
                "#F97316" if p["team"] == team1 else "#60A5FA"
                for p in selected
            ],
            text=[str(p["score"]) for p in selected],
            textposition='outside',
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1", height=320,
            xaxis=dict(gridcolor="#1F2937", tickangle=-35),
            yaxis=dict(gridcolor="#1F2937"),
            margin=dict(l=10,r=10,t=20,b=80),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Table
        df_d11 = pd.DataFrame([{
            "Player":      p["player"],
            "Team":        p["team"],
            "Role":        ROLE_FULL.get(p["role"],"BAT"),
            "D11 Score":   p["score"],
            "Tag":         "C" if p == captain else "VC" if p == vc else "",
        } for p in selected])
        st.dataframe(df_d11.sort_values("D11 Score", ascending=False), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — MATCH SCORECARD PREDICTION
# ══════════════════════════════════════════════════════════════════════════════

elif page == "🔮  Match Scorecard Prediction":
    st.markdown(f'<div class="sec-hdr">Working on It {page}</div>', unsafe_allow_html=True)
    if 0:
        st.markdown('<div class="sec-hdr">🔮 PREDICTED MATCH SCORECARD</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#64748B;margin-bottom:20px">{team1} vs {team2} · {season} — Statistical model (H2H × Recent form blend)</p>', unsafe_allow_html=True)

        tab_t1, tab_t2, tab_summary = st.tabs([f"🔴 {team1}", f"🔵 {team2}", "🏆 Match Summary"])

        def build_scorecard(squad, batting_vs_team, label_color):
            rows = []
            for p, info in squad.items():
                pred = predict_performance(p, batting_vs_team)
                role = ROLE_MAP.get(info.get("role","Batter"), "BAT")
                rows.append({
                    "Player":    p,
                    "Role":      role,
                    "Pred Runs": pred["runs"],
                    "Pred SR":   pred["sr"],
                    "Pred 4s":   pred["fours"],
                    "Pred 6s":   pred["sixes"],
                    "Pred Wkts": pred["wickets"],
                    "Pred Econ": pred["economy"],
                    "H2H Games": pred["h2h_matches"],
                })
            rows.sort(key=lambda x: x["Pred Runs"], reverse=True)
            return rows

        def render_scorecard(squad, opp_team, team_name, color):
            rows = build_scorecard(squad, opp_team, color)

            # Top-5 batting heroes
            top5 = rows[:5]
            cols = st.columns(5)
            for col, r in zip(cols, top5):
                conf = "🔥" if r["Pred Runs"] >= 35 else "✅" if r["Pred Runs"] >= 20 else "📉"
                col.markdown(f"""
                <div class="stat-card" style="border-left:3px solid {color}">
                    <div style="font-size:.7rem;color:#64748B;margin-bottom:2px">{conf} {r['Player'][:14]}</div>
                    <div class="stat-val" style="color:{color};font-size:2rem">{r['Pred Runs']}</div>
                    <div class="stat-lbl">PRED RUNS</div>
                    <div style="color:#64748B;font-size:.7rem;margin-top:4px">SR {r['Pred SR']:.0f} · {r['Pred 4s']}×4 · {r['Pred 6s']}×6</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Runs bar chart
            fig = go.Figure(go.Bar(
                x=[r["Player"][:12] for r in rows],
                y=[r["Pred Runs"]   for r in rows],
                marker_color=color, opacity=.85,
                text=[str(r["Pred Runs"]) for r in rows],
                textposition='outside',
            ))
            fig.update_layout(
                title=f"Predicted Batting — {team_name}",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1", height=300,
                margin=dict(l=10,r=10,t=40,b=80),
                xaxis=dict(gridcolor="#1F2937", tickangle=-40),
                yaxis=dict(gridcolor="#1F2937"),
                title_font_color=color,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Bowling chart
            bowl_rows = [r for r in rows if r["Pred Wkts"] > 0]
            bowl_rows.sort(key=lambda x: x["Pred Wkts"], reverse=True)
            if bowl_rows:
                fig2 = go.Figure(go.Bar(
                    x=[r["Player"][:12] for r in bowl_rows],
                    y=[r["Pred Wkts"]   for r in bowl_rows],
                    marker_color="#60A5FA",
                    text=[f"{r['Pred Wkts']:.2f}" for r in bowl_rows],
                    textposition='outside',
                ))
                fig2.update_layout(
                    title=f"Predicted Wickets — {team_name} bowlers",
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#CBD5E1", height=280,
                    margin=dict(l=10,r=10,t=40,b=80),
                    xaxis=dict(gridcolor="#1F2937", tickangle=-40),
                    yaxis=dict(gridcolor="#1F2937"),
                    title_font_color="#60A5FA",
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Full table
            st.markdown("**Full Prediction Table**")
            ROLE_FULL2 = {"WK":"🧤WK","BAT":"🏏Bat","AR":"🔀AR","BOWL":"⚾Bowl"}
            df = pd.DataFrame([{
                "Player":   r["Player"],
                "Role":     ROLE_FULL2.get(r["Role"],"🏏Bat"),
                "Pred Runs":r["Pred Runs"],
                "Pred SR":  r["Pred SR"],
                "4s":       r["Pred 4s"],
                "6s":       r["Pred 6s"],
                "Wkts":     f"{r['Pred Wkts']:.2f}",
                "Economy":  f"{r['Pred Econ']:.2f}" if r["Pred Econ"]>0 else "—",
                "H2H M":    r["H2H Games"],
            } for r in rows])
            st.dataframe(df.sort_values("Pred Runs", ascending=False),
                        use_container_width=True, hide_index=True, height=380)

            total = sum(r["Pred Runs"] for r in rows)
            return total, rows

        with tab_t1:
            t1_total, t1_rows = render_scorecard(squad1, team2, team1, "#F97316")

        with tab_t2:
            t2_total, t2_rows = render_scorecard(squad2, team1, team2, "#60A5FA")

        with tab_summary:
            st.markdown('<div class="sec-hdr" style="font-size:1.4rem">🏆 PREDICTED MATCH SUMMARY</div>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns([2,1,2])
            with c1:
                st.markdown(f"""
                <div class="stat-card" style="border-left:4px solid #F97316;padding:28px">
                    <div style="font-family:'Bebas Neue';font-size:1.4rem;color:#F97316;letter-spacing:2px">{team1}</div>
                    <div style="font-family:'Bebas Neue';font-size:3.5rem;color:#E8EAF0;margin:8px 0">{int(t1_total)}</div>
                    <div style="color:#64748B;font-size:.8rem">PREDICTED TEAM RUNS</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown("""
                <div style="display:flex;align-items:center;justify-content:center;height:100%;
                            font-family:'Bebas Neue';font-size:2rem;color:#64748B;letter-spacing:3px">
                    VS
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="stat-card" style="border-left:4px solid #60A5FA;padding:28px">
                    <div style="font-family:'Bebas Neue';font-size:1.4rem;color:#60A5FA;letter-spacing:2px">{team2}</div>
                    <div style="font-family:'Bebas Neue';font-size:3.5rem;color:#E8EAF0;margin:8px 0">{int(t2_total)}</div>
                    <div style="color:#64748B;font-size:.8rem">PREDICTED TEAM RUNS</div>
                </div>""", unsafe_allow_html=True)

            st.divider()

            # Winner prediction
            winner = team1 if t1_total >= t2_total else team2
            margin = abs(t1_total - t2_total)
            w_col  = "#F97316" if winner == team1 else "#60A5FA"
            conf   = "HIGH" if margin > 30 else "MEDIUM" if margin > 15 else "LOW"
            conf_c = "#34D399" if conf=="HIGH" else "#FBBF24" if conf=="MEDIUM" else "#EF4444"

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

            # Top performers prediction (combined)
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

            # Comparison radar
            st.divider()
            st.markdown("**Team Strength Comparison**")
            t1_avg_sr   = round(sum(r["Pred SR"]   for r in t1_rows) / len(t1_rows), 1) if t1_rows else 0
            t2_avg_sr   = round(sum(r["Pred SR"]   for r in t2_rows) / len(t2_rows), 1) if t2_rows else 0
            t1_wkts     = round(sum(r["Pred Wkts"] for r in t1_rows), 2)
            t2_wkts     = round(sum(r["Pred Wkts"] for r in t2_rows), 2)
            t1_top_run  = max((r["Pred Runs"] for r in t1_rows), default=0)
            t2_top_run  = max((r["Pred Runs"] for r in t2_rows), default=0)

            cats = ["Team Runs","Avg SR","Wickets","Top Score","Depth"]
            def n(v, mx): return min(v/mx*100,100) if mx>0 else 0

            mx_runs = max(t1_total, t2_total, 1)
            mx_sr   = max(t1_avg_sr, t2_avg_sr, 1)
            mx_wkts = max(t1_wkts, t2_wkts, 1)
            mx_top  = max(t1_top_run, t2_top_run, 1)

            # "depth" = number of players predicted to score 20+
            t1_dep = sum(1 for r in t1_rows if r["Pred Runs"] >= 20)
            t2_dep = sum(1 for r in t2_rows if r["Pred Runs"] >= 20)

            t1v = [n(t1_total,mx_runs), n(t1_avg_sr,mx_sr), n(t1_wkts,mx_wkts), n(t1_top_run,mx_top), n(t1_dep,11)]
            t2v = [n(t2_total,mx_runs), n(t2_avg_sr,mx_sr), n(t2_wkts,mx_wkts), n(t2_top_run,mx_top), n(t2_dep,11)]

            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(r=t1v+[t1v[0]], theta=cats+[cats[0]],
                fill='toself', name=team1, line_color='#F97316', fillcolor='rgba(249,115,22,.2)'))
            fig_r.add_trace(go.Scatterpolar(r=t2v+[t2v[0]], theta=cats+[cats[0]],
                fill='toself', name=team2, line_color='#60A5FA', fillcolor='rgba(96,165,250,.15)'))
            fig_r.update_layout(
                polar=dict(radialaxis=dict(range=[0,100], gridcolor='#1F2937', color='#64748B'),
                        angularaxis=dict(gridcolor='#1F2937', color='#64748B'),
                        bgcolor='rgba(0,0,0,0)'),
                paper_bgcolor='rgba(0,0,0,0)', font_color='#CBD5E1',
                legend=dict(bgcolor='rgba(0,0,0,0)'), height=400,
            )
            st.plotly_chart(fig_r, use_container_width=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center;color:#374151;font-size:.75rem;padding:16px">
    🏏 IPL Analytics Pro &nbsp;·&nbsp; Data: IPL 2008–2025
    &nbsp;·&nbsp; Predictions are statistical estimates, not guarantees
</div>
""", unsafe_allow_html=True)
