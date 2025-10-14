# -*- coding: utf-8 -*-
"""
Login Logger für AGRO F66 Dashboard
Trackt User-Logins diskret für Admin-Analysen
"""

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

class LoginLogger:
    def __init__(self, log_file='logs/login_history.csv'):
        self.log_file = log_file
        # Stelle sicher, dass der logs-Ordner existiert
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Erstelle CSV wenn nicht vorhanden
        if not os.path.exists(log_file):
            df = pd.DataFrame(columns=['timestamp', 'username', 'name', 'role', 'niederlassung', 'action'])
            df.to_csv(log_file, index=False)
    
    def log_login(self, user_data):
        """Loggt einen Login"""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': user_data.get('username', 'unknown'),
            'name': user_data.get('name', 'unknown'),
            'role': user_data.get('role', 'user'),
            'niederlassung': ', '.join(user_data.get('niederlassungen', [])),
            'action': 'login'
        }
        
        # Append zu CSV
        df = pd.DataFrame([log_entry])
        df.to_csv(self.log_file, mode='a', header=False, index=False)
    
    def log_logout(self, user_data):
        """Loggt einen Logout"""
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'username': user_data.get('username', 'unknown'),
            'name': user_data.get('name', 'unknown'),
            'role': user_data.get('role', 'user'),
            'niederlassung': ', '.join(user_data.get('niederlassungen', [])),
            'action': 'logout'
        }
        
        df = pd.DataFrame([log_entry])
        df.to_csv(self.log_file, mode='a', header=False, index=False)
    
    def get_logs(self, days=30):
        """Liest die letzten X Tage"""
        if not os.path.exists(self.log_file):
            return pd.DataFrame()
        
        df = pd.read_csv(self.log_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filtere letzte X Tage
        cutoff = datetime.now() - pd.Timedelta(days=days)
        df = df[df['timestamp'] >= cutoff]
        
        return df.sort_values('timestamp', ascending=False)
    
    def get_stats(self):
        """Erstellt Statistiken"""
        df = self.get_logs(days=30)
        
        if len(df) == 0:
            return None
        
        stats = {
            'total_logins': len(df[df['action'] == 'login']),
            'unique_users': df['username'].nunique(),
            'most_active_user': df['username'].mode()[0] if len(df) > 0 else 'N/A',
            'logins_today': len(df[(df['action'] == 'login') & 
                                   (df['timestamp'].dt.date == datetime.now().date())]),
            'last_login': df[df['action'] == 'login'].iloc[0] if len(df) > 0 else None
        }
        
        return stats