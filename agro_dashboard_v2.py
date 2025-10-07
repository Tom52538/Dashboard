# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
from io import BytesIO
import json
import hashlib
import csv

# ========================================
# SICHERHEITS-FUNKTIONEN
# ========================================

def log_download(user, filename, niederlassung, num_rows):
    """Protokolliert jeden Download für Audit"""
    log_file = 'download_log.csv'
    log_exists = os.path.exists(log_file)
    
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow(['Timestamp', 'User', 'Filename', 'Niederlassung', 'Rows'])
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user,
            filename,
            niederlassung,
            num_rows
        ])

def filter_export_columns(df):
    """Entfernt sensible Spalten aus Exports"""
    sensitive_cols = ['Omschrijving']
    export_cols = [col for col in df.columns if col not in sensitive_cols]
    return df[export_cols]

def to_excel_secure(df, user_info, filename):
    """Erstellt Excel mit Wasserzeichen und Sicherheit"""
    df_export = filter_export_columns(df)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Daten')
        
        worksheet = writer.sheets['Daten']
        
        from openpyxl.comments import Comment
        watermark = f"Exportiert von: {user_info['name']}\nDatum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\nNiederlassung: {user_info.get('filter', 'Alle')}"
        worksheet['A1'].comment = Comment(watermark, "AGRO F66 System")
        
        for idx, col in enumerate(df_export.columns):
            max_length = max(
                df_export[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    log_download(
        user_info['name'],
        filename,
        user_info.get('filter', 'Alle'),
        len(df_export)
    )
    
    return output.getvalue()

def to_excel(df):
    """Konvertiert DataFrame zu Excel-Bytes für Download (normaler Export)"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Daten')
        
        worksheet = writer.sheets['Daten']
        
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    return output.getvalue()

# ========================================
# LOGIN-SYSTEM
# ========================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ users.json nicht gefunden!")
        st.stop()

def check_login(username, password):
    users = load_users()
    username = username.lower().strip()
    
    if username in users:
        if users[username]['password'] == hash_password(password):
            return users[username]
    return None

def login_page():
    st.set_page_config(page_title="AGRO F66 Login", layout="wide")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🚜 AGRO F66")
        st.subheader("Maschinen Dashboard v2.0")
        st.markdown("---")
        
        with st.form("login_form"):
            username = st.text_input("Benutzername", key="login_username")
            password = st.text_input("Passwort", type="password", key="login_password")
            submit = st.form_submit_button("Anmelden", use_container_width=True)
            
            if submit:
                user_data = check_login(username, password)
                if user_data:
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = username
                    st.session_state['user_data'] = user_data
                    st.rerun()
                else:
                    st.error("❌ Ungültiger Benutzername oder Passwort")
        
        st.markdown("---")
        st.caption("Version 2.0 mit KI-Chat | Bei Problemen Admin kontaktieren")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = None
    st.session_state['user_data'] = None
    if 'chat_messages' in st.session_state:
        del st.session_state['chat_messages']
    st.rerun()

# Prüfe Login-Status
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
    st.stop()

# Ab hier: Benutzer ist eingeloggt
user_data = st.session_state['user_data']
is_admin = user_data['role'] == 'admin'
user_niederlassung = user_data['niederlassung']

# ========================================
# DASHBOARD CODE
# ========================================

# Page Config NACH Login
st.set_page_config(page_title="AGRO F66 Dashboard v2", layout="wide")

# Header
col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
with col_header1:
    st.title("AGRO F66 Dashboard v2.0 🤖")
with col_header2:
    st.info(f"👤 **{user_data['name']}**")
with col_header3:
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# Daten laden
@st.cache_data(ttl=3600)
def load_data():
    """Lädt Dashboard_Master_DE_v2.xlsx mit neuen Übersetzungen"""
    try:
        df = pd.read_excel("Dashboard_Master_DE_v2.xlsx", dtype={'VH-nr.': str})
        
        if 'VH-nr.' in df.columns:
            df['VH-nr.'] = df['VH-nr.'].astype(str).str.strip()
        
        kosten_spalten = [col for col in df.columns if 'Kosten' in col]
        umsatz_spalten = [col for col in df.columns if 'Umsätze' in col]
        db_spalten = [col for col in df.columns if 'DB' in col]
        
        for col in kosten_spalten + umsatz_spalten + db_spalten:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    except FileNotFoundError:
        st.error("❌ Dashboard_Master_DE_v2.xlsx nicht gefunden!")
        st.stop()
    except Exception as e:
        st.error(f"❌ Fehler: {e}")
        st.stop()

def get_file_info():
    """Zeigt Datei-Informationen und prüft ob Datei aktualisiert wurde"""
    if os.path.exists("Dashboard_Master_DE_v2.xlsx"):
        timestamp = os.path.getmtime("Dashboard_Master_DE_v2.xlsx")
        last_update = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")
        file_size = os.path.getsize("Dashboard_Master_DE_v2.xlsx") / (1024 * 1024)
        
        cache_key = 'file_timestamp'
        if cache_key not in st.session_state:
            st.session_state[cache_key] = timestamp
        elif st.session_state[cache_key] != timestamp:
            st.cache_data.clear()
            st.session_state[cache_key] = timestamp
            st.rerun()
        
        return last_update, file_size
    return "Unbekannt", 0

# Info-Banner
last_update, file_size = get_file_info()
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.info(f"📅 **Update:** {last_update}")
with col_info2:
    st.info(f"💾 **Größe:** {file_size:.2f} MB")

df = load_data()

with col_info3:
    st.success(f"✅ **{len(df):,} Datensätze**")

if st.button("🔄 Neu laden"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")

# Monate extrahieren
cost_cols = [col for col in df.columns if col.startswith('Kosten ') and 'YTD' not in col]
months = [col.replace('Kosten ', '') for col in cost_cols]

# Niederlassungs-Optionen
has_nl = 'Niederlassung' in df.columns

if has_nl:
    nl_options = ['Gesamt'] + sorted([nl for nl in df['Niederlassung'].unique() if nl != 'Unbekannt'])
else:
    nl_options = ['Gesamt']

# ========================================
# SIDEBAR: Filter + Chat
# ========================================

with st.sidebar:
    st.header("⚙️ Filter")
    
    # Admin / Niederlassung
    if is_admin:
        st.success("🔓 **Admin-Zugriff**")
        master_nl_filter = st.selectbox("Niederlassung", nl_options, key='master_nl')
    else:
        st.warning(f"🔒 **Zugriff beschränkt**")
        st.info(f"**Niederlassung:** {user_niederlassung}")
        master_nl_filter = user_niederlassung
    
    st.markdown("---")
    
    # Produkt-Filter
    st.markdown("### 📦 Produkt-Filter")
    
    has_product_cols = '1. Product Family' in df.columns
    
    if has_product_cols:
        product_families = ['Alle'] + sorted([f for f in df['1. Product Family'].dropna().unique() if str(f) != 'nan'])
        selected_family = st.selectbox("Product Family", product_families, key='pf')
        
        if selected_family != 'Alle':
            df_filtered_for_group = df[df['1. Product Family'] == selected_family]
        else:
            df_filtered_for_group = df
        
        product_groups = ['Alle'] + sorted([g for g in df_filtered_for_group['2. Product Group'].dropna().unique() if str(g) != 'nan'])
        selected_group = st.selectbox("Product Group", product_groups, key='pg')
    else:
        selected_family = 'Alle'
        selected_group = 'Alle'
    
    st.markdown("---")
    show_active = st.checkbox("Nur Maschinen mit YTD-Aktivität", value=True)
    
    # Basis-Filterung
    df_base = df.copy()
    if show_active:
        df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]
    
    if master_nl_filter != 'Gesamt' and has_nl:
        df_base = df_base[df_base['Niederlassung'] == master_nl_filter]
    
    if has_product_cols:
        if selected_family != 'Alle':
            df_base = df_base[df_base['1. Product Family'] == selected_family]
        if selected_group != 'Alle':
            df_base = df_base[df_base['2. Product Group'] == selected_group]
    
    # Speichere Filter für Export
    user_data['filter'] = master_nl_filter
    
    st.metric("Gefilterte Maschinen", f"{len(df_base):,}")
    st.metric("Ausgewählte NL", master_nl_filter)
    if has_product_cols and selected_family != 'Alle':
        st.metric("Produkt-Filter", f"{selected_family}")
    
    # ========================================
    # CHAT BEREICH
    # ========================================
    
    st.markdown("---")
    st.markdown("### 💬 Frag deine Daten")
    st.caption("Powered by Claude AI")
    
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    
    # Chat Container
    with st.container():
        if len(st.session_state['chat_messages']) == 0:
            st.info("👋 Stell mir eine Frage!")
            st.markdown("**Beispiele:**")
            st.markdown("• Top 5 Maschinen?")
            st.markdown("• Verluste in Leipzig?")
            st.markdown("• Marge-Trend?")
        else:
            for msg in st.session_state['chat_messages'][-5:]:  # Nur letzte 5
                if msg['role'] == 'user':
                    st.markdown(f"**Du:** {msg['content']}")
                else:
                    st.markdown(f"🤖 {msg['content']}")
    
    # Chat Input
    user_question = st.text_input("Deine Frage:", key="chat_input", placeholder="z.B. Welche Maschine läuft am besten?")
    
    col_send, col_clear = st.columns([3, 1])
    
    with col_send:
        if st.button("📤 Senden", use_container_width=True, disabled=not user_question):
            if user_question:
                st.session_state['chat_messages'].append({
                    'role': 'user',
                    'content': user_question
                })
                
                response = f"Ich analysiere: '{user_question}'. Diese Funktion wird bald aktiviert."
                
                st.session_state['chat_messages'].append({
                    'role': 'assistant',
                    'content': response
                })
                
                st.rerun()
    
    with col_clear:
        if st.button("🗑️", use_container_width=True, help="Chat löschen"):
            st.session_state['chat_messages'] = []
            st.rerun()
    
    st.caption("🔒 Chat-Daten werden nicht gespeichert")

# ========================================
# MAIN DASHBOARD CONTENT (FULLWIDTH!)
# ========================================
    
# === ÜBERSICHT ===
st.header("📊 Übersicht")

ytd_kosten = df_base['Kosten YTD'].sum()
ytd_umsaetze = df_base['Umsätze YTD'].sum()
ytd_db = df_base['DB YTD'].sum()
ytd_marge = (ytd_db / ytd_umsaetze * 100) if ytd_umsaetze != 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("YTD Kosten", f"€ {ytd_kosten:,.0f}")
with col2:
    st.metric("YTD Umsätze", f"€ {ytd_umsaetze:,.0f}")
with col3:
    st.metric("YTD DB", f"€ {ytd_db:,.0f}", delta=f"{ytd_marge:.1f}%")
with col4:
    st.metric("YTD Marge", f"{ytd_marge:.1f}%")
    
    # === MONATLICHE ENTWICKLUNG ===
    st.header("📈 Monatliche Entwicklung")
    
    monthly_data = []
    for month in months:
        cost_col = f'Kosten {month}'
        rev_col = f'Umsätze {month}'
        db_col = f'DB {month}'
        
        monthly_data.append({
            'Monat': month,
            'Kosten': df_base[cost_col].sum(),
            'Umsaetze': df_base[rev_col].sum(),
            'DB': df_base[db_col].sum()
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
    
    fig.add_trace(go.Bar(name='Umsätze', x=df_monthly['Monat'], y=df_monthly['Umsaetze'], 
                         marker_color='#22c55e', text=df_monthly['Umsaetze'].apply(lambda x: f'€{x/1000:.0f}k'),
                         textposition='outside'), row=1, col=1)
    fig.add_trace(go.Bar(name='Kosten', x=df_monthly['Monat'], y=df_monthly['Kosten'], 
                         marker_color='#ef4444', text=df_monthly['Kosten'].apply(lambda x: f'€{x/1000:.0f}k'),
                         textposition='outside'), row=1, col=1)
    
    colors_db = ['#22c55e' if x >= 0 else '#ef4444' for x in df_monthly['DB']]
    fig.add_trace(go.Bar(name='DB (€)', x=df_monthly['Monat'], y=df_monthly['DB'], 
                         marker_color=colors_db, showlegend=False,
                         text=df_monthly['DB'].apply(lambda x: f'€{x/1000:.0f}k'),
                         textposition='outside'), row=1, col=2)
    
    colors_marge = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_monthly['Marge %']]
    fig.add_trace(go.Bar(name='Marge %', x=df_monthly['Monat'], y=df_monthly['Marge %'], 
                         marker_color=colors_marge, showlegend=False,
                         text=df_monthly['Marge %'].apply(lambda x: f'{x:.1f}%'),
                         textposition='outside'), row=2, col=1)
    
    df_monthly['Kum_Umsaetze'] = df_monthly['Umsaetze'].cumsum()
    df_monthly['Kum_DB'] = df_monthly['DB'].cumsum()
    fig.add_trace(go.Scatter(name='Kum. Umsätze', x=df_monthly['Monat'], y=df_monthly['Kum_Umsaetze'],
                             mode='lines+markers', line=dict(color='#22c55e', width=3)), row=2, col=2)
    fig.add_trace(go.Scatter(name='Kum. DB', x=df_monthly['Monat'], y=df_monthly['Kum_DB'],
                             mode='lines+markers', line=dict(color='#3b82f6', width=3)), row=2, col=2)
    
    fig.update_layout(height=800, showlegend=True, barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # === TOP 10 MASCHINEN ===
    st.header("🏆 Top 10 Maschinen")
    
    sort_top = st.selectbox(
        "Sortieren nach:",
        ["DB YTD (Höchster Gewinn)", "Umsätze YTD (Höchster Umsatz)", "Marge YTD % (Beste Marge)", "Kosten YTD (Höchste Kosten)"],
        key='sort_top_10'
    )
    
    df_top_relevant = df_base[df_base['Umsätze YTD'] >= 1000]
    
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
            label="📥 Sicher exportieren (Excel)",
            data=to_excel_secure(top_10_display, user_data, f'top_10_{master_nl_filter}.xlsx'),
            file_name=f'top_10_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            help="🔒 Export ohne Beschreibungen, mit Wasserzeichen"
        )
    
    with col2:
        fig_top = go.Figure()
        
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
            showlegend=True
        )
        st.plotly_chart(fig_top, use_container_width=True)
    
    # === WORST 10 MASCHINEN ===
    st.header("⚠️ Worst 10 Maschinen")
    
    sort_worst = st.selectbox(
        "Sortieren nach:",
        ["DB YTD (Niedrigster/Negativster)", "Marge YTD % (Schlechteste Marge)", "Kosten YTD (Höchste Kosten)", "Umsätze YTD (Niedrigster Umsatz)"],
        key='sort_worst_10'
    )
    
    df_worst_relevant = df_base[df_base['Kosten YTD'] >= 1000]
    
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
            label="📥 Sicher exportieren (Excel)",
            data=to_excel_secure(worst_10_display, user_data, f'worst_10_{master_nl_filter}.xlsx'),
            file_name=f'worst_10_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            help="🔒 Export ohne Beschreibungen, mit Wasserzeichen"
        )
    
    with col2:
        fig_worst = go.Figure()
        
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
        
        colors_worst_db = ['#22c55e' if x >= 0 else '#ef4444' for x in worst_10_display['DB YTD']]
        fig_worst.add_trace(go.Bar(
            name='DB',
            y=y_labels_worst,
            x=worst_10_display['DB YTD'],
            orientation='h',
            marker_color=colors_worst_db,
            text=worst_10_display['DB YTD'].apply(lambda x: f'€{x/1000:.0f}k' if x != 0 else ''),
            textposition='inside'
        ))
        
        fig_worst.update_layout(
            barmode='stack',
            height=400,
            xaxis_title='Euro (€)',
            yaxis=dict(autorange='reversed'),
            showlegend=True
        )
        st.plotly_chart(fig_worst, use_container_width=True)
    
    # === MONATSTABELLE ===
    st.header("📅 Detaillierte Monatsdaten")
    
    monthly_table = []
    for month in months:
        cost_col = f'Kosten {month}'
        rev_col = f'Umsätze {month}'
        db_col = f'DB {month}'
        
        monthly_table.append({
            'Monat': month,
            'Kosten': df_base[cost_col].sum(),
            'Umsaetze': df_base[rev_col].sum(),
            'DB': df_base[db_col].sum()
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
        
        styled_table = df_table.style.format({
            'Kosten': '€ {:,.0f}',
            'Umsaetze': '€ {:,.0f}',
            'DB': '€ {:,.0f}',
            'Marge %': '{:.1f}%'
        }).applymap(highlight_marge, subset=['Marge %'])
        
        st.dataframe(styled_table, use_container_width=True, height=400)
        
        st.download_button(
            label="📥 Export Monatsdaten (Excel)",
            data=to_excel(df_table),
            file_name=f'monatsdaten_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
    
    with col2:
        fig_mini = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Monatliche Marge %', 'DB-Entwicklung (€)'),
            row_heights=[0.5, 0.5]
        )
        
        colors_trend = ['#22c55e' if x >= 10 else '#f59e0b' if x >= 5 else '#ef4444' for x in df_table['Marge %']]
        fig_mini.add_trace(go.Bar(
            x=df_table['Monat'],
            y=df_table['Marge %'],
            marker_color=colors_trend,
            text=df_table['Marge %'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside',
            showlegend=False
        ), row=1, col=1)
        
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
        st.plotly_chart(fig_mini, use_container_width=True)
    
    # Monatliche Insights
    best_month = df_table.loc[df_table['Marge %'].idxmax()]
    worst_month = df_table.loc[df_table['Marge %'].idxmin()]
    highest_revenue = df_table.loc[df_table['Umsaetze'].idxmax()]
    total_db = df_table['DB'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Bester Monat", best_month['Monat'], f"{best_month['Marge %']:.1f}%")
    with col2:
        st.metric("Schlechtester Monat", worst_month['Monat'], f"{worst_month['Marge %']:.1f}%")
    with col3:
        st.metric("Höchster Umsatz", highest_revenue['Monat'], f"€ {highest_revenue['Umsaetze']:,.0f}")
    with col4:
        st.metric("Gesamt DB (YTD)", f"€ {total_db:,.0f}")
    
    # === MASCHINEN OHNE UMSÄTZE ===
    st.header("⚠️ Maschinen ohne Umsätze")
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gesamt Maschinen", len(df_no_revenue))
    with col2:
        st.metric("Gesamtkosten", f"€ {total_cost:,.0f}")
    with col3:
        pareto_percentage = (pareto_count / len(df_no_revenue) * 100) if len(df_no_revenue) > 0 else 0
        st.metric("Top (80/20)", f"{pareto_count} ({pareto_percentage:.0f}%)")
    with col4:
        pareto_cost = df_no_revenue_pareto['Kosten YTD'].sum()
        st.metric("Deren Kosten", f"€ {pareto_cost:,.0f}")
    
    if len(df_no_revenue) > 0:
        df_no_revenue_display = df_no_revenue_pareto[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']].copy()
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            display_no_rev = df_no_revenue_display.copy()
            display_no_rev['VH-nr.'] = display_no_rev['VH-nr.'].astype(str)
            display_no_rev['Kosten YTD'] = display_no_rev['Kosten YTD'].apply(lambda x: f"€ {x:,.2f}")
            st.dataframe(display_no_rev, use_container_width=True, hide_index=True, height=400)
            
            st.download_button(
                label="📥 Export (Excel)",
                data=to_excel(df_no_revenue[['VH-nr.', 'Code', 'Omschrijving', 'Kosten YTD', 'Niederlassung']]),
                file_name=f'ohne_umsaetze_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
        
        with col2:
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
                height=400,
                xaxis_title='Kosten (€)',
                yaxis=dict(autorange='reversed'),
                showlegend=False
            )
            st.plotly_chart(fig_no_rev, use_container_width=True)
    else:
        st.success("✅ Keine Maschinen ohne Umsätze!")
    
    # === PRODUKTANALYSE ===
    if has_product_cols:
        st.header("📦 Produktanalyse")
        
        if len(df_base) > 0:
            product_family_stats = df_base.groupby('1. Product Family').agg({
                'VH-nr.': 'count',
                'Kosten YTD': 'sum',
                'Umsätze YTD': 'sum',
                'DB YTD': 'sum'
            }).reset_index()
            
            product_family_stats.columns = ['Product Family', 'Anzahl', 'Kosten YTD', 'Umsätze YTD', 'DB YTD']
            product_family_stats['Marge %'] = (product_family_stats['DB YTD'] / product_family_stats['Umsätze YTD'] * 100).fillna(0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Kategorien", len(product_family_stats))
            with col2:
                st.metric("Gesamt Umsatz", f"€ {product_family_stats['Umsätze YTD'].sum():,.0f}")
            with col3:
                st.metric("Gesamt DB", f"€ {product_family_stats['DB YTD'].sum():,.0f}")
            with col4:
                avg_marge = (product_family_stats['DB YTD'].sum() / product_family_stats['Umsätze YTD'].sum() * 100) if product_family_stats['Umsätze YTD'].sum() > 0 else 0
                st.metric("Ø Marge", f"{avg_marge:.1f}%")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### Umsatz nach Product Family")
                
                product_family_chart = product_family_stats.sort_values('Umsätze YTD', ascending=False)
                
                fig_family = go.Figure()
                
                fig_family.add_trace(go.Bar(
                    y=product_family_chart['Product Family'],
                    x=product_family_chart['Umsätze YTD'],
                    orientation='h',
                    marker_color='#22c55e',
                    text=product_family_chart['Umsätze YTD'].apply(lambda x: f'€{x/1000:.0f}k'),
                    textposition='outside'
                ))
                
                fig_family.update_layout(
                    height=400,
                    xaxis_title='Umsatz (€)',
                    yaxis=dict(autorange='reversed'),
                    showlegend=False
                )
                
                st.plotly_chart(fig_family, use_container_width=True)
            
            with col_right:
                st.markdown("#### Marge % nach Product Family")
                
                product_family_marge_chart = product_family_stats.sort_values('Marge %', ascending=False)
                
                colors_marge = ['#22c55e' if x >= 20 else '#f59e0b' if x >= 10 else '#ef4444' for x in product_family_marge_chart['Marge %']]
                
                fig_marge = go.Figure()
                
                fig_marge.add_trace(go.Bar(
                    y=product_family_marge_chart['Product Family'],
                    x=product_family_marge_chart['Marge %'],
                    orientation='h',
                    marker_color=colors_marge,
                    text=product_family_marge_chart['Marge %'].apply(lambda x: f'{x:.1f}%'),
                    textposition='outside'
                ))
                
                fig_marge.update_layout(
                    height=400,
                    xaxis_title='Marge (%)',
                    yaxis=dict(autorange='reversed'),
                    showlegend=False
                )
                
                st.plotly_chart(fig_marge, use_container_width=True)
            
            st.markdown("#### Produkt-Mix Übersicht")
            
            sort_product_mix = st.selectbox(
                "Sortieren nach:",
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
                file_name=f'produktanalyse_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # Product Groups
            if '2. Product Group' in df_base.columns:
                st.markdown("---")
                st.markdown("#### Top 20 Product Groups")
                
                sort_groups = st.selectbox(
                    "Sortieren nach:",
                    ["Umsätze YTD (Höchster)", "DB YTD (Höchster Gewinn)", "Marge % (Beste)", "Anzahl (Meiste Maschinen)"],
                    key='sort_product_groups'
                )
                
                product_group_stats = df_base.groupby('2. Product Group').agg({
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

st.markdown("---")
st.caption("🤖 AGRO F66 Dashboard v2.0 | Alle Rechte vorbehalten")
