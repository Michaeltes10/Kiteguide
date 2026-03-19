"""
Spot Detail Page — KiteGuide
Shows detailed information for a single kitespot.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from spot_pages import get_spot_info, get_all_spots

st.set_page_config(page_title="KiteGuide — Spot", page_icon="🪁", layout="wide")

# ---------------------------------------------------------------------------
# CSS (reuse main app styling)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.block-container { padding-top: 1.5rem; max-width: 1000px; }

.spot-hero {
    background: linear-gradient(135deg, rgba(12,25,41,0.8) 0%, rgba(19,35,55,0.6) 50%, rgba(56,189,248,0.3) 100%),
                url('https://www.kitemana.nl/Public/img/contentpages/tips/kitesurfen.jpg') center/cover no-repeat;
    border-radius: 16px;
    padding: 3rem 2.5rem 2.5rem;
    margin-bottom: 2rem;
}
.spot-hero h1 {
    font-size: 2.4rem;
    font-weight: 800;
    color: #fff;
    margin: 0 0 0.3rem 0;
    text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.spot-hero p {
    color: rgba(255,255,255,0.8);
    font-size: 1.05rem;
    margin: 0;
    text-shadow: 0 1px 10px rgba(0,0,0,0.4);
}

.info-card {
    background: #162032;
    border: 1px solid rgba(56,189,248,0.15);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.info-card h3 {
    color: #38BDF8;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.info-card p, .info-card li {
    color: #E8EDF5;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0;
}
.info-card ul {
    margin: 0.3rem 0 0 0;
    padding-left: 1.2rem;
}
.info-card li {
    margin-bottom: 0.3rem;
}

.info-label {
    color: rgba(232,237,245,0.5);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.info-value {
    color: #E8EDF5;
    font-size: 1rem;
    font-weight: 600;
}

.back-link {
    display: inline-block;
    color: #38BDF8;
    font-weight: 600;
    text-decoration: none;
    margin-bottom: 1rem;
    font-size: 0.95rem;
}
.back-link:hover { text-decoration: underline; }

.webcam-container {
    border-radius: 12px;
    overflow: hidden;
    margin: 1rem 0;
    background: #0D1825;
    border: 1px solid rgba(56,189,248,0.15);
}
.webcam-container iframe {
    width: 100%;
    height: 400px;
    border: none;
}

.tip-badge {
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.5rem;
    color: #E8EDF5;
    font-size: 0.9rem;
}

.footer {
    text-align: center;
    padding: 2rem 0 1rem;
    color: rgba(232,237,245,0.4);
    font-size: 0.8rem;
    border-top: 1px solid rgba(56,189,248,0.1);
    margin-top: 3rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Get spot from query params
# ---------------------------------------------------------------------------
params = st.query_params
spot_slug = params.get("spot", None)

if not spot_slug:
    # Show spot selector
    st.markdown('<a class="back-link" href="/">← Terug naar KiteGuide</a>', unsafe_allow_html=True)
    st.markdown("## Kies een kitespot")
    spots = get_all_spots()
    for name, info in spots.items():
        st.markdown(
            f'<a href="/Spot_Detail?spot={info["slug"]}" style="text-decoration:none">'
            f'<div class="info-card" style="cursor:pointer">'
            f'<h3>{info["title"]}</h3>'
            f'<p>{info["subtitle"]}</p>'
            f'</div></a>',
            unsafe_allow_html=True,
        )
    st.stop()

# Find spot by slug
spot = None
for name, info in get_all_spots().items():
    if info["slug"] == spot_slug:
        spot = info
        break

if not spot:
    st.error("Spot niet gevonden.")
    st.stop()

# ---------------------------------------------------------------------------
# Back link
# ---------------------------------------------------------------------------
st.markdown('<a class="back-link" href="/">← Terug naar KiteGuide</a>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="spot-hero">'
    f'<h1>{spot["title"]}</h1>'
    f'<p>{spot["subtitle"]}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="info-card">'
    f'<h3>Over deze spot</h3>'
    f'<p>{spot["description"]}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Quick facts (2 columns)
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Windrichting</h3>'
        f'<p><strong>{spot["wind_directions"]}</strong></p>'
        f'<p style="margin-top:0.5rem; color:rgba(232,237,245,0.6); font-size:0.85rem">{spot["wind_note"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Water type</h3>'
        f'<p>{spot["water_type"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Niveau</h3>'
        f'<p>{spot["level"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Parkeren</h3>'
        f'<p><strong>{spot["parking_address"]}</strong></p>'
        f'<p style="margin-top:0.3rem">{spot["parking_price"]}</p>'
        f'<p style="margin-top:0.5rem; color:rgba(232,237,245,0.6); font-size:0.85rem">{spot["parking_info"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Voorzieningen</h3>'
        f'<p>{spot["facilities"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="info-card">'
        f'<h3>Regels</h3>'
        f'<p>{spot["rules"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Webcam
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="info-card">'
    f'<h3>Webcam</h3>'
    f'<p style="margin-bottom:0.8rem">{spot["webcam_label"]}</p>'
    f'</div>',
    unsafe_allow_html=True,
)

if spot["webcam_type"] == "youtube":
    st.markdown(
        f'<div class="webcam-container">'
        f'<iframe src="{spot["webcam_embed"]}?autoplay=0" allowfullscreen></iframe>'
        f'</div>',
        unsafe_allow_html=True,
    )
elif spot["webcam_type"] == "twitch":
    st.markdown(
        f'<div class="webcam-container">'
        f'<iframe src="{spot["webcam_embed"]}" allowfullscreen></iframe>'
        f'</div>',
        unsafe_allow_html=True,
    )
elif spot["webcam_type"] == "hls":
    st.markdown(
        f'<div class="info-card">'
        f'<p>Bekijk de live webcam op: '
        f'<a href="https://webcam-havenijmuiden.nl/" target="_blank" style="color:#38BDF8">'
        f'webcam-havenijmuiden.nl</a></p>'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="info-card">'
        f'<p>Bekijk de webcam op: '
        f'<a href="{spot["webcam_embed"]}" target="_blank" style="color:#38BDF8">'
        f'{spot["webcam_credit"]}</a></p>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Tips
# ---------------------------------------------------------------------------
tips_html = "".join(f'<div class="tip-badge">💡 {tip}</div>' for tip in spot["tips"])
st.markdown(
    f'<div class="info-card">'
    f'<h3>Tips</h3>'
    f'{tips_html}'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="info-card">'
    f'<h3>Locatie</h3>'
    f'<p>Coordinaten: {spot["coordinates"]}</p>'
    f'</div>',
    unsafe_allow_html=True,
)
lat, lon = [float(x.strip()) for x in spot["coordinates"].split(",")]
import pandas as pd
st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=13)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="footer">'
    'KiteGuide · Data: Open-Meteo · '
    'Scores zijn indicatief, check altijd lokale omstandigheden!'
    '</div>',
    unsafe_allow_html=True,
)
