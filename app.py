"""
AGRO Dashboard - Vollständige Version mit Google Drive Integration
Alle Features aus agro_dashboard_v2.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from io import BytesIO
from auth import google_login, logout, get_credentials, get_user_email
from data_loader import get_data
from users import (
    get_user_info, 
    is_admin, 
    get_allowed_niederlassungen,
    get_niederlassung_options,
    get_user_display_name,
    filter_dataframe_by_user
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def to_excel(df):
    """Konvertiert DataFrame zu Excel-Bytes für Download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Daten')
        worksheet = writer.sheets['Daten']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    return output.getvalue()

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide", page_icon="🚜")

# ============================================================================
# AUTHENTICATION
# ============================================================================

# Auth-Funktion aufrufen (managed Session State intern)
user_info = google_login()

# Wenn nicht eingeloggt, stoppt google_login() die App automatisch
if not user_info:
    st.stop()

# User ist eingeloggt
user_email = user_info.get('email', 'Unbekannt')
user_display = get_user_display_name(user_email)
user_is_admin = is_admin(user_email)

# ============================================================================
# HEADER
# ============================================================================

col_header1, col_header2 = st.columns([4, 1])

with col_header1:
    st.title("🚜 AGRO F66 Maschinen Dashboard")
    st.caption(f"Angemeldet als: **{user_display}**")
    if user_is_admin:
        if get_user_info(user_email).get("role") == "superadmin":
            st.caption("🔧 Developer / Super Admin Zugriff")
        else:
            st.caption("🔐 Admin-Zugriff")

with col_header2:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

st.markdown("---")

# ============================================================================
# DATEN LADEN
# ============================================================================

@st.cache_data(ttl=3600)
def load_and_prepare_data(_credentials):
    """Lädt Daten von Google Drive und bereitet sie auf"""
    # Temporär credentials in session state setzen für get_data()
    st.session_state['credentials'] = _credentials
    
    df = get_data()
    
    if df is None or df.empty:
        st.error("❌ Keine Daten geladen!")
        st.stop()
    
    # VH-nr. als String
    if 'VH-nr.' in df.columns:
        df['VH-nr.'] = df['VH-nr.'].astype(str).str.strip()
    
    # Numerische Spalten konvertieren
    kosten_spalten = [col for col in df.columns if 'Kosten' in col]
    umsatz_spalten = [col for col in df.columns if 'Umsätze' in col]
    db_spalten = [col for col in df.columns if 'DB' in col]
    
    for col in kosten_spalten + umsatz_spalten + db_spalten:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).round(2)
    
    return df

with st.spinner("🔄 Lade Daten von Google Drive..."):
    credentials = get_credentials()
    df = load_and_prepare_data(credentials)

# WICHTIG: Daten nach User-Rechten filtern!
df = filter_dataframe_by_user(df, user_email)

if df.empty:
    st.error("❌ Keine Daten verfügbar für deine Niederlassung(en)!")
    st.info("💡 Kontaktiere deinen Administrator.")
    st.stop()

# Info-Banner
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.info(f"📅 **Geladen:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
with col_info2:
    st.info(f"📊 **Datei:** Dashboard_Master_DE_v2.xlsx")
with col_info3:
    st.success(f"✅ **{len(df):,} Datensätze** geladen")

if st.button("🔄 Daten neu laden"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# ============================================================================
# MONATE EXTRAHIEREN
# ============================================================================

cost_cols = [col for col in df.columns if col.startswith('Kosten ') and 'YTD' not in col]
months = [col.replace('Kosten ', '') for col in cost_cols]

# ============================================================================
# SIDEBAR - FILTER
# ============================================================================

st.sidebar.header("⚙️ Filter")

# MASTER-FILTER - NIEDERLASSUNG (basierend auf User-Rechten)
st.sidebar.markdown("### 🎯 Master-Filter")
st.sidebar.info("Dieser Filter gilt für ALLE Auswertungen")

has_nl = 'Niederlassung' in df.columns

# Niederlassungs-Optionen basierend auf User-Rolle
nl_options = get_niederlassung_options(user_email)

if not nl_options:
    st.sidebar.error("❌ Keine Niederlassungen verfügbar!")
    st.stop()

master_nl_filter = st.sidebar.selectbox(
    "Niederlassung (alle Sektionen)", 
    nl_options, 
    key='master_nl'
)

# PRODUKT-FILTER
st.sidebar.markdown("---")
st.sidebar.markdown("### 📦 Produkt-Filter")

has_product_cols = '1. Product Family' in df.columns

if has_product_cols:
    product_families = ['Alle'] + sorted([fam for fam in df['1. Product Family'].dropna().unique() if str(fam) != 'nan'])
    selected_family = st.sidebar.selectbox("Product Family", product_families, key='product_family')
    
    # Product Group - dynamisch basierend auf Family
    if selected_family != 'Alle':
        df_filtered_for_group = df[df['1. Product Family'] == selected_family]
    else:
        df_filtered_for_group = df
    
    product_groups = ['Alle'] + sorted([grp for grp in df_filtered_for_group['2. Product Group'].dropna().unique() if str(grp) != 'nan'])
    selected_group = st.sidebar.selectbox("Product Group", product_groups, key='product_group')
else:
    selected_family = 'Alle'
    selected_group = 'Alle'

st.sidebar.markdown("---")

# AKTIVITÄTS-FILTER
show_active = st.sidebar.checkbox("✅ Nur Maschinen mit YTD-Aktivität", value=True)

# ============================================================================
# BASIS-FILTERUNG ANWENDEN
# ============================================================================

df_base = df.copy()

# Aktivitäts-Filter
if show_active:
    df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]

# Niederlassungs-Filter (nur wenn Admin "Gesamt" gewählt hat)
if master_nl_filter != 'Gesamt' and has_nl:
    df_base = df_base[df_base['Niederlassung'] == master_nl_filter]
# Wenn "Gesamt": df_base bleibt wie es ist (bereits gefiltert nach User-Rechten)

# Produkt-Filter
if has_product_cols:
    if selected_family != 'Alle':
        df_base = df_base[df_base['1. Product Family'] == selected_family]
    if selected_group != 'Alle':
        df_base = df_base[df_base['2. Product Group'] == selected_group]

# SIDEBAR METRIKEN
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Gefilterte Daten")
st.sidebar.metric("Gefilterte Maschinen", f"{len(df_base):,}")
st.sidebar.metric("Ausgewählte NL", master_nl_filter)
if has_product_cols and selected_family != 'Alle':
    st.sidebar.metric("Produkt-Filter", f"{selected_family}")

# EXPORT ALLE MASCHINEN
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Daten Export")

export_columns = ['VH-nr.', 'Code', 'Omschrijving', 'Niederlassung', 
                  'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']

# Nur Spalten exportieren, die auch existieren
export_cols_available = [col for col in export_columns if col in df_base.columns]
df_export_all = df_base[export_cols_available].copy()

st.sidebar.download_button(
    label=f"📥 Alle Maschinen ({len(df_base):,})",
    data=to_excel(df_export_all),
    file_name=f'alle_maschinen_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    use_container_width=True,
    help="Exportiert alle aktuell gefilterten Maschinen"
)

# ============================================================================
# ÜBERSICHT SEKTION
# ============================================================================

st.header("📊 Übersicht")

df_overview = df_base.copy()

ytd_kosten = df_overview['Kosten YTD'].sum()
ytd_umsaetze = df_overview['Umsätze YTD'].sum()
ytd_db = df_overview['DB YTD'].sum()
ytd_marge = (ytd_db / ytd_umsaetze * 100) if ytd_umsaetze != 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💰 YTD Kosten", f"€ {ytd_kosten:,.0f}")
with col2:
    st.metric("💵 YTD Umsätze", f"€ {ytd_umsaetze:,.0f}")
with col3:
    st.metric("💎 YTD Deckungsbeitrag", f"€ {ytd_db:,.0f}", delta=f"{ytd_marge:.1f}%")
with col4:
    st.metric("📊 YTD Marge", f"{ytd_marge:.1f}%")

st.markdown("---")

# ============================================================================
# MONATLICHE ENTWICKLUNG (4 CHARTS)
# ============================================================================

st.header("📈 Monatliche Entwicklung")

df_monthly_base = df_base.copy()

monthly_data = []
for month in months:
    monthly_data.append({
        'Monat': month,
        'Kosten': df_monthly_base[f'Kosten {month}'].sum(),
        'Umsaetze': df_monthly_base[f'Umsätze {month}'].sum(),
        'DB': df_monthly_base[f'DB {month}'].sum()
    })

df_monthly = pd.DataFrame(monthly_data)
df_monthly['Marge %'] = (df_monthly['DB'] / df_monthly['Umsaetze'] * 100).fillna(0)

# 4 Subplots
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

# Chart 2: DB (€) mit Farben
colors_db = ['#22c55e' if x >= 0 else '#ef4444' for x in df_monthly['DB']]
fig.add_trace(go.Bar(name='DB (€)', x=df_monthly['Monat'], y=df_monthly['DB'], 
                     marker_color=colors_db, showlegend=False,
                     text=df_monthly['DB'].apply(lambda x: f'€{x/1000:.0f}k'),
                     textposition='outside'), row=1, col=2)

min_db = df_monthly['DB'].min()
max_db = df_monthly['DB'].max()
y_range_db = [min_db * 1.2 if min_db < 0 else 0, max_db * 1.15]
fig.update_yaxes(range=y_range_db, row=1, col=2)

# Chart 3: Marge % mit Farben
colors_marge = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_monthly['Marge %']]
fig.add_trace(go.Bar(name='Marge %', x=df_monthly['Monat'], y=df_monthly['Marge %'], 
                     marker_color=colors_marge, showlegend=False,
                     text=df_monthly['Marge %'].apply(lambda x: f'{x:.1f}%'),
                     textposition='outside'), row=2, col=1)

min_marge = df_monthly['Marge %'].min()
max_marge = df_monthly['Marge %'].max()
y_range_marge = [min_marge * 1.2 if min_marge < 0 else 0, max_marge * 1.15]
fig.update_yaxes(range=y_range_marge, row=2, col=1)

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

st.markdown("---")

# ============================================================================
# TOP 10 PERFORMER
# ============================================================================

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

# ============================================================================
# WORST 10 PERFORMER
# ============================================================================

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
        marker_color='#22c55e' if worst_10_display['DB YTD'].min() >= 0 else '#ef4444',
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

# ============================================================================
# PRODUKTANALYSE
# ============================================================================

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
        
        # TOP 20 PRODUCT GROUPS
        if '2. Product Group' in df_products.columns:
            st.markdown("---")
            st.markdown("#### 🏅 Top 20 Product Groups")
            
            st.markdown("### 🔽 Sortieren nach:")
            sort_groups = st.selectbox(
                "Wähle Sortierung für Product Groups:",
                ["Umsätze YTD (Höchster)", "DB YTD (Höchster Gewinn)", "Marge % (Beste)", "Anzahl (Meiste Maschinen)"],
                key='sort_product_groups'
            )
            
            product_group_stats = df_products.groupby('2. Product Group').agg({
                'VH-nr.': 'count',
                'Umsätze YTD': 'sum',
                'DB YTD': 'sum'
            }).reset_index()
            
            product_group_stats.columns = ['Product Group', 'Anzahl', 'Umsätze YTD', 'DB YTD']
            product_group_stats['Marge %'] = (product_group_stats['DB YTD'] / product_group_stats['Umsätze YTD'] * 100).fillna(0)
            
            if "Umsätze YTD" in sort_groups:
                product_group_stats = product_group_stats.sort_values('Umsätze YTD', ascending=False).head(20)
            elif "DB YTD" in sort_groups:
                product_group_stats = product_group_stats.sort_values('DB YTD', ascending=False).head(20)
            elif "Marge %" in sort_groups:
                product_group_stats = product_group_stats.sort_values('Marge %', ascending=False).head(20)
            else:
                product_group_stats = product_group_stats.sort_values('Anzahl', ascending=False).head(20)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                display_groups = product_group_stats.copy()
                display_groups['Anzahl'] = display_groups['Anzahl'].apply(lambda x: f"{x:,}")
                display_groups['Umsätze YTD'] = display_groups['Umsätze YTD'].apply(lambda x: f"€ {x:,.0f}")
                display_groups['DB YTD'] = display_groups['DB YTD'].apply(lambda x: f"€ {x:,.0f}")
                display_groups['Marge %'] = display_groups['Marge %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display_groups, use_container_width=True, hide_index=True, height=400)
            
            with col2:
                fig_groups = go.Figure()
                
                fig_groups.add_trace(go.Bar(
                    y=product_group_stats['Product Group'],
                    x=product_group_stats['Umsätze YTD'],
                    orientation='h',
                    marker_color='#3b82f6',
                    text=product_group_stats['Umsätze YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
                    textposition='outside'
                ))
                
                fig_groups.update_layout(
                    height=400,
                    xaxis_title='Umsatz (€)',
                    yaxis=dict(autorange='reversed'),
                    showlegend=False
                )
                
                st.plotly_chart(fig_groups, use_container_width=True)
    else:
        st.info("Keine Daten für Produktanalyse verfügbar. Bitte Filter anpassen.")

st.markdown("---")

# ============================================================================
# DETAILLIERTE MONATSDATEN
# ============================================================================

st.header("📋 Detaillierte Monatsdaten")

df_table_base = df_base.copy()

monthly_table = []
for month in months:
    monthly_table.append({
        'Monat': month,
        'Kosten': df_table_base[f'Kosten {month}'].sum(),
        'Umsaetze': df_table_base[f'Umsätze {month}'].sum(),
        'DB': df_table_base[f'DB {month}'].sum()
    })

df_table = pd.DataFrame(monthly_table)
df_table['Marge %'] = (df_table['DB'] / df_table['Umsaetze'] * 100).fillna(0)

col1, col2 = st.columns(2)

with col1:
    def highlight_marge(val):
        if isinstance(val, str) and '%' in val:
            num = float(val.replace('%', '').replace(',', '.'))
            if num >= 10:
                return 'background-color: #d1fae5; color: #065f46; font-weight: bold'
            elif num >= 5:
                return 'background-color: #fef3c7; color: #92400e'
            else:
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold'
        return ''
    
    def highlight_db(val):
        if isinstance(val, str) and '€' in val:
            num = float(val.replace('€', '').replace(',', '').strip())
            if num >= 0:
                return 'color: #059669; font-weight: bold'
            else:
                return 'color: #dc2626; font-weight: bold'
        return ''
    
    styled_table = df_table.style.format({
        'Kosten': '€ {:,.0f}',
        'Umsaetze': '€ {:,.0f}',
        'DB': '€ {:,.0f}',
        'Marge %': '{:.1f}%'
    }).applymap(highlight_marge, subset=['Marge %']).applymap(highlight_db, subset=['DB'])
    
    st.dataframe(styled_table, use_container_width=True, height=400)
    
    st.download_button(
        label="📥 Export Monatsdaten (Excel)",
        data=to_excel(df_table),
        file_name=f'monatsdaten_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True
    )

with col2:
    fig_mini = make_subplots(rows=2, cols=1, subplot_titles=('Monatliche Marge %', 'DB-Entwicklung (€)'), row_heights=[0.5, 0.5])
    
    colors_trend = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_table['Marge %']]
    fig_mini.add_trace(go.Bar(x=df_table['Monat'], y=df_table['Marge %'], marker_color=colors_trend,
        text=df_table['Marge %'].apply(lambda x: f'{x:.1f}%'), textposition='outside', showlegend=False), row=1, col=1)
    
    fig_mini.add_trace(go.Scatter(x=df_table['Monat'], y=df_table['DB'], mode='lines+markers',
        line=dict(color='#3b82f6', width=3), marker=dict(size=10), fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)', showlegend=False), row=2, col=1)
    
    fig_mini.update_layout(height=400, showlegend=False)
    fig_mini.update_yaxes(title_text="Marge (%)", row=1, col=1)
    fig_mini.update_yaxes(title_text="DB (€)", row=2, col=1)
    
    st.plotly_chart(fig_mini, use_container_width=True)

st.markdown("### 💡 Monatliche Insights")
col1, col2, col3, col4 = st.columns(4)

best_month = df_table.loc[df_table['Marge %'].idxmax()]
worst_month = df_table.loc[df_table['Marge %'].idxmin()]
highest_revenue = df_table.loc[df_table['Umsaetze'].idxmax()]
total_db = df_table['DB'].sum()

with col1:
    st.metric("🏆 Bester Monat (Marge)", best_month['Monat'], f"{best_month['Marge %']:.1f}%")
with col2:
    st.metric("📉 Schlechtester Monat (Marge)", worst_month['Monat'], f"{worst_month['Marge %']:.1f}%")
with col3:
    st.metric("💰 Höchster Umsatz", highest_revenue['Monat'], f"€ {highest_revenue['Umsaetze']:,.0f}")
with col4:
    st.metric("💎 Gesamt DB (YTD)", f"€ {total_db:,.0f}", f"{(total_db/df_table['Umsaetze'].sum()*100):.1f}%")

st.markdown("---")

# ============================================================================
# MASCHINEN OHNE UMSÄTZE (PARETO)
# ============================================================================

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

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption("🚜 AGRO F66 Dashboard v2.0 | Powered by Google Drive & Streamlit | 📊 Alle Daten in Echtzeit")