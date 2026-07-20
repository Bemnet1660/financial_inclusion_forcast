import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page config
st.set_page_config(page_title="Ethiopia Financial Inclusion Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('data/enriched/ethiopia_fi_unified_data_enriched.csv')
    df['observation_date'] = pd.to_datetime(df['observation_date'], errors='coerce')
    return df

df = load_data()
obs = df[df['record_type'] == 'observation']
events = df[df['record_type'] == 'event']

# --- Sidebar ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Trends", "Forecasts"])

# --- HELPER: Get latest value ---
def get_latest(indicator):
    sub = obs[obs['indicator_code'] == indicator].sort_values('observation_date')
    if not sub.empty:
        return sub.iloc[-1]['value_numeric'], sub.iloc[-1]['observation_date'].year
    return None, None

# --- PAGE 1: OVERVIEW ---
if page == "Overview":
    st.title("📊 Ethiopia Financial Inclusion Overview")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    acc_val, acc_year = get_latest('ACC_OWNERSHIP')
    mm_val, mm_year = get_latest('ACC_MM_ACCOUNT')
    dig_val, dig_year = get_latest('USG_DIGITAL_PAYMENT')
    
    with col1:
        st.metric("Account Ownership", f"{acc_val:.1f}%", f"as of {acc_year}")
    with col2:
        st.metric("Mobile Money Accounts", f"{mm_val:.2f}%", f"as of {mm_year}")
    with col3:
        st.metric("Digital Payment Usage", f"{dig_val:.1f}%", f"as of {dig_year}")
    with col4:
        st.metric("Total Events Tracked", len(events))
    
    st.markdown("### Key Milestones")
    st.dataframe(events[['observation_date', 'indicator', 'category']].sort_values('observation_date', ascending=False).head(5))

# --- PAGE 2: TRENDS ---
elif page == "Trends":
    st.title("📈 Indicator Trends")
    
    indicators = obs['indicator_code'].unique()
    selected = st.multiselect("Select Indicators", indicators, default=['ACC_OWNERSHIP', 'USG_DIGITAL_PAYMENT'])
    
    if selected:
        fig = go.Figure()
        for ind in selected:
            sub = obs[obs['indicator_code'] == ind].sort_values('observation_date')
            fig.add_trace(go.Scatter(
                x=sub['observation_date'],
                y=sub['value_numeric'],
                mode='lines+markers',
                name=ind
            ))
        # Add events as vertical lines
        for _, ev in events.iterrows():
            fig.add_vline(x=ev['observation_date'], line_dash="dash", line_color="red", opacity=0.5)
            fig.add_annotation(x=ev['observation_date'], y=0.95, yref="paper", text=ev['indicator'][:15], 
                               showarrow=False, angle=45, font=dict(size=8))
        
        fig.update_layout(title="Time Series with Events", xaxis_title="Date", yaxis_title="Value")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Correlation Heatmap")
    obs_wide = obs.pivot(index='observation_date', columns='indicator_code', values='value_numeric')
    corr = obs_wide.corr()
    fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
    st.plotly_chart(fig_corr, use_container_width=True)

# --- PAGE 3: FORECASTS ---
else:
    st.title("🔮 Forecasts (2025-2027)")
    
    # Load forecast data (or compute on the fly)
    # For demo, we generate forecasts here using simple logic
    @st.cache_data
    def generate_forecast():
        years = [2025, 2026, 2027]
        # Based on Task 4 outputs
        acc_forecast = [50.0, 50.8, 51.5]
        acc_lower = [47.0, 48.0, 49.0]
        acc_upper = [53.0, 54.0, 55.0]
        
        usage_base = [38.0, 39.5, 40.5]
      usage_scenario = [38.0, 41.5, 43.0]  # with event boost in 2026-27
        usage_lower = [35.0, 37.0, 38.0]
        usage_upper = [41.0, 43.0, 44.0]
        
        return pd.DataFrame({
            'year': years,
            'ACC_OWNERSHIP': acc_forecast,
            'ACC_lower': acc_lower,
            'ACC_upper': acc_upper,
            'USG_DIGITAL_PAYMENT_base': usage_base,
            'USG_DIGITAL_PAYMENT_scenario': usage_scenario,
            'USG_lower': usage_lower,
            'USG_upper': usage_upper
        })
    
    forecast_df = generate_forecast()
    
    scenario = st.radio("Scenario", ["Baseline", "With Events"])
    
    fig = go.Figure()
    
    # Historical
    acc_hist = obs[obs['indicator_code'] == 'ACC_OWNERSHIP'].sort_values('observation_date')
    usage_hist = obs[obs['indicator_code'] == 'USG_DIGITAL_PAYMENT'].sort_values('observation_date')
    
    fig.add_trace(go.Scatter(x=acc_hist['observation_date'], y=acc_hist['value_numeric'], 
                             mode='lines+markers', name='Access (Historical)', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=usage_hist['observation_date'], y=usage_hist['value_numeric'], 
                             mode='lines+markers', name='Usage (Historical)', line=dict(color='green')))
    
    # Forecasts
    if scenario == "Baseline":
        fig.add_trace(go.Scatter(x=forecast_df['year'], y=forecast_df['ACC_OWNERSHIP'], 
                                 mode='lines+markers', name='Access Forecast', line=dict(color='blue', dash='dash')))
        fig.add_trace(go.Scatter(x=forecast_df['year'], y=forecast_df['USG_DIGITAL_PAYMENT_base'], 
                                 mode='lines+markers', name='Usage Forecast', line=dict(color='green', dash='dash')))
        # CIs for Usage
        fig.add_trace(go.Scatter(x=list(forecast_df['year']) + list(forecast_df['year'][::-1]), 
                                 y=list(forecast_df['USG_upper']) + list(forecast_df['USG_lower'][::-1]),
                                 fill='toself', fillcolor='rgba(0,255,0,0.2)', line=dict(color='rgba(255,255,255,0)'),
                                 name='Usage CI'))
    else:
        fig.add_trace(go.Scatter(x=forecast_df['year'], y=forecast_df['ACC_OWNERSHIP'], 
                                 mode='lines+markers', name='Access Forecast (Base)', line=dict(color='blue', dash='dash')))
        fig.add_trace(go.Scatter(x=forecast_df['year'], y=forecast_df['USG_DIGITAL_PAYMENT_scenario'], 
                                 mode='lines+markers', name='Usage Forecast (with Events)', line=dict(color='orange', dash='dot')))
        # CIs for Usage scenario
        fig.add_trace(go.Scatter(x=list(forecast_df['year']) + list(forecast_df['year'][::-1]), 
                                 y=list(forecast_df['USG_upper'] + 2.5) + list(forecast_df['USG_lower'][::-1]),
                                 fill='toself', fillcolor='rgba(255,165,0,0.2)', line=dict(color='rgba(255,255,255,0)'),
                                 name='Usage CI (Scenario)'))
    
    fig.update_layout(title=f"Forecast ({scenario} Scenario)", xaxis_title="Year", yaxis_title="Percentage")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Forecast Table")
    st.dataframe(forecast_df.style.format("{:.1f}"))
    
    # Download button
    csv = forecast_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Forecast CSV", data=csv, file_name="forecast_2025_2027.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.info("Data source: Global Findex, NBE, GSMA, Operator reports")
      
