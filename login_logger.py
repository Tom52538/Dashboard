# -*- coding: utf-8 -*-
"""
Login Logger für AGRO F66 Dashboard
Speichert Login-Daten persistent in Google Sheets
"""

import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pytz
import pandas as pd

class LoginLogger:
    def __init__(self):
        """Initialisiert Google Sheets Verbindung"""
        self.sheet = None
        self.setup_sheets()
    
    def setup_sheets(self):
        """Stellt Verbindung zu Google Sheets her"""
        try:
            # Credentials aus Streamlit Secrets
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=scopes
            )
            
            client = gspread.authorize(credentials)
            
            # Sheet öffnen
            sheet_id = st.secrets["google_sheets"]["sheet_id"]
            spreadsheet = client.open_by_key(sheet_id)
            
            # Erstes Worksheet verwenden
            self.sheet = spreadsheet.sheet1
            
            # Header erstellen falls nicht vorhanden
            try:
                headers = self.sheet.row_values(1)
                if not headers or headers[0] != 'timestamp':
                    self.sheet.insert_row(['timestamp', 'username', 'name', 'role', 'niederlassung', 'action'], 1)
            except:
                self.sheet.insert_row(['timestamp', 'username', 'name', 'role', 'niederlassung', 'action'], 1)
                
        except Exception as e:
            st.error(f"⚠️ Fehler beim Verbinden mit Google Sheets: {e}")
            self.sheet = None
    
    def log_login(self, user_data):
        """Loggt einen Login"""
        if not self.sheet:
            return
        
        try:
            log_entry = [
                datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S'),
                user_data.get('username', 'unknown'),
                user_data.get('name', 'unknown'),
                user_data.get('role', 'user'),
                ', '.join(user_data.get('niederlassungen', [])),
                'login'
            ]
            
            self.sheet.append_row(log_entry)
            
        except Exception as e:
            st.error(f"⚠️ Fehler beim Loggen: {e}")
    
    def log_logout(self, user_data):
        """Loggt einen Logout"""
        if not self.sheet:
            return
        
        try:
            log_entry = [
                datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S'),
                user_data.get('username', 'unknown'),
                user_data.get('name', 'unknown'),
                user_data.get('role', 'user'),
                ', '.join(user_data.get('niederlassungen', [])),
                'logout'
            ]
            
            self.sheet.append_row(log_entry)
            
        except Exception as e:
            st.error(f"⚠️ Fehler beim Loggen: {e}")
    
    def get_logs(self, days=30):
        """Liest die letzten X Tage aus Google Sheets"""
        if not self.sheet:
            return None
        
        try:
            # Alle Daten holen
            all_data = self.sheet.get_all_records()
            
            if not all_data:
                return None
            
            df = pd.DataFrame(all_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filtere letzte X Tage - mit Europe/Berlin Zeitzone
            berlin_tz = pytz.timezone('Europe/Berlin')
            cutoff = datetime.now(berlin_tz) - pd.Timedelta(days=days)
            
            # Konvertiere cutoff zu naive datetime für Vergleich
            cutoff = cutoff.replace(tzinfo=None)
            
            df = df[df['timestamp'] >= cutoff]
            
            return df.sort_values('timestamp', ascending=False)
            
        except Exception as e:
            st.error(f"⚠️ Fehler beim Lesen der Logs: {e}")
            return None
    
    def get_stats(self):
        """Erstellt Statistiken"""
        df = self.get_logs(days=30)
        
        if df is None or len(df) == 0:
            return None
        
        # Heutiges Datum in Europe/Berlin Zeitzone
        berlin_tz = pytz.timezone('Europe/Berlin')
        today = datetime.now(berlin_tz).date()
        
        stats = {
            'total_logins': len(df[df['action'] == 'login']),
            'unique_users': df['username'].nunique(),
            'most_active_user': df['username'].mode()[0] if len(df) > 0 else 'N/A',
            'logins_today': len(df[(df['action'] == 'login') & 
                                   (df['timestamp'].dt.date == today)]),
            'last_login': df[df['action'] == 'login'].iloc[0] if len(df) > 0 else None
        }
        
        return stats
