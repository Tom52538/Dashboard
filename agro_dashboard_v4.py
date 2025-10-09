"""
AGRO F66 Dashboard v4.0
Mit Username/Passwort Login (Simple Auth)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from auth_simple import SimpleAuth, show_login_page, show_user_info

# Seiten-Config
st.set_page_config(
    page_title="AGRO F66 Dashboard",
    page_icon="🚜",
    layout="wide"
)

# Auth-Instanz
auth = SimpleAuth()

# Login-Check
if not auth.is_authenticated():
    show_login_page()
    st.stop()

# User ist eingeloggt - zeige Dashboard
user = auth.get_current_user()

# Sidebar mit User-Info
show_user_info()

# Header
st.title("🚜 AGRO F66 Maschinen Dashboard")
st.markdown(f"Willkommen, **{user['name']}**!")

# Daten laden
@st.cache_data
def load_data():
    """Lade Excel-Daten"""
    try:
        df = pd.read_excel('Dashboard_Master_DE_v2.xlsx')
        return df
    except FileNotFoundError:
        st.error("❌ Datei 'Dashboard_Master_DE_v2.xlsx' nicht gefunden!")
        return None

df = load_data()

if df is None:
    st.stop()

# Filter nach Niederlassung (basierend auf User-Rechten)
user_niederlassungen = user['niederlassungen']

if user_niederlassungen != ['alle']:
    # Filter nur auf User-Niederlassungen
    df = df[df['Niederlassung'].isin(user_niederlassungen)]
    st.info(f"📍 Gefiltert auf: {', '.join(user_niederlassungen)}")

# Sidebar-Filter
with st.sidebar:
    st.markdown("---")
    st.subheader("🎯 Filter")
    
    # Niederlassung-Filter (nur für SuperAdmin/Admin)
    if user_niederlassungen == ['alle']:
        available_nl = ['Alle'] + sorted(df['Niederlassung'].dropna().unique().tolist())
    else:
        available_nl = ['Alle'] + sorted(user_niederlassungen)
    
    selected_nl = st.selectbox(
        "Niederlassung",
        options=available_nl,
        index=0
    )
    
    if selected_nl != 'Alle':
        df = df[df['Niederlassung'] == selected_nl]

# KPIs
st.markdown("---")
st.subheader("📊 Übersicht")

col1, col2, col3, col4 = st.columns(4)

total_kosten = df['Kosten YTD'].sum()
total_umsatz = df['Umsätze YTD'].sum()
total_db = df['DB YTD'].sum()
marge = (total_db / total_umsatz * 100) if total_umsatz != 0 else 0

with col1:
    st.metric(
        label="💰 Kosten YTD",
        value=f"€ {total_kosten:,.0f}"
    )

with col2:
    st.metric(
        label="💵 Umsätze YTD",
        value=f"€ {total_umsatz:,.0f}"
    )

with col3:
    st.metric(
        label="💎 DB YTD",
        value=f"€ {total_db:,.0f}"
    )

with col4:
    st.metric(
        label="📈 Marge",
        value=f"{marge:.1f}%"
    )

# Monatliche Entwicklung
st.markdown("---")
st.subheader("📈 Monatliche Entwicklung")

months = ['Jan 25', 'Feb 25', 'Mar 25', 'Apr 25', 'Mai 25', 'Jun 25', 
          'Jul 25', 'Aug 25', 'Sep 25']

monthly_kosten = []
monthly_umsatz = []

for month in months:
    kosten_col = f'Kosten {month}'
    umsatz_col = f'Umsätze {month}'
    
    if kosten_col in df.columns and umsatz_col in df.columns:
        monthly_kosten.append(df[kosten_col].sum())
        monthly_umsatz.append(df[umsatz_col].sum())
    else:
        monthly_kosten.append(0)
        monthly_umsatz.append(0)

# Chart
fig = go.Figure()

fig.add_trace(go.Bar(
    name='Kosten',
    x=months,
    y=monthly_kosten,
    marker_color='#ef4444'
))

fig.add_trace(go.Bar(
    name='Umsätze',
    x=months,
    y=monthly_umsatz,
    marker_color='#10b981'
))

fig.update_layout(
    barmode='group',
    title='Monatliche Entwicklung',
    xaxis_title='Monat',
    yaxis_title='Betrag (€)',
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# Top 10 Maschinen
st.markdown("---")
st.subheader("🏆 Top 10 Maschinen (nach DB YTD)")

top_10 = df.nlargest(10, 'DB YTD')[
    ['VH-nr.', 'Beschreibung', 'Niederlassung', 'Kosten YTD', 'Umsätze YTD', 'DB YTD']
].copy()

# Formatierung
top_10['Kosten YTD'] = top_10['Kosten YTD'].apply(lambda x: f"€ {x:,.0f}")
top_10['Umsätze YTD'] = top_10['Umsätze YTD'].apply(lambda x: f"€ {x:,.0f}")
top_10['DB YTD'] = top_10['DB YTD'].apply(lambda x: f"€ {x:,.0f}")

st.dataframe(top_10, use_container_width=True, hide_index=True)

# Statistiken
st.markdown("---")
st.subheader("📊 Statistiken")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📦 Anzahl Maschinen", len(df))

with col2:
    avg_db = df['DB YTD'].mean()
    st.metric("💎 Ø DB pro Maschine", f"€ {avg_db:,.0f}")

with col3:
    positive_db = len(df[df['DB YTD'] > 0])
    st.metric("✅ Maschinen mit positivem DB", positive_db)

# Debug-Info (nur für Admins)
if user['role'] in ['superadmin', 'admin']:
    with st.expander("🔧 Debug-Info"):
        st.write(f"**User:** {user['username']}")
        st.write(f"**Rolle:** {user['role']}")
        st.write(f"**Niederlassungen:** {user['niederlassungen']}")
        st.write(f"**Gefilterte Datensätze:** {len(df)}")
        st.write(f"**Verfügbare Spalten:** {df.columns.tolist()}")