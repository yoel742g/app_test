import pandas as pd

# Dateiname der Excel-Datei
dateiname = 'FERTKopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx'

# Einlesen des Tabellenblatts 'H25'
df = pd.read_excel(dateiname, sheet_name='H25', header=None, engine='openpyxl')

# Tagestypen (Zeile 4) und Zeiten (Spalte 2) extrahieren
tagestypen = df.iloc[3, 2:].values
zeiten = df.iloc[4:, 1].values

# Spaltenindizes für 'SA' (Samstag) ermitteln
sa_spalten_indizes = [i + 2 for i, dt in enumerate(tagestypen) if str(dt).strip().upper() == 'SA']

alle_daten_liste = []

# Daten durchlaufen
for idx in sa_spalten_indizes:
    # Datum aus Zeile 3 extrahieren und formatieren (z.B. '2012-01-01')
    datum_roh = str(df.iloc[2, idx]).strip()
    datum_formatiert = pd.to_datetime(datum_roh).strftime('%Y-%m-%d')

    # Werte als Float extrahieren
    werte_roh = df.iloc[4:, idx]
    if werte_roh.dtype == 'object':
        werte = werte_roh.replace(',', '.', regex=True).astype(float).values.tolist()
    else:
        werte = werte_roh.astype(float).values.tolist()

    # Für jedes 15-Minuten-Intervall eine eigene Zeile anlegen
    for i, t in enumerate(zeiten):
        if pd.isna(t):
            continue

        alle_daten_liste.append({
            "Datum": datum_formatiert,
            "Uhrzeit": str(t).strip(),
            "Verbrauch": werte[i]
        })

# In DataFrame umwandeln
df_export = pd.DataFrame(alle_daten_liste)

# Als CSV im deutschen Format exportieren
df_export.to_csv('Export_SA_Werte_H25_Zeilen.csv', index=False, sep=';', decimal=',')