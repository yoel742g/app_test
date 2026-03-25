import requests
import pandas as pd
import numpy as np


def exportiere_15min_pv_daten():
    # ==========================================
    # 1. PARAMETER DEINER ANLAGE
    # ==========================================
    lat = 51.0504
    lon = 13.7373
    kwp = 10.0
    loss = 14
    angle = 30
    aspect = 10

    url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

    params = {
        'lat': lat,
        'lon': lon,
        'pvcalculation': 1,
        'peakpower': kwp,
        'loss': loss,
        'angle': angle,
        'aspect': aspect,
        'startyear': 2019,
        'endyear': 2019,
        'outputformat': 'json'
    }

    print("Lade stündliche Daten von der EU-Datenbank herunter (das kann ein paar Sekunden dauern)...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Fehler bei der API-Anfrage: {response.status_code}")
        return

    # ==========================================
    # 2. DATEN VERARBEITEN UND AUF 15 MIN RECHNEN
    # ==========================================
    data = response.json()
    df = pd.DataFrame(data['outputs']['hourly'])

    # Zeit parsen und direkt als Index setzen (Wir sind hier noch in UTC)
    df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M', utc=True)
    df = df.set_index('time')

    # Leistung von Watt (P) in Kilowatt (kW) umrechnen
    df['P_kW'] = df['P'] / 1000.0

    print("Rechne stündliche Daten auf ein 15-Minuten-Raster um...")

    # === HIER IST DER NEUE FIX ===
    # Wir runden die Zeiten auf glatte Stunden ('h'), SOLANGE WIR NOCH IN UTC SIND!
    # In UTC gibt es keine Sommerzeit, also auch keinen AmbiguousTimeError.
    df.index = df.index.round('h')

    # DANACH erst in die deutsche Zeitzone umwandeln
    df = df.tz_convert('Europe/Berlin')

    # Resampling und Interpolation
    df_15min = df[['P_kW']].resample('15min').interpolate(method='time')
    df_15min['P_kW'] = df_15min['P_kW'].clip(lower=0)

    # Zwingen Pandas in ein perfektes 365-Tage-Raster (exakt 35.040 Werte für 2025/2019).
    ziel_index = pd.date_range(start='2019-01-01 00:00:00', periods=35040, freq='15min', tz='Europe/Berlin')
    df_15min = df_15min.reindex(ziel_index).fillna(0.0)

    # ==========================================
    # 3. FÜR DEN CSV-EXPORT AUFBEREITEN
    # ==========================================
    df_export = df_15min.reset_index()
    df_export.columns = ['time', 'Erzeugte_Leistung_kW']

    df_export['Datum'] = df_export['time'].dt.strftime('%d.%m.%Y')
    df_export['Uhrzeit'] = df_export['time'].dt.strftime('%H:%M')

    df_export = df_export[['Datum', 'Uhrzeit', 'Erzeugte_Leistung_kW']]

    # Als CSV speichern
    output_filename = "FINALpv_ertrag_15min_komplettes_jahr.csv"
    df_export.to_csv(output_filename, index=False, sep=';', decimal=',')

    print(f"Fertig! Die Datei wurde erfolgreich als '{output_filename}' gespeichert.")
    print(f"Sie enthält nun EXAKT {len(df_export)} Zeilen.")


def lade_pv_erzeugung_als_array(csv_dateiname):
    df = pd.read_csv(csv_dateiname, sep=';', decimal=',')
    pv_array = np.array(df['Erzeugte_Leistung_kW'].fillna(0.0))
    return pv_array


def pv_erstellen():
    exportiere_15min_pv_daten()
    return lade_pv_erzeugung_als_array("FINALpv_ertrag_15min_komplettes_jahr.csv")


if __name__ == "__main__":
    test_array = pv_erstellen()
    print(f"Kontrolle - Das Array hat {len(test_array)} Einträge.")
    print(f"Erzeugte Energie (Beispiel Mittags): {test_array[520]:.2f} kW")