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
        dynamisch = cm.calculate_dynamic(4000.0, 30, 10, 7500, 40, 15, 18, 11, 18, 3500)
        statisch = cm.calculate_static(4000.0, 30, 10, 7500, 40, 15, 18, 11, 18, 3500)

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
        
    else:
        st.info("Bitte links Parameter wählen und 'Berechnung starten' klicken.")

if __name__ == "__main__":
    main()
