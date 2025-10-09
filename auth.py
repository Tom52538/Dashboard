"""
Google OAuth Authentication mit Rollen-System
Funktioniert mit privaten und Firmen-Accounts
"""

import streamlit as st
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from config import CONFIG
from users import validate_user_access, get_user_display_name, get_user_statistics

# OAuth Scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# FIX: Scope-Validierung relaxen (Google fügt automatisch 'openid' hinzu)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Für Development

def check_email_allowed(email):
    """
    Prüft ob Email-Domain erlaubt ist UND ob User berechtigt ist
    
    Returns:
        (bool, str): (is_allowed, message)
    """
    if not email:
        return False, "Keine Email"
    
    # Validierung mit Rollen-System
    is_allowed, message = validate_user_access(email)
    
    # Debug-Info anzeigen
    if CONFIG["show_debug"]:
        st.sidebar.write("🔍 Debug:")
        st.sidebar.write(f"- Email: {email}")
        st.sidebar.write(f"- Status: {message}")
        
        # User-Statistiken
        stats = get_user_statistics(email)
        if stats.get("exists"):
            st.sidebar.write(f"- Rolle: {stats['role']}")
            st.sidebar.write(f"- Region: {stats['region']}")
            st.sidebar.write(f"- Niederlassungen: {stats['niederlassungen_count']}")
    
    return is_allowed, message

def get_oauth_flow():
    """
    Erstellt OAuth Flow aus Streamlit Secrets
    """
    # Redirect URI aus Secrets
    redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    
    if CONFIG["show_debug"]:
        st.sidebar.write(f"🔗 Redirect URI: {redirect_uri}")
    
    # OAuth Client Config
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": st.secrets["google_oauth"]["auth_uri"],
            "token_uri": st.secrets["google_oauth"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
            "redirect_uris": [redirect_uri]
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def google_login():
    """
    Google Login mit OAuth 2.0 + Rollen-System
    Returns: user_info dict oder None
    """
    
    # Session State Init
    if 'user_info' not in st.session_state:
        st.session_state['user_info'] = None
    if 'credentials' not in st.session_state:
        st.session_state['credentials'] = None
    
    # Token Exchange nach Redirect (ERST prüfen!)
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code']
        
        with st.spinner("🔐 Login wird verarbeitet..."):
            try:
                flow = get_oauth_flow()
                
                # Token holen
                flow.fetch_token(code=code)
                credentials = flow.credentials
                
                # User Info abrufen
                service = build('oauth2', 'v2', credentials=credentials)
                user_info = service.userinfo().get().execute()
                
                email = user_info.get('email')
                
                # Email & Rollen-Check
                is_allowed, message = check_email_allowed(email)
                
                if not is_allowed:
                    st.error(message)
                    st.info("💡 Kontaktiere deinen Administrator für Zugriff.")
                    st.stop()
                
                # Display Name holen
                display_name = get_user_display_name(email)
                
                # Speichern
                st.session_state['user_info'] = user_info
                st.session_state['credentials'] = credentials
                
                # Query Params clearen
                st.query_params.clear()
                
                st.success(f"✅ Eingeloggt als: {display_name}")
                st.balloons()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Login fehlgeschlagen: {str(e)}")
                if CONFIG["show_debug"]:
                    st.exception(e)
                st.query_params.clear()
                st.stop()
    
    # Bereits eingeloggt?
    if st.session_state['user_info']:
        return st.session_state['user_info']
    
    # Login UI
    st.title(f"🔐 {CONFIG['app_name']}")
    
    st.markdown("---")
    
    if CONFIG["show_debug"]:
        st.info(f"🔧 Modus: {st.secrets.get('environment', {}).get('environment', 'production').upper()}")
    
    # OAuth Flow starten
    try:
        flow = get_oauth_flow()
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Login Button (öffnet in gleichem Tab)
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
            <a href="{auth_url}" style="
                display: inline-block;
                padding: 0.75rem 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: all 0.3s ease;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)';" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';">
                🔐 Mit @colle.eu anmelden
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("ℹ️ Nach dem Login mit deinem Google-Account wirst du automatisch zurück zur App geleitet.")
        
    except Exception as e:
        st.error(f"❌ Fehler beim OAuth Flow: {str(e)}")
        if CONFIG["show_debug"]:
            st.write("**Debug Info:**")
            st.exception(e)
        st.stop()
    
    return None

def logout():
    """
    Logout - löscht Session State
    """
    st.session_state['user_info'] = None
    st.session_state['credentials'] = None
    st.query_params.clear()
    st.rerun()

def get_user_email():
    """
    Gibt Email des eingeloggten Users zurück
    """
    if 'user_info' in st.session_state and st.session_state['user_info']:
        return st.session_state['user_info'].get('email')
    return None

def get_credentials():
    """
    Gibt Google Credentials zurück
    """
    if 'credentials' in st.session_state:
        return st.session_state['credentials']
    return None
