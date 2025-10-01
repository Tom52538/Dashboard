# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
from io import BytesIO

# Funktion für Excel-Export
def to_excel(df):
    """Konvertiert DataFrame zu Excel-Bytes für Download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Daten')
        
        # Worksheet formatieren
        worksheet = writer.sheets['Daten']
        
        # Spaltenbreiten anpassen
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    return output.getvalue()

# Page Config
st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide")

st.title("AGRO F66 Maschinen Dashboard")

# Daten laden - OHNE File Upload!
@st.cache_data(ttl=86400)  # Cache für 24 Stunden
def load_data():
    """Lädt Dashboard_Master.xlsx direkt aus dem Repository"""
    try:
        df = pd.read_excel("Dashboard_Master.xlsx", dtype={'VH-nr.': str})
        
        # VH-Nr. als Text sicherstellen (falls trotzdem als Zahl gelesen)
        if 'VH-nr.' in df.columns:
            df['VH-nr.'] = df['VH-nr.'].astype(str).str.strip()
        
        # Automatische Bereinigung: Runde alle numerischen Werte auf 2 Dezimalstellen
        kosten_spalten = [col for col in df.columns if 'Kosten' in col]
        umsatz_spalten = [col for col in df.columns if 'Umsätze' in col]
        db_spalten = [col for col in df.columns if 'DB' in col]
        
        for col in kosten_spalten + umsatz_spalten + db_spalten:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    except FileNotFoundError:
        st.error("❌ Dashboard_Master.xlsx nicht gefunden! Bitte stelle sicher, dass die Datei im Repository liegt.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Daten: {e}")
        st.stop()

def get_file_info():
    """Zeigt Datei-Informationen"""
    if os.path.exists("Dashboard_Master.xlsx"):
        timestamp = os.path.getmtime("Dashboard_Master.xlsx")
        last_update = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")
        file_size = os.path.getsize("Dashboard_Master.xlsx") / (1024 * 1024)  # MB
        return last_update, file_size
    return "Unbekannt", 0

# Info-Banner
last_update, file_size = get_file_info()
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.info(f"📅 **Letztes Update:** {last_update}")
with col_info2:
    st.info(f"💾 **Dateigröße:** {file_size:.2f} MB")

# Daten laden
df = load_data()

with col_info3:
    st.success(f"✅ **{len(df):,} Datensätze** geladen")

# Cache-Clear Button (für manuelle Updates)
if st.button("🔄 Daten neu laden"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

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

# MASTER-FILTER: Steuert alle Sektionen
st.sidebar.markdown("### 🎯 Master-Filter")
st.sidebar.info("Dieser Filter gilt für ALLE Auswertungen auf der Seite")
master_nl_filter = st.sidebar.selectbox(
    "Niederlassung (alle Sektionen)", 
    nl_options, 
    key='master_nl'
)

st.sidebar.markdown("---")

show_active = st.sidebar.checkbox("Nur Maschinen mit YTD-Aktivität", value=True)

# Basis-Filterung
df_base = df.copy()
if show_active:
    df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]

# Master-Filter anwenden
if master_nl_filter != 'Gesamt' and has_nl:
    df_base = df_base[df_base['Niederlassung'] == master_nl_filter]

st.sidebar.metric("Gefilterte Maschinen", f"{len(df_base):,}")
st.sidebar.metric("Ausgewählte NL", master_nl_filter)

# === ÜBERSICHT SEKTION ===
st.header("Übersicht")

# Übersicht Daten nutzen gefilterte Basis
df_overview = df_base.copy()

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

# Monatliche Daten nutzen gefilterte Basis
df_monthly_base = df_base.copy()

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

# Chart 2: DB in Euro - mit dynamischer Y-Achse
colors_db = ['#22c55e' if x >= 0 else '#ef4444' for x in df_monthly['DB']]
fig.add_trace(go.Bar(name='DB (€)', x=df_monthly['Monat'], y=df_monthly['DB'], 
                     marker_color=colors_db, showlegend=False,
                     text=df_monthly['DB'].apply(lambda x: f'€{x/1000:.0f}k'),
                     textposition='outside'), row=1, col=2)

# Dynamische Y-Achse für DB - berücksichtigt negative Werte
min_db = df_monthly['DB'].min()
max_db = df_monthly['DB'].max()
y_range_db = [min_db * 1.2 if min_db < 0 else 0, max_db * 1.15]
fig.update_yaxes(range=y_range_db, row=1, col=2)

# Chart 3: Marge in % - mit dynamischer Y-Achse
colors_marge = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_monthly['Marge %']]
fig.add_trace(go.Bar(name='Marge %', x=df_monthly['Monat'], y=df_monthly['Marge %'], 
                     marker_color=colors_marge, showlegend=False,
                     text=df_monthly['Marge %'].apply(lambda x: f'{x:.1f}%'),
                     textposition='outside'), row=2, col=1)

# Dynamische Y-Achse für Marge - berücksichtigt negative Werte
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

# === TOP PERFORMER ===
st.header("Top 10 Maschinen (YTD)")

# Top Performer nutzen gefilterte Basis
df_top = df_base.copy()

# Filtere nur relevante Maschinen (mindestens €1000 Umsatz)
df_top_relevant = df_top[df_top['Umsätze YTD'] >= 1000]

# Sortiere nach HÖCHSTEM DB (= hoher Umsatz + gute Marge) - ABSTEIGEND
top_10 = df_top_relevant.nlargest(10, 'DB YTD')
top_10_display = top_10[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()

# Sortiere die Anzeige nach DB YTD absteigend (höchster DB zuerst)
top_10_display = top_10_display.sort_values('DB YTD', ascending=False)

st.markdown("#### Tabelle & Chart")

col1, col2 = st.columns([1, 1])
with col1:
    top_display = top_10_display.copy()
    top_display['VH-nr.'] = top_display['VH-nr.'].astype(str)  # Als Text anzeigen
    top_display['Kosten YTD'] = top_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['Umsätze YTD'] = top_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['DB YTD'] = top_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    top_display['Marge YTD %'] = top_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(top_display, use_container_width=True, hide_index=True, height=400)

with col2:
    # Gestapelter Balken: Kosten + DB = Umsatz
    fig_top = go.Figure()
    
    # Y-Achsen Label: VH-Nr. + Code
    y_labels = top_10_display['VH-nr.'].astype(str) + ' | ' + top_10_display['Code'].astype(str)
    
    fig_top.add_trace(go.Bar(
        name='Kosten',
        y=y_labels,
        x=top_10_display['Kosten YTD'],
        orientation='h',
        marker_color='#ef4444',
        text=top_10_display['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='inside'
    ))
    
    fig_top.add_trace(go.Bar(
        name='DB',
        y=y_labels,
        x=top_10_display['DB YTD'],
        orientation='h',
        marker_color='#22c55e',
        text=top_10_display['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
        textposition='inside'
    ))
    
    # Marge als Text am Ende
    for idx, row in top_10_display.iterrows():
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

# === WORST PERFORMER ===
st.header("Worst 10 Maschinen (YTD)")

# Worst Performer nutzen gefilterte Basis
df_worst = df_base.copy()

# Filtere nur relevante Maschinen (mindestens €1000 Kosten)
df_worst_relevant = df_worst[df_worst['Kosten YTD'] >= 1000]

# Sortiere nach NIEDRIGSTEM DB (= hohe Kosten + schlechte Marge) - AUFSTEIGEND
worst_10 = df_worst_relevant.nsmallest(10, 'DB YTD')
worst_10_display = worst_10[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()

# Sortiere die Anzeige nach DB YTD aufsteigend (niedrigster DB zuerst)
worst_10_display = worst_10_display.sort_values('DB YTD', ascending=True)

st.markdown("#### Tabelle & Chart")

col1, col2 = st.columns([1, 1])
with col1:
    worst_display = worst_10_display.copy()
    worst_display['VH-nr.'] = worst_display['VH-nr.'].astype(str)  # Als Text anzeigen
    worst_display['Kosten YTD'] = worst_display['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['Umsätze YTD'] = worst_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['DB YTD'] = worst_display['DB YTD'].apply(lambda x: f"€ {x:,.2f}")
    worst_display['Marge YTD %'] = worst_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(worst_display, use_container_width=True, hide_index=True, height=400)

with col2:
    # Gestapelter Balken: Kosten + DB = Umsatz
    fig_worst = go.Figure()
    
    # Y-Achsen Label: VH-Nr. + Code
    y_labels_worst = worst_10_display['VH-nr.'].astype(str) + ' | ' + worst_10_display['Code'].astype(str)
    
    fig_worst.add_trace(go.Bar(
        name='Kosten',
        y=y_labels_worst,
        x=worst_10_display['Kosten YTD'],
        orientation='h',
        marker_color='#ef4444',
        text=worst_10_display['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k' if x != 0 else ''),
        textposition='inside'
    ))
    
    fig_worst.add_trace(go.Bar(
        name='DB',
        y=y_labels_worst,
        x=worst_10_display['DB YTD'],
        orientation='h',
        marker_color='#22c55e' if worst_10_display['DB YTD'].min() >= 0 else '#ef4444',
        text=worst_10_display['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k' if x != 0 else ''),
        textposition='inside'
    ))
    
    # Marge als Text
    for idx, row in worst_10_display.iterrows():
        y_label = str(row['VH-nr.']) + ' | ' + str(row['Code'])
        fig_worst.add_annotation(
            x=row['Umsätze YTD'] if row['Umsätze YTD'] > 0 else row['Kosten YTD'],
            y=y_label,
            text=f"{row['Marge YTD %']:.1f}%",
            showarrow=False,
            xanchor='left',
            xshift=5,
            font=dict(size=12, color='#dc2626')
        )
    
    fig_worst.update_layout(
        barmode='stack',
        height=400,
        xaxis_title='Euro (€)',
        yaxis=dict(autorange='reversed'),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_worst, use_container_width=True)

# === MONATSTABELLE ===
st.header("Detaillierte Monatsdaten")

# Monatstabelle nutzt gefilterte Basis
df_table_base = df_base.copy()

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

# Moderne Visualisierung statt einfacher Tabelle
col1, col2 = st.columns(2)

with col1:
    # Heatmap-Style Tabelle mit Farbcodierung
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

with col2:
    # Sparkline-Charts für jeden Monat
    fig_mini = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monatliche Marge %', 'DB-Entwicklung (€)'),
        row_heights=[0.5, 0.5]
    )
    
    # Marge Trend
    colors_trend = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_table['Marge %']]
    fig_mini.add_trace(go.Bar(
        x=df_table['Monat'],
        y=df_table['Marge %'],
        marker_color=colors_trend,
        text=df_table['Marge %'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        showlegend=False
    ), row=1, col=1)
    
    # DB Trend
    fig_mini.add_trace(go.Scatter(
        x=df_table['Monat'],
        y=df_table['DB'],
        mode='lines+markers',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)',
        showlegend=False
    ), row=2, col=1)
    
    fig_mini.update_layout(height=400, showlegend=False)
    fig_mini.update_yaxes(title_text="Marge (%)", row=1, col=1)
    fig_mini.update_yaxes(title_text="DB (€)", row=2, col=1)
    
    st.plotly_chart(fig_mini, use_container_width=True)

# Zusätzliche Insights
st.markdown("### Monatliche Insights")
col1, col2, col3, col4 = st.columns(4)

best_month = df_table.loc[df_table['Marge %'].idxmax()]
worst_month = df_table.loc[df_table['Marge %'].idxmin()]
highest_revenue = df_table.loc[df_table['Umsaetze'].idxmax()]
total_db = df_table['DB'].sum()

with col1:
    st.metric("Bester Monat (Marge)", best_month['Monat'], f"{best_month['Marge %']:.1f}%")
with col2:
    st.metric("Schlechtester Monat (Marge)", worst_month['Monat'], f"{worst_month['Marge %']:.1f}%")
with col3:
    st.metric("Höchster Umsatz", highest_revenue['Monat'], f"€ {highest_revenue['Umsaetze']:,.0f}")
with col4:
    st.metric("Gesamt DB (YTD)", f"€ {total_db:,.0f}", f"{(total_db/df_table['Umsaetze'].sum()*100):.1f}%")

# EXPORT
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.download_button(
        label="📥 Export als Excel",
        data=to_excel(df_table),
        file_name=f'dashboard_monatsdaten_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

with col_exp2:
    st.download_button(
        label="📄 Export als CSV",
        data=df_table.to_csv(index=False).encode('utf-8'),
        file_name=f'dashboard_monatsdaten_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )

# === MASCHINEN OHNE UMSÄTZE ===
st.header("⚠️ Maschinen ohne Umsätze (nur Kosten)")
st.markdown("Diese Maschinen verursachen Kosten aber generieren keinen Umsatz")

# Filtere Maschinen: Kosten > 0 UND Umsätze = 0
df_no_revenue = df_base[(df_base['Kosten YTD'] > 0) & (df_base['Umsätze YTD'] == 0)].copy()

# Sortiere nach höchsten Kosten (absteigend)
df_no_revenue = df_no_revenue.sort_values('Kosten YTD', ascending=False)

# Berechne 80/20 Regel (Pareto-Prinzip)
total_cost = df_no_revenue['Kosten YTD'].sum()
target_cost = total_cost * 0.8  # 80% der Kosten

# Finde die Maschinen die 80% der Kosten verursachen
cumulative_cost = 0
pareto_count = 0
for idx, cost in enumerate(df_no_revenue['Kosten YTD']):
    cumulative_cost += cost
    pareto_count = idx + 1
    if cumulative_cost >= target_cost:
        break

# Top Pareto-Maschinen (die 20% die 80% der Kosten verursachen)
df_no_revenue_pareto = df_no_revenue.head(pareto_count)
df_no_revenue_display = df_no_revenue_pareto[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']].copy()

# Zusammenfassung
col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
with col_sum1:
    st.metric("Gesamt Maschinen", len(df_no_revenue))
with col_sum2:
    st.metric("Gesamtkosten", f"€ {total_cost:,.0f}")
with col_sum3:
    pareto_percentage = (pareto_count / len(df_no_revenue) * 100) if len(df_no_revenue) > 0 else 0
    st.metric("Top Maschinen (80/20)", f"{pareto_count} ({pareto_percentage:.0f}%)")
with col_sum4:
    pareto_cost = df_no_revenue_pareto['Kosten YTD'].sum()
    pareto_cost_percentage = (pareto_cost / total_cost * 100) if total_cost > 0 else 0
    st.metric("Deren Kosten", f"€ {pareto_cost:,.0f} ({pareto_cost_percentage:.0f}%)")

st.markdown("#### Pareto-Analyse: Maschinen die 80% der Kosten verursachen")
st.info(f"📊 **{pareto_count} Maschinen** ({pareto_percentage:.1f}% aller Maschinen ohne Umsätze) verursachen **€{pareto_cost:,.0f}** ({pareto_cost_percentage:.1f}% der Gesamtkosten)")

col1, col2 = st.columns([1.5, 1])

with col1:
    # Tabelle
    display_no_rev = df_no_revenue_display.copy()
    display_no_rev['VH-nr.'] = display_no_rev['VH-nr.'].astype(str)
    display_no_rev['Kosten YTD'] = display_no_rev['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
    st.dataframe(display_no_rev, use_container_width=True, hide_index=True, height=500)

with col2:
    # Chart: Kosten-Verteilung (Top 10 aus Pareto-Maschinen)
    if len(df_no_revenue_display) > 0:
        # Zeige nur die Top 10 im Chart für bessere Lesbarkeit
        df_chart_top10 = df_no_revenue_display.head(10)
        
        fig_no_rev = go.Figure()
        
        y_labels_no_rev = df_chart_top10['VH-nr.'].astype(str) + ' | ' + df_chart_top10['Code'].astype(str)
        
        fig_no_rev.add_trace(go.Bar(
            y=y_labels_no_rev,
            x=df_chart_top10['Kosten YTD'],
            orientation='h',
            marker_color='#ef4444',
            text=df_chart_top10['Kosten YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
            textposition='outside'
        ))
        
        fig_no_rev.update_layout(
            height=500,
            xaxis_title='Kosten (€)',
            yaxis=dict(autorange='reversed'),
            showlegend=False,
            title=f"Top 10 Kostenverursacher"
        )
        st.plotly_chart(fig_no_rev, use_container_width=True)
    else:
        st.success("✅ Keine Maschinen ohne Umsätze gefunden!")

# Export für diese Sektion
if len(df_no_revenue) > 0:
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        st.download_button(
            label="📥 Export Alle (Excel)",
            data=to_excel(df_no_revenue[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']]),
            file_name=f'maschinen_ohne_umsaetze_alle_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    with col_exp2:
        st.download_button(
            label="📥 Export Top (80/20) Excel",
            data=to_excel(df_no_revenue_pareto[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']]),
            file_name=f'maschinen_ohne_umsaetze_pareto_{master_nl_filter}_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
