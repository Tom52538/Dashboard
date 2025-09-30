import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Konfiguration
st.set_page_config(page_title="AGRO F66 Dashboard", layout="wide", page_icon="📊")

def find_nl(text, nl_map):
    """Findet Niederlassung aus Text"""
    if pd.isna(text):
        return None
    text = str(text).upper().strip()
    
    if text in nl_map:
        return text
    
    for nl in nl_map.keys():
        if nl in text:
            return nl
    
    special = {
        'OWF': 'OSTWESTFALEN', 'OWL': 'OSTWESTFALEN',
        'HAMBRUG': 'HAMBURG', 'AUSGBURG': 'AUGSBURG',
        'PHILLIPSBURG': 'PHILIPPSBURG'
    }
    
    for key, val in special.items():
        if key in text:
            return val
    
    return None

def load_data(masterfile, nl_file):
    """Lädt Masterfile und NL-Mapping"""
    
    # Masterfile laden
    df = pd.read_excel(masterfile)
    
    # NL-Mapping laden
    nl_df = pd.read_excel(nl_file)
    nl_map = dict(zip(nl_df.iloc[:, 2].str.upper().str.strip(), nl_df.iloc[:, 2].str.strip()))
    
    # NL zuordnen
    df['NL'] = df['Ordernr. klant'].apply(lambda x: find_nl(x, nl_map))
    df['NL_Name'] = df['NL'].map(lambda x: nl_map.get(x, x) if x else None)
    
    return df, nl_map

def aggregate_monthly(df, nl_filter=None):
    """Aggregiert monatliche Daten"""
    if nl_filter and nl_filter != 'Alle':
        df = df[df['NL'] == nl_filter]
    
    months = ['Jan 25', 'Feb 25', 'Mar 25', 'Apr 25', 'Mai 25', 'Jun 25', 'Jul 25', 'Aug 25']
    
    results = []
    for month in months:
        kosten_col = f'Kosten {month}'
        umsatz_col = f'Umsätze {month}'
        db_col = f'DB {month}'
        
        kosten = df[kosten_col].sum() if kosten_col in df.columns else 0
        umsatz = df[umsatz_col].sum() if umsatz_col in df.columns else 0
        db = df[db_col].sum() if db_col in df.columns else (umsatz - kosten)
        marge = (db / umsatz * 100) if umsatz > 0 else 0
        
        results.append({
            'Monat': month.split()[0],
            'Umsatz': umsatz,
            'Kosten': kosten,
            'DB': db,
            'Marge': marge
        })
    
    return pd.DataFrame(results)

def get_top_verlust(df, nl_filter=None, top_n=5):
    """Top 5 Maschinen mit schlechtestem Gesamt-DB (YTD)"""
    if nl_filter and nl_filter != 'Alle':
        df = df[df['NL'] == nl_filter]
    
    months = ['Jan 25', 'Feb 25', 'Mar 25', 'Apr 25', 'Mai 25', 'Jun 25', 'Jul 25', 'Aug 25']
    
    df_copy = df.copy()
    
    db_cols = [f'DB {m}' for m in months if f'DB {m}' in df.columns]
    df_copy['Gesamt_DB'] = df_copy[db_cols].sum(axis=1)
    
    umsatz_cols = [f'Umsätze {m}' for m in months if f'Umsätze {m}' in df.columns]
    df_copy['Gesamt_Umsatz'] = df_copy[umsatz_cols].sum(axis=1)
    
    df_copy = df_copy[df_copy['Gesamt_Umsatz'] > 5000]
    
    top = df_copy.nsmallest(top_n, 'Gesamt_DB')
    
    result_data = []
    
    for idx, row in top.iterrows():
        row_data = {
            'VH-nr.': row['VH-nr.'],
            'Code': row['Code'],
            'Omschrijving': row['Omschrijving'],
            'Gesamt_DB': row['Gesamt_DB'],
            'Gesamt_Umsatz': row['Gesamt_Umsatz'],
            'NL_Name': row['NL_Name']
        }
        
        for month in months:
            umsatz_col = f'Umsätze {month}'
            db_col = f'DB {month}'
            
            if all(col in df.columns for col in [umsatz_col, db_col]):
                umsatz = row[umsatz_col]
                db = row[db_col]
                marge = (db / umsatz * 100) if umsatz > 0 else 0
                row_data[f'Marge_{month.split()[0]}'] = marge
            else:
                row_data[f'Marge_{month.split()[0]}'] = 0
        
        result_data.append(row_data)
    
    return pd.DataFrame(result_data)

def main():
    st.title("📊 AGRO F66 Dashboard")
    st.caption("Januar bis August 2025")
    
    # Sidebar für File Upload
    with st.sidebar:
        st.markdown("### 📁 Dateien hochladen")
        
        masterfile = st.file_uploader(
            "Masterfile",
            type=['xlsx'],
            help="Dashboard_Master.xlsx"
        )
        
        nl_file = st.file_uploader(
            "NL-Mapping Datei",
            type=['xlsx'],
            help="04_AGRO NL Relatie Nr.xlsx"
        )
        
        st.divider()
        
        if masterfile and nl_file:
            st.success("✅ Beide Dateien hochgeladen")
        else:
            st.warning("⚠️ Bitte beide Dateien hochladen")
    
    if masterfile and nl_file:
        try:
            with st.spinner("Lade Daten..."):
                df, nl_map = load_data(masterfile, nl_file)
            
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
                
                st.caption(f"📈 {len(df):,} Maschinen")
            
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
                
                min_marge = monthly_df['Marge'].min()
                max_marge = monthly_df['Marge'].max()
                y_min = min(0, min_marge - 5)
                y_max = max(30, max_marge + 5)
                
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
                    yaxis=dict(range=[y_min, y_max], ticksuffix='%', zeroline=True, zerolinewidth=2, zerolinecolor='gray'),
                    legend=dict(orientation='h', y=-0.15),
                    hovermode='x unified'
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Charts - Untere Zeile
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("#### Top 5 Worst Performing Maschinen (YTD)")
                verlust_df = get_top_verlust(df, selected_nl, 5)
                
                if len(verlust_df) > 0:
                    display_df = verlust_df.copy()
                    
                    display_df['Gesamt DB'] = display_df['Gesamt_DB'].apply(lambda x: f"{x:,.0f} €")
                    display_df['Code'] = display_df['Code'].str[:12]
                    display_df['Beschreibung'] = display_df['Omschrijving'].str[:15]
                    
                    marge_cols = ['Marge_Jan', 'Marge_Feb', 'Marge_Mär', 'Marge_Apr', 
                                 'Marge_Mai', 'Marge_Jun', 'Marge_Jul', 'Marge_Aug']
                    
                    for col in marge_cols:
                        if col in display_df.columns:
                            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%")
                    
                    show_cols = ['Code', 'Beschreibung', 'Gesamt DB'] + marge_cols
                    display_df = display_df[show_cols]
                    
                    display_df.columns = ['Code', 'Beschreibung', 'YTD DB', 'Jan', 'Feb', 'Mär', 
                                          'Apr', 'Mai', 'Jun', 'Jul', 'Aug']
                    
                    st.dataframe(
                        display_df, 
                        use_container_width=True, 
                        hide_index=True,
                        height=250
                    )
                    
                    st.caption("📊 Margen in % | YTD = Gesamt-DB Jan-Aug")
                else:
                    st.info("Keine signifikanten Verluste gefunden")
            
            with col4:
                st.markdown("#### Zusätzliche Analyse")
                
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
                
                trend = monthly_df['Marge'].iloc[-1] - monthly_df['Marge'].iloc[0]
                if trend > 0:
                    st.success(f"📈 Positiver Trend: +{trend:.2f}% (Jan→Aug)")
                else:
                    st.error(f"📉 Negativer Trend: {trend:.2f}% (Jan→Aug)")
                
                critical_months = monthly_df[monthly_df['Marge'] < 15]
                if len(critical_months) > 0:
                    st.warning(f"⚠️ {len(critical_months)} Monat(e) unter 15% Marge")
                
        except Exception as e:
            st.error(f"❌ Fehler beim Verarbeiten: {e}")
            st.exception(e)
    
    else:
        st.info("👆 Bitte laden Sie beide Dateien in der Sidebar hoch")
        
        with st.expander("ℹ️ Workflow"):
            st.markdown("""
            ### So nutzen Sie das Dashboard:
            
            **1. Daten vorbereiten (auf Ihrem PC):**
            ```
            cd "K:\\Umsatz pro Maschine Dashboard"
            python create_masterfile.py
            ```
            Dies erstellt `Dashboard_Master.xlsx` aus den Rohdaten.
            
            **2. Dateien hochladen (in der Sidebar):**
            - Dashboard_Master.xlsx
            - 04_AGRO NL Relatie Nr.xlsx
            
            **3. Dashboard nutzen:**
            - Niederlassung filtern
            - Margen analysieren
            - Problem-Maschinen identifizieren
            
            **4. Daten aktualisieren:**
            - Script neu ausführen → neue Masterfile
            - Masterfile im Dashboard hochladen → fertig
            """)

if __name__ == "__main__":
    main()
