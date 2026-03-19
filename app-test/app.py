"""
Kite Advisor NL — Test Version
Streamlit app. Works without API keys (Open-Meteo only).
"""

import streamlit as st
import pandas as pd
from utils import (
    load_spots,
    geocode_postcode,
    get_forecast,
    get_current_conditions,
    rank_spots,
    degrees_to_compass,
    parse_dir_windows,
    is_direction_in_window,
)
from alerts import (
    find_alert_sessions,
    group_sessions,
    save_ics_events,
    generate_ics_event,
    format_alert_message,
    send_email_alert,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Kite Advisor NL", page_icon="🪁", layout="wide")

# ---------------------------------------------------------------------------
# Custom CSS — Duotone-inspired dark premium design
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---------- Google Font ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ---------- Global ---------- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit header & footer */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* ---------- Main container ---------- */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* ---------- Hero banner ---------- */
.hero-banner {
    background: linear-gradient(135deg, rgba(12,25,41,0.75) 0%, rgba(19,35,55,0.6) 50%, rgba(56,189,248,0.3) 100%),
                url('https://www.kitemana.nl/Public/img/contentpages/tips/kitesurfen.jpg') center/cover no-repeat;
    border-radius: 16px;
    padding: 3.5rem 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(56,189,248,0.2) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.hero-subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.85);
    margin: 0;
    font-weight: 400;
    text-shadow: 0 1px 10px rgba(0,0,0,0.4);
}

/* ---------- Section headers ---------- */
.section-header {
    font-size: 1.5rem;
    font-weight: 700;
    color: #E8EDF5;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #38BDF8;
    display: inline-block;
}

/* ---------- Metric cards ---------- */
.metric-card {
    background: #162032;
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover {
    border-color: #38BDF8;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #38BDF8;
}
.metric-label {
    font-size: 0.8rem;
    color: rgba(232,237,245,0.6);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

/* ---------- Status badges ---------- */
.badge-ok {
    background: rgba(0,200,83,0.15);
    color: #00C853;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-bad {
    background: rgba(244,0,0,0.15);
    color: #FF5252;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* ---------- Spot cards ---------- */
.spot-card {
    background: #162032;
    border: 1px solid rgba(56,189,248,0.15);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.spot-card:hover {
    border-color: #38BDF8;
    background: #1a2640;
}
.spot-name {
    font-weight: 600;
    font-size: 1rem;
    color: #E8EDF5;
}
.spot-type {
    font-size: 0.8rem;
    color: rgba(232,237,245,0.5);
}
.spot-wind {
    font-size: 1.2rem;
    font-weight: 700;
    color: #38BDF8;
}
.spot-detail {
    font-size: 0.8rem;
    color: rgba(232,237,245,0.6);
}

/* ---------- Dataframe styling ---------- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(135deg, #38BDF8, #0EA5E9);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.3px;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #5CCBFA, #1DB5F0);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(56,189,248,0.3);
}
.stButton > button:active {
    transform: translateY(0);
}

/* Primary button variant */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F40000, #CC0000);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #FF2020, #E00000);
    box-shadow: 0 4px 15px rgba(244,0,0,0.3);
}

/* Download buttons */
.stDownloadButton > button {
    background: transparent;
    border: 1px solid rgba(56,189,248,0.4);
    color: #38BDF8;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s;
}
.stDownloadButton > button:hover {
    background: rgba(56,189,248,0.1);
    border-color: #38BDF8;
}

/* ---------- Inputs ---------- */
.stTextInput > div > div > input {
    background: #162032;
    border: 1px solid rgba(56,189,248,0.3);
    border-radius: 8px;
    color: #E8EDF5;
    font-size: 0.95rem;
}
.stTextInput > div > div > input:focus {
    border-color: #38BDF8;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.2);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: #0D1825;
    border-right: 1px solid rgba(56,189,248,0.1);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* Sidebar header */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
    color: #38BDF8;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 700;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    background: #162032;
    border-radius: 8px;
    font-weight: 600;
    color: #E8EDF5;
}

/* ---------- Score bar ---------- */
.score-bar-bg {
    background: rgba(56,189,248,0.1);
    border-radius: 6px;
    height: 8px;
    width: 100%;
}
.score-bar-fill {
    background: linear-gradient(90deg, #38BDF8, #7DD3FC);
    border-radius: 6px;
    height: 8px;
}

/* ---------- Alert card ---------- */
.alert-card {
    background: linear-gradient(135deg, #162032, #1a2640);
    border-left: 4px solid #00C853;
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.alert-card .alert-title {
    font-weight: 600;
    color: #E8EDF5;
    font-size: 1rem;
}
.alert-card .alert-detail {
    color: rgba(232,237,245,0.6);
    font-size: 0.85rem;
    margin-top: 0.3rem;
}

/* ---------- Footer ---------- */
.footer {
    text-align: center;
    padding: 2rem 0 1rem;
    color: rgba(232,237,245,0.4);
    font-size: 0.8rem;
    border-top: 1px solid rgba(56,189,248,0.1);
    margin-top: 3rem;
}
.footer a {
    color: #38BDF8;
    text-decoration: none;
}

/* ---------- Divider ---------- */
hr {
    border: none;
    border-top: 1px solid rgba(56,189,248,0.1);
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <p class="hero-title">🪁 Kite Advisor NL</p>
    <p class="hero-subtitle">Vind de beste kitespot — gebaseerd op wind, richting en jouw locatie.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero section — postcode + e-mail (prominent on start screen)
# ---------------------------------------------------------------------------
col_post, col_email = st.columns([1, 2])
with col_post:
    postcode = st.text_input(
        "📍 Jouw postcode",
        value="1065 XZ",
        help="We zoeken de beste kitespots in jouw buurt.",
    )
with col_email:
    alert_email = st.text_input(
        "📧 E-mailadres voor wind alerts",
        value="",
        placeholder="jouw@email.nl",
        help="Ontvang een e-mail + agenda-uitnodiging zodra er 20+ knopen wind komt.",
    )

alert_signup = st.button("Aanmelden voor Wind alert (gratis)")
if alert_signup:
    if alert_email:
        st.success(f"Je bent aangemeld voor wind alerts op {alert_email}!")
    else:
        st.warning("Vul eerst je e-mailadres in om je aan te melden.")

# ---------------------------------------------------------------------------
# Sidebar — overige instellingen
# ---------------------------------------------------------------------------
st.sidebar.markdown("## INSTELLINGEN")
board_type = st.sidebar.selectbox("Board type", ["Twintip", "Foil"])
level = st.sidebar.selectbox("Niveau", ["Beginner", "Intermediate", "Advanced"])
water_filter = st.sidebar.selectbox("Water type", ["Alles", "Zee", "Binnenwater"])
days_ahead = st.sidebar.slider("Dagen vooruit", 1, 7, 7)
min_kn = st.sidebar.number_input(
    "Minimum knopen",
    min_value=5,
    max_value=40,
    value=16 if board_type == "Twintip" else 9,
)
max_kn = st.sidebar.number_input(
    "Maximum knopen",
    min_value=10,
    max_value=60,
    value=35,
)
st.sidebar.markdown("---")
alert_threshold_kn = st.sidebar.number_input(
    "Alert drempel (knopen)",
    min_value=10,
    max_value=50,
    value=20,
    help="Je krijgt een alert bij wind >= dit aantal knopen.",
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
spots_df = load_spots()
user_loc = geocode_postcode(postcode)

if user_loc is None:
    st.error(f"Kon postcode '{postcode}' niet vinden. Probeer een andere postcode.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div class="metric-card">'
    f'<div class="metric-value">{user_loc[0]:.3f}</div>'
    f'<div class="metric-label">Latitude</div>'
    f'</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f'<div class="metric-card" style="margin-top:0.5rem">'
    f'<div class="metric-value">{user_loc[1]:.3f}</div>'
    f'<div class="metric-label">Longitude</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Section 1 — Nu per spot (with styled cards)
# ---------------------------------------------------------------------------
st.markdown('<p class="section-header">Actuele wind per spot</p>', unsafe_allow_html=True)

now_rows = []
for _, spot in spots_df.iterrows():
    cond = get_current_conditions(spot["lat"], spot["lon"])
    if cond is None:
        continue

    dir_windows = parse_dir_windows(str(spot["dir_windows_deg"]))
    dir_ok = is_direction_in_window(cond["wind_dir_deg"], dir_windows)

    now_rows.append({
        "name": spot["name"],
        "type": "sea" if spot["water_type"] == "sea" else "inland",
        "wind_kn": round(cond["wind_kn"], 1),
        "gust_kn": round(cond["gust_kn"], 1) if cond["gust_kn"] else 0,
        "dir_label": cond["wind_dir_label"],
        "dir_deg": int(cond["wind_dir_deg"]),
        "dir_ok": dir_ok,
    })

if now_rows:
    for row in now_rows:
        type_icon = "🌊" if row["type"] == "sea" else "🏞️"
        badge = '<span class="badge-ok">OK</span>' if row["dir_ok"] else '<span class="badge-bad">NIET OK</span>'
        st.markdown(
            f'<div class="spot-card">'
            f'  <div>'
            f'    <span class="spot-name">{row["name"]}</span>'
            f'    <span class="spot-type"> {type_icon}</span>'
            f'    <br><span class="spot-detail">{row["dir_label"]} ({row["dir_deg"]}°) · Gusts {row["gust_kn"]} kn</span>'
            f'  </div>'
            f'  <div style="text-align:right">'
            f'    <span class="spot-wind">{row["wind_kn"]} kn</span><br>'
            f'    {badge}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("Geen actuele data beschikbaar.")

# ---------------------------------------------------------------------------
# Section 2 — Forecast ranking
# ---------------------------------------------------------------------------
st.markdown('<p class="section-header">Beste spots — komende uren/dagen</p>', unsafe_allow_html=True)

st.markdown("""
> **Hoe werkt de score?**
> - Spots worden *alleen* getoond als de windrichting binnen het toegestane venster valt.
> - Score is gebaseerd op windsnelheid (ideale range), gust-stabiliteit en richting.
> - Hogere score = betere sessie. Spots bovenaan → daar moet je heen!
""")

# We fetch forecast per spot and then rank
with st.spinner("Forecasts ophalen en berekenen..."):
    all_forecasts = {}
    for _, spot in spots_df.iterrows():
        fc = get_forecast(spot["lat"], spot["lon"], days=days_ahead)
        if not fc.empty:
            all_forecasts[spot["name"]] = fc

    # Build combined forecast frame for ranking
    ranked = rank_spots(
        spots_df=spots_df,
        forecast_hours=pd.concat(
            [
                fc.assign(_spot_name=name)
                for name, fc in all_forecasts.items()
            ],
            ignore_index=True,
        ) if all_forecasts else pd.DataFrame(),
        board_type=board_type,
        level=level,
        water_filter=water_filter,
        min_kn_override=float(min_kn),
        max_kn=float(max_kn),
    )

ranked_rows = []
for _, spot in spots_df.iterrows():
    name = spot["name"]
    if name not in all_forecasts:
        continue
    fc = all_forecasts[name]
    partial = rank_spots(
        spots_df=spots_df[spots_df["name"] == name],
        forecast_hours=fc,
        board_type=board_type,
        level=level,
        water_filter=water_filter,
        min_kn_override=float(min_kn),
        max_kn=float(max_kn),
    )
    if not partial.empty:
        ranked_rows.append(partial)

if ranked_rows:
    ranked = pd.concat(ranked_rows, ignore_index=True)
    ranked = ranked.sort_values("score", ascending=False).reset_index(drop=True)
else:
    ranked = pd.DataFrame()

if ranked.empty:
    st.warning("Geen geschikte spots gevonden voor de huidige instellingen.")
else:
    # Top picks as styled cards
    st.markdown('<p class="section-header" style="font-size:1.2rem">🏆 Top aanbevelingen</p>', unsafe_allow_html=True)
    top = ranked.head(10).copy()

    for _, r in top.iterrows():
        time_str = r["time"].strftime("%a %d %b %H:%M")
        score_pct = min(r["score"] * 100, 100)
        score_color = "#00C853" if r["score"] > 0.5 else "#38BDF8" if r["score"] > 0.1 else "#FF9800"
        st.markdown(
            f'<div class="spot-card">'
            f'  <div style="flex:1">'
            f'    <span class="spot-name">{r["spot"]}</span><br>'
            f'    <span class="spot-detail">{time_str} · {r["wind_dir"]} · {r["model"]}</span>'
            f'  </div>'
            f'  <div style="text-align:right; min-width:120px">'
            f'    <span class="spot-wind">{r["wind_kn"]} kn</span>'
            f'    <span class="spot-detail"> (gusts {r["gust_kn"]})</span><br>'
            f'    <div class="score-bar-bg" style="margin-top:6px">'
            f'      <div class="score-bar-fill" style="width:{score_pct}%; background:linear-gradient(90deg,{score_color},{score_color})"></div>'
            f'    </div>'
            f'    <span class="spot-detail">{r["score"]:.3f}</span>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Per-spot detail tables
    st.markdown('<p class="section-header" style="font-size:1.2rem">Detail per spot</p>', unsafe_allow_html=True)
    spot_names = ranked["spot"].unique()
    for sname in spot_names:
        spot_data = ranked[ranked["spot"] == sname].copy()
        if spot_data.empty:
            continue
        best = spot_data.iloc[0]
        with st.expander(
            f"{sname} — beste score {best['score']:.2f} "
            f"({best['time'].strftime('%a %H:%M')}, "
            f"{best['wind_dir']} {best['wind_kn']} kn)"
        ):
            display = spot_data.copy()
            display["time"] = display["time"].dt.strftime("%a %d %b %H:%M")
            st.dataframe(
                display[["time", "wind_dir", "wind_kn", "gust_kn", "score", "model"]],
                use_container_width=True,
                hide_index=True,
            )

# ---------------------------------------------------------------------------
# Section 3 — Wind alerts & agenda
# ---------------------------------------------------------------------------
st.markdown('<p class="section-header">Wind Alerts & Agenda</p>', unsafe_allow_html=True)

with st.spinner("Wind alerts berekenen..."):
    alert_sessions_raw = find_alert_sessions(
        spots_df,
        days=days_ahead,
        board_type=board_type,
        level=level,
        wind_threshold_kn=float(alert_threshold_kn),
    )
    sessions = group_sessions(alert_sessions_raw)
    wind_sessions = [s for s in sessions if s["calendar_event"]]

if not wind_sessions:
    st.info(
        f"Geen sessies met {alert_threshold_kn}+ knopen gevonden "
        f"in de komende {days_ahead} dagen."
    )
else:
    st.success(
        f"{len(wind_sessions)} sessie(s) met {alert_threshold_kn}+ knopen gevonden!"
    )
    for session in wind_sessions:
        msg = format_alert_message(session)
        start_ts = pd.Timestamp(session["start"]).strftime("%a %d %b %H:%M")
        st.markdown(
            f'<div class="alert-card">'
            f'  <div class="alert-title">{session["spot"]} — {start_ts}</div>'
            f'  <div class="alert-detail">{msg}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Generate .ics downloads
    st.markdown('<p class="section-header" style="font-size:1.1rem">Toevoegen aan je agenda</p>', unsafe_allow_html=True)
    dl_cols = st.columns(min(len(wind_sessions), 3))
    for i, session in enumerate(wind_sessions):
        ics_content = generate_ics_event(session)
        start_str = pd.Timestamp(session["start"]).strftime("%a %d %b %H:%M")
        filename = f"kite_{session['spot'].replace(' ', '_')}.ics"
        with dl_cols[i % len(dl_cols)]:
            st.download_button(
                label=f"📅 {session['spot']} — {start_str}",
                data=ics_content,
                file_name=filename,
                mime="text/calendar",
                key=f"ics_{session['spot']}_{session['start']}",
            )

    # Email sending
    if alert_email:
        if st.button("Verstuur alert + agenda naar mijn e-mail", type="primary"):
            ics_files = save_ics_events(wind_sessions)
            sent = send_email_alert(
                to_email=alert_email,
                sessions=wind_sessions,
                ics_files=ics_files,
            )
            if sent:
                st.success(f"E-mail met agenda-uitnodiging(en) verzonden naar {alert_email}!")
            else:
                st.warning(
                    "E-mail kon niet verzonden worden. "
                    "SMTP is nog niet geconfigureerd. "
                    "Je kunt de .ics bestanden hierboven handmatig downloaden "
                    "en in je agenda importeren."
                )
    else:
        st.info(
            "Vul hierboven je e-mailadres in om alerts + agenda-uitnodigingen "
            "per e-mail te ontvangen."
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="footer">'
    'Kite Advisor NL · Data: Open-Meteo · '
    'Scores zijn indicatief, check altijd lokale omstandigheden!'
    '</div>',
    unsafe_allow_html=True,
)
