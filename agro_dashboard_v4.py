# -*- coding: utf-8 -*-
"""
AGRO F66 Dashboard v4.0 - KORRIGIERTE VERSION
Mit Simple Login System - ALLE Spaltennamen geprüft!
TEIL 1 von 2: Imports bis Datenfilter
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

# ========================================
# PAGE CONFIG
# ========================================
st.set_page_config(
    page_title="AGRO F66 Dashboard",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# AUTHENTICATION
# ========================================
def check_credentials(username, password):
    """Simple authentication - Passwörter plain text für Demo"""
    users = {
        "tgerkens@colle.eu": {"password": "test123", "name": "Tobias Gerkens", "role": "superadmin", "niederlassungen": "Gesamt"},
        "thell@colle.eu": {"password": "test123", "name": "Theresa Hell", "role": "admin", "niederlassungen": "Augsburg, München, Stuttgart"},
        "ckuehner@colle.eu": {"password": "test123", "name": "Christian Kühner", "role": "admin", "niederlassungen": "Arnstadt, Halle, Leipzig"},
        "sschulz@colle.eu": {"password": "test123", "name": "Simon Schulz", "role": "admin", "niederlassungen": "Bremen, Hamburg, Hannover"},
        "augsburg": {"password": "test123", "name": "User Augsburg", "role": "user", "niederlassungen": "Augsburg"},
        "muenchen": {"password": "test123", "name": "User München", "role": "user", "niederlassungen": "München"},
        "stuttgart": {"password": "test123", "name": "User Stuttgart", "role": "user", "niederlassungen": "Stuttgart"},
        "arnstadt": {"password": "test123", "name": "User Arnstadt", "role": "user", "niederlassungen": "Arnstadt"},
        "halle": {"password": "test123", "name": "User Halle", "role": "user", "niederlassungen": "Halle"},
        "leipzig": {"password": "test123", "name": "User Leipzig", "role": "user", "niederlassungen": "Leipzig"},
        "bremen": {"password": "test123", "name": "User Bremen", "role": "user", "niederlassungen": "Bremen"},
        "hamburg": {"password": "test123", "name": "User Hamburg", "role": "user", "niederlassungen": "Hamburg"},
        "hannover": {"password": "test123", "name": "User Hannover", "role": "user", "niederlassungen": "Hannover"},
        "kassel": {"password": "test123", "name": "User Kassel", "role": "user", "niederlassungen": "Kassel"},
        "koeln": {"password": "test123", "name": "User Köln", "role": "user", "niederlassungen": "Köln"}
    }
    
    if username in users and users[username]["password"] == password:
        return users[username]
    return None

# Login Screen
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🚜 AGRO F66 Dashboard")
    st.subheader("Bitte anmelden")
    
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")
    
    if st.button("Anmelden"):
        user_data = check_credentials(username, password)
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user = user_data
            st.rerun()
        else:
            st.error("❌ Ungültige Anmeldedaten!")
    st.stop()

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
# HEADER & USER INFO
# ========================================
col1, col2, col3 = st.columns([2, 3, 1])
with col1:
    st.title("🚜 AGRO F66 Dashboard")
with col2:
    st.markdown(f"### 👤 {st.session_state.user['name']}")
with col3:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ========================================
# SIDEBAR FILTER
# ========================================
st.sidebar.header("🎯 Filter")

# Niederlassung Filter basierend auf User-Rolle
user_role = st.session_state.user['role']
user_niederlassungen = st.session_state.user['niederlassungen']

if user_role == 'superadmin':
    # SuperAdmin sieht alle
    niederlassungen_list = ['Gesamt'] + sorted(df['Master NL'].unique().tolist())
else:
    # Andere User sehen nur ihre zugewiesenen Niederlassungen
    if user_niederlassungen == 'Gesamt':
        niederlassungen_list = ['Gesamt'] + sorted(df['Master NL'].unique().tolist())
    else:
        allowed = [nl.strip() for nl in user_niederlassungen.split(',')]
        niederlassungen_list = allowed

master_nl_filter = st.sidebar.selectbox(
    "Niederlassung",
    niederlassungen_list,
    index=0
)

# Daten filtern
if master_nl_filter == "Gesamt":
    df_base = df.copy()
else:
    df_base = df[df['Master NL'] == master_nl_filter].copy()

# Filter: Nur Maschinen mit Aktivität
df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsaetze YTD'] != 0)]

# Debug Info
with st.sidebar.expander("🔍 Debug Info"):
    st.write(f"**Gefilterte Maschinen:** {len(df_base)}")
    st.write(f"**Verfügbare Spalten:** {list(df_base.columns)}")

st.sidebar.markdown("---")
st.sidebar.caption("📊 Version 4.0 | Simple Login")

# ========================================
# ========================================
# FORTSETZUNG VON TEIL 1
# Füge diesen Code DIREKT nach Teil 1 ein!
# ========================================

# ========================================
# ÜBERSICHT (KPIs)
# ========================================
st.header("📊 Übersicht")

total_kosten = df_base['Kosten YTD'].sum()
total_umsatz = df_base['Umsaetze YTD'].sum()
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

months = ['Jan', 'Feb', 'Mrz', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
kosten_monthly = []
umsatz_monthly = []
db_monthly = []

for month in months:
    kosten_col = f'Kosten {month}'
    umsatz_col = f'Umsaetze {month}'
    
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
        
        top_display = top_10[['VH-nr.', 'Code', 'Master NL', 'Kosten YTD', 'Umsaetze YTD', 'DB YTD', 'Marge YTD %']].copy()
        top_display['Kosten YTD'] = top_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
        top_display['Umsaetze YTD'] = top_display['Umsaetze YTD'].apply(lambda x: f"€ {x:,.2f}")
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
                x=row['Umsaetze YTD'],
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
st.caption("🚜 AGRO F66 Dashboard v4.0 | Simple Login | 📊 Alle Daten in Echtzeit")
