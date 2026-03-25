import requests
import pandas as pd
import numpy as np

def exportiere_15min_pv_daten():
    # ==========================================
    # 1. PARAMETER DEINER ANLAGE
    # ==========================================
    lat = 51.0504  # Breitengrad (z.B. Dresden)
    lon = 13.7373  # Längengrad
    kwp = 10.0  # Anlagenleistung in kWp
    loss = 14  # Systemverluste in %
    angle = 35  # Dachneigung in Grad
    aspect = 0  # Ausrichtung (0 = Süd, 90 = West, -90 = Ost)

    url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"

    params = {
        'lat': lat,
        'lon': lon,
        'pvcalculation': 1,
        'peakpower': kwp,
        'loss': loss,
        'angle': angle,
        'aspect': aspect,
        'startyear': 2020,  # Lade ein typisches Jahr herunter (2020 ist oft gut verfügbar)
        'endyear': 2020,
        'outputformat': 'json'
    }

    print("Lade stündliche Daten von der EU-Datenbank herunter (das kann ein paar Sekunden dauern)...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Fehler bei der API-Anfrage: {response.status_code}")
        print(response.text)
        return

    # ==========================================
    # 2. DATEN VERARBEITEN UND AUF 15 MIN RECHNEN
    # ==========================================
    data = response.json()
    df = pd.DataFrame(data['outputs']['hourly'])

    # Text in ein echtes Datum/Uhrzeit-Format umwandeln (UTC)
    df['time'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M', utc=True)

    # Leistung von Watt (P) in Kilowatt (kW) umrechnen
    df['P_kW'] = df['P'] / 1000.0

    # Nur Zeit und Leistung behalten und Zeit als Index setzen (wichtig für Pandas)
    df = df[['time', 'P_kW']].set_index('time')

    print("Rechne stündliche Daten auf ein 15-Minuten-Raster um...")
    # DAS IST DER TRICK: resample('15min') erstellt die 15-Min-Lücken, interpolate() füllt sie sinnvoll auf
    df_15min = df.resample('15min').interpolate(method='linear')

    # Verhindern, dass durch Rundungen der Mathematik negative Leistung entsteht
    df_15min['P_kW'] = df_15min['P_kW'].clip(lower=0)

    # ==========================================
    # 3. FÜR DEN CSV-EXPORT AUFBEREITEN
    # ==========================================
    df_15min = df_15min.reset_index()

    # In die deutsche Zeitzone umwandeln (damit der Mittag auch zur echten Uhrzeit am Mittag ist)
    df_15min['time'] = df_15min['time'].dt.tz_convert('Europe/Berlin')

    # Spalten für Excel/CSV aufteilen
    df_15min['Datum'] = df_15min['time'].dt.strftime('%d.%m.%Y')
    df_15min['Uhrzeit'] = df_15min['time'].dt.strftime('%H:%M')

    # Reihenfolge festlegen und umbenennen
    df_export = df_15min[['Datum', 'Uhrzeit', 'P_kW']]
    df_export.columns = ['Datum', 'Uhrzeit', 'Erzeugte_Leistung_kW']

    # Als CSV speichern (sep=';' und decimal=',' für deutsches Excel)
    output_filename = "FINALpv_ertrag_15min_komplettes_jahr.csv"
    df_export.to_csv(output_filename, index=False, sep=';', decimal=',')

    print(f"Fertig! Die Datei wurde erfolgreich als '{output_filename}' gespeichert.")
    print(f"Sie enthält nun {len(df_export)} Zeilen (für jedes 15-Minuten-Intervall des Jahres eine).")

def lade_pv_erzeugung_als_array(csv_dateiname):
    df = pd.read_csv(csv_dateiname, sep=';', decimal=',')
    erzeugung_reihe = pd.to_numeric(df['Erzeugte_Leistung_kW'], errors='coerce').fillna(0.0)
    pv_array = np.array(erzeugung_reihe)
    pv_array = pv_array[:-97]
    for i in range(4):
        pv_array = np.insert(pv_array, 0, 0.)

    return pv_array


def pv_erstellen():
    exportiere_15min_pv_daten()
    pv_array = lade_pv_erzeugung_als_array("FINALpv_ertrag_15min_komplettes_jahr.csv")
    return pv_array


