"""
Einfaches Login-System für AGRO F66 Dashboard
Ohne Google OAuth - nur Username/Passwort
SICHERE VERSION - Passwörter nur in Streamlit Secrets!
"""

import streamlit as st
import hashlib
from typing import Dict, Optional

class SimpleAuth:
    """Einfaches Authentifizierungs-System"""
    
    def __init__(self):
        # User-Datenbank aus Secrets laden
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Lade User-Daten aus Streamlit Secrets"""
        try:
            # Aus Streamlit Secrets laden
            if hasattr(st, 'secrets') and 'users' in st.secrets:
                users_dict = {}
                
                # Secrets haben Format: [users.username]
                for username in st.secrets['users']:
                    user_secrets = st.secrets['users'][username]
                    users_dict[username] = {
                        'password_hash': str(user_secrets.get('password_hash')).strip().strip('"'),
                        'name': str(user_secrets.get('name')).strip(),
                        'role': str(user_secrets.get('role')).strip(),
                        'niederlassungen': list(user_secrets.get('niederlassungen', []))
                    }
                
                return users_dict
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Secrets: {e}")
            st.stop()
        
        # Wenn keine Secrets gefunden
        st.error("❌ Keine User-Daten in Secrets gefunden!")
        st.info("Bitte konfiguriere die Secrets in Streamlit Cloud.")
        st.stop()
    
    def _hash_password(self, password: str) -> str:
        """Hash ein Passwort mit SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        Login-Funktion
        Returns: User-Daten wenn erfolgreich, None wenn fehlgeschlagen
        """
        username = username.lower().strip()
        
        if username not in self.users:
            return None
        
        user_data = self.users[username]
        password_hash = self._hash_password(password)
        
        if password_hash == user_data['password_hash']:
            return {
                'username': username,
                'name': user_data['name'],
                'role': user_data['role'],
                'niederlassungen': user_data['niederlassungen']
            }
        
        return None
    
    def logout(self):
        """Logout-Funktion"""
        if 'user' in st.session_state:
            del st.session_state['user']
        if 'authenticated' in st.session_state:
            del st.session_state['authenticated']
    
    def is_authenticated(self) -> bool:
        """Prüfe ob User eingeloggt ist"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict]:
        """Hole aktuellen User"""
        return st.session_state.get('user', None)


def show_login_page():
    """Zeige Login-Seite"""
    # Styling
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🚜 AGRO F66")
        st.subheader("Maschinen Dashboard")
        st.markdown("---")
    
    # Login-Form
    with st.form("login_form"):
        username = st.text_input("Benutzername", placeholder="tgerkens")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Anmelden", use_container_width=True)
    
    if submit:
        if not username or not password:
            st.error("Bitte alle Felder ausfüllen!")
            return
        
        auth = SimpleAuth()
        user_data = auth.login(username, password)
        
        if user_data:
            # Login erfolgreich
            st.session_state['authenticated'] = True
            st.session_state['user'] = user_data
            st.success(f"Willkommen, {user_data['name']}!")
            st.rerun()
        else:
            st.error("Ungültige Anmeldedaten!")
    
    # Info-Box
    st.markdown("---")
    st.info("""
    **Hinweis:**
    - SuperAdmin: Zugriff auf alle Niederlassungen
    - Admin: Zugriff auf mehrere Niederlassungen
    - User: Zugriff auf eine Niederlassung
    """)


def show_user_info():
    """Zeige User-Info in Sidebar"""
    auth = SimpleAuth()
    user = auth.get_current_user()
    
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**👤 {user['name']}**")
            st.caption(f"🔧 {user['username']}")
            
            # Rolle anzeigen
            role_emoji = {
                'superadmin': '👑',
                'admin': '⭐',
                'user': '👤'
            }
            st.caption(f"{role_emoji.get(user['role'], '👤')} {user['role'].title()}")
            
            # Niederlassungen
            if user['niederlassungen'] == ['alle']:
                st.caption("🌍 Alle Niederlassungen")
            else:
                st.caption(f"📍 {', '.join(user['niederlassungen'])}")
            
            # Logout-Button
            if st.button("🚪 Abmelden", use_container_width=True):
                auth.logout()
                st.rerun()
