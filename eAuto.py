import datetime


def generiere_lade_profil(
        fahrleistung_woche_tag_km: float,
        fahrleistung_wochenende_tag_km: float,
        verbrauch_pro_100km: float,
        wallbox_leistung_kw: float,
        ladebeginn_stunde: int
) -> list[float]:
    """
    Erstellt ein 15-Minuten-Lastprofil (in kWh) für das Laden eines E-Autos im Jahr 2025.
    Die nachzuladende Energie berechnet sich rein aus der gefahrenen Strecke des Tages.
    Gibt eine Liste mit 35.040 Einträgen zurück.
    """
    # 2025 hat 365 Tage: 365 * 24 * 4 = 35.040 Intervalle
    anzahl_intervalle = 35040
    lade_profil = [0.0] * anzahl_intervalle

    # Max. Energie, die die Wallbox in 15 Minuten (0.25 Stunden) in den Akku schieben kann
    max_energie_pro_intervall = wallbox_leistung_kw * 0.25

    # Startdatum für 2025 festlegen (1. Januar 2025 ist ein Mittwoch)
    start_datum = datetime.date(2025, 1, 1)

    for tag_index in range(365):
        aktuelles_datum = start_datum + datetime.timedelta(days=tag_index)

        # Wochentag prüfen (Montag=0 ... Sonntag=6)
        ist_wochenende = aktuelles_datum.weekday() >= 5

        # Tageskilometer festlegen
        tageskilometer = fahrleistung_wochenende_tag_km if ist_wochenende else fahrleistung_woche_tag_km

        # Zu ladende Energie entspricht exakt dem Tagesverbrauch
        energie_zu_laden = (tageskilometer / 100.0) * verbrauch_pro_100km

        if energie_zu_laden > 0:
            # Index für den Ladebeginn (z. B. 18:00 Uhr) des aktuellen Tages berechnen
            intervall_idx = (tag_index * 24 * 4) + (ladebeginn_stunde * 4)

            # Laden, bis die verbrauchte Energie des Tages wieder "aufgefüllt" ist
            while energie_zu_laden > 0 and intervall_idx < anzahl_intervalle:
                # Wir laden entweder die vollen 15 Min oder nur den Rest, der noch fehlt
                lademenge = min(max_energie_pro_intervall, energie_zu_laden)

                lade_profil[intervall_idx] = lademenge
                energie_zu_laden -= lademenge

                intervall_idx += 1

    return lade_profil


# === BEISPIELAUFRUF ===
profil_2025 = generiere_lade_profil(
    fahrleistung_woche_tag_km=40.0,
    fahrleistung_wochenende_tag_km=15.0,
    verbrauch_pro_100km=18.0,
    wallbox_leistung_kw=11.0,
    ladebeginn_stunde=18
)

# Überprüfung
print(f"Anzahl der 15-Min-Intervalle: {len(profil_2025)}")
print(f"Gesamt geladene Energie im Jahr: {sum(profil_2025):.2f} kWh")