"""
Kite Advisor NL — alerts.py
Alert worker: checks forecasts and generates alerts.
Includes .ics calendar event generation for 25+ knot sessions.

Test version: prints alerts to console / generates .ics files.
Pro version: extend with Telegram, email, Google Calendar API.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd

from utils import (
    load_spots,
    get_forecast,
    parse_dir_windows,
    compute_score,
    degrees_to_compass,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ALERT_SCORE_THRESHOLD = 0.6
ALERT_WIND_THRESHOLD_KN = 20  # Calendar + email event trigger
CHECK_INTERVAL_SECONDS = 3600  # 1 hour
DEFAULT_BOARD = "Twintip"
DEFAULT_LEVEL = "Intermediate"
ICS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "calendar_events")

# ---------------------------------------------------------------------------
# Alert generation
# ---------------------------------------------------------------------------

def find_alert_sessions(
    spots_df: pd.DataFrame,
    days: int = 7,
    board_type: str = DEFAULT_BOARD,
    level: str = DEFAULT_LEVEL,
    score_threshold: float = ALERT_SCORE_THRESHOLD,
    wind_threshold_kn: float = ALERT_WIND_THRESHOLD_KN,
) -> List[Dict]:
    """
    Scan all spots for upcoming sessions that meet alert criteria.
    Returns list of alert dicts.
    """
    alerts = []

    for _, spot in spots_df.iterrows():
        fc = get_forecast(spot["lat"], spot["lon"], days=days)
        if fc.empty:
            continue

        dir_windows = parse_dir_windows(str(spot["dir_windows_deg"]))
        if board_type == "Foil":
            spot_min = float(spot["min_kn_foil"])
        else:
            spot_min = float(spot["min_kn_twintip"])

        for _, hr in fc.iterrows():
            wind_kn = hr["wind_kn"]
            gust_kn = hr["gust_kn"]
            wind_dir = hr["wind_dir_deg"]
            if pd.isna(wind_kn) or pd.isna(wind_dir):
                continue

            score = compute_score(
                wind_kn=wind_kn,
                gust_kn=gust_kn if pd.notna(gust_kn) else wind_kn,
                wind_dir_deg=wind_dir,
                dir_windows=dir_windows,
                min_kn=spot_min,
                level=level,
            )
            if score is None:
                continue

            # Two alert triggers:
            # 1) Score above threshold (good session)
            # 2) Wind >= 25 kn with valid direction (calendar event)
            is_high_score = score >= score_threshold
            is_strong_wind = wind_kn >= wind_threshold_kn

            if is_high_score or is_strong_wind:
                alerts.append({
                    "spot": spot["name"],
                    "lat": spot["lat"],
                    "lon": spot["lon"],
                    "time": hr["time"],
                    "wind_kn": round(wind_kn, 1),
                    "gust_kn": round(gust_kn, 1) if pd.notna(gust_kn) else None,
                    "wind_dir": degrees_to_compass(wind_dir),
                    "wind_dir_deg": wind_dir,
                    "score": score,
                    "trigger": "wind_threshold" if is_strong_wind else "high_score",
                })

    return alerts


# ---------------------------------------------------------------------------
# Group consecutive hours into sessions
# ---------------------------------------------------------------------------

def group_sessions(alerts: List[Dict], max_gap_hours: int = 2) -> List[Dict]:
    """
    Group consecutive alert hours for the same spot into sessions.
    Returns list of session dicts with start/end times.
    """
    if not alerts:
        return []

    df = pd.DataFrame(alerts)
    df = df.sort_values(["spot", "time"])
    sessions = []

    for spot_name, group in df.groupby("spot"):
        group = group.sort_values("time").reset_index(drop=True)
        session_start = None
        session_end = None
        session_alerts = []

        for i, row in group.iterrows():
            t = row["time"]
            if session_start is None:
                session_start = t
                session_end = t
                session_alerts = [row]
            elif (t - session_end).total_seconds() <= max_gap_hours * 3600:
                session_end = t
                session_alerts.append(row)
            else:
                sessions.append(_build_session(spot_name, session_start, session_end, session_alerts))
                session_start = t
                session_end = t
                session_alerts = [row]

        if session_start is not None:
            sessions.append(_build_session(spot_name, session_start, session_end, session_alerts))

    return sessions


def _build_session(spot: str, start, end, alert_rows) -> Dict:
    """Build a session summary dict."""
    winds = [r["wind_kn"] for r in alert_rows]
    scores = [r["score"] for r in alert_rows]
    dirs = [r["wind_dir"] for r in alert_rows]
    has_threshold = any(r["trigger"] == "wind_threshold" for r in alert_rows)

    return {
        "spot": spot,
        "start": start,
        "end": end + timedelta(hours=1),  # end is inclusive hour
        "avg_wind_kn": round(sum(winds) / len(winds), 1),
        "max_wind_kn": max(winds),
        "best_score": max(scores),
        "main_dir": max(set(dirs), key=dirs.count),
        "hours": len(alert_rows),
        "calendar_event": has_threshold,
    }


# ---------------------------------------------------------------------------
# .ics calendar file generation
# ---------------------------------------------------------------------------

def generate_ics_event(session: Dict) -> str:
    """Generate an .ics calendar event string for a kite session."""
    uid = str(uuid.uuid4())
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    start_dt = pd.Timestamp(session["start"])
    end_dt = pd.Timestamp(session["end"])

    # Format for .ics
    dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend = end_dt.strftime("%Y%m%dT%H%M%S")

    summary = (
        f"🪁 Kitesurfen {session['spot']} — "
        f"{session['avg_wind_kn']} kn {session['main_dir']}"
    )
    description = (
        f"Kite sessie @ {session['spot']}\\n"
        f"Wind: {session['avg_wind_kn']} kn (max {session['max_wind_kn']} kn)\\n"
        f"Richting: {session['main_dir']}\\n"
        f"Score: {session['best_score']:.2f}\\n"
        f"Duur: {session['hours']} uur\\n"
        f"\\nAutomatisch aangemaakt door Kite Advisor NL"
    )

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Kite Advisor NL//NL
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART;TZID=Europe/Amsterdam:{dtstart}
DTEND;TZID=Europe/Amsterdam:{dtend}
SUMMARY:{summary}
DESCRIPTION:{description}
STATUS:TENTATIVE
BEGIN:VALARM
TRIGGER:-PT120M
ACTION:DISPLAY
DESCRIPTION:Kite sessie over 2 uur @ {session['spot']}!
END:VALARM
END:VEVENT
END:VCALENDAR"""
    return ics


def save_ics_events(sessions: List[Dict], output_dir: str = ICS_OUTPUT_DIR) -> List[str]:
    """
    Generate and save .ics files for sessions with calendar_event=True (25+ kn).
    Returns list of saved file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []

    for session in sessions:
        if not session.get("calendar_event"):
            continue

        ics_content = generate_ics_event(session)
        start_str = pd.Timestamp(session["start"]).strftime("%Y%m%d_%H%M")
        filename = f"kite_{session['spot'].replace(' ', '_')}_{start_str}.ics"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(ics_content)
        saved.append(filepath)

    return saved


# ---------------------------------------------------------------------------
# Format alert message (for console / Telegram / email)
# ---------------------------------------------------------------------------

def format_alert_message(session: Dict) -> str:
    """Format a compact, actionable alert message."""
    start = pd.Timestamp(session["start"]).strftime("%a %d %b %H:%M")
    end = pd.Timestamp(session["end"]).strftime("%H:%M")
    icon = "🏁" if session["calendar_event"] else "💨"

    return (
        f"{icon} {session['spot']} — score {session['best_score']:.2f}, "
        f"{start}–{end} {session['main_dir']} "
        f"{session['avg_wind_kn']}–{session['max_wind_kn']} kn — ga!"
    )


# ---------------------------------------------------------------------------
# Main check (called hourly or on-demand)
# ---------------------------------------------------------------------------

def run_alert_check(
    days: int = 7,
    board_type: str = DEFAULT_BOARD,
    level: str = DEFAULT_LEVEL,
    generate_calendar: bool = True,
) -> Dict:
    """
    Run a full alert check:
    1. Load spots
    2. Scan forecasts
    3. Group into sessions
    4. Generate .ics for 25+ kn sessions
    5. Return results

    In test version: prints to console.
    In pro version: send via Telegram / email.
    """
    spots = load_spots()
    alerts = find_alert_sessions(spots, days=days, board_type=board_type, level=level)
    sessions = group_sessions(alerts)

    messages = []
    ics_files = []

    for session in sessions:
        msg = format_alert_message(session)
        messages.append(msg)
        print(msg)

    if generate_calendar:
        calendar_sessions = [s for s in sessions if s["calendar_event"]]
        if calendar_sessions:
            ics_files = save_ics_events(calendar_sessions)
            print(f"\n📅 {len(ics_files)} agenda-afspraken aangemaakt in {ICS_OUTPUT_DIR}/")
            for f in ics_files:
                print(f"   → {f}")

    return {
        "alerts": alerts,
        "sessions": sessions,
        "messages": messages,
        "ics_files": ics_files,
    }


# ---------------------------------------------------------------------------
# Stubs for Pro version
# ---------------------------------------------------------------------------

def send_telegram_alert(message: str, chat_id: str, bot_token: str):
    """TODO: Implement Telegram alert sending."""
    raise NotImplementedError("Telegram alerts not yet implemented. Add in app-pro.")


def send_email_alert(
    to_email: str,
    sessions: List[Dict],
    ics_files: Optional[List[str]] = None,
) -> bool:
    """
    Send a kite wind alert email with .ics attachments.
    Uses SMTP (configured via env vars or Streamlit secrets).
    Falls back to a simple summary if SMTP is not configured.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "michael@mijncadeau.nl")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        print(f"⚠️ SMTP niet geconfigureerd — e-mail naar {to_email} overgeslagen.")
        return False

    # Build email body
    body_lines = ["🪁 Kite Advisor NL — Wind Alert!\n"]
    for session in sessions:
        body_lines.append(format_alert_message(session))
    body_lines.append("\nVeel plezier op het water! 🤙")

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = f"🪁 Kite Alert: {len(sessions)} sessie(s) met 20+ knopen!"

    msg.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

    # Attach .ics files
    if ics_files:
        for ics_path in ics_files:
            if os.path.exists(ics_path):
                with open(ics_path, "r") as f:
                    ics_content = f.read()
                part = MIMEBase("text", "calendar", method="REQUEST")
                part.set_payload(ics_content.encode("utf-8"))
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(ics_path),
                )
                msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"✅ E-mail verzonden naar {to_email}")
        return True
    except Exception as e:
        print(f"❌ E-mail verzenden mislukt: {e}")
        return False


def create_google_calendar_event(session: Dict, credentials_path: str):
    """
    TODO: Implement Google Calendar API integration.
    This would use the Google Calendar API to directly create events
    instead of generating .ics files.
    """
    raise NotImplementedError("Google Calendar API not yet implemented. Add in app-pro.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🪁 Kite Advisor NL — Alert Check")
    print("=" * 50)
    result = run_alert_check()
    if not result["sessions"]:
        print("Geen goede sessies gevonden in de komende dagen.")
    print(f"\nTotaal: {len(result['sessions'])} sessies, "
          f"{len(result['ics_files'])} agenda-items")
