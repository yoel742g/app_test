import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculator_main as cm
from datetime import datetime

# --- MAIN STREAMLIT APP ---
def main():
    st.set_page_config(page_title="SachsenEnergie AG - Tarif-Check", layout="wide")
    st.markdown("<h1 style='color: #005eb8;'>SachsenEnergie AG</h1>", unsafe_allow_html=True)
    st.title("⚡ Dynamik-Rechner für Einfamilienhäuser")

    with st.sidebar:
        st.header("Konfiguration")
        h0 = st.number_input("Hausstrom [kWh]", 1000, 10000, 3500)
        hp = st.number_input("Wärmepumpe [kWh]", 0, 10000, 5000)
        ev = st.number_input("Fahrleistung [km]", 0, 50000, 15000)
        pv = st.slider("PV-Leistung [kWp]", 0.0, 20.0, 10.0)
        bat = st.slider("Speicher [kWh]", 0.0, 20.0, 10.0)
        enwg = st.selectbox("§ 14a EnWG Modul", [1, 2])
        smart = st.toggle("Optimierung aktivieren", True)
        calc_btn = st.button("Berechnung starten", type="primary")

    if calc_btn:
        #dynamischer_preis = cm.calculate_dynamic(wp_jahr, pv_neigung, pv_ausrichtung, pv_kwp, ea_wochentag, ea_wochenende, ea_verbrauch, ea_leistung, ea_beginn)
        #statischer_preis = cm.calculate_dynamic(wp_jahr, pv_neigung, pv_ausrichtung, pv_kwp, ea_wochentag, ea_wochenende, ea_verbrauch, ea_leistung, ea_beginn)
        # UI Anzeige
        dynamisch = cm.calculate_dynamic(4000.0, 30, 10, 7500, 40, 15, 18, 11, 18)
        statisch = cm.calculate_static(4000.0, 30, 10, 7500, 40, 15, 18, 11, 18)

        col_left, col_right = st.columns(2)

        # 2. Werte in der rechten Spalte ausgeben
        with col_right:
            st.subheader("🛠️ Debugging-Werte")
            
            # Variante A: Simples st.write (zeigt Listen, Dicts, Floats etc. an)
            # st.write("**Wert Dynamisch:**", dynamisch)
            # st.write("**Wert Statisch:**", statisch)
            
            # Variante B: Wenn es reine Zahlen/Strings sind, sieht st.metric toll aus:
            st.metric("Kosten Dynamisch", f"{dynamisch} €")
            st.metric("Kosten Statisch", f"{statisch} €")
            
        
        '''st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ersparnis/Jahr", f"{metrics['Ersparnis [€/J]']} €")
        c2.metric("Autarkiegrad", f"{metrics['Autarkiegrad [%]']} %")
        c3.metric("Preis Dynamisch", f"{metrics['Effektiver Preis Dynamisch [ct/kWh]']} ct")
        c4.metric("Preis Statisch", f"{metrics['Effektiver Preis Statisch [ct/kWh]']} ct")

        col_left, col_right = st.columns(2)
        
        with col_left: 
            st.plotly_chart(plot_cost_comparison(metrics), use_container_width=True)
        with col_right:
            date_sel = st.date_input("Detailansicht wählen", value=datetime(2025, 6, 15))
            st.plotly_chart(plot_load_profile(df, (pd.to_datetime(date_sel), pd.to_datetime(date_sel)+pd.Timedelta(days=2))), use_container_width=True)'''
    else:
        st.info("Bitte links Parameter wählen und 'Berechnung starten' klicken.")

if __name__ == "__main__":
    main()
