"""
Einfaches Login-System für AGRO F66 Dashboard
Ohne Google OAuth - nur Username/Passwort
"""

import streamlit as st
import hashlib
import json
from typing import Dict, List, Optional

class SimpleAuth:
    """Einfaches Authentifizierungs-System"""
    
    def __init__(self):
        # User-Datenbank laden
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Lade User-Daten aus Secrets oder JSON"""
        try:
            # Versuche aus Streamlit Secrets zu laden
            if hasattr(st, 'secrets') and 'users' in st.secrets:
                return dict(st.secrets['users'])
        except:
            pass
        
        # Fallback: Default Users (für lokale Entwicklung)
        return {
            "tgerkens@colle.eu": {
                "password_hash": self._hash_password("admin"),
                "name": "Thomas Gerkens",
                "role": "superadmin",
                "niederlassungen": ["alle"]
            },
            "lhendricks@colle.eu": {
                "password_hash": self._hash_password("admin"),
                "name": "L. Hendricks",
                "role": "admin",
                "niederlassungen": ["Ostwestfalen", "Leipzig", "Peine"]
            },
            "jmueller@colle.eu": {
                "password_hash": self._hash_password("owl123"),
                "name": "J. Müller",
                "role": "user",
                "niederlassungen": ["Ostwestfalen"]
            },
            "jblaut@colle.eu": {
                "password_hash": self._hash_password("lej123"),
                "name": "J. Blaut",
                "role": "user",
                "niederlassungen": ["Leipzig"]
            },
            "mjuenemann@colle.eu": {
                "password_hash": self._hash_password("pei123"),
                "name": "M. Jünemann",
                "role": "user",
                "niederlassungen": ["Peine"]
            },
            "sortgiese@colle.eu": {
                "password_hash": self._hash_password("ham123"),
                "name": "S. Ortgiese",
                "role": "user",
                "niederlassungen": ["Hamburg"]
            },
            "kluedemann@colle.eu": {
                "password_hash": self._hash_password("bre123"),
                "name": "K. Lüdemann",
                "role": "user",
                "niederlassungen": ["Bremen"]
            },
            "berlin@colle.eu": {
                "password_hash": self._hash_password("ber123"),
                "name": "Berlin User",
                "role": "user",
                "niederlassungen": ["Berlin"]
            },
            "hvoss@colle.eu": {
                "password_hash": self._hash_password("lee123"),
                "name": "H. Voss",
                "role": "user",
                "niederlassungen": ["Leer"]
            },
            "merk@colle.eu": {
                "password_hash": self._hash_password("phi123"),
                "name": "M. Erk",
                "role": "user",
                "niederlassungen": ["Philippsburg"]
            },
            "asteiner@colle.eu": {
                "password_hash": self._hash_password("aug123"),
                "name": "A. Steiner",
                "role": "user",
                "niederlassungen": ["Augsburg"]
            },
            "kpommerening@colle.eu": {
                "password_hash": self._hash_password("fra123"),
                "name": "K. Pommerening",
                "role": "user",
                "niederlassungen": ["Frankfurt"]
            },
            "hbrandel@colle.eu": {
                "password_hash": self._hash_password("saa123"),
                "name": "H. Brandel",
                "role": "user",
                "niederlassungen": ["Saarland"]
            },
            "mdrescher@colle.eu": {
                "password_hash": self._hash_password("admin"),
                "name": "M. Drescher",
                "role": "admin",
                "niederlassungen": ["Hamburg", "Bremen", "Berlin", "Leer"]
            },
            "usehlinger@colle.eu": {
                "password_hash": self._hash_password("admin"),
                "name": "U. Sehlinger",
                "role": "admin",
                "niederlassungen": ["Philippsburg", "Augsburg", "Frankfurt", "Saarland"]
            }
        }
    
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
    
    def get_user_niederlassungen(self, username: str) -> List[str]:
        """Hole die Niederlassungen für einen User"""
        if username in self.users:
            nl = self.users[username]['niederlassungen']
            if 'alle' in nl:
                return ['alle']  # SuperAdmin sieht alles
            return nl
        return []
    
    def is_authenticated(self) -> bool:
        """Prüfe ob User eingeloggt ist"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict]:
        """Hole aktuellen User"""
        return st.session_state.get('user', None)
    
    def require_auth(self):
        """Decorator-Funktion: Erfordert Login"""
        if not self.is_authenticated():
            st.warning(⚠️ Bitte zuerst einloggen!")
            st.stop()


def show_login_page():
    """Zeige Login-Seite"""
    st.set_page_config(
        page_title="AGRO F66 - Login",
        page_icon="🚜",
        layout="wide"
    )
    
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
        username = st.text_input("Benutzername", placeholder="email@colle.eu")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Anmelden", use_container_width=True)
    
    if submit:
        if not username or not password:
            st.error("❌ Bitte alle Felder ausfüllen!")
            return
        
        auth = SimpleAuth()
        user_data = auth.login(username, password)
        
        if user_data:
            # Login erfolgreich
            st.session_state['authenticated'] = True
            st.session_state['user'] = user_data
            st.success(f"✅ Willkommen, {user_data['name']}!")
            st.rerun()
        else:
            st.error("❌ Ungültige Anmeldedaten!")
    
    # Info-Box
    st.markdown("---")
    st.info("""
    **ℹ️ Hinweis:**
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
            st.caption(f"📧 {user['username']}")
            
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