import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculator_main as cm
from datetime import datetime

# --- MAIN STREAMLIT APP ---
def main():
    st.set_page_config(page_title="Studi Energy Check - Tarif-Check", layout="wide")
    st.markdown("<h1 style='color: #d50037;'>Der Stecker Checker</h1> <br> <h2>🔌Deine Dose – Deine Regeln🔌</h2>", unsafe_allow_html=True)
    st.title("Dynamik-Rechner für Einfamilienhäuser")

    with st.sidebar:
        st.header("Konfiguration")
        
        # --- 1. Hausstrom ---
        hausstrom_optionen = {
            "1 Person (1.500 kWh)": 1500,
            "2 Personen (2.500 kWh)": 2500,
            "3 Personen (3.500 kWh)": 3500,
            "4 Personen (4.500 kWh)": 4500,
            "Eigene Eingabe...": "custom"
        }

        auswahl_hausstrom = st.selectbox(
            "Welchen Energiebedarf hat Ihr Haushalt?", 
            options=list(hausstrom_optionen.keys()),
            index=2 
        )

        if hausstrom_optionen[auswahl_hausstrom] == "custom":
            h0 = st.number_input(
                "Eigener Energiebedarf (volle kWh)", 
                min_value=500, 
                max_value=20000, 
                value=3500, 
                step=100
            )
        else:
            h0 = hausstrom_optionen[auswahl_hausstrom]
            
        st.divider()

        # --- 2. PV-Anlage ---
        ar_dict = {"Süden":0, "Süd-Westen":45, "Westen":90, "Nord-Westen":135, "Norden":180, "Nord-Osten":-135, "Osten":-90, "Süd-Osten":-45}
        pv, dn, ar, bat_capacity, bat_power = 0, 30, "Süden", 0, 0
        hat_pv = st.radio("Haben Sie eine PV-Anlage im Einsatz?", ["Ja", "Nein"], index=1)
        if hat_pv == "Ja":
            pv = st.number_input("PV-Leistung [kWp]", 1, 25, 10)
            dn = st.number_input("Dachneigung [°]", 0, 60, 30)
            ar = st.selectbox("Ausrichtung", ["Norden", "Nord-Osten", "Osten", "Süd-Osten", "Süden", "Süd-Westen", "Westen", "Nord-Westen"])
            ar_deg = ar_dict[ar]
            
            # --- 3. Speicher (Nur relevant, wenn PV vorhanden) ---
            hat_speicher = st.radio("Haben Sie einen dazugehörigen Energiespeicher im Einsatz?", ["Ja", "Nein"], index=1)
            if hat_speicher == "Ja":
                bat_capacity = st.number_input("Speicherkapazität [kWh]", 1, 100, 10)
                bat_power = st.number_input("Abgabeleistung [kW]", 0,15,3) 
                
        
        st.divider()

        # --- 4. E-Auto ---
        ev_charge_hour = 0 # default Ladezeit 00:00 Uhr
        wallbox_power = 0
        km_woche, km_wochenende, verbrauch_100km = 0, 0, 0
        hat_ev = st.radio("Besitzen Sie ein E-Auto, welches Sie zuhause laden?", ["Ja", "Nein"], index=1)
        if hat_ev == "Ja":
            km_woche = st.number_input("Fahrstrecke pro Wochentag [km]", min_value=0, value=40, step=5)
            km_wochenende = st.number_input("Fahrstrecke pro Tag am Wochenende [km]", min_value=0, value=20, step=5)
            verbrauch_100km = st.number_input("Verbrauch auf 100km [kWh]", min_value=0., value=15., step=0.1)
            
            uhrzeiten = [f"{i:02d}:00" for i in range(24)]
            auswahl_zeit = st.selectbox("Wann laden Sie normalerweise Ihr Auto?", options=uhrzeiten, index=17)
            ev_charge_hour = int(auswahl_zeit.split(":")[0])
            
            wallbox_power = st.selectbox("Welche Ausgangsleistung liefert Ihre Wallbox? [kW]", [11,22])

        st.divider()

        # --- 5. Wärmepumpe ---
        hp = 0
        hat_wp = st.radio("Heizen Sie mit einer Wärmepumpe?", ["Ja", "Nein"], index=1)
        if hat_wp == "Ja":
            wp_bekannt = st.radio("Kennen Sie den jährlichen Energieverbrauch [kWh] Ihrer Wärmepumpe?", ["Ja", "Nein (Rechnung mit Fixwert)"], index=1)
            if wp_bekannt == "Ja":
                hp = st.number_input("Wie viel Energie [kWh] benötigen Sie zum Heizen?", min_value=0, value=5000, step=100)
            else:
                hp = 5000 # Fixwert
        
        st.divider()

        col_enwg, col_info = st.columns([4,1])
        st.markdown("""
        <style>
        .tooltip {
          position: relative;
          display: inline-block;
          cursor: pointer;
          margin-left: 6px;
          color: #d50037;
          font-weight: bold;
        }
        
        .tooltip .tooltiptext {
          visibility: hidden;
          width: 320px;
          background-color: #f9f9f9;
          color: #000;
          text-align: left;
          border-radius: 8px;
          padding: 10px;
          position: absolute;
          z-index: 1;
          top: 125%;
          left: 0;
          box-shadow: 0px 2px 10px rgba(0,0,0,0.2);
          font-size: 13px;
        }
        
        .tooltip:hover .tooltiptext {
          visibility: visible;
        }
        </style>
        
        <div style="display: flex; align-items: center;">
          <span style="font-size:16px; font-weight:600;">§ 14a EnWG Modul</span>
          
          <div class="tooltip">ⓘ
            <div class="tooltiptext">
              <b><ins>Modul 1</ins></b><br>
              Einmal jährlich Gutschrift über 168€, unabhängig von der Verbrauchszeit.<br><br>
              <b><ins>Modul 2</ins></b><br>
              Auf jede kWh, die Ihr E-Auto an der Wallbox lädt, wird ein 60 prozentiger Rabatt angewandt.<br>
              ➤ Lohnt sich für Vielfahrer.<br><br>
              <b><ins>Modul 3</ins></b><br>
             Tagsüber ist der Energiepreis relativ hoch, nachts (23 - 05 Uhr) relativ niedrig.<br>
              ➤ Ideal für das Nachtladen.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    
        enwg = st.selectbox("", [1, 2, 3], label_visibility="collapsed")
        smart = st.toggle("Optimierung aktivieren", True)
        
        # Leerraum vor dem Button für besseres Design
        st.write("") 
        calc_btn = st.button("Berechnung starten", type="primary", use_container_width=True)

    # --- HAUPTBEREICH (Ergebnisse) ---
    if calc_btn:
        dynamischer_preis = cm.calculate_dynamic(hp, dn, ar_deg, pv, km_woche, km_wochenende, verbrauch_100km, wallbox_power, ev_charge_hour, h0, bat_capacity, bat_power)
        statischer_preis = cm.calculate_static(hp, dn, ar_deg, pv, km_woche, km_wochenende, verbrauch_100km, wallbox_power, ev_charge_hour, h0, bat_capacity, bat_power)
        # h0 = Hausstrom
        # UI Anzeige
        #dynamischer_preis = cm.calculate_dynamic(4000.0, 30, 10, 7.5, 40, 15, 18, 11, 18, 3500)
        #statischer_preis = cm.calculate_static(4000.0, 30, 10, 7.5, 40, 15, 18, 11, 18, 3500)

        col_left, col_right = st.columns(2)

        # 2. Werte in der rechten Spalte ausgeben
        with col_right:
            st.subheader("🛠️ Debugging-Werte")
            
            # Variante A: Simples st.write (zeigt Listen, Dicts, Floats etc. an)
            # st.write("**Wert Dynamisch:**", dynamisch)
            # st.write("**Wert Statisch:**", statisch)
            
            # Variante B: Wenn es reine Zahlen/Strings sind, sieht st.metric toll aus:
            st.metric("Kosten Dynamisch", f"{dynamischer_preis} €")
            st.metric("Kosten Statisch", f"{statischer_preis} €")
    
    

    # --- OLD ---
#    if calc_btn:
#        gen = LoadProfileGenerator()
#        te = TariffEngine()
#        opt = EnergyOptimizer(battery_cap_kwh=bat)
#        calc = EconomicCalculator()
#
#        # Simulation
#        config_data = {
#            'h0_kwh': h0, 
#            'hp_kwh': hp, 
#            'ev_km': ev, 
#            'ev_charge_hour': ev_charge_hour, 
#            'pv_kwp': pv
#        }
#        df = gen.get_combined_dataframe(config_data)
#        df['spot_price_pure'] = te.generate_synthetic_spot_prices(df.index)
#        df['dynamic_price_brutto'] = te.get_dynamic_tariff_components(df['spot_price_pure'])
#        df = opt.simulate_smart_system(df, use_dynamic_logic=smart)
#        metrics = calc.calculate_annual_metrics(df, te.get_static_tariff_details(), te, enwg_module=enwg)

        # UI Anzeige
#        st.divider()
#        c1, c2, c3, c4 = st.columns(4)
#        c1.metric("Ersparnis/Jahr", f"{metrics['Ersparnis [€/J]']} €")
#        c2.metric("Autarkiegrad", f"{metrics['Autarkiegrad [%]']} %")
#        c3.metric("Preis Dynamisch", f"{metrics['Effektiver Preis Dynamisch [ct/kWh]']} ct")
#        c4.metric("Preis Statisch", f"{metrics['Effektiver Preis Statisch [ct/kWh]']} ct")

#        col_left, col_right = st.columns(2)
#        with col_left: 
#            st.plotly_chart(plot_cost_comparison(metrics), use_container_width=True)
#        with col_right:
#            date_sel = st.date_input("Detailansicht wählen", value=datetime(2025, 6, 15))
#            st.plotly_chart(plot_load_profile(df, (pd.to_datetime(date_sel), pd.to_datetime(date_sel)+pd.Timedelta(days=2))), use_container_width=True)
    else:
        st.info("Bitte nutzen Sie die Konfiguration auf der linken Seite und klicken Sie auf 'Berechnung starten'.")









if __name__ == "__main__":
    main()
