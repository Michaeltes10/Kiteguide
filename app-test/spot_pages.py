"""
Spot detail pages — KiteGuide
Each spot has its own detailed information page with webcam, parking, wind info.
"""

# ---------------------------------------------------------------------------
# Spot data registry
# ---------------------------------------------------------------------------
SPOT_INFO = {
    "Wijk aan Zee": {
        "slug": "wijk-aan-zee",
        "title": "Wijk aan Zee",
        "subtitle": "Brede stranden, golven en een relaxte kitesurf-community",
        "description": (
            "Wijk aan Zee is een van de populairste kitespots van Noord-Holland. "
            "Met een breed strand heb je alle ruimte om op te tuigen, te launchen en te landen. "
            "Er kunnen flinke golven binnenrollen en er kan een sterke stroming staan, "
            "vooral bij vloed. Afhankelijk van het getij kun je meer of minder staan, "
            "maar richting zee wordt het al snel diep. De sfeer is relaxed — kiters helpen "
            "elkaar en er is een leuke mix van beginners en gevorderden."
        ),
        "water_type": "Zee (Noordzee)",
        "level": "Gevorderd",
        "wind_directions": "Noord-noordwest tot en met Zuidwest",
        "wind_note": (
            "West en west-noordwest wind staat recht aanlandig. "
            "Zorg dat je hoogte kunt houden, anders drijf je terug naar de kust."
        ),
        "parking_address": "Kitesurfpad 1951, Velsen-Noord",
        "parking_info": (
            "Gratis parkeren. Rij helemaal tot het einde van de Reyndersweg, voorbij de "
            "laatste windmolen. Daar vind je een kleine parkeerplaats — het kan snel vol zijn. "
            "Let op: er zijn meldingen van auto-inbraken. Laat geen waardevolle spullen achter."
        ),
        "parking_price": "Gratis",
        "facilities": "Restaurant Aloha en Timboektoe op loopafstand (Noordpier)",
        "rules": (
            "Kitesurfen is toegestaan vanaf De Bunker richting Wijk aan Zee (door de "
            "strandhuisjes) en richting Velsen via zone 1."
        ),
        "coordinates": "52.4825, 4.5817",
        "webcam_type": "youtube",
        "webcam_embed": "https://www.youtube.com/embed/5rkyZrQv674",
        "webcam_label": "Live HD Webcam — Surfweer.nl / Aloha Noordpier",
        "webcam_credit": "surfweer.nl",
        "tips": [
            "Check altijd het getij — bij vloed kan het een flinke klotsbak zijn",
            "West/WNW wind is recht aanlandig, ideaal maar krachtig",
            "Brede strand geeft ruimte, maar de parkeerplaats is klein",
            "Schoenen zijn handig op het strand",
        ],
    },
    "IJmuiden": {
        "slug": "ijmuiden",
        "title": "IJmuiden",
        "subtitle": "Waar het vaak harder waait dan elders aan de kust",
        "description": (
            "IJmuiden is een krachtige kitespot aan de Noord-Hollandse kust. "
            "Doordat de spot iets verder in zee ligt, waait het hier vaak harder "
            "dan op nabijgelegen spots. Het strand loopt langzaam af, waardoor je "
            "een behoorlijk eind kunt staan. De pier breekt golven en vermindert "
            "de stroming, wat het bij noordwestenwind een prima oefenspot maakt "
            "voor beginners."
        ),
        "water_type": "Zee (Noordzee)",
        "level": "Beginners tot gevorderd",
        "wind_directions": "Noordwest, West, Zuidwest en zelfs Zuid",
        "wind_note": (
            "Uniek: bij zuidenwind kun je hier nog varen — elders langs de Noordzee "
            "is dit aflandig en gevaarlijk. Ga NOOIT het water op met aflandige wind."
        ),
        "parking_address": "Kennemerstrand 174, IJmuiden",
        "parking_info": (
            "Betaald parkeren op een groot parkeerterrein bij de KNRM. "
            "Apr-okt: eerste half uur gratis, daarna vanaf EUR 1,80. Dagkaart EUR 10. "
            "Winter (nov-feb): werkdagen eerste 30 min gratis, daarna EUR 0,30/30 min."
        ),
        "parking_price": "Betaald (max EUR 10/dag)",
        "facilities": "Strandpaviljoen Zilt aan Zee, diverse strandtenten, kitescholen (Wind4Water)",
        "rules": (
            "Zone 1: het hele jaar kitesurfen toegestaan. Zone 2: verboden tijdens hoogseizoen. "
            "40 meter strook tot de vloedlijn vrij houden voor wandelaars. "
            "Minimaal 50 meter afstand van de pier houden."
        ),
        "coordinates": "52.4630, 4.5680",
        "webcam_type": "hls",
        "webcam_embed": "https://5b8d2cbe62ad6.streamlock.net/live/ijmuiden1.stream/playlist.m3u8",
        "webcam_label": "Live Webcam Haven IJmuiden",
        "webcam_credit": "webcam-havenijmuiden.nl",
        "tips": [
            "Bij NW-wind is zone 1 ideaal voor beginners",
            "Het strand loopt langzaam af — je kunt ver staan",
            "Zuidenwind is hier uniek vaarbaar, maar wees voorzichtig",
            "Parkeren is betaald, neem muntgeld of pin mee",
        ],
    },
    "Muiderberg": {
        "slug": "muiderberg",
        "title": "Muiderberg",
        "subtitle": "Vlak water vlakbij Amsterdam — ideaal voor beginners",
        "description": (
            "Muiderberg ligt aan het IJmeer, vlak bij Amsterdam, en is de perfecte "
            "beginnerspot. Het water blijft tot 300 meter uit de kust ondiep en vlak, "
            "waardoor je overal kunt staan. De spot is compact en heeft een gezellige sfeer. "
            "Let op: bij zuidelijke wind wordt het vlagerig door de bomen in de omgeving."
        ),
        "water_type": "Binnenwater (IJmeer)",
        "level": "Beginners",
        "wind_directions": "Noordwest, Noord, Noordoost",
        "wind_note": (
            "Beste windrichting is Noord of Noordwest. Bij andere richtingen wordt "
            "de wind snel vlagerig door omliggende bomen. Zuidenwind is aflandig — niet varen!"
        ),
        "parking_address": "Kruising Dijkweg & Kerkepad, Muiderberg",
        "parking_info": (
            "Gratis parkeren op een klein parkeerplaatsje aan het Kerkpad. "
            "Parkeer NIET op of langs de dijk — dit levert een boete op. "
            "Bij drukte mag soms de parkeerplaats van de voetbalvereniging worden gebruikt."
        ),
        "parking_price": "Gratis",
        "facilities": "Geen directe voorzieningen op de spot",
        "rules": (
            "Niet kiten in de vaargeul en niet in het zwemmersgedeelte. "
            "Apr-okt: zwemmerszone afgebakend met gele lijnen. Niet kiten bij de haven."
        ),
        "coordinates": "52.3291, 5.1134",
        "webcam_type": "link",
        "webcam_embed": "https://www.windfinder.com/webcams/muiderberg",
        "webcam_label": "Webcams Muiderberg — Windfinder",
        "webcam_credit": "windfinder.com",
        "tips": [
            "Pomp je kite op bij het water — op het grasveld valt de wind weg",
            "Je kunt 300m ver staan, ideaal om te oefenen",
            "Parkeer netjes — we zijn te gast en willen blijven kiten",
            "Pas op voor kites in de bomen bij vlagerige wind",
        ],
    },
    "Medemblik": {
        "slug": "medemblik",
        "title": "Medemblik",
        "subtitle": "Een van de weinige spots in Nederland voor oostenwind",
        "description": (
            "Kitespot Medemblik (ook bekend als strandje Nesbos) ligt aan het IJsselmeer "
            "en is uniek omdat je hier met oostenwind kunt kiten — daar zijn weinig spots "
            "voor in Nederland. Het water blijft tot 150 meter uit de kust ondiep. "
            "De bodem is bedekt met schelpen, dus schoenen zijn geen overbodige luxe."
        ),
        "water_type": "Binnenwater (IJsselmeer)",
        "level": "Beginners tot gevorderd",
        "wind_directions": "Noord, Noordoost, Oost",
        "wind_note": (
            "Bij NNW of ZO wind wordt het vlagerig. "
            "Het bijzondere aan Medemblik is dat oostenwind hier prima werkt."
        ),
        "parking_address": "Oosterdijk 8, Medemblik (kruising Droge Wijmersweg)",
        "parking_info": (
            "Gratis, grote parkeerplaats. In het weekend wordt deze 's avonds soms "
            "half afgesloten om overlast te voorkomen. Parkeer netjes — boeren moeten "
            "hier soms maaien."
        ),
        "parking_price": "Gratis",
        "facilities": "Geen vaste horeca, soms een snackwagen in de zomer",
        "rules": (
            "ALLEEN kitesurfen van april tot oktober. Nov-mrt is verboden (vogelbescherming). "
            "Vaar alleen tussen de gele boeien. Daarbuiten is Natura 2000 / havengebied — verboden. "
            "Bij Vlietsingel strand en de jachthaven is kitesurfen jaarrond verboden."
        ),
        "coordinates": "52.7553, 5.1223",
        "webcam_type": "link",
        "webcam_embed": "https://webcam-medemblik.nl/",
        "webcam_label": "Live Webcam Medemblik",
        "webcam_credit": "webcam-medemblik.nl",
        "tips": [
            "Schoenen aan! De bodem zit vol schelpen",
            "Launchzone is krap met bomen aan de rand",
            "Spot raakt snel vol, kom vroeg",
            "Kitesurfen bij Andijk (ten oosten) is verboden",
        ],
    },
    "Schellinkhout": {
        "slug": "schellinkhout",
        "title": "Schellinkhout",
        "subtitle": "Enorme stadiepte in een beschutte baai aan het IJsselmeer",
        "description": (
            "Schellinkhout is een grote baai aan het IJsselmeer, ten zuiden van Hoorn. "
            "Het bijzondere: je kunt tot wel 800 meter uit de kust staan! Het water is "
            "vlak met korte chop — lekker voor tricks en comfortabel varen. "
            "De spot is geschikt voor alle niveaus en er zijn meerdere kitescholen actief."
        ),
        "water_type": "Binnenwater (IJsselmeer)",
        "level": "Alle niveaus",
        "wind_directions": "Zuidoost tot en met West",
        "wind_note": "Je kunt hier met vrijwel elke windrichting kiten.",
        "parking_address": "De Laan 4, Schellinkhout",
        "parking_info": (
            "Gratis parkeren, uitsluitend beneden op de parkeerplaats. "
            "Op de dijk is parkeren verboden en er wordt gehandhaafd. "
            "Parkeer je langs de dijk, laat dan voldoende ruimte voor verkeer."
        ),
        "parking_price": "Gratis",
        "facilities": "Snackwagen in de zomer, midgetgolfbaan op de dijk met eten/drinken, surfshop op het fabrieksterrein",
        "rules": (
            "In de zomer is er een afgebakend zwemmersgedeelte. "
            "Kites oppompen en launchen/landen op het tweede gedeelte van het grasveld."
        ),
        "coordinates": "52.6380, 5.1850",
        "webcam_type": "twitch",
        "webcam_embed": "https://player.twitch.tv/?channel=kitefeel&parent=localhost&parent=127.0.0.1",
        "webcam_label": "Live Webcam KiteFEEL Surfcenter — gericht op zuidwest",
        "webcam_credit": "kitefeel.nl",
        "tips": [
            "800 meter stadiepte — nergens in NL zoveel ruimte",
            "Korte chop is ideaal voor tricks oefenen",
            "Kan erg druk worden in de zomer, kom vroeg",
            "Kite launchen op het tweede stuk grasveld, niet bij het water",
        ],
    },
}


def get_spot_info(spot_name: str) -> dict | None:
    """Get spot info by name (case-insensitive partial match)."""
    for name, info in SPOT_INFO.items():
        if name.lower() in spot_name.lower() or spot_name.lower() in name.lower():
            return info
    return None


def get_all_spots() -> dict:
    """Return all spot info."""
    return SPOT_INFO
