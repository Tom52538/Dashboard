import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide")

# Title
st.title("🚜 AGRO F66 Maschinen Dashboard")

# Load data
@st.cache_data
def load_data(file):
    if isinstance(file, str):
        df = pd.read_excel(file)
    else:
        df = pd.read_excel(file)
    return df

# Check if file exists in repo, otherwise show upload
data_file = 'Dashboard_Master.xlsx'
df = None

if os.path.exists(data_file):
    try:
        df = load_data(data_file)
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {str(e)}")
else:
    st.warning("⚠️ Dashboard_Master.xlsx nicht gefunden. Bitte lade die Datei hoch:")
    uploaded_file = st.file_uploader("Excel-Datei hochladen", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            st.success("✅ Datei erfolgreich geladen!")
        except Exception as e:
            st.error(f"❌ Fehler beim Laden: {str(e)}")

# Nur fortfahren wenn Daten geladen sind
if df is not None:
    # Verfügbare Monate extrahieren (aus Spaltennamen)
    cost_cols = [col for col in df.columns if col.startswith('Kosten ')]
    revenue_cols = [col for col in df.columns if col.startswith('Umsätze ')]
    db_cols = [col for col in df.columns if col.startswith('DB ')]
    
    # Monatsnamen extrahieren
    months = []
    for col in cost_cols:
        month_part = col.replace('Kosten ', '')
        months.append(month_part)
    
    st.sidebar.header("Filter")
    st.sidebar.write(f"📊 Geladene Maschinen: {len(df)}")
    st.sidebar.write(f"📅 Verfügbare Monate: {len(months)}")
    
    # Monat Filter
    selected_month = st.sidebar.selectbox("Monat auswählen", months, index=len(months)-1)
    
    # Spalten für den ausgewählten Monat
    cost_col = f'Kosten {selected_month}'
    revenue_col = f'Umsätze {selected_month}'
    db_col = f'DB {selected_month}'
    
    # Daten für den ausgewählten Monat
    df_month = df[['VH-nr.', 'Code', 'Omschrijving', 'Status', cost_col, revenue_col, db_col]].copy()
    df_month.columns = ['Maschinennummer', 'Code', 'Beschreibung', 'Status', 'Kosten', 'Umsätze', 'DB']
    
    # Status Filter
    status_options = ['Alle'] + sorted(df_month['Status'].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Status Filter", status_options)
    
    if selected_status != 'Alle':
        df_month = df_month[df_month['Status'] == selected_status]
    
    # Nur Maschinen mit Kosten oder Umsätzen anzeigen
    show_active_only = st.sidebar.checkbox("Nur aktive Maschinen (Kosten/Umsätze > 0)", value=True)
    if show_active_only:
        df_month = df_month[(df_month['Kosten'] != 0) | (df_month['Umsätze'] != 0)]
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_cost = df_month['Kosten'].sum()
    total_revenue = df_month['Umsätze'].sum()
    total_db = df_month['DB'].sum()
    avg_margin = (total_db / total_revenue * 100) if total_revenue != 0 else 0
    
    with col1:
        st.metric("💰 Gesamtkosten", f"€{total_cost:,.0f}")
    with col2:
        st.metric("📈 Gesamtumsatz", f"€{total_revenue:,.0f}")
    with col3:
        st.metric("💵 Deckungsbeitrag", f"€{total_db:,.0f}")
    with col4:
        st.metric("📊 Ø Marge", f"{avg_margin:.1f}%")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Übersicht", "🔍 Top/Flop Maschinen", "📋 Detaildaten"])
    
    with tab1:
        st.subheader(f"Monatsübersicht: {selected_month}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Kosten vs Umsätze Balkendiagramm
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                name='Kosten',
                x=['Gesamt'],
                y=[total_cost],
                marker_color='#ef4444'
            ))
            fig1.add_trace(go.Bar(
                name='Umsätze',
                x=['Gesamt'],
                y=[total_revenue],
                marker_color='#22c55e'
            ))
            fig1.update_layout(
                title='Kosten vs. Umsätze',
                barmode='group',
                height=400,
                yaxis_title='Euro (€)'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Deckungsbeitrag Waterfall
            fig2 = go.Figure(go.Waterfall(
                x=['Umsätze', 'Kosten', 'DB'],
                y=[total_revenue, -total_cost, total_db],
                measure=['relative', 'relative', 'total'],
                text=[f"€{total_revenue:,.0f}", f"-€{total_cost:,.0f}", f"€{total_db:,.0f}"],
                textposition='outside',
                connector={'line': {'color': 'rgb(63, 63, 63)'}},
                decreasing={'marker': {'color': '#ef4444'}},
                increasing={'marker': {'color': '#22c55e'}},
                totals={'marker': {'color': '#3b82f6'}}
            ))
            fig2.update_layout(
                title='Deckungsbeitrag Aufschlüsselung',
                height=400,
                yaxis_title='Euro (€)'
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("🏆 Top & Flop Performer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 nach Umsatz
            top_revenue = df_month.nlargest(10, 'Umsätze')[['Maschinennummer', 'Beschreibung', 'Umsätze']]
            
            fig3 = go.Figure(go.Bar(
                x=top_revenue['Umsätze'],
                y=top_revenue['Maschinennummer'].astype(str),
                orientation='h',
                marker_color='#22c55e',
                text=top_revenue['Umsätze'].apply(lambda x: f'€{x:,.0f}'),
                textposition='outside'
            ))
            fig3.update_layout(
                title='Top 10 Maschinen nach Umsatz',
                height=500,
                xaxis_title='Umsatz (€)',
                yaxis=dict(autorange='reversed')
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Top 10 schlechteste Marge
            worst_db = df_month.nsmallest(10, 'DB')[['Maschinennummer', 'Beschreibung', 'DB']]
            
            fig4 = go.Figure(go.Bar(
                x=worst_db['DB'],
                y=worst_db['Maschinennummer'].astype(str),
                orientation='h',
                marker_color='#ef4444',
                text=worst_db['DB'].apply(lambda x: f'€{x:,.0f}'),
                textposition='outside'
            ))
            fig4.update_layout(
                title='Top 10 Schlechteste Maschinen (DB)',
                height=500,
                xaxis_title='Deckungsbeitrag (€)',
                yaxis=dict(autorange='reversed')
            )
            st.plotly_chart(fig4, use_container_width=True)
        
        # Verteilung nach Status
        st.subheader("📊 Verteilung nach Status")
        status_summary = df_month.groupby('Status').agg({
            'Kosten': 'sum',
            'Umsätze': 'sum',
            'DB': 'sum'
        }).reset_index()
        
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(name='Kosten', x=status_summary['Status'], y=status_summary['Kosten'], marker_color='#ef4444'))
        fig5.add_trace(go.Bar(name='Umsätze', x=status_summary['Status'], y=status_summary['Umsätze'], marker_color='#22c55e'))
        fig5.update_layout(
            title='Kosten & Umsätze nach Status',
            barmode='group',
            height=400,
            xaxis_title='Status',
            yaxis_title='Euro (€)'
        )
        st.plotly_chart(fig5, use_container_width=True)
    
    with tab3:
        st.subheader("📋 Alle Maschinen im Detail")
        
        # Suche
        search = st.text_input("🔍 Suche nach Maschinennummer oder Beschreibung")
        if search:
            df_display = df_month[
                df_month['Maschinennummer'].astype(str).str.contains(search, case=False, na=False) |
                df_month['Beschreibung'].astype(str).str.contains(search, case=False, na=False)
            ]
        else:
            df_display = df_month
        
        # Sortierung
        sort_by = st.selectbox("Sortieren nach", ['DB', 'Umsätze', 'Kosten', 'Maschinennummer'])
        ascending = st.checkbox("Aufsteigend", value=False)
        
        df_display = df_display.sort_values(by=sort_by, ascending=ascending)
        
        # Marge berechnen
        df_display['Marge %'] = (df_display['DB'] / df_display['Umsätze'] * 100).fillna(0).round(1)
        
        # Styling für negative Werte
        def color_negative(val):
            if isinstance(val, (int, float)):
                color = '#ef4444' if val < 0 else '#22c55e' if val > 0 else 'black'
                return f'color: {color}'
            return ''
        
        st.dataframe(
            df_display.style.applymap(color_negative, subset=['DB', 'Marge %']),
            use_container_width=True,
            height=600
        )
        
        st.download_button(
            label="📥 Export als CSV",
            data=df_display.to_csv(index=False).encode('utf-8'),
            file_name=f'maschinen_export_{selected_month}.csv',
            mime='text/csv'
        )
else:
    st.info("👆 Bitte lade die Dashboard_Master.xlsx Datei hoch oder stelle sicher, dass sie im Repository liegt.")
