import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# Konfiguration
st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide", page_icon="📊")

def find_nl(text, nl_map):
    """Findet Niederlassung aus Text"""
    if pd.isna(text):
        return None
    text = str(text).upper().strip()
    
    # Exakte Matches
    if text in nl_map:
        return text
    
    # Teil-Matches
    for nl in nl_map.keys():
        if nl in text:
            return nl
    
    # Spezialfälle
    special = {
        'OWF': 'OSTWESTFALEN', 'OWL': 'OSTWESTFALEN',
        'HAMBRUG': 'HAMBURG', 'AUSGBURG': 'AUGSBURG',
        'PHILLIPSBURG': 'PHILIPPSBURG'
    }
    for key, val in special.items():
        if key in text:
            return val
    
    return None

def load_data(nl_file, main_file):
    """Lädt und verarbeitet die Excel-Dateien"""
    
    # NL-Mapping laden
    nl_df = pd.read_excel(nl_file)
    nl_map = dict(zip(
        nl_df.iloc[:, 2].str.upper().str.strip(), 
        nl_df.iloc[:, 2].str.strip()
    ))
    
    # Hauptdatei laden
    df = pd.read_excel(main_file)
    
    # NL zuordnen (Spalte H = Index 7)
    df['NL'] = df.iloc[:, 7].apply(lambda x: find_nl(x, nl_map))
    df['NL_Name'] = df['NL'].map(lambda x: nl_map.get(x, x) if x else None)
    
    return df, nl_map

def aggregate_monthly(df, nl_filter=None):
    """Aggregiert monatliche Daten"""
    if nl_filter and nl_filter != 'Alle':
        df = df[df['NL'] == nl_filter]
    
    months = {
        'Jan': ('Kosten Jan 25', 'Umsätze Jan 25'),
        'Feb': ('Kosten Feb 25', 'Umsätze Feb 25'),
        'Mär': ('Kosten Mar 25', 'Umsätze Mar 25'),
        'Apr': ('Kosten Apr 25', 'Umsätze Apr 25'),
        'Mai': ('Kosten Mai 25', 'Umsätze Mai 25'),
        'Jun': ('Kosten Jun 25', 'Umsätze Jun 25'),
        'Jul': ('Kosten Jul 25', 'Umsätze Jul 25'),
        'Aug': ('Kosten Aug 25', 'Umsätze Aug 25')
    }
    
    results = []
    for month, (k_col, u_col) in months.items():
        kosten = df[k_col].sum()
        umsatz = df[u_col].sum()
        db = umsatz - kosten
        marge = (db / umsatz * 100) if umsatz > 0 else 0
        
        results.append({
            'Monat': month,
            'Umsatz': umsatz,
            'Kosten': kosten,
            'DB': db,
            'Marge': marge
        })
    
    return pd.DataFrame(results)

def get_top_verlust(df, nl_filter=None, top_n=5):
    """Top Verlust-Projekte März -> April"""
    if nl_filter and nl_filter != 'Alle':
        df = df[df['NL'] == nl_filter]
    
    df = df[df['Umsätze Mar 25'] > 1000].copy()
    
    df['März_DB'] = df['Umsätze Mar 25'] - df['Kosten Mar 25']
    df['April_DB'] = df['Umsätze Apr 25'] - df['Kosten Apr 25']
    df['DB_Change'] = df['April_DB'] - df['März_DB']
    
    top = df.nsmallest(top_n, 'DB_Change')
    
    return top[['VH-nr.', 'Code', 'Omschrijving', 'Umsätze Mar 25', 'Umsätze Apr 25', 'DB_Change', 'NL_Name']]

def main():
    st.title("📊 AGRO F66 Dashboard")
    st.caption("Januar bis August 2025")
    
    # Sidebar für File Upload
    with st.sidebar:
        st.markdown("### 📁 Dateien hochladen")
        
        nl_file = st.file_uploader(
            "NL-Mapping Datei",
            type=['xlsx'],
            help="AGRO NL Relatie Nr.xlsx"
        )
        
        main_file = st.file_uploader(
            "Hauptdatei",
            type=['xlsx'],
            help="V10 F66 AGRO Jan Aug 2025.xlsx"
        )
        
        st.divider()
        
        if nl_file and main_file:
            st.success("✅ Beide Dateien hochgeladen")
        else:
            st.warning("⚠️ Bitte beide Dateien hochladen")
    
    # Wenn beide Dateien hochgeladen sind
    if nl_file and main_file:
        try:
            # Daten laden
            with st.spinner("Lade Daten..."):
                df, nl_map = load_data(nl_file, main_file)
            
            # Sidebar Statistiken
            with st.sidebar:
                st.markdown("### 📊 Statistiken")
                monthly_all = aggregate_monthly(df)
                total_umsatz = monthly_all['Umsatz'].sum()
                total_kosten = monthly_all['Kosten'].sum()
                total_db = total_umsatz - total_kosten
                avg_marge = (total_db / total_umsatz * 100) if total_umsatz > 0 else 0
                
                st.metric("Gesamt-Umsatz", f"{total_umsatz:,.0f} €")
                st.metric("Gesamt-Kosten", f"{total_kosten:,.0f} €")
                st.metric("Gesamt-DB", f"{total_db:,.0f} €")
                st.metric("Ø Marge", f"{avg_marge:.2f}%")
                
                st.caption(f"📈 {len(df):,} Datensätze verarbeitet")
            
            # Niederlassungs-Filter
            nl_sorted = df.groupby('NL')['Umsätze Jan 25'].sum().sort_values(ascending=False).index.tolist()
            nl_options = ['Alle'] + [nl for nl in nl_sorted if nl and nl in nl_map]
            
            st.divider()
            
            cols = st.columns([1, 5])
            with cols[0]:
                st.markdown("**Niederlassung:**")
            with cols[1]:
                selected_nl = st.selectbox(
                    "Filter",
                    nl_options,
                    format_func=lambda x: x if x == 'Alle' else nl_map.get(x, x),
                    label_visibility="collapsed"
                )
            
            nl_display = "Alle Niederlassungen" if selected_nl == 'Alle' else nl_map.get(selected_nl, selected_nl)
            st.markdown(f"### {nl_display}")
            
            # Monatliche Daten aggregieren
            monthly_df = aggregate_monthly(df, selected_nl)
            
            # Charts - Obere Zeile
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Monatliche Entwicklung: Umsatz vs Kosten")
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(
                    x=monthly_df['Monat'], 
                    y=monthly_df['Umsatz'], 
                    name='Umsatz', 
                    marker_color='#3b82f6',
                    text=monthly_df['Umsatz'].apply(lambda x: f"{x/1000:.0f}k"),
                    textposition='outside'
                ))
                fig1.add_trace(go.Bar(
                    x=monthly_df['Monat'], 
                    y=monthly_df['Kosten'], 
                    name='Kosten', 
                    marker_color='#ef4444',
                    text=monthly_df['Kosten'].apply(lambda x: f"{x/1000:.0f}k"),
                    textposition='outside'
                ))
                fig1.update_layout(
                    height=350, 
                    margin=dict(t=20, b=20, l=20, r=20), 
                    legend=dict(orientation='h', y=-0.15),
                    hovermode='x unified'
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.markdown("#### DB-Margen Entwicklung")
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=monthly_df['Monat'], 
                    y=monthly_df['Marge'], 
                    mode='lines+markers',
                    name='DB-Marge %',
                    line=dict(color='#f59e0b', width=3),
                    marker=dict(size=10),
                    text=monthly_df['Marge'].apply(lambda x: f"{x:.1f}%"),
                    textposition='top center'
                ))
                fig2.add_hline(
                    y=20, 
                    line_dash="dash", 
                    line_color="red", 
                    annotation_text="Ziel: 20%",
                    annotation_position="right"
                )
                fig2.update_layout(
                    height=350, 
                    margin=dict(t=20, b=20, l=20, r=20),
                    yaxis=dict(range=[0, max(30, monthly_df['Marge'].max() + 5)], ticksuffix='%'),
                    legend=dict(orientation='h', y=-0.15),
                    hovermode='x unified'
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Charts - Untere Zeile
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### Top 5 Verlust-Projekte (März → April)")
                verlust_df = get_top_verlust(df, selected_nl, 5)
                
                if len(verlust_df) > 0:
                    display_df = verlust_df.copy()
                    display_df.columns = ['VH-Nr', 'Code', 'Beschreibung', 'März €', 'April €', 'Δ DB €', 'NL']
                    display_df['März €'] = display_df['März €'].apply(lambda x: f"{x:,.0f} €")
                    display_df['April €'] = display_df['April €'].apply(lambda x: f"{x:,.0f} €")
                    display_df['Δ DB €'] = display_df['Δ DB €'].apply(lambda x: f"{x:,.0f} €")
                    display_df['Beschreibung'] = display_df['Beschreibung'].str[:25]
                    
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        height=350
                    )
                else:
                    st.info("Keine Verlust-Projekte gefunden")
            
            with col4:
                st.markdown("#### Zusätzliche Analyse")
                
                # Zeige Margen-Vergleich
                avg_marge_filtered = monthly_df['Marge'].mean()
                
                col4a, col4b = st.columns(2)
                with col4a:
                    st.metric(
                        "Ø Marge", 
                        f"{avg_marge_filtered:.2f}%",
                        delta=f"{avg_marge_filtered - 20:.2f}% vs Ziel"
                    )
                with col4b:
                    best_month = monthly_df.loc[monthly_df['Marge'].idxmax()]
                    st.metric(
                        "Beste Marge",
                        f"{best_month['Marge']:.2f}%",
                        delta=best_month['Monat']
                    )
                
                # Margen-Trend Indikator
                trend = monthly_df['Marge'].iloc[-1] - monthly_df['Marge'].iloc[0]
                if trend > 0:
                    st.success(f"📈 Positiver Trend: +{trend:.2f}% (Jan→Aug)")
                else:
                    st.error(f"📉 Negativer Trend: {trend:.2f}% (Jan→Aug)")
                
                # Kritische Monate
                critical_months = monthly_df[monthly_df['Marge'] < 15]
                if len(critical_months) > 0:
                    st.warning(f"⚠️ {len(critical_months)} Monat(e) unter 15% Marge")
                
        except Exception as e:
            st.error(f"❌ Fehler beim Verarbeiten der Daten: {e}")
            st.exception(e)
    
    else:
        # Anleitung wenn keine Dateien hochgeladen
        st.info("👆 Bitte laden Sie beide Excel-Dateien in der Sidebar hoch, um das Dashboard zu starten.")
        
        with st.expander("ℹ️ Anleitung"):
            st.markdown("""
            ### So verwenden Sie das Dashboard:
            
            1. **Dateien hochladen** (in der Sidebar links):
               - `AGRO NL Relatie Nr.xlsx` - Niederlassungs-Mapping
               - `V10 F66 AGRO Jan Aug 2025.xlsx` - Hauptdatei mit Umsätzen/Kosten
            
            2. **Niederlassung auswählen** - Filter nach spezifischer Niederlassung oder "Alle"
            
            3. **Dashboard analysieren**:
               - Monatliche Umsatz- und Kostenentwicklung
               - DB-Margen Trend mit 20% Ziellinie
               - Top 5 Verlust-Projekte (März → April)
            
            4. **Daten aktualisieren** - Einfach neue Dateien hochladen
            """)

if __name__ == "__main__":
    main()
