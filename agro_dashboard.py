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

# Prüfe ob Niederlassungs-Spalte existiert
has_nl = 'Niederlassung' in df.columns

if has_nl:
    nl_options = ['Gesamt'] + sorted([nl for nl in df['Niederlassung'].unique() if nl != 'Unbekannt'])
else:
    nl_options = ['Gesamt']

# Globaler YTD Filter in Sidebar
st.sidebar.header("Globale Filter")
show_active = st.sidebar.checkbox("Nur Maschinen mit YTD-Aktivitaet", value=True)

# Basis-Filterung
df_base = df.copy()
if show_active:
    df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]

st.sidebar.metric("Basis-Maschinen", f"{len(df_base):,}")

# === ÜBERSICHT SEKTION ===
st.header("Übersicht")
col_filter, col_space = st.columns([1, 3])
with col_filter:
    nl_overview = st.selectbox("NL-Filter Übersicht", nl_options, key='nl_overview')

# Übersicht Daten filtern
df_overview = df_base.copy()
if nl_overview != 'Gesamt' and has_nl:
    df_overview = df_overview[df_overview['Niederlassung'] == nl_overview]

ytd_kosten = df_overview['Kosten YTD'].sum()
ytd_umsaetze = df_overview['Umsätze YTD'].sum()
ytd_db = df_overview['DB YTD'].sum()
ytd_marge = (ytd_db / ytd_umsaetze * 100) if ytd_umsaetze != 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("YTD Kosten", f"€ {ytd_kosten:,.0f}")
with col2:
    st.metric("YTD Umsätze", f"€ {ytd_umsaetze:,.0f}")
with col3:
    st.metric("YTD Deckungsbeitrag", f"€ {ytd_db:,.0f}", delta=f"{ytd_marge:.1f}%")
with col4:
    st.metric("YTD Marge", f"{ytd_marge:.1f}%")

# === MONATLICHE ENTWICKLUNG ===
st.header("Monatliche Entwicklung")
col_filter2, col_space2 = st.columns([1, 3])
with col_filter2:
    nl_monthly = st.selectbox("NL-Filter Monatsdaten", nl_options, key='nl_monthly')

# Monatliche Daten filtern
df_monthly_base = df_base.copy()
if nl_monthly != 'Gesamt' and has_nl:
    df_monthly_base = df_monthly_base[df_monthly_base['Niederlassung'] == nl_monthly]

monthly_data = []
for month in months:
    cost_col = f'Kosten {month}'
    rev_col = f'Umsätze {month}'
    db_col = f'DB {month}'
    
    monthly_data.append({
        'Monat': month,
        'Kosten': df_monthly_base[cost_col].sum(),
        'Umsaetze': df_monthly_base[rev_col].sum(),
        'DB': df_monthly_base[db_col].sum()
    })

df_monthly = pd.DataFrame(monthly_data)
df_monthly['Marge %'] = (df_monthly['DB'] / df_monthly['Umsaetze'] * 100).fillna(0)

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

# === TOP PERFORMER ===
st.header("Top Performing Maschinen (YTD)")
col_filter3, col_space3 = st.columns([1, 3])
with col_filter3:
    nl_top = st.selectbox("NL-Filter Top Performer", nl_options, key='nl_top')

df_top = df_base.copy()
if nl_top != 'Gesamt' and has_nl:
    df_top = df_top[df_top['Niederlassung'] == nl_top]

top_10_umsatz = df_top.nlargest(10, 'Umsätze YTD')[['Code', 'Omschrijving', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']]

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### Tabelle")
    top_display = top_10_umsatz.copy()
    top_display['Umsätze YTD'] = top_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['DB YTD'] = top_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['Marge YTD %'] = top_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(top_display, use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### Chart")
    fig_top = go.Figure(go.Bar(
        x=top_10_umsatz['Umsätze YTD'],
        y=top_10_umsatz['Code'].astype(str),
        orientation='h',
        marker_color='#22c55e',
        text=top_10_umsatz['Umsätze YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='outside'
    ))
    fig_top.update_layout(height=400, xaxis_title='Umsatz YTD (€)', yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_top, use_container_width=True)

# === WORST PERFORMER ===
st.header("Worst Performing Maschinen (YTD)")
col_filter4, col_space4 = st.columns([1, 3])
with col_filter4:
    nl_worst = st.selectbox("NL-Filter Worst Performer", nl_options, key='nl_worst')

df_worst = df_base.copy()
if nl_worst != 'Gesamt' and has_nl:
    df_worst = df_worst[df_worst['Niederlassung'] == nl_worst]

worst_10_db = df_worst.nsmallest(10, 'DB YTD')[['Code', 'Omschrijving', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']]

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### Tabelle")
    worst_display = worst_10_db.copy()
    worst_display['Umsätze YTD'] = worst_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['DB YTD'] = worst_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['Marge YTD %'] = worst_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(worst_display, use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### Chart")
    fig_worst = go.Figure(go.Bar(
        x=worst_10_db['DB YTD'],
        y=worst_10_db['Code'].astype(str),
        orientation='h',
        marker_color='#ef4444',
        text=worst_10_db['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='outside'
    ))
    fig_worst.update_layout(height=400, xaxis_title='DB YTD (€)', yaxis=dict(autorange='reversed'))
    st.plotly_chart(fig_worst, use_container_width=True)

# === MONATSTABELLE ===
st.header("Detaillierte Monatsdaten")
col_filter5, col_space5 = st.columns([1, 3])
with col_filter5:
    nl_table = st.selectbox("NL-Filter Monatstabelle", nl_options, key='nl_table')

df_table_base = df_base.copy()
if nl_table != 'Gesamt' and has_nl:
    df_table_base = df_table_base[df_table_base['Niederlassung'] == nl_table]

monthly_table = []
for month in months:
    cost_col = f'Kosten {month}'
    rev_col = f'Umsätze {month}'
    db_col = f'DB {month}'
    
    monthly_table.append({
        'Monat': month,
        'Kosten': df_table_base[cost_col].sum(),
        'Umsaetze': df_table_base[rev_col].sum(),
        'DB': df_table_base[db_col].sum()
    })

df_table = pd.DataFrame(monthly_table)
df_table['Marge %'] = (df_table['DB'] / df_table['Umsaetze'] * 100).fillna(0)

st.dataframe(df_table.style.format({
    'Kosten': '€ {:,.0f}',
    'Umsaetze': '€ {:,.0f}',
    'DB': '€ {:,.0f}',
    'Marge %': '{:.1f}%'
}), use_container_width=True)

# EXPORT
st.download_button(
    label="Export als CSV",
    data=df_table.to_csv(index=False).encode('utf-8'),
    file_name=f'dashboard_export_{nl_table}_{pd.Timestamp.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)
