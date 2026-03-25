import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculator_main as cm
from datetime import datetime

'''
# --- MODUL 1: LASTPROFIL GENERATOR ---
class LoadProfileGenerator:
    def __init__(self, year=2025):
        self.year = year
        self.time_index = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', freq='H')
        
    def generate_h0_profile(self, annual_demand_kwh):
        # Umwandlung in numpy arrays, um AttributeError zu vermeiden
        hour = self.time_index.hour.values
        day_of_year = self.time_index.dayofyear.values
        
        base_curve = 0.5 + 0.5 * np.sin((hour - 6) * np.pi / 12)**2
        seasonal_factor = 1 + 0.2 * np.cos(day_of_year * 2 * np.pi / 365)
        profile = base_curve * seasonal_factor
        
        # Sicherstellen, dass wir np.sum verwenden
        return (profile / np.sum(profile)) * annual_demand_kwh

    def generate_pv_profile(self, installed_kwp, location_factor=1050):
        hour = self.time_index.hour.values
        day_of_year = self.time_index.dayofyear.values
        
        seasonal_intensity = 0.5 * (1 + np.cos((day_of_year - 172) * 2 * np.pi / 365))
        daily_curve = np.maximum(0, np.sin((hour - 5) * np.pi / 14))
        pv_profile = daily_curve * seasonal_intensity
        
        total_yield = installed_kwp * location_factor
        return (pv_profile / np.sum(pv_profile)) * total_yield

    def generate_hp_profile(self, annual_demand_kwh):
        day_of_year = self.time_index.dayofyear.values
        temp_profile = 9 - 11 * np.cos((day_of_year - 15) * 2 * np.pi / 365)
        heating_demand = np.maximum(0, 15 - temp_profile)
        cop = 3.0 + 0.05 * (temp_profile + 5)
        hp_profile = heating_demand / cop
        return (hp_profile / np.sum(hp_profile)) * annual_demand_kwh

    def generate_ev_profile(self, annual_mileage_km, consumption_per_100km=18):
        total_demand_kwh = (annual_mileage_km / 100) * consumption_per_100km
        hour = self.time_index.hour.values
        ev_profile = np.zeros(len(self.time_index))
        # Laden primär zwischen 17 und 22 Uhr
        charge_window = (hour >= 17) & (hour <= 22)
        ev_profile[charge_window] = 1.0
        ev_profile *= np.random.uniform(0.5, 1.5, size=len(ev_profile))
        return (ev_profile / np.sum(ev_profile)) * total_demand_kwh

    def get_combined_dataframe(self, config):
        df = pd.DataFrame(index=self.time_index)
        df['load_h0'] = self.generate_h0_profile(config['h0_kwh'])
        df['load_hp'] = self.generate_hp_profile(config['hp_kwh'])
        df['load_ev'] = self.generate_ev_profile(config['ev_km'])
        df['pv_gen'] = self.generate_pv_profile(config['pv_kwp'])
        df['total_load'] = df['load_h0'] + df['load_hp'] + df['load_ev']
        df['net_load'] = df['total_load'] - df['pv_gen']
        return df

# --- MODUL 2: TARIF ENGINE ---
class TariffEngine:
    def __init__(self, tax_and_levies=0.18):
        self.tax_and_levies = tax_and_levies
        self.vat = 1.19
        
    def generate_synthetic_spot_prices(self, time_index):
        hour = time_index.hour.values
        base_price = 0.06
        variation = 0.04 * np.sin((hour - 2) * np.pi / 12)**2 
        pv_dip = np.where((hour >= 11) & (hour <= 15), -0.02, 0)
        spot_prices = base_price + variation + pv_dip
        return spot_prices + np.random.normal(0, 0.005, len(time_index))

    def get_static_tariff_details(self):
        return {'working_price': 0.32, 'base_price_year': 145.0}

    def get_dynamic_tariff_components(self, spot_prices, grid_fee_standard=0.10):
        service_fee = 0.015
        return (spot_prices + grid_fee_standard + self.tax_and_levies + service_fee) * self.vat

    def apply_14a_enwg(self, df, module=1, grid_fee_standard=0.10):
        if module == 1:
            return 150.0, df
        elif module == 2:
            df['reduction_14a_kwh'] = (grid_fee_standard * 0.60) * self.vat
            return 0, df
        return 0, df

    def get_imsys_cost(self, consumption):
        if consumption > 10000: return 50.0
        elif consumption > 6000: return 30.0
        else: return 20.0

# --- MODUL 3: ENERGY OPTIMIZER ---
class EnergyOptimizer:
    def __init__(self, battery_cap_kwh=10.0, battery_max_kw=5.0, battery_eff=0.95):
        self.cap = battery_cap_kwh
        self.max_kw = battery_max_kw
        self.eff = battery_eff

    def simulate_smart_system(self, df, use_dynamic_logic=False):
        soc = 0.0
        grid_import, grid_export, battery_soc_history = [], [], []
        
        if use_dynamic_logic:
            df = self._optimize_ev_charging(df)
        
        base_load = (df['load_h0'] + df['load_hp']).values
        ev_load = (df['load_ev_opt'] if 'load_ev_opt' in df.columns else df['load_ev']).values
        pv_gen = df['pv_gen'].values
        prices = df['dynamic_price_brutto'].values

        for i in range(len(df)):
            current_pv = pv_gen[i]
            current_load = base_load[i] + ev_load[i]
            current_price = prices[i]
            net_balance = current_pv - current_load
            
            day_start = (i // 24) * 24
            daily_price_threshold = np.percentile(prices[day_start:day_start+24], 25)

            grid_to_battery = 0
            if use_dynamic_logic and current_price <= daily_price_threshold and soc < (self.cap * 0.8):
                grid_to_battery = min(self.max_kw, self.cap - soc)
            
            if net_balance > 0:
                charge_amount = min(net_balance, self.max_kw, (self.cap - soc) / self.eff)
                soc += charge_amount * self.eff
                current_export = net_balance - charge_amount
                current_import = grid_to_battery
            else:
                needed = abs(net_balance)
                discharge_amount = min(needed, self.max_kw, soc * self.eff)
                soc -= (discharge_amount / self.eff)
                current_import = (needed - discharge_amount) + grid_to_battery
                current_export = 0
            
            grid_import.append(current_import)
            grid_export.append(current_export)
            battery_soc_history.append(soc)

        df['grid_import'] = grid_import
        df['grid_export'] = grid_export
        df['battery_soc'] = battery_soc_history
        return df

    def _optimize_ev_charging(self, df):
        df = df.copy()
        df['load_ev_opt'] = 0.0
        for day, group in df.groupby(df.index.date):
            daily_ev_energy = group['load_ev'].sum()
            if daily_ev_energy > 0:
                cheapest_hours = group['dynamic_price_brutto'].nsmallest(4).index
                df.loc[cheapest_hours, 'load_ev_opt'] = daily_ev_energy / 4
        return df

# --- MODUL 4: ECONOMIC CALCULATOR ---
class EconomicCalculator:
    def __init__(self, feed_in_tariff=0.08, vat=1.19):
        self.feed_in_tariff = feed_in_tariff
        self.vat = vat

    def calculate_annual_metrics(self, df_result, static_config, tariff_engine, enwg_module=1):
        total_consumption = (df_result['load_h0'] + df_result['load_hp'] + df_result['load_ev']).sum()
        total_import = df_result['grid_import'].sum()
        total_export = df_result['grid_export'].sum()
        
        cost_static = (total_import * static_config['working_price']) + static_config['base_price_year']
        cost_dynamic_work = (df_result['grid_import'] * df_result['dynamic_price_brutto']).sum()
        cost_dynamic_base = static_config['base_price_year'] + tariff_engine.get_imsys_cost(total_consumption)
        
        reduction_14a, _ = tariff_engine.apply_14a_enwg(df_result, module=enwg_module)
        if enwg_module == 2:
            reduction_14a = (df_result['load_hp'] + df_result['load_ev']).sum() * (0.10 * 0.60 * self.vat)
            
        total_cost_dynamic = cost_dynamic_work + cost_dynamic_base - reduction_14a
        
        metrics = {
            "Ersparnis [€/J]": round(cost_static - total_cost_dynamic, 2),
            "Ersparnis [%]": round(((cost_static - total_cost_dynamic) / cost_static) * 100, 1) if cost_static > 0 else 0,
            "Autarkiegrad [%]": round((1 - (total_import / total_consumption)) * 100, 1) if total_consumption > 0 else 0,
            "Eigenverbrauchsquote [%]": round((1 - (total_export / df_result['pv_gen'].sum())) * 100, 1) if df_result['pv_gen'].sum() > 0 else 0,
            "Kosten Statisch [€/J]": round(cost_static, 2),
            "Kosten Dynamisch [€/J]": round(total_cost_dynamic, 2),
            "Effektiver Preis Dynamisch [ct/kWh]": round((total_cost_dynamic / total_consumption)*100, 2) if total_consumption > 0 else 0,
            "Effektiver Preis Statisch [ct/kWh]": round((cost_static / total_consumption)*100, 2) if total_consumption > 0 else 0
        }
        return metrics

# --- MODUL 6: VISUALIZATION HELPERS ---
def plot_load_profile(df, date_range):
    mask = (df.index >= date_range[0]) & (df.index <= date_range[1])
    sub_df = df.loc[mask]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sub_df.index, y=sub_df['total_load'], name="Verbrauch", fill='tozeroy', line_color='#d32f2f'))
    fig.add_trace(go.Scatter(x=sub_df.index, y=sub_df['pv_gen'], name="PV-Erzeugung", fill='tozeroy', line_color='#fbc02d'))
    fig.add_trace(go.Scatter(x=sub_df.index, y=sub_df['grid_import'], name="Netzbezug", line=dict(dash='dash', color='#1976d2')))
    fig.update_layout(title="Lastgang vs. Erzeugung", template="plotly_white", margin=dict(l=20,r=20,t=40,b=20))
    return fig

def plot_cost_comparison(metrics):
    fig = px.bar(x=['Statisch', 'Dynamisch'], y=[metrics['Kosten Statisch [€/J]'], metrics['Kosten Dynamisch [€/J]']],
                 color=['Statisch', 'Dynamisch'], color_discrete_map={'Statisch': '#9e9e9e', 'Dynamisch': '#005eb8'},
                 title="Jahreskosten Vergleich (€)")
    return fig
'''
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
