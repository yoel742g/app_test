import pandas as pd
import numpy as np
import PVAnlage as pv
import waermepumpe as wp
import eAuto as ea
import haushalt as ha
summe = 0
einspeiseverguetung = 7.78

einspeise = 0
abnahme = 0

speicher_ladung = 0
speicher_max = 11
speicher_leistung = 3

def lade_strompreise_als_array(csv_dateiname):
    df = pd.read_csv(csv_dateiname, sep=';', decimal=',')
    preis_reihe = pd.to_numeric(df['Endkundenpreis_brutto (Cent/kWh)'], errors='coerce').fillna(0.0)
    preis_array = np.array(preis_reihe)
    return preis_array


def calculate_dynamic(wp_bedarf, pv_neigung, pv_ausrichtung, pv_kwp, ea_wochentag, ea_wochenende, ea_verbrauch, ea_leistung, ea_beginn, ha_verbrauch):
    pv_datei_name = "2025_15min_pv-ertrag.csv"
    preis_datei_name = "2025_15min_spotmarktpreis.csv"

    mein_wp_array = wp.berechne_waermepumpe_verbrauch(temp_datei="2025_15min_temperaturverlauf.csv", t_base=15.0, jahresbedarf=wp_bedarf, verbose=False)
    mein_pv_array = pv.pv_erstellen(pv_neigung, pv_ausrichtung, pv_kwp)
    mein_ea_array = ea.generiere_lade_profil(fahrleistung_woche_tag_km=ea_wochentag, fahrleistung_wochenende_tag_km=ea_wochenende, verbrauch_pro_100km=ea_verbrauch, wallbox_leistung_kw=ea_leistung, ladebeginn_stunde=ea_beginn)
    mein_preis_array = lade_strompreise_als_array(preis_datei_name)
    mein_haushalt_array = ha.generate_yearly_profile_2025(ha_verbrauch)
    #einspeisevergütung
    for i in range(len(mein_pv_array)):
        verbrauch = mein_wp_array[i] + mein_ea_array[i] + mein_haushalt_array[i]

        bilanz = verbrauch - (mein_pv_array[i] * 0.25)

        if bilanz > 0.0:

            if 0 < speicher_ladung < bilanz and speicher_leistung*0.25 > speicher_ladung:
                bilanz -= speicher_ladung * 0.9
                speicher_ladung = 0
            elif speicher_ladung > 0 and bilanz > speicher_leistung*0.25 and speicher_leistung*0.25 < speicher_ladung:
                bilanz -= speicher_leistung*0.25
                speicher_ladung -= (speicher_leistung*0.25)/0.9
            elif speicher_ladung > 0 and bilanz < speicher_leistung*0.25 and bilanz/0.9 < speicher_ladung:
                speicher_ladung -= bilanz/0.9
                bilanz = 0
            summe += bilanz * mein_preis_array[i]
            abnahme += 1

        elif bilanz < 0.0:
            if speicher_ladung < speicher_max:
                speicher_ladung -= bilanz*0.9
                print("Ladung von ", bilanz*-1)
                if speicher_ladung >= speicher_max:
                    speicher_ladung = speicher_max
                print("Aktuelle Ladung: ", speicher_ladung)
            else:
                print("Einspeise: ", bilanz * einspeiseverguetung)
                summe += bilanz * einspeiseverguetung
                print("Summe: ", summe)
                einspeise += 1

    summe = summe / 100 #Von cent in euro Umrechnen
    print(sum(mein_wp_array), sum(mein_pv_array)*0.25)
    if summe > 10000: #Fixkosten, Abhängig von Stromverbrauchsklasse
        summe += 133.82
    elif summe > 6000:
        summe += 123.82
    else:
        summe += 113.82
    summe = round(summe, 2)
    print(summe)
    return summe

def calculate_static(wp_bedarf, pv_neigung, pv_ausrichtung, pv_kwp, ea_wochentag, ea_wochenende, ea_verbrauch, ea_leistung, ea_beginn, ha_verbrauch):
    pv_datei_name = "2025_15min_pv-ertrag.csv"

    mein_preis_array = []
    mein_wp_array = wp.berechne_waermepumpe_verbrauch(temp_datei="2025_15min_temperaturverlauf.csv", t_base=15.0, jahresbedarf=wp_bedarf, verbose=False)
    mein_pv_array = pv.pv_erstellen(pv_neigung, pv_ausrichtung, pv_kwp)
    mein_ea_array = ea.generiere_lade_profil(fahrleistung_woche_tag_km=ea_wochentag, fahrleistung_wochenende_tag_km=ea_wochenende, verbrauch_pro_100km=ea_verbrauch, wallbox_leistung_kw=ea_leistung, ladebeginn_stunde=ea_beginn)
    
    for i in range(35040)
        mein_preis_array.append(32.4)
    
    mein_haushalt_array = ha.generate_yearly_profile_2025(ha_verbrauch)
    #einspeisevergütung
    for i in range(len(mein_pv_array)):
        verbrauch = mein_wp_array[i] + mein_ea_array[i] + mein_haushalt_array[i]

        bilanz = verbrauch - (mein_pv_array[i] * 0.25)

        if bilanz > 0.0:

            if 0 < speicher_ladung < bilanz and speicher_leistung*0.25 > speicher_ladung:
                bilanz -= speicher_ladung * 0.9
                speicher_ladung = 0
            elif speicher_ladung > 0 and bilanz > speicher_leistung*0.25 and speicher_leistung*0.25 < speicher_ladung:
                bilanz -= speicher_leistung*0.25
                speicher_ladung -= (speicher_leistung*0.25)/0.9
            elif speicher_ladung > 0 and bilanz < speicher_leistung*0.25 and bilanz/0.9 < speicher_ladung:
                speicher_ladung -= bilanz/0.9
                bilanz = 0
            summe += bilanz * mein_preis_array[i]
            abnahme += 1

        elif bilanz < 0.0:
            if speicher_ladung < speicher_max:
                speicher_ladung -= bilanz*0.9
                print("Ladung von ", bilanz*-1)
                if speicher_ladung >= speicher_max:
                    speicher_ladung = speicher_max
                print("Aktuelle Ladung: ", speicher_ladung)
            else:
                print("Einspeise: ", bilanz * einspeiseverguetung)
                summe += bilanz * einspeiseverguetung
                print("Summe: ", summe)
                einspeise += 1

    summe = summe / 100 #Von cent in euro Umrechnen
    summe += 123.09
    summe = round(summe, 2)
    print(summe)
    return summe

