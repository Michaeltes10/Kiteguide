# Kite Advisor NL — Pro Versie

Modulaire versie met ondersteuning voor meerdere weermodellen en integraties.

## Snel starten

```bash
cd app-pro
pip install -r requirements.txt
streamlit run app.py
```

Werkt direct met Open-Meteo + AROME (via Open-Meteo). Extra modellen activeer je via `.env`.

## Weermodellen (prioriteit)

| Model | Status | Bereik | Opmerking |
|-------|--------|--------|-----------|
| AROME 1.3 | Werkend (via Open-Meteo) | 48 uur | Heilig voor NL korte termijn |
| Windguru WG | Stub (needs API key) | 14 dagen | Globaal beeld voor weekplanning |
| Soarcast | Stub | 3 dagen | Nederlandse bron |
| Open-Meteo | Werkend | 16 dagen | Altijd beschikbare fallback |

### Extra providers activeren

Maak een `.env` bestand:

```env
WINDGURU_API_KEY=jouw_key_hier
KNMI_API_KEY=jouw_key_hier
GOOGLE_MAPS_API_KEY=jouw_key_hier
```

## Spots

Spots staan in `spots_nkv.json`. Voeg een nieuw object toe aan de array:

```json
{
  "name": "Spotsnaam",
  "lat": 52.123,
  "lon": 4.567,
  "water_type": "flat",
  "dir_windows_deg": "180-270",
  "min_kn_twintip": 14,
  "min_kn_foil": 9,
  "windguru_spot_id": 12345,
  "soarcast_spot_slug": "slug",
  "nkv_url": "https://..."
}
```

## Architectuur

```
app-pro/
  app.py          → Streamlit UI
  utils.py        → Domeinlogica (scoring, helpers)
  providers.py    → Modulaire weerdata providers
  spots_nkv.json  → Spotdatabase
```

`providers.py` bevat:
- `WeatherProvider` — abstracte base class
- `AromeProvider` — AROME 1.3 via Open-Meteo Météo-France endpoint
- `WindguruProvider` — stub, wacht op API key
- `SoarcastProvider` — stub
- `KNMIProvider` — stub voor live metingen
- `RijkswaterstaatProvider` — stub voor getij
- `GoogleMapsProvider` — stub voor reistijd
- `ProviderManager` — cascade met automatische fallback

## TODO's voor volledige Pro-versie

- [ ] Windguru API integratie (betaald account nodig)
- [ ] Soarcast data scraping/API
- [ ] KNMI live metingen koppelen
- [ ] Rijkswaterstaat getijdata integreren
- [ ] Google Maps reistijd berekening
- [ ] Telegram alerts (via alerts.py)
- [ ] Google Calendar API directe integratie
- [ ] Volledige NKV spotkaart importeren
