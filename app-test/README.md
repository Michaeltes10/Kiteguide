# Kite Advisor NL — Test Versie

Werkende Streamlit app die de beste kitespots in Nederland toont op basis van wind, richting en jouw locatie. **Geen API keys nodig** — draait volledig op Open-Meteo.

## Snel starten

```bash
cd app-test
pip install -r requirements.txt
streamlit run app.py
```

De app opent in je browser. Standaard postcode: **1057 TB** (Amsterdam West).

## Wat doet het?

- **Nu-overzicht**: actuele wind per spot (richting, knopen, gusts)
- **Forecast ranking**: beste spots voor de komende dagen, gerangschikt op score
- **Windrichting filter**: spots worden alleen getoond als de wind uit de juiste hoek komt
- **Score**: gebaseerd op windsnelheid, gust-stabiliteit en richting

## Spots

De app bevat 5 seed spots:

| Spot | Type | Windrichting | Min kn (twintip) |
|------|------|-------------|-------------------|
| Wijk aan Zee | Zee | SW–WNW (220°–300°) | 16 |
| IJmuiden | Zee | SW–WNW (220°–300°) | 16 |
| Muiderberg | Binnenwater | N–S (0°–180°) | 14 |
| Medemblik | Binnenwater | NE–SSE (40°–170°) | 14 |
| Schellinkhout | Binnenwater | NE–SSE (40°–170°) | 14 |

### Nieuwe spot toevoegen

Voeg een regel toe aan `nkv_spots_full.csv`:

```csv
Naam,52.123,4.567,flat,"180-270",14,9,12345,slug,https://...
```

- `dir_windows_deg`: richting in graden, bijv. `220-300` of `220-300;330-20` voor meerdere vensters
- `water_type`: `sea` of `flat`

## Alerts & Agenda

Run `python alerts.py` om een alert-check te doen. Bij 25+ knopen wind worden automatisch `.ics` bestanden aangemaakt die je in je agenda kunt importeren (Google Calendar, Apple Calendar, Outlook).

```bash
python alerts.py
```

Bestanden verschijnen in `calendar_events/`.

## Databron

Alle weerdata komt van [Open-Meteo](https://open-meteo.com/) (gratis, geen key nodig).

## Later uitbreiden

Zie `app-pro/` voor de versie met modulaire providers (AROME, Windguru, Soarcast, KNMI).
