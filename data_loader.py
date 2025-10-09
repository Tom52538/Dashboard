"""
Lädt Daten von Google Drive
Unterstützt Excel (.xlsx) und Google Sheets
"""

import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from config import CONFIG

@st.cache_data(ttl=CONFIG["cache_ttl"], show_spinner="📥 Lade Daten von Google Drive...")
def load_from_drive(_credentials, file_id):
    """
    Lädt Excel/Sheets von Google Drive
    
    Args:
        _credentials: Google OAuth Credentials (mit _ = nicht cachen)
        file_id: Drive File ID
    
    Returns:
        DataFrame oder None
    """
    try:
        # Drive API Service
        service = build('drive', 'v3', credentials=_credentials)
        
        # File Metadata holen
        file_metadata = service.files().get(
            fileId=file_id, 
            fields='name,mimeType,size'
        ).execute()
        
        file_name = file_metadata.get('name', 'Unknown')
        mime_type = file_metadata.get('mimeType', '')
        file_size = int(file_metadata.get('size', 0))
        
        if CONFIG["show_debug"]:
            st.sidebar.write("📄 Datei-Info:")
            st.sidebar.write(f"- Name: {file_name}")
            st.sidebar.write(f"- Typ: {mime_type}")
            st.sidebar.write(f"- Größe: {file_size / 1024:.1f} KB")
        
        # Google Sheets oder normale Datei?
        if mime_type == 'application/vnd.google-apps.spreadsheet':
            # Echtes Google Sheets → Als Excel exportieren
            if CONFIG["show_debug"]:
                st.sidebar.write("📊 Lade als Google Sheets (export)...")
            
            request = service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # Normale Datei (Excel, PDF, etc.) → Direkter Download
            if CONFIG["show_debug"]:
                st.sidebar.write(f"📁 Lade Datei direkt (Type: {mime_type})...")
            
            request = service.files().get_media(fileId=file_id)
        
        # Download
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        
        done = False
        with st.spinner('📥 Downloade Datei...'):
            while not done:
                status, done = downloader.next_chunk()
                if status and CONFIG["show_debug"]:
                    progress = int(status.progress() * 100)
                    st.sidebar.write(f"⏳ Download: {progress}%")
        
        # Excel laden
        file_buffer.seek(0)
        df = pd.read_excel(file_buffer, engine='openpyxl')
        
        # Erfolg!
        st.success(f"✅ {len(df):,} Zeilen geladen: {file_name}")
        
        if CONFIG["show_debug"]:
            st.sidebar.write(f"📊 Spalten: {len(df.columns)}")
            st.sidebar.write(f"📏 Zeilen: {len(df):,}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden von Drive: {e}")
        if CONFIG["show_debug"]:
            st.exception(e)
        return None

@st.cache_data(ttl=CONFIG["cache_ttl"])
def load_local_fallback(file_path):
    """
    Fallback: Lädt lokale Excel-Datei
    Für Entwicklung ohne Drive-Zugriff
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        st.warning(f"⚠️ Lokale Datei geladen: {file_path}")
        return df
    except FileNotFoundError:
        st.error(f"❌ Datei nicht gefunden: {file_path}")
        return None
    except Exception as e:
        st.error(f"❌ Fehler beim Laden: {e}")
        return None

def load_data():
    """
    Haupt-Loader mit Smart Fallback
    
    1. Versucht von Google Drive zu laden (wenn credentials vorhanden)
    2. Fallback zu lokaler Datei (für Development)
    
    Returns:
        DataFrame oder None
    """
    
    # Credentials aus Session State
    if 'credentials' not in st.session_state or not st.session_state['credentials']:
        st.error("❌ Nicht eingeloggt! Bitte zuerst anmelden.")
        return None
    
    credentials = st.session_state['credentials']
    
    # File ID aus Secrets
    if 'drive' not in st.secrets or 'file_id' not in st.secrets['drive']:
        st.error("❌ Keine File ID in secrets.toml konfiguriert!")
        return None
    
    file_id = st.secrets['drive']['file_id']
    
    # Von Drive laden
    df = load_from_drive(credentials, file_id)
    
    # Fallback zu lokal (falls Drive fehlschlägt)
    if df is None and CONFIG["show_debug"]:
        st.warning("⚠️ Drive-Laden fehlgeschlagen, versuche lokale Datei...")
        df = load_local_fallback("Dashboard_Master_DE_v2.xlsx")
    
    return df

def validate_dataframe(df):
    """
    Prüft ob DataFrame die erwarteten Spalten hat
    
    Returns:
        (bool, list) - (is_valid, missing_columns)
    """
    required_columns = [
        'VH-nr.',
        'Niederlassung',
        'Kosten YTD',
        'Umsätze YTD',
        'DB YTD'
    ]
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        st.error(f"❌ Fehlende Spalten: {', '.join(missing)}")
        if CONFIG["show_debug"]:
            st.write("Verfügbare Spalten:", list(df.columns))
        return False, missing
    
    return True, []

def get_data():
    """
    Convenience Function: Lädt und validiert Daten
    
    Returns:
        DataFrame oder None
    """
    df = load_data()
    
    if df is None:
        return None
    
    # Validierung
    is_valid, missing = validate_dataframe(df)
    
    if not is_valid:
        return None
    
    return df