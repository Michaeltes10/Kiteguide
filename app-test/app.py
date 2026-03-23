"""
Kite Advisor NL — Test Version
Streamlit app. Works without API keys (Open-Meteo only).
"""

import urllib.parse
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
from spot_pages import get_spot_info
from alerts import (
    find_alert_sessions,
    group_sessions,
    save_ics_events,
    generate_ics_event,
    format_alert_message,
    send_email_alert,
)

# ---------------------------------------------------------------------------
# Dutch formatting helpers
# ---------------------------------------------------------------------------
_NL_DAYS = {
    "Mon": "maandag", "Tue": "dinsdag", "Wed": "woensdag", "Thu": "donderdag",
    "Fri": "vrijdag", "Sat": "zaterdag", "Sun": "zondag",
}
_NL_MONTHS = {
    "Jan": "januari", "Feb": "februari", "Mar": "maart", "Apr": "april",
    "May": "mei", "Jun": "juni", "Jul": "juli", "Aug": "augustus",
    "Sep": "september", "Oct": "oktober", "Nov": "november", "Dec": "december",
}
_NL_WIND_DIR = {
    "N": "Noord", "NNE": "Noord-Noordoost", "NE": "Noordoost", "ENE": "Oost-Noordoost",
    "E": "Oost", "ESE": "Oost-Zuidoost", "SE": "Zuidoost", "SSE": "Zuid-Zuidoost",
    "S": "Zuid", "SSW": "Zuid-Zuidwest", "SW": "Zuidwest", "WSW": "West-Zuidwest",
    "W": "West", "WNW": "West-Noordwest", "NW": "Noordwest", "NNW": "Noord-Noordwest",
}


def format_nl_datetime(dt) -> str:
    """Format a datetime as 'dinsdag 24 maart om 13:00 uur'."""
    day = _NL_DAYS.get(dt.strftime("%a"), dt.strftime("%a"))
    month = _NL_MONTHS.get(dt.strftime("%b"), dt.strftime("%b"))
    return f"{day} {dt.day} {month} om {dt.strftime('%H:%M')} uur"


def format_nl_datetime_short(dt) -> str:
    """Format a datetime as 'dinsdag 13:00 uur'."""
    day = _NL_DAYS.get(dt.strftime("%a"), dt.strftime("%a"))
    return f"{day} {dt.strftime('%H:%M')} uur"


def nl_wind_dir(abbr: str) -> str:
    """Translate wind direction abbreviation to Dutch full name."""
    return _NL_WIND_DIR.get(abbr, abbr)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="KiteGuide", page_icon="🪁", layout="wide")

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

/* ---------- Action buttons (Agenda / WhatsApp) ---------- */
.action-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: filter 0.2s;
}
.action-btn:hover { filter: brightness(1.2); }
.cal-btn {
    background: rgba(56,189,248,0.15);
    border: 1px solid rgba(56,189,248,0.3);
    color: #38BDF8;
}
.wa-btn {
    background: rgba(37,211,102,0.15);
    border: 1px solid rgba(37,211,102,0.3);
    color: #25D366;
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
    <p class="hero-title">KiteGuide</p>
    <p class="hero-subtitle">Ontdek waar en wanneer jij kan kiten bij jou in de buurt!</p>
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
        help="Ontvang een e-mail + agenda-uitnodiging zodra er wind komt.",
    )

# ---------------------------------------------------------------------------
# Inline settings (visible on mobile before signup)
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    '<p style="color:#38BDF8;font-weight:700;font-size:0.9rem;text-transform:uppercase;'
    'letter-spacing:1px;margin-bottom:0.5rem">Instellingen</p>',
    unsafe_allow_html=True,
)
board_type = "Twintip"
level = "Intermediate"
water_filter = "Alles"
days_ahead = st.slider("Dagen vooruit", 1, 7, 7, key="main_days")
col_s1, col_s2 = st.columns(2)
with col_s1:
    min_kn = st.number_input(
        "Minimum knopen",
        min_value=5, max_value=40, value=18,
        key="main_min_kn",
    )
with col_s2:
    max_kn = st.number_input(
        "Maximum knopen",
        min_value=10, max_value=60, value=45,
        key="main_max_kn",
    )
alert_threshold_kn = st.number_input(
    "Alert drempel (knopen)",
    min_value=10, max_value=50, value=20,
    help="Je krijgt een alert bij wind >= dit aantal knopen.",
    key="main_alert_threshold",
)
st.markdown("---")

alert_signup = st.button("Aanmelden voor Wind alert (gratis)")
if alert_signup:
    if alert_email:
        st.success(f"Je bent aangemeld voor wind alerts op {alert_email}!")
    else:
        st.warning("Vul eerst je e-mailadres in om je aan te melden.")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
spots_df = load_spots()
user_loc = geocode_postcode(postcode)

if user_loc is None:
    st.error(f"Kon postcode '{postcode}' niet vinden. Probeer een andere postcode.")
    st.stop()


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
        badge = '<span class="badge-ok">Juiste windrichting</span>' if row["dir_ok"] else '<span class="badge-bad">Niet vaarbaar</span>'
        dir_label_nl = nl_wind_dir(row["dir_label"])
        # Make spot name a link to detail page if available
        spot_info = get_spot_info(row["name"])
        if spot_info:
            name_html = f'<a href="/Spot_Detail?spot={spot_info["slug"]}" style="color:#E8EDF5;text-decoration:none;border-bottom:1px solid #38BDF8" class="spot-name">{row["name"]}</a>'
        else:
            name_html = f'<span class="spot-name">{row["name"]}</span>'
        st.markdown(
            f'<div class="spot-card">'
            f'  <div>'
            f'    {name_html}'
            f'    <span class="spot-type"> {type_icon}</span>'
            f'    <br><span class="spot-detail">{dir_label_nl} ({row["dir_deg"]}°) · Gusts {row["gust_kn"]} kn</span>'
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
    st.markdown('<p class="section-header" style="font-size:1.2rem">Zet deze dagen en tijden in je agenda!</p>', unsafe_allow_html=True)
    top = ranked.head(10).copy()

    for idx, (_, r) in enumerate(top.iterrows()):
        time_str = format_nl_datetime(r["time"])
        wind_dir_nl = nl_wind_dir(r["wind_dir"])
        score_pct = min(r["score"] * 100, 100)
        score_color = "#00C853" if r["score"] > 0.5 else "#38BDF8" if r["score"] > 0.1 else "#FF9800"
        r_spot_info = get_spot_info(r["spot"])
        if r_spot_info:
            r_name_html = f'<a href="/Spot_Detail?spot={r_spot_info["slug"]}" style="color:#E8EDF5;text-decoration:none;border-bottom:1px solid #38BDF8" class="spot-name">{r["spot"]}</a>'
        else:
            r_name_html = f'<span class="spot-name">{r["spot"]}</span>'

        # --- WhatsApp share URL ---
        dt = r["time"]
        nl_day = _NL_DAYS.get(dt.strftime("%a"), dt.strftime("%a"))
        nl_month = _NL_MONTHS.get(dt.strftime("%b"), dt.strftime("%b"))
        wa_date = f"{nl_day} {dt.day} {nl_month}"
        wa_time = dt.strftime("%H:%M")
        wa_text = (
            f"Zullen we samen gaan kiten op {wa_date} om {wa_time}? "
            f"Er staat {r['wind_kn']} knopen {wind_dir_nl} en vlagen tot {r['gust_kn']} kn "
            f"bij {r['spot']}! 🪁"
        )
        wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"

        # --- Google Calendar URL ---
        cal_title = urllib.parse.quote(f"Kiten {r['spot']} - {r['wind_kn']} kn {wind_dir_nl}")
        cal_start = dt.strftime("%Y%m%dT%H%M%S")
        cal_end_dt = dt + pd.Timedelta(hours=2)
        cal_end = cal_end_dt.strftime("%Y%m%dT%H%M%S")
        cal_details = urllib.parse.quote(
            f"Wind: {r['wind_kn']} kn ({wind_dir_nl})\n"
            f"Vlagen: {r['gust_kn']} kn\n"
            f"Spot: {r['spot']}\n"
            f"Score: {r['score']:.2f}"
        )
        cal_location = urllib.parse.quote(r["spot"])
        gcal_url = (
            f"https://calendar.google.com/calendar/render?action=TEMPLATE"
            f"&text={cal_title}&dates={cal_start}/{cal_end}"
            f"&details={cal_details}&location={cal_location}"
        )

        st.markdown(
            f'<div class="spot-card" style="flex-wrap:wrap">'
            f'  <div style="flex:1">'
            f'    {r_name_html}<br>'
            f'    <span class="spot-detail">{time_str} · {wind_dir_nl} · {r["model"]}</span>'
            f'  </div>'
            f'  <div style="text-align:right; min-width:120px">'
            f'    <span class="spot-wind">{r["wind_kn"]} kn</span>'
            f'    <span class="spot-detail"> (gusts {r["gust_kn"]})</span><br>'
            f'    <div class="score-bar-bg" style="margin-top:6px">'
            f'      <div class="score-bar-fill" style="width:{score_pct}%; background:linear-gradient(90deg,{score_color},{score_color})"></div>'
            f'    </div>'
            f'    <span class="spot-detail">{r["score"]:.3f}</span>'
            f'  </div>'
            f'  <div style="width:100%; display:flex; gap:8px; margin-top:10px">'
            f'    <a href="{gcal_url}" target="_blank" class="action-btn cal-btn">📅 Agenda</a>'
            f'    <a href="{wa_url}" target="_blank" class="action-btn wa-btn">💬 WhatsApp</a>'
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
            f"({format_nl_datetime_short(best['time'])}, "
            f"{nl_wind_dir(best['wind_dir'])} {best['wind_kn']} kn)"
        ):
            display = spot_data.copy()
            display["wind_dir"] = display["wind_dir"].apply(nl_wind_dir)
            display["time"] = display["time"].apply(format_nl_datetime)
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
        start_ts = format_nl_datetime(pd.Timestamp(session["start"]))
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
        start_str = format_nl_datetime(pd.Timestamp(session["start"]))
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
