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
    # ENTFERNE Beschreibungen (sensibel)
    sensitive_cols = ['Omschrijving']
    
    # Behalte alle anderen Spalten
    export_cols = [col for col in df.columns if col not in sensitive_cols]
    
    return df[export_cols]

def to_excel_secure(df, user_info, filename):
    """Erstellt Excel mit Wasserzeichen und Sicherheit"""
    # Entferne sensible Spalten
    df_export = filter_export_columns(df)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Daten')
        
        worksheet = writer.sheets['Daten']
        
        # Wasserzeichen als Kommentar in A1
        from openpyxl.comments import Comment
        watermark = f"Exportiert von: {user_info['name']}\nDatum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\nNiederlassung: {user_info.get('filter', 'Alle')}"
        worksheet['A1'].comment = Comment(watermark, "AGRO F66 System")
        
        # Spaltenbreiten anpassen
        for idx, col in enumerate(df_export.columns):
            max_length = max(
                df_export[col].astype(str).map(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    # Log Download
    log_download(
        user_info['name'],
        filename,
        user_info.get('filter', 'Alle'),
        len(df_export)
    )
    
    return output.getvalue()

# ========================================
# LOGIN-SYSTEM (unverändert)
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
        st.error("❌ Dashboard_Master_DE.xlsx nicht gefunden!")
        st.stop()
    except Exception as e:
        st.error(f"❌ Fehler: {e}")
        st.stop()

def get_file_info():
    """Zeigt Datei-Informationen und prüft ob Datei aktualisiert wurde"""
    if os.path.exists("Dashboard_Master_DE_v2.xlsx"):
        timestamp = os.path.getmtime("Dashboard_Master_DE_v2.xlsx")
        last_update = datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")
        file_size = os.path.getsize("Dashboard_Master_DE.xlsx") / (1024 * 1024)
        
        cache_key = 'file_timestamp'
        if cache_key not in st.session_state:
            st.session_state[cache_key] = timestamp
        elif st.session_state[cache_key] != timestamp:
            st.cache_data.clear()
            st.session_state[cache_key] = timestamp
            st.rerun()
        
        return last_update, file_size
    return "Unbekannt", 0

# Layout: Main Content + Chat Sidebar
col_main, col_chat = st.columns([3, 1])

with col_main:
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

# ========================================
# CHAT SIDEBAR (RECHTS)
# ========================================

with col_chat:
    st.markdown("### 💬 Frag deine Daten")
    st.caption("Powered by Claude AI")
    
    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
    
    # Chat container
    chat_container = st.container(height=400)
    
    with chat_container:
        if len(st.session_state['chat_messages']) == 0:
            st.info("👋 Stell mir eine Frage zu deinen Daten!")
            st.markdown("**Beispiele:**")
            st.markdown("- Top 5 Maschinen?")
            st.markdown("- Verluste in Leipzig?")
            st.markdown("- Marge-Trend?")
        else:
            for msg in st.session_state['chat_messages']:
                if msg['role'] == 'user':
                    st.markdown(f"**Du:** {msg['content']}")
                else:
                    st.markdown(f"🤖 **Claude:** {msg['content']}")
    
    # Chat input
    user_question = st.text_input("Deine Frage:", key="chat_input", placeholder="z.B. Welche Maschine läuft am besten?")
    
    col_send, col_clear = st.columns([3, 1])
    
    with col_send:
        if st.button("📤 Senden", use_container_width=True, disabled=not user_question):
            if user_question:
                # Add user message
                st.session_state['chat_messages'].append({
                    'role': 'user',
                    'content': user_question
                })
                
                # Prepare anonymized data for Claude
                # TODO: Implement Claude API call here
                # For now, placeholder response
                response = f"Ich analysiere deine Frage: '{user_question}'. Diese Funktion wird in Kürze aktiviert."
                
                st.session_state['chat_messages'].append({
                    'role': 'assistant',
                    'content': response
                })
                
                st.rerun()
    
    with col_clear:
        if st.button("🗑️", use_container_width=True, help="Chat löschen"):
            st.session_state['chat_messages'] = []
            st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Chat-Daten werden nicht gespeichert")
    st.caption("📊 Nur aggregierte Daten, keine Details")

# ========================================
# MAIN DASHBOARD (Vereinfachte Version)
# ========================================

with col_main:
    st.markdown("---")
    
    # Filter (wie gehabt)
    has_nl = 'Niederlassung' in df.columns
    
    if has_nl:
        nl_options = ['Gesamt'] + sorted([nl for nl in df['Niederlassung'].unique() if nl != 'Unbekannt'])
    else:
        nl_options = ['Gesamt']
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if is_admin:
            st.success("🔓 Admin")
            master_nl_filter = st.selectbox("Niederlassung", nl_options, key='master_nl')
        else:
            st.warning(f"🔒 {user_niederlassung}")
            master_nl_filter = user_niederlassung
    
    with col_f2:
        has_product_cols = '1. Product Family' in df.columns
        if has_product_cols:
            product_families = ['Alle'] + sorted([f for f in df['1. Product Family'].dropna().unique() if str(f) != 'nan'])
            selected_family = st.selectbox("Product Family", product_families, key='pf')
        else:
            selected_family = 'Alle'
    
    with col_f3:
        show_active = st.checkbox("Nur aktive YTD", value=True)
    
    # Basis-Filterung
    df_base = df.copy()
    if show_active:
        df_base = df_base[(df_base['Kosten YTD'] != 0) | (df_base['Umsätze YTD'] != 0)]
    
    if master_nl_filter != 'Gesamt' and has_nl:
        df_base = df_base[df_base['Niederlassung'] == master_nl_filter]
    
    if has_product_cols and selected_family != 'Alle':
        df_base = df_base[df_base['1. Product Family'] == selected_family]
    
    # Speichere Filter-Info für Export
    user_data['filter'] = master_nl_filter
    
    # Übersicht
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
        st.metric("YTD DB", f"€ {ytd_db:,.0f}")
    with col4:
        st.metric("YTD Marge", f"{ytd_marge:.1f}%")
    
    st.markdown("---")
    
    # Top 10
    st.header("🏆 Top 10 Maschinen")
    
    df_top = df_base[df_base['Umsätze YTD'] >= 1000].nlargest(10, 'DB YTD')
    top_10_display = df_top[['VH-nr.', 'Code', 'Kosten YTD', 'Umsätze YTD', 'DB YTD', 'Marge YTD %']].copy()
    
    # Formatierung
    top_display = top_10_display.copy()
    top_display['VH-nr.'] = top_display['VH-nr.'].astype(str)
    top_display['Kosten YTD'] = top_display['Kosten YTD'].apply(lambda x: f"€ {x:,.0f}")
    top_display['Umsätze YTD'] = top_display['Umsätze YTD'].apply(lambda x: f"€ {x:,.0f}")
    top_display['DB YTD'] = top_display['DB YTD'].apply(lambda x: f"€ {x:,.0f}")
    top_display['Marge YTD %'] = top_display['Marge YTD %'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(top_display, use_container_width=True, hide_index=True)
    
    # SICHERER EXPORT mit Wasserzeichen
    st.download_button(
        label="📥 Sicher exportieren (Excel)",
        data=to_excel_secure(top_10_display, user_data, f'top_10_{master_nl_filter}.xlsx'),
        file_name=f'top_10_{master_nl_filter}_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
        help="Export ohne Beschreibungen, mit Wasserzeichen"
    )
    
    st.info("🔒 Export enthält keine Beschreibungen (Datenschutz)")
    
    st.markdown("---")
    st.caption("Version 2.0 Beta - Weitere Features folgen")