# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide")

st.title("AGRO F66 Maschinen Dashboard")

uploaded_file = st.file_uploader("Dashboard_Master.xlsx hochladen", type=['xlsx'])

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

if uploaded_file is None:
    st.info("Bitte lade die Dashboard_Master.xlsx hoch")
    st.stop()

df = load_data(uploaded_file)

# Monate extrahieren
cost_cols = [col for col in df.columns if col.startswith('Kosten ') and 'YTD' not in col]
months = [col.replace('Kosten ', '') for col in cost_cols]

# SIDEBAR FILTER
st.sidebar.header("Filter")

# Niederlassungsfilter
if 'Niederlassung' in df.columns:
    nl_options = ['Gesamt'] + sorted([nl for nl in df['Niederlassung'].unique() if nl != 'Unbekannt'])
    selected_nl = st.sidebar.selectbox("Niederlassung", nl_options)
else:
    selected_nl = 'Gesamt'
    st.sidebar.warning("Keine Niederlassungs-Spalte gefunden")

# YTD Filter
show_active = st.sidebar.checkbox("Nur Maschinen mit YTD-Aktivitaet", value=True)

# Daten filtern
df_filtered = df.copy()
if show_active:
    df_filtered = df_filtered[(df_filtered['Kosten YTD'] != 0) | (df_filtered['Umsätze YTD'] != 0)]

if selected_nl != 'Gesamt' and 'Niederlassung' in df.columns:
    df_filtered = df_filtered[df_filtered['Niederlassung'] == selected_nl]

st.sidebar.metric("Gefilterte Maschinen", f"{len(df_filtered):,}")

# DATEN VORBEREITEN
monthly_data = []
for month in months:
    cost_col = f'Kosten {month}'
    rev_col = f'Umsätze {month}'
    db_col = f'DB {month}'
    
    monthly_data.append({
        'Monat': month,
        'Kosten': df_filtered[cost_col].sum(),
        'Umsaetze': df_filtered[rev_col].sum(),
        'DB': df_filtered[db_col].sum()
    })

df_monthly = pd.DataFrame(monthly_data)
df_monthly['Marge %'] = (df_monthly['DB'] / df_monthly['Umsaetze'] * 100).fillna(0)

# YTD Werte
ytd_kosten = df_filtered['Kosten YTD'].sum()
ytd_umsaetze = df_filtered['Umsätze YTD'].sum()
ytd_db = df_filtered['DB YTD'].sum()
ytd_marge = (ytd_db / ytd_umsaetze * 100) if ytd_umsaetze != 0 else 0

# HEADER KPIs
st.subheader(f"Übersicht: {selected_nl}")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("YTD Kosten", f"€ {ytd_kosten:,.0f}")
with col2:
    st.metric("YTD Umsätze", f"€ {ytd_umsaetze:,.0f}")
with col3:
    st.metric("YTD Deckungsbeitrag", f"€ {ytd_db:,.0f}", 
              delta=f"{ytd_marge:.1f}%" if ytd_marge >= 0 else f"{ytd_marge:.1f}%")
with col4:
    st.metric("YTD Marge", f"{ytd_marge:.1f}%")

# MONATLICHE ENTWICKLUNG
st.subheader("Monatliche Entwicklung")

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Umsätze & Kosten pro Monat', 'Deckungsbeitrag pro Monat (€)', 
                    'Deckungsbeitrag pro Monat (%)', 'Kumulative Entwicklung'),
    specs=[[{"secondary_y": False}, {"secondary_y": False}],
           [{"secondary_y": False}, {"secondary_y": False}]]
)

# Chart 1: Umsätze & Kosten
fig.add_trace(go.Bar(name='Umsätze', x=df_monthly['Monat'], y=df_monthly['Umsaetze'], 
                     marker_color='#22c55e', text=df_monthly['Umsaetze'].apply(lambda x: f'€{x/1000:.0f}k'),
                     textposition='outside'), row=1, col=1)
fig.add_trace(go.Bar(name='Kosten', x=df_monthly['Monat'], y=df_monthly['Kosten'], 
                     marker_color='#ef4444', text=df_monthly['Kosten'].apply(lambda x: f'€{x/1000:.0f}k'),
                     textposition='outside'), row=1, col=1)

# Chart 2: DB in Euro
colors_db = ['#22c55e' if x >= 0 else '#ef4444' for x in df_monthly['DB']]
fig.add_trace(go.Bar(name='DB (€)', x=df_monthly['Monat'], y=df_monthly['DB'], 
                     marker_color=colors_db, showlegend=False,
                     text=df_monthly['DB'].apply(lambda x: f'€{x/1000:.0f}k'),
                     textposition='outside'), row=1, col=2)

# Chart 3: Marge in %
colors_marge = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_monthly['Marge %']]
fig.add_trace(go.Bar(name='Marge %', x=df_monthly['Monat'], y=df_monthly['Marge %'], 
                     marker_color=colors_marge, showlegend=False,
                     text=df_monthly['Marge %'].apply(lambda x: f'{x:.1f}%'),
                     textposition='outside'), row=2, col=1)
fig.add_hline(y=10, line_dash="dash", line_color="red", row=2, col=1, 
              annotation_text="Ziel: 10%", annotation_position="right")

# Chart 4: Kumulative Entwicklung
df_monthly['Kum_Umsaetze'] = df_monthly['Umsaetze'].cumsum()
df_monthly['Kum_DB'] = df_monthly['DB'].cumsum()
fig.add_trace(go.Scatter(name='Kum. Umsätze', x=df_monthly['Monat'], y=df_monthly['Kum_Umsaetze'],
                         mode='lines+markers', line=dict(color='#22c55e', width=3)), row=2, col=2)
fig.add_trace(go.Scatter(name='Kum. DB', x=df_monthly['Monat'], y=df_monthly['Kum_DB'],
                         mode='lines+markers', line=dict(color='#3b82f6', width=3)), row=2, col=2)

fig.update_layout(height=800, showlegend=True, barmode='group')
fig.update_xaxes(title_text="Monat", row=2, col=1)
fig.update_xaxes(title_text="Monat", row=2, col=2)
fig.update_yaxes(title_text="Euro (€)", row=1, col=1)
fig.update_yaxes(title_text="Euro (€)", row=1, col=2)
fig.update_yaxes(title_text="Marge (%)", row=2, col=1)
fig.update_yaxes(title_text="Euro (€)", row=2, col=2)

st.plotly_chart(fig, use_container_width=True)

# TOP & WORST PERFORMING MASCHINEN
st.subheader("Top & Worst Performing Maschinen (YTD)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 10 nach Umsatz")
    top_10_umsatz = df_filtered.nlargest(10, 'Umsätze YTD')[['Code', 'Omschrijving', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']]
    top_10_umsatz['Umsätze YTD'] = top_10_umsatz['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_10_umsatz['DB YTD'] = top_10_umsatz['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_10_umsatz['Marge YTD %'] = top_10_umsatz['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(top_10_umsatz, use_container_width=True, hide_index=True)
    
    # Chart
    top_10_chart = df_filtered.nlargest(10, 'Umsätze YTD')
    fig_top = go.Figure(go.Bar(
        x=top_10_chart['Umsätze YTD'],
        y=top_10_chart['Code'].astype(str),
        orientation='h',
        marker_color='#22c55e',
        text=top_10_chart['Umsätze YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='outside'
    ))
    fig_top.update_layout(height=400, xaxis_title='Umsatz YTD (€)', yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_top, use_container_width=True)

with col2:
    st.markdown("### Worst 10 nach DB")
    worst_10_db = df_filtered.nsmallest(10, 'DB YTD')[['Code', 'Omschrijving', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']]
    worst_10_db['Umsätze YTD'] = worst_10_db['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_10_db['DB YTD'] = worst_10_db['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_10_db['Marge YTD %'] = worst_10_db['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(worst_10_db, use_container_width=True, hide_index=True)
    
    # Chart
    worst_10_chart = df_filtered.nsmallest(10, 'DB YTD')
    fig_worst = go.Figure(go.Bar(
        x=worst_10_chart['DB YTD'],
        y=worst_10_chart['Code'].astype(str),
        orientation='h',
        marker_color='#ef4444',
        text=worst_10_chart['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='outside'
    ))
    fig_worst.update_layout(height=400, xaxis_title='DB YTD (€)', yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_worst, use_container_width=True)

# MONATSTABELLE
st.subheader("Detaillierte Monatsdaten")
st.dataframe(df_monthly.style.format({
    'Kosten': '€ {:,.0f}',
    'Umsaetze': '€ {:,.0f}',
    'DB': '€ {:,.0f}',
    'Marge %': '{:.1f}%'
}), use_container_width=True)

# EXPORT
st.download_button(
    label="Export als CSV",
    data=df_monthly.to_csv(index=False).encode('utf-8'),
    file_name=f'dashboard_export_{selected_nl}_{pd.Timestamp.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)
