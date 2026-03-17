"""
Kite Advisor NL — Pro Version
Streamlit app with modular provider support.
Falls back to Open-Meteo if no API keys are configured.
"""

import streamlit as st
import pandas as pd
from utils import (
    load_spots,
    geocode_postcode,
    get_forecast,
    get_all_forecasts,
    get_current_conditions,
    get_available_models,
    rank_spots,
    degrees_to_compass,
    parse_dir_windows,
    is_direction_in_window,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Kite Advisor NL Pro", page_icon="🪁", layout="wide")
st.title("🪁 Kite Advisor NL — Pro")
st.caption("Modulaire versie met ondersteuning voor meerdere weermodellen.")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("Instellingen")
postcode = st.sidebar.text_input("Postcode", value="1057 TB")
board_type = st.sidebar.selectbox("Board type", ["Twintip", "Foil"])
level = st.sidebar.selectbox("Niveau", ["Beginner", "Intermediate", "Advanced"])
water_filter = st.sidebar.selectbox("Water type", ["Alles", "Zee", "Binnenwater"])
days_ahead = st.sidebar.slider("Dagen vooruit", 1, 14, 3)
min_kn = st.sidebar.number_input(
    "Minimum knopen",
    min_value=5, max_value=40,
    value=16 if board_type == "Twintip" else 9,
)
max_kn = st.sidebar.number_input("Maximum knopen", min_value=10, max_value=60, value=35)

# Model selection
available_models = get_available_models()
st.sidebar.markdown("---")
st.sidebar.subheader("Weermodellen")
st.sidebar.caption(f"Beschikbaar: {', '.join(available_models)}")
preferred_model = st.sidebar.selectbox(
    "Voorkeur model",
    ["Automatisch"] + available_models,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
spots_df = load_spots()
user_loc = geocode_postcode(postcode)

if user_loc is None:
    st.error(f"Kon postcode '{postcode}' niet vinden.")
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
        "Gusts (kn)": round(cond["gust_kn"], 1) if cond.get("gust_kn") else "-",
        "Richting": f"{cond.get('wind_dir_label', '')} ({int(cond['wind_dir_deg'])}°)",
        "Richting OK": "✅" if dir_ok else "❌",
        "Model": cond.get("model", "Open-Meteo"),
    })

if now_rows:
    st.dataframe(pd.DataFrame(now_rows), use_container_width=True, hide_index=True)
else:
    st.info("Geen actuele data beschikbaar.")

# ---------------------------------------------------------------------------
# Section 2 — Forecast ranking
# ---------------------------------------------------------------------------
st.header("📊 Beste spots — komende uren/dagen")

st.markdown("""
> **Score uitleg**: Spots worden alleen getoond bij juiste windrichting.
> Score = windsnelheid (ideale range) + gust-stabiliteit + tij-factor - reistijd.
> Hogere score = betere sessie.
""")

model_pref = None if preferred_model == "Automatisch" else preferred_model

with st.spinner("Forecasts ophalen…"):
    ranked_rows = []
    for _, spot in spots_df.iterrows():
        fc = get_forecast(spot["lat"], spot["lon"], days=days_ahead,
                          preferred_model=model_pref)
        if fc.empty:
            continue
        partial = rank_spots(
            spots_df=spots_df[spots_df["name"] == spot["name"]],
            forecast_hours=fc,
            board_type=board_type,
            level=level,
            water_filter=water_filter,
            min_kn_override=float(min_kn),
            max_kn=float(max_kn),
            user_location=user_loc,
        )
        if not partial.empty:
            ranked_rows.append(partial)

if ranked_rows:
    ranked = pd.concat(ranked_rows, ignore_index=True)
    ranked = ranked.sort_values("score", ascending=False).reset_index(drop=True)
else:
    ranked = pd.DataFrame()

if ranked.empty:
    st.warning("Geen geschikte spots gevonden.")
else:
    st.subheader("🏆 Top aanbevelingen")
    top = ranked.head(10).copy()
    top["time"] = top["time"].dt.strftime("%a %d %b %H:%M")
    display_cols = ["spot", "time", "wind_dir", "wind_kn", "gust_kn", "score", "model"]
    if "travel_min" in top.columns and top["travel_min"].notna().any():
        display_cols.append("travel_min")
    st.dataframe(top[display_cols], use_container_width=True, hide_index=True)

    st.subheader("📋 Detail per spot")
    for sname in ranked["spot"].unique():
        spot_data = ranked[ranked["spot"] == sname].copy()
        if spot_data.empty:
            continue
        best = spot_data.iloc[0]
        with st.expander(
            f"**{sname}** — score {best['score']:.2f} "
            f"({best['time'].strftime('%a %H:%M')}, "
            f"{best['wind_dir']} {best['wind_kn']} kn)"
        ):
            display = spot_data.copy()
            display["time"] = display["time"].dt.strftime("%a %d %b %H:%M")
            st.dataframe(
                display[["time", "wind_dir", "wind_kn", "gust_kn", "score", "model"]],
                use_container_width=True, hide_index=True,
            )

    # Model comparison (if multiple available)
    if len(available_models) > 1:
        st.subheader("🔬 Model vergelijking")
        st.caption("Dezelfde spot via verschillende modellen — handig om te checken.")
        compare_spot = st.selectbox("Spot", spots_df["name"].tolist())
        spot_row = spots_df[spots_df["name"] == compare_spot].iloc[0]
        all_fc = get_all_forecasts(spot_row["lat"], spot_row["lon"], days=2)
        if all_fc:
            for model_name, fc_df in all_fc.items():
                st.markdown(f"**{model_name}**")
                display = fc_df.head(24).copy()
                display["time"] = display["time"].dt.strftime("%a %H:%M")
                st.dataframe(
                    display[["time", "wind_dir_label", "wind_kn", "gust_kn"]],
                    use_container_width=True, hide_index=True,
                )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Kite Advisor NL Pro · Modellen: " + ", ".join(available_models) +
    " · Scores zijn indicatief!"
)
