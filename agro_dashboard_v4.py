# -*- coding: utf-8 -*-
"""
AGRO F66 Dashboard v4.0 - KORRIGIERTE VERSION
Mit auth_simple.py Integration + ECHTE Spaltennamen aus Excel
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from auth_simple import SimpleAuth, show_login_page, show_user_info

# ========================================
# PAGE CONFIG
# ========================================
st.set_page_config(
    page_title="AGRO F66 Dashboard Umsätze pro Maschine",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# AUTHENTICATION
# ========================================
auth = SimpleAuth()

# Login-Check
if not auth.is_authenticated():
    show_login_page()
    st.stop()

# User-Info holen
current_user = auth.get_current_user()

# ========================================
# DATEN LADEN
# ========================================
@st.cache_data
def load_data():
    """Lädt Excel-Daten"""
    try:
        df = pd.read_excel('Dashboard_Master_DE_v2.xlsx')
        return df
    except Exception as e:
        st.error(f"❌ Fehler beim Laden: {e}")
        return None

df = load_data()

if df is None:
    st.stop()

# ========================================
# HEADER
# ========================================
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    st.title("🚜 AGRO F66 Dashboard")
with col2:
    st.markdown(f"### 👤 {current_user['name']}")
with col3:
    if st.button("🚪 Logout"):
        auth.logout()
        st.rerun()

# ========================================
# SIDEBAR FILTER
# ========================================
st.sidebar.header("🎯 Filter")

# User-Niederlassungen holen
user_niederlassungen = current_user['niederlassungen']

# Filter-Optionen basierend auf Rolle
if user_niederlassungen == ['alle']:
    # SuperAdmin sieht alle
    niederlassungen_list = ['Gesamt'] + sorted(df['Niederlassung'].unique().tolist())
else:
    # Andere: nur zugewiesene NL
    niederlassungen_list = ['Gesamt'] + user_niederlassungen

master_nl_filter = st.sidebar.selectbox(
    "Niederlassung",
    niederlassungen_list,
    index=0
)

# Daten filtern
if master_nl_filter == "Gesamt":
    if user_niederlassungen == ['alle']:
        df_base = df.copy()
    else:
        # Admin/User: nur ihre Niederlassungen
        df_base = df[df['Niederlassung'].isin(user_niederlassungen)].copy()
else:
    df_base = df[df['Niederlassung'] == master_nl_filter].copy()

# Filter: Nur Maschinen mit Aktivität
df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]

# User-Info in Sidebar
show_user_info()

# Debug Info
with st.sidebar.expander("🔍 Debug Info"):
    st.write(f"**Gefilterte Maschinen:** {len(df_base)}")
    st.write(f"**Niederlassungen:** {user_niederlassungen}")

st.sidebar.markdown("---")
st.sidebar.caption("📊 Version 4.0 | Simple Auth")

# ========================================
# ÜBERSICHT (KPIs)
# ========================================
st.header("📊 Übersicht")

total_kosten = df_base['Kosten YTD'].sum()
total_umsatz = df_base['Umsätze YTD'].sum()
total_db = df_base['DB YTD'].sum()
marge_prozent = (total_db / total_umsatz * 100) if total_umsatz != 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 Kosten YTD", f"€ {total_kosten:,.0f}")
with col2:
    st.metric("💵 Umsätze YTD", f"€ {total_umsatz:,.0f}")
with col3:
    st.metric("💎 Deckungsbeitrag YTD", f"€ {total_db:,.0f}")
with col4:
    st.metric("📈 Marge YTD", f"{marge_prozent:.1f}%")

st.markdown("---")

# ========================================
# MONATLICHE ENTWICKLUNG
# ========================================
st.header("📅 Monatliche Entwicklung")

months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
kosten_monthly = []
umsatz_monthly = []
db_monthly = []

for month in months:
    kosten_col = f'Kosten {month} 25'
    umsatz_col = f'Umsätze {month} 25'
    
    if kosten_col in df_base.columns and umsatz_col in df_base.columns:
        kosten = df_base[kosten_col].sum()
        umsatz = df_base[umsatz_col].sum()
        db = umsatz - kosten
        
        kosten_monthly.append(kosten)
        umsatz_monthly.append(umsatz)
        db_monthly.append(db)
    else:
        kosten_monthly.append(0)
        umsatz_monthly.append(0)
        db_monthly.append(0)

fig_monthly = go.Figure()
fig_monthly.add_trace(go.Bar(name='Kosten', x=months, y=kosten_monthly, marker_color='#ef4444'))
fig_monthly.add_trace(go.Bar(name='Umsätze', x=months, y=umsatz_monthly, marker_color='#22c55e'))
fig_monthly.add_trace(go.Scatter(name='DB', x=months, y=db_monthly, mode='lines+markers', 
                                  line=dict(color='#3b82f6', width=3), marker=dict(size=8)))

fig_monthly.update_layout(
    barmode='group',
    height=400,
    xaxis_title='Monat',
    yaxis_title='Euro (€)',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

st.plotly_chart(fig_monthly, use_container_width=True)

st.markdown("---")

# ========================================
# TOP 10 PERFORMER
# ========================================
st.header("🏆 Top 10 Maschinen (nach DB)")

df_top = df_base[df_base['DB YTD'] > 0].copy()

if len(df_top) >= 10:
    top_10 = df_top.nlargest(10, 'DB YTD')
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Tabelle")
        
        top_display = top_10[['VH-nr.', 'Code', 'Niederlassung', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()
        top_display['Kosten YTD'] = top_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
        top_display['Umsätze YTD'] = top_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
        top_display['DB YTD'] = top_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
        top_display['Marge YTD %'] = top_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(top_display, use_container_width=True, hide_index=True, height=400)
    
    with col2:
        st.subheader("📊 Chart")
        
        fig_top = go.Figure()
        
        y_labels = top_10['VH-nr.'].astype(str) + ' | ' + top_10['Code'].astype(str)
        
        fig_top.add_trace(go.Bar(
            name='Kosten',
            y=y_labels,
            x=top_10['Kosten YTD'],
            orientation='h',
            marker_color='#ef4444',
            text=top_10['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
            textposition='inside'
        ))
        
        fig_top.add_trace(go.Bar(
            name='DB',
            y=y_labels,
            x=top_10['DB YTD'],
            orientation='h',
            marker_color='#22c55e',
            text=top_10['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
            textposition='inside'
        ))
        
        # Marge Annotations
        for idx, row in top_10.iterrows():
            y_label = str(row['VH-nr.']) + ' | ' + str(row['Code'])
            fig_top.add_annotation(
                x=row['Umsätze YTD'],
                y=y_label,
                text=f"{row['Marge YTD %']:.1f}%",
                showarrow=False,
                xanchor='left',
                xshift=5,
                font=dict(size=12, color='#059669' if row['Marge YTD %'] >= 10 else '#d97706')
            )
        
        fig_top.update_layout(
            barmode='stack',
            height=400,
            xaxis_title='Euro (€)',
            yaxis=dict(autorange='reversed'),
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info(f"⚠️ Nicht genug Maschinen mit positivem DB ({len(df_top)} gefunden)")

st.markdown("---")

# ========================================
# FOOTER
# ========================================
st.caption("🚜 Dashboard v4.0 | Simple Auth | 📊 ")
