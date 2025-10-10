# -*- coding: utf-8 -*-
"""
Simple Authentication System für Streamlit
"""

import streamlit as st
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
    def get_users() -> Dict:
        """Gibt die Benutzer-Datenbank zurück"""
        return {
            'tgerkens': {
                'password': 'admin123',
                'name': 'Tom Gerkens',
                'role': 'superadmin',
                'niederlassungen': ['alle']
            },
            'admin': {
                'password': 'admin123',
                'name': 'Admin User',
                'role': 'admin',
                'niederlassungen': ['Coevorden', 'Vriezenveen', 'Emmen']
            },
            'user': {
                'password': 'user123',
                'name': 'Standard User',
                'role': 'user',
                'niederlassungen': ['Coevorden']
            }
        }
    
    def login(self, username: str, password: str) -> bool:
        """Versucht Login mit Benutzername und Passwort"""
        users = self.get_users()
        
        if username in users and users[username]['password'] == password:
            st.session_state.authenticated = True
            st.session_state.current_user = users[username]
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
