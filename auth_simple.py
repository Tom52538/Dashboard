# -*- coding: utf-8 -*-
"""
Simple Authentication System für Streamlit
"""

import streamlit as st
import hashlib
from typing import Dict, Optional

class SimpleAuth:
    """Einfaches Authentication System mit Session State"""
    
    def __init__(self):
        # Session State initialisieren
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Erstellt SHA256 Hash von Passwort"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def get_users() -> Dict:
        """Gibt die Benutzer-Datenbank zurück"""
        return {
            'tgerkens': {
                'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  # admin
                'name': 'Thomas Gerkens',
                'role': 'superadmin',
                'niederlassungen': ['alle']
            },
            'lhendricks': {
                'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  # admin
                'name': 'L. Hendricks',
                'role': 'admin',
                'niederlassungen': ['Ostwestfalen', 'Leipzig', 'Peine']
            },
            'mdrescher': {
                'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  # admin
                'name': 'M. Drescher',
                'role': 'admin',
                'niederlassungen': ['Hamburg', 'Bremen', 'Berlin', 'Leer']
            },
            'usehlinger': {
                'password_hash': '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',  # admin
                'name': 'U. Sehlinger',
                'role': 'admin',
                'niederlassungen': ['Philippsburg', 'Augsburg', 'Frankfurt', 'Saarland']
            },
            'jmueller': {
                'password_hash': '365d6ac067e363086b982763345b079d8a6c235640882d95bfeeaecf3c52f8d6',
                'name': 'J. Müller',
                'role': 'user',
                'niederlassungen': ['Ostwestfalen']
            },
            'jblaut': {
                'password_hash': 'fb90221b40de2ee33e577f2e8cedf6daadb928c8879e1df8df0739d39a307689',
                'name': 'J. Blaut',
                'role': 'user',
                'niederlassungen': ['Leipzig']
            },
            'mjuenemann': {
                'password_hash': '383f54815d9f0a379862b56159a5c178c7bbcce2b012448010d30579f2747be1',
                'name': 'M. Jünemann',
                'role': 'user',
                'niederlassungen': ['Peine']
            },
            'sortgiese': {
                'password_hash': '7286e930b6a9ab3cd7194b12abbd85fe89fe316c41e44ce0aa38a0da7bbe3a8f',
                'name': 'S. Ortgiese',
                'role': 'user',
                'niederlassungen': ['Hamburg']
            },
            'kluedemann': {
                'password_hash': '9c1602308c2008d5d43c9f3924cccf539b8bcb5177a03565b4ad94b48788b5f9',
                'name': 'K. Lüdemann',
                'role': 'user',
                'niederlassungen': ['Bremen']
            },
            'berlin': {
                'password_hash': '23821ac93172231f77b3c24f3867477f43de0b8368030f43e3edee03eb99b5e3',
                'name': 'Berlin User',
                'role': 'user',
                'niederlassungen': ['Berlin']
            },
            'hvoss': {
                'password_hash': 'd1578b827105ac997993ca9c5a7039898007ea7b0e8cb9c48dba4ea39dcebad8',
                'name': 'H. Voss',
                'role': 'user',
                'niederlassungen': ['Leer']
            },
            'merk': {
                'password_hash': '292d985fc79079b41c31c6a519fb617f8689546282121340e144e624cbf4da9a',
                'name': 'M. Erk',
                'role': 'user',
                'niederlassungen': ['Philippsburg']
            },
            'asteiner': {
                'password_hash': '567d0273846b142a9b148a9b5396add9f571266ec01b1765f6d0720cbb1ee4f5',
                'name': 'A. Steiner',
                'role': 'user',
                'niederlassungen': ['Augsburg']
            },
            'kpommerening': {
                'password_hash': '326d71452790d0a33be07264337d0204fc0f233495834e85c3cbbed30ba05b88',
                'name': 'K. Pommerening',
                'role': 'user',
                'niederlassungen': ['Frankfurt']
            },
            'hbrandel': {
                'password_hash': 'f400f6af8e88692bd6f6c9d4660b138f719815254152805928f3a7a45081b788',
                'name': 'H. Brandel',
                'role': 'user',
                'niederlassungen': ['Saarland']
            }
        }
    
    def login(self, username: str, password: str) -> bool:
        """Versucht Login mit Benutzername und Passwort"""
        users = self.get_users()
        
        if username in users:
            password_hash = self.hash_password(password)
            if users[username]['password_hash'] == password_hash:
                st.session_state.authenticated = True
                user_data = users[username].copy()
                user_data.pop('password_hash')  # Hash nicht im Session State speichern
                st.session_state.current_user = user_data
                return True
        return False
    
    def logout(self):
        """Loggt den Benutzer aus"""
        st.session_state.authenticated = False
        st.session_state.current_user = None
    
    def is_authenticated(self) -> bool:
        """Prüft ob Benutzer eingeloggt ist"""
        return st.session_state.authenticated
    
    def get_current_user(self) -> Optional[Dict]:
        """Gibt den aktuellen Benutzer zurück"""
        return st.session_state.current_user


def show_login_page():
    """Zeigt die Login-Seite mit zentrierter Box"""
    
    # Zentriertes Layout mit Spalten
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🚜 AGRO F66</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Maschinen Dashboard</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login Form
        with st.form("login_form"):
            username = st.text_input("Benutzername", key="login_username")
            password = st.text_input("Passwort", type="password", key="login_password")
            submit = st.form_submit_button("Anmelden", use_container_width=True)
            
            if submit:
                auth = SimpleAuth()
                if auth.login(username, password):
                    st.rerun()
                else:
                    st.error("❌ Ungültige Anmeldedaten")
        
        st.markdown("---")
        
        # Hinweise
        st.info("**Hinweis:**")
        st.markdown("""
        - **SuperAdmin**: Zugriff auf alle Niederlassungen
        - **Admin**: Zugriff auf mehrere Niederlassungen
        - **User**: Zugriff auf eine Niederlassung
        """)


def show_user_info():
    """Zeigt Benutzer-Info in der Sidebar"""
    auth = SimpleAuth()
    if auth.is_authenticated():
        user = auth.get_current_user()
        
        st.sidebar.markdown("### 👤 Benutzer-Info")
        st.sidebar.markdown(f"**Name:** {user['name']}")
        st.sidebar.markdown(f"**Rolle:** {user['role']}")
        
        if user['niederlassungen'] == ['alle']:
            st.sidebar.markdown("**Zugriff:** Alle Niederlassungen")
        else:
            st.sidebar.markdown(f"**Zugriff:** {', '.join(user['niederlassungen'])}")
