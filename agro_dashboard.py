# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide")

st.title("AGRO F66 Maschinen Dashboard")

uploaded_file = st.file_uploader("Dashboard_Master.xlsx hochladen", type=['xlsx'], key='file_uploader')

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    return df

df = None

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        st.success(f"Datei geladen: {len(df):,} Maschinen")
    except Exception as e:
        st.error(f"Fehler beim Laden: {str(e)}")
        st.stop()
else:
    st.info("Bitte lade die Dashboard_Master.xlsx hoch um zu starten")
    st.stop()

cost_cols = [col for col in df.columns if col.startswith('Kosten ')]
revenue_cols = [col for col in df.columns if col.startswith('Umsaetze ') or col.startswith('Umsätze ')]
db_cols = [col for col in df.columns if col.startswith('DB ')]

months = []
for col in cost_cols:
    month_part = col.replace('Kosten ', '')
    months.append(month_part)

st.sidebar.header("Filter")
st.sidebar.write(f"Geladene Maschinen: {len(df)}")
st.sidebar.write(f"Verfuegbare Monate: {len(months)}")

selected_month = st.sidebar.selectbox("Monat auswaehlen", months, index=len(months)-1)

# Filter basierend auf YTD statt einzelnem Monat
show_active_only = st.sidebar.checkbox("Maschinen ohne YTD-Aktivität ausblenden", value=True)

cost_col = f'Kosten {selected_month}'
revenue_col = None
for col in df.columns:
    if col.startswith('Umsaetze ') or col.startswith('Umsätze '):
        if selected_month in col:
            revenue_col = col
            break
db_col = f'DB {selected_month}'

df_month = df[['VH-nr.', 'Code', 'Omschrijving', cost_col, revenue_col, db_col]].copy()
df_month.columns = ['Maschinennummer', 'Code', 'Beschreibung', 'Kosten', 'Umsaetze', 'DB']

if show_active_only:
    df_month = df_month[(df_month['Kosten'] != 0) | (df_month['Umsaetze'] != 0)]

col1, col2, col3, col4 = st.columns(4)

total_cost = df_month['Kosten'].sum()
total_revenue = df_month['Umsaetze'].sum()
total_db = df_month['DB'].sum()
avg_margin = (total_db / total_revenue * 100) if total_revenue != 0 else 0

with col1:
    st.metric("Gesamtkosten", f"EUR {total_cost:,.0f}")
with col2:
    st.metric("Gesamtumsatz", f"EUR {total_revenue:,.0f}")
with col3:
    st.metric("Deckungsbeitrag", f"EUR {total_db:,.0f}")
with col4:
    st.metric("Durchschn. Marge", f"{avg_margin:.1f}%")

tab1, tab2, tab3 = st.tabs(["Uebersicht", "Top/Flop Maschinen", "Detaildaten"])

with tab1:
    st.subheader(f"Monatsuebersicht: {selected_month}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name='Kosten', x=['Gesamt'], y=[total_cost], marker_color='#ef4444'))
        fig1.add_trace(go.Bar(name='Umsaetze', x=['Gesamt'], y=[total_revenue], marker_color='#22c55e'))
        fig1.update_layout(title='Kosten vs. Umsaetze', barmode='group', height=400, yaxis_title='Euro')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = go.Figure(go.Waterfall(
            x=['Umsaetze', 'Kosten', 'DB'],
            y=[total_revenue, -total_cost, total_db],
            measure=['relative', 'relative', 'total'],
            text=[f"EUR {total_revenue:,.0f}", f"-EUR {total_cost:,.0f}", f"EUR {total_db:,.0f}"],
            textposition='outside',
            connector={'line': {'color': 'rgb(63, 63, 63)'}},
            decreasing={'marker': {'color': '#ef4444'}},
            increasing={'marker': {'color': '#22c55e'}},
            totals={'marker': {'color': '#3b82f6'}}
        ))
        fig2.update_layout(title='Deckungsbeitrag Aufschluesselung', height=400, yaxis_title='Euro')
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Top & Flop Performer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        top_revenue = df_month.nlargest(10, 'Umsaetze')[['Maschinennummer', 'Beschreibung', 'Umsaetze']]
        
        fig3 = go.Figure(go.Bar(
            x=top_revenue['Umsaetze'],
            y=top_revenue['Maschinennummer'].astype(str),
            orientation='h',
            marker_color='#22c55e',
            text=top_revenue['Umsaetze'].apply(lambda x: f'EUR {x:,.0f}'),
            textposition='outside'
        ))
        fig3.update_layout(title='Top 10 Maschinen nach Umsatz', height=500, xaxis_title='Umsatz', yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        worst_db = df_month.nsmallest(10, 'DB')[['Maschinennummer', 'Beschreibung', 'DB']]
        
        fig4 = go.Figure(go.Bar(
            x=worst_db['DB'],
            y=worst_db['Maschinennummer'].astype(str),
            orientation='h',
            marker_color='#ef4444',
            text=worst_db['DB'].apply(lambda x: f'EUR {x:,.0f}'),
            textposition='outside'
        ))
        fig4.update_layout(title='Top 10 Schlechteste Maschinen (DB)', height=500, xaxis_title='Deckungsbeitrag', yaxis=dict(autorange='reversed'))
        st.plotly_chart(fig4, use_container_width=True)
    


with tab3:
    st.subheader("Alle Maschinen im Detail")
    
    search = st.text_input("Suche nach Maschinennummer oder Beschreibung")
    if search:
        df_display = df_month[
            df_month['Maschinennummer'].astype(str).str.contains(search, case=False, na=False) |
            df_month['Beschreibung'].astype(str).str.contains(search, case=False, na=False)
        ]
    else:
        df_display = df_month
    
    sort_by = st.selectbox("Sortieren nach", ['DB', 'Umsaetze', 'Kosten', 'Maschinennummer'])
    ascending = st.checkbox("Aufsteigend", value=False)
    
    df_display = df_display.sort_values(by=sort_by, ascending=ascending)
    
    df_display['Marge %'] = (df_display['DB'] / df_display['Umsaetze'] * 100).fillna(0).round(1)
    
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
        label="Export als CSV",
        data=df_display.to_csv(index=False).encode('utf-8'),
        file_name=f'maschinen_export_{selected_month}.csv',
        mime='text/csv'
    )
