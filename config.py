"""
Konfiguration für Multi-Environment Support
DEV (privat) vs PROD (Firma)
"""

import streamlit as st

def get_config():
    """
    Gibt Config basierend auf Environment zurück
    Liest 'environment' aus secrets.toml
    """
    env = st.secrets.get("environment", "production")
    
    config = {
        "development": {
            "app_name": "Umsätze pro Maschine Dashboard [DEV]",
            "allowed_domains": ["gmail.com", "colle.eu"],  # Gmail für Developer + Firma
            "require_workspace": False,
            "cache_ttl": 300,  # 5 Min (schnelleres Testing)
            "show_debug": True
        },
        "production": {
            "app_name": "Umsätze pro Maschine Dashboard",
            "allowed_domains": ["colle.eu"],  # NUR Firmen-Domain
            "require_workspace": False,  # False, falls kein Google Workspace
            "cache_ttl": 3600,  # 1 Stunde
            "show_debug": False
        }
    }
    
    return config.get(env, config["production"])

# Globale Config - wird beim Import geladen
CONFIG = get_config()