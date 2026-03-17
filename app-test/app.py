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
st.title("🪁 Kite Advisor NL")
st.caption("Vind de beste kitespot — gebaseerd op wind, richting en jouw locatie.")

# ---------------------------------------------------------------------------
# Hero section — postcode + e-mail (prominent on start screen)
# ---------------------------------------------------------------------------
col_pc, col_email = st.columns(2)
with col_pc:
    postcode = st.text_input(
        "📍 Jouw postcode",
        value="1057 TB",
        help="We zoeken de beste kitespots in jouw buurt.",
    )
with col_email:
    alert_email = st.text_input(
        "📧 E-mailadres voor wind alerts",
        placeholder="jouw@email.nl",
        help="Ontvang een e-mail + agenda-uitnodiging zodra er 20+ knopen wind komt.",
    )

# ---------------------------------------------------------------------------
# Sidebar — overige instellingen
# ---------------------------------------------------------------------------
st.sidebar.header("Instellingen")
board_type = st.sidebar.selectbox("Board type", ["Twintip", "Foil"])
level = st.sidebar.selectbox("Niveau", ["Beginner", "Intermediate", "Advanced"])
water_filter = st.sidebar.selectbox("Water type", ["Alles", "Zee", "Binnenwater"])
days_ahead = st.sidebar.slider("Dagen vooruit", 1, 7, 3)
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

st.sidebar.success(f"Locatie: {user_loc[0]:.3f}, {user_loc[1]:.3f}")

# ---------------------------------------------------------------------------
# Section 1 — Nu per spot
# ---------------------------------------------------------------------------
st.header("☀️ Nu — actuele wind per spot")

now_rows = []
for _, spot in spots_df.iterrows():
    cond = get_current_conditions(spot["lat"], spot["lon"])
    if cond is None:
        continue

    dir_windows = parse_dir_windows(str(spot["dir_windows_deg"]))
    dir_ok = is_direction_in_window(cond["wind_dir_deg"], dir_windows)

    now_rows.append({
        "Spot": spot["name"],
        "Type": "🌊" if spot["water_type"] == "sea" else "🏞️",
        "Wind (kn)": round(cond["wind_kn"], 1),
        "Gusts (kn)": round(cond["gust_kn"], 1) if cond["gust_kn"] else "-",
        "Richting": f"{cond['wind_dir_label']} ({int(cond['wind_dir_deg'])}°)",
        "Richting OK": "✅" if dir_ok else "❌",
    })

if now_rows:
    now_df = pd.DataFrame(now_rows)
    st.dataframe(now_df, use_container_width=True, hide_index=True)
else:
    st.info("Geen actuele data beschikbaar.")

# ---------------------------------------------------------------------------
# Section 2 — Forecast ranking
# ---------------------------------------------------------------------------
st.header("📊 Beste spots — komende uren/dagen")

st.markdown("""
> **Hoe werkt de score?**
> - Spots worden *alleen* getoond als de windrichting binnen het toegestane venster valt.
> - Score is gebaseerd op windsnelheid (ideale range), gust-stabiliteit en richting.
> - Hogere score = betere sessie. Spots bovenaan → daar moet je heen!
""")

# We fetch forecast per spot and then rank
with st.spinner("Forecasts ophalen en berekenen…"):
    all_forecasts = {}
    for _, spot in spots_df.iterrows():
        fc = get_forecast(spot["lat"], spot["lon"], days=days_ahead)
        if not fc.empty:
            all_forecasts[spot["name"]] = fc

    # Build combined forecast frame for ranking
    # We rank every spot × hour combination
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

# But the ranking above passes ALL hours through a single spots loop.
# Let's redo more carefully: per spot, use its own forecast.
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
    # Top picks
    st.subheader("🏆 Top aanbevelingen")
    top = ranked.head(10).copy()
    top["time"] = top["time"].dt.strftime("%a %d %b %H:%M")
    st.dataframe(
        top[["spot", "time", "wind_dir", "wind_kn", "gust_kn", "score", "model"]],
        use_container_width=True,
        hide_index=True,
    )

    # Per-spot detail tables
    st.subheader("📋 Detail per spot")
    spot_names = ranked["spot"].unique()
    for sname in spot_names:
        spot_data = ranked[ranked["spot"] == sname].copy()
        if spot_data.empty:
            continue
        best = spot_data.iloc[0]
        with st.expander(
            f"**{sname}** — beste score {best['score']:.2f} "
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
st.header("📧 Wind Alerts & Agenda")

with st.spinner("Wind alerts berekenen…"):
    alert_sessions_raw = find_alert_sessions(
        spots_df,
        days=days_ahead,
        board_type=board_type,
        level=level,
        wind_threshold_kn=float(alert_threshold_kn),
    )
    sessions = group_sessions(alert_sessions_raw)
    # Filter to sessions that have wind >= threshold
    wind_sessions = [s for s in sessions if s["calendar_event"]]

if not wind_sessions:
    st.info(
        f"Geen sessies met {alert_threshold_kn}+ knopen gevonden "
        f"in de komende {days_ahead} dagen."
    )
else:
    st.success(
        f"🎉 {len(wind_sessions)} sessie(s) met {alert_threshold_kn}+ knopen gevonden!"
    )
    for session in wind_sessions:
        msg = format_alert_message(session)
        st.markdown(f"- {msg}")

    # Generate .ics downloads
    st.subheader("📅 Toevoegen aan je agenda")
    for session in wind_sessions:
        ics_content = generate_ics_event(session)
        start_str = pd.Timestamp(session["start"]).strftime("%a %d %b %H:%M")
        filename = f"kite_{session['spot'].replace(' ', '_')}.ics"
        st.download_button(
            label=f"📅 {session['spot']} — {start_str} ({session['avg_wind_kn']} kn)",
            data=ics_content,
            file_name=filename,
            mime="text/calendar",
            key=f"ics_{session['spot']}_{session['start']}",
        )

    # Email sending
    st.subheader("📧 Ontvang per e-mail")
    if alert_email:
        if st.button("📧 Verstuur alert + agenda naar mijn e-mail", type="primary"):
            ics_files = save_ics_events(wind_sessions)
            sent = send_email_alert(
                to_email=alert_email,
                sessions=wind_sessions,
                ics_files=ics_files,
            )
            if sent:
                st.success(f"✅ E-mail met agenda-uitnodiging(en) verzonden naar {alert_email}!")
            else:
                st.warning(
                    "⚠️ E-mail kon niet verzonden worden. "
                    "SMTP is nog niet geconfigureerd. "
                    "Je kunt de .ics bestanden hierboven handmatig downloaden "
                    "en in je agenda importeren."
                )
    else:
        st.info(
            "⬆️ Vul hierboven je e-mailadres in om alerts + agenda-uitnodigingen "
            "per e-mail te ontvangen."
        )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Kite Advisor NL · Test versie · Data: Open-Meteo · "
    "Scores zijn indicatief, check altijd lokale omstandigheden!"
)
