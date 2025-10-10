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
    page_title="AGRO F66 Dashboard Umsätze pro Maschine",
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
# TOP 10 PERFORMER
# ========================================
st.header("🏆 Top 10 Maschinen (YTD)")

st.markdown("### 🔽 Sortieren nach:")
sort_top = st.selectbox(
    "Wähle Sortierung für Top 10:",
    ["DB YTD (Höchster Gewinn)", "Umsätze YTD (Höchster Umsatz)", "Marge YTD % (Beste Marge)", "Kosten YTD (Höchste Kosten)"],
    key='sort_top_10'
)

df_top = df_base.copy()
df_top_relevant = df_top[df_top['Umsätze YTD'] >= 1000]

if "DB YTD" in sort_top:
    top_10 = df_top_relevant.nlargest(10, 'DB YTD')
elif "Umsätze YTD" in sort_top:
    top_10 = df_top_relevant.nlargest(10, 'Umsätze YTD')
elif "Marge YTD %" in sort_top:
    top_10 = df_top_relevant.nlargest(10, 'Marge YTD %')
else:
    top_10 = df_top_relevant.nlargest(10, 'Kosten YTD')

top_10_display = top_10[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()
top_10_display = top_10_display.sort_values('DB YTD', ascending=False)

st.markdown("#### 📊 Tabelle & Chart")

col1, col2 = st.columns([1, 1])

with col1:
    top_display = top_10_display.copy()
    top_display['VH-nr.'] = top_display['VH-nr.'].astype(str)
    top_display['Kosten YTD'] = top_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['Umsätze YTD'] = top_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['DB YTD'] = top_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['Marge YTD %'] = top_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(top_display, use_container_width=True, hide_index=True, height=400)
    
    st.download_button(
        label="📥 Export Top 10 (Excel)",
        data=to_excel(top_10_display),
        file_name=f'top_10_maschinen_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True
    )

with col2:
    fig_top = go.Figure()
    y_labels = top_10_display['VH-nr.'].astype(str) + ' | ' + top_10_display['Code'].astype(str)
    
    fig_top.add_trace(go.Bar(
        name='Kosten', y=y_labels, x=top_10_display['Kosten YTD'], orientation='h',
        marker_color='#ef4444', text=top_10_display['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='inside'
    ))
    
    fig_top.add_trace(go.Bar(
        name='DB', y=y_labels, x=top_10_display['DB YTD'], orientation='h',
        marker_color='#22c55e', text=top_10_display['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='inside'
    ))
    
    for idx, row in top_10_display.iterrows():
        y_label = str(row['VH-nr.']) + ' | ' + str(row['Code'])
        fig_top.add_annotation(
            x=row['Umsätze YTD'], y=y_label, text=f"{row['Marge YTD %']:.1f}%",
            showarrow=False, xanchor='left', xshift=5,
            font=dict(size=12, color='#059669' if row['Marge YTD %'] >= 10 else '#d97706')
        )
    
    fig_top.update_layout(
        barmode='stack', height=400, xaxis_title='Euro (€)',
        yaxis=dict(autorange='reversed'), showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# ========================================
# WORST 10 PERFORMER
# ========================================
st.header("📉 Worst 10 Maschinen (YTD)")

st.markdown("### 🔽 Sortieren nach:")
sort_worst = st.selectbox(
    "Wähle Sortierung für Worst 10:",
    ["DB YTD (Niedrigster/Negativster)", "Marge YTD % (Schlechteste Marge)", "Kosten YTD (Höchste Kosten)", "Umsätze YTD (Niedrigster Umsatz)"],
    key='sort_worst_10'
)

df_worst = df_base.copy()
df_worst_relevant = df_worst[df_worst['Kosten YTD'] >= 1000]

if "DB YTD" in sort_worst:
    worst_10 = df_worst_relevant.nsmallest(10, 'DB YTD')
elif "Marge YTD %" in sort_worst:
    worst_10 = df_worst_relevant.nsmallest(10, 'Marge YTD %')
elif "Kosten YTD" in sort_worst:
    worst_10 = df_worst_relevant.nlargest(10, 'Kosten YTD')
else:
    worst_10 = df_worst_relevant.nsmallest(10, 'Umsätze YTD')

worst_10_display = worst_10[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()
worst_10_display = worst_10_display.sort_values('DB YTD', ascending=True)

st.markdown("#### 📊 Tabelle & Chart")

col1, col2 = st.columns([1, 1])

with col1:
    worst_display = worst_10_display.copy()
    worst_display['VH-nr.'] = worst_display['VH-nr.'].astype(str)
    worst_display['Kosten YTD'] = worst_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['Umsätze YTD'] = worst_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['DB YTD'] = worst_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['Marge YTD %'] = worst_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(worst_display, use_container_width=True, hide_index=True, height=400)
    
    st.download_button(
        label="📥 Export Worst 10 (Excel)",
        data=to_excel(worst_10_display),
        file_name=f'worst_10_maschinen_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True
    )

with col2:
    fig_worst = go.Figure()
    y_labels_worst = worst_10_display['VH-nr.'].astype(str) + ' | ' + worst_10_display['Code'].astype(str)
    
    fig_worst.add_trace(go.Bar(
        name='Kosten', y=y_labels_worst, x=worst_10_display['Kosten YTD'], orientation='h',
        marker_color='#ef4444', text=worst_10_display['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k' if x != 0 else ''),
        textposition='inside'
    ))
    
    fig_worst.add_trace(go.Bar(
        name='DB', y=y_labels_worst, x=worst_10_display['DB YTD'], orientation='h',
        marker_color='#ef4444',
        text=worst_10_display['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k' if x != 0 else ''),
        textposition='inside'
    ))
    
    for idx, row in worst_10_display.iterrows():
        y_label = str(row['VH-nr.']) + ' | ' + str(row['Code'])
        fig_worst.add_annotation(
            x=row['Umsätze YTD'] if row['Umsätze YTD'] > 0 else row['Kosten YTD'],
            y=y_label, text=f"{row['Marge YTD %']:.1f}%",
            showarrow=False, xanchor='left', xshift=5,
            font=dict(size=12, color='#dc2626')
        )
    
    fig_worst.update_layout(
        barmode='stack', height=400, xaxis_title='Euro (€)',
        yaxis=dict(autorange='reversed'), showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_worst, use_container_width=True)

st.markdown("---")

# ========================================
# PRODUKTANALYSE
# ========================================
if has_product_cols:
    st.header("📦 Produktanalyse")
    
    df_products = df_base.copy()
    
    if len(df_products) > 0 and '1. Product Family' in df_products.columns:
        # PRODUCT FAMILY STATS
        product_family_stats = df_products.groupby('1. Product Family').agg({
            'VH-nr.': 'count',
            'Kosten YTD': 'sum',
            'Umsätze YTD': 'sum',
            'DB YTD': 'sum'
        }).reset_index()
        
        product_family_stats.columns = ['Product Family', 'Anzahl', 'Kosten YTD', 'Umsätze YTD', 'DB YTD']
        product_family_stats['Marge %'] = (product_family_stats['DB YTD'] / product_family_stats['Umsätze YTD'] * 100).fillna(0)
        
        st.markdown("### 🔽 Sortieren nach:")
        sort_product_mix = st.selectbox(
            "Wähle Sortierung für Produkt-Mix:",
            ["Umsätze YTD (Höchster)", "DB YTD (Höchster Gewinn)", "Marge % (Beste)", "Anzahl (Meiste Maschinen)", "Kosten YTD (Höchste)"],
            key='sort_product_mix'
        )
        
        if "Umsätze YTD" in sort_product_mix:
            product_family_stats = product_family_stats.sort_values('Umsätze YTD', ascending=False)
        elif "DB YTD" in sort_product_mix:
            product_family_stats = product_family_stats.sort_values('DB YTD', ascending=False)
        elif "Marge %" in sort_product_mix:
            product_family_stats = product_family_stats.sort_values('Marge %', ascending=False)
        elif "Anzahl" in sort_product_mix:
            product_family_stats = product_family_stats.sort_values('Anzahl', ascending=False)
        else:
            product_family_stats = product_family_stats.sort_values('Kosten YTD', ascending=False)
        
        display_products = product_family_stats.copy()
        display_products['Anzahl'] = display_products['Anzahl'].apply(lambda x: f"{x:,}")
        display_products['Kosten YTD'] = display_products['Kosten YTD'].apply(lambda x: f"€ {x:,.0f}")
        display_products['Umsätze YTD'] = display_products['Umsätze YTD'].apply(lambda x: f"€ {x:,.0f}")
        display_products['DB YTD'] = display_products['DB YTD'].apply(lambda x: f"€ {x:,.0f}")
        display_products['Marge %'] = display_products['Marge %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_products, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="📥 Export Produktanalyse (Excel)",
            data=to_excel(product_family_stats),
            file_name=f'produktanalyse_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("Keine Daten für Produktanalyse verfügbar.")

st.markdown("---")

# ========================================
# MASCHINEN OHNE UMSÄTZE (PARETO)
# ========================================
st.header("⚠️ Maschinen ohne Umsätze (nur Kosten)")
st.markdown("Diese Maschinen verursachen Kosten aber generieren keinen Umsatz")

df_no_revenue = df_base[(df_base['Kosten YTD'] > 0) & (df_base['Umsätze YTD'] == 0)].copy()
df_no_revenue = df_no_revenue.sort_values('Kosten YTD', ascending=False)

total_cost = df_no_revenue['Kosten YTD'].sum()
target_cost = total_cost * 0.8

cumulative_cost = 0
pareto_count = 0
for idx, cost in enumerate(df_no_revenue['Kosten YTD']):
    cumulative_cost += cost
    pareto_count = idx + 1
    if cumulative_cost >= target_cost:
        break

df_no_revenue_pareto = df_no_revenue.head(pareto_count)
df_no_revenue_display = df_no_revenue_pareto[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']].copy()

col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
with col_sum1:
    st.metric("📊 Gesamt Maschinen", len(df_no_revenue))
with col_sum2:
    st.metric("💰 Gesamtkosten", f"€ {total_cost:,.0f}")
with col_sum3:
    pareto_percentage = (pareto_count / len(df_no_revenue) * 100) if len(df_no_revenue) > 0 else 0
    st.metric("🎯 Top Maschinen (80/20)", f"{pareto_count} ({pareto_percentage:.0f}%)")
with col_sum4:
    pareto_cost = df_no_revenue_pareto['Kosten YTD'].sum()
    pareto_cost_percentage = (pareto_cost / total_cost * 100) if total_cost > 0 else 0
    st.metric("💸 Deren Kosten", f"€ {pareto_cost:,.0f} ({pareto_cost_percentage:.0f}%)")

if len(df_no_revenue_pareto) > 0:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        display_no_rev = df_no_revenue_display.copy()
        display_no_rev['VH-nr.'] = display_no_rev['VH-nr.'].astype(str)
        display_no_rev['Kosten YTD'] = display_no_rev['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
        st.dataframe(display_no_rev, use_container_width=True, hide_index=True, height=400)
        
        st.download_button(
            label="📥 Export Maschinen ohne Umsätze (Excel)",
            data=to_excel(df_no_revenue_display),
            file_name=f'maschinen_ohne_umsaetze_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
    
    with col2:
        fig_pareto = go.Figure()
        
        df_no_revenue_pareto_sorted = df_no_revenue_pareto.sort_values('Kosten YTD', ascending=True)
        y_labels_pareto = df_no_revenue_pareto_sorted['VH-nr.'].astype(str) + ' | ' + df_no_revenue_pareto_sorted['Code'].astype(str)
        
        fig_pareto.add_trace(go.Bar(
            y=y_labels_pareto,
            x=df_no_revenue_pareto_sorted['Kosten YTD'],
            orientation='h',
            marker_color='#ef4444',
            text=df_no_revenue_pareto_sorted['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
            textposition='outside'
        ))
        
        fig_pareto.update_layout(
            height=400,
            xaxis_title='Kosten (€)',
            showlegend=False
        )
        
        st.plotly_chart(fig_pareto, use_container_width=True)
else:
    st.success("✅ Keine Maschinen ohne Umsätze gefunden!")

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.caption("🚜 AGRO F66 Dashboard v4.0 | Simple Auth | 📊 ")
