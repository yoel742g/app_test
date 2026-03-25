import pandas as pd


def berechne_waermepumpe_verbrauch(temp_datei, t_base=15.0, jahresbedarf=4000.0, verbose=False):
    """
    Liest die Temperaturdaten ein und berechnet den Energieverbrauch der Wärmepumpe
    für jedes 15-Minuten-Intervall.

    :param temp_datei: Pfad zur CSV-Datei mit den Temperaturdaten.
    :param t_base: Heizgrenztemperatur in °C (Standard: 15.0).
    :param jahresbedarf: Jährlicher Heizenergiebedarf in kWh (Standard: 4000.0).
    :param verbose: Wenn True, werden Zwischenschritte in der Konsole ausgegeben.
    :return: Eine 1-D Python-Liste mit exakt 35.040 Werten (Verbrauch in kWh pro 15 min).
    """
    if verbose:
        print("Lade und strukturiere Temperaturdaten...")

    df_temp = pd.read_csv(temp_datei, sep=";", decimal=",")
    df_temp = df_temp.melt(id_vars=['Datum'], var_name='Uhrzeit', value_name='Temperatur')
    df_temp['Uhrzeit'] = df_temp['Uhrzeit'].str[:5]
    df_temp = df_temp.sort_values(['Datum', 'Uhrzeit']).reset_index(drop=True)
    df_temp['Temperatur'] = df_temp['Temperatur'].ffill()

    if verbose:
        print("Berechne dynamischen Energieverbrauch...")

    df_temp['Delta_T'] = (t_base - df_temp['Temperatur']).clip(lower=0)
    df_temp['COP'] = (2.5 + 0.1 * df_temp['Temperatur']).clip(lower=1.0, upper=5.5)
    df_temp['Bedarf_roh'] = df_temp['Delta_T'] / df_temp['COP']

    summe_bedarf = df_temp['Bedarf_roh'].sum()

    if summe_bedarf == 0:
        return [0.0] * len(df_temp)

    df_temp['Verbrauch_kWh'] = (df_temp['Bedarf_roh'] / summe_bedarf) * jahresbedarf

    return df_temp['Verbrauch_kWh'].tolist()


# =====================================================================
# TEST- / EINGABEBEREICH (Wird beim "import" automatisch ignoriert!)
# =====================================================================
if __name__ == "__main__":
    datei_temperatur = "temperatur_verlauf_2025_15min.csv"

    pos = True
    while pos:
        eingabe = input("Geben Sie ihren Jahresverbrauch in vollen kWh an (Enter für 4000 kWh): ").strip()

        try:
            if eingabe == "":
                bedarf_input = 4000.0
                print("Kein Wert eingegeben. Verwende Standardwert: 4000 kWh.")
            else:
                bedarf_input = float(eingabe)

            # Da wir die Datei hier direkt ausführen, setzen wir verbose=True
            verbrauch_15min_liste = berechne_waermepumpe_verbrauch(
                temp_datei=datei_temperatur,
                t_base=15.0,
                jahresbedarf=bedarf_input,
                verbose=True
            )

            print("-" * 50)
            print(f"Erfolgreich {len(verbrauch_15min_liste)} Werte (15-Min-Intervalle) generiert.")
            print(f"Erster Wert (01.01. 00:00): {verbrauch_15min_liste[0]:.4f} kWh")
            print(f"Letzter Wert (31.12. 23:45): {verbrauch_15min_liste[-1]:.4f} kWh")
            print(f"Summe der Liste (Kontrolle): {sum(verbrauch_15min_liste):.1f} kWh")
            print("-" * 50)

            pos = False


        except ValueError:
            print("Bitte geben Sie eine gültige Zahl ein oder drücken Sie einfach Enter!")
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{datei_temperatur}' wurde nicht gefunden.")
            pos = False
        except Exception as e:
            print(f"Es gab einen unerwarteten Fehler: {e}")
            pos = False


