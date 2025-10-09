"""
User Management mit Rollen-System
Admins: Zugriff auf alle Niederlassungen ihrer Region
Users: Zugriff nur auf ihre Niederlassung
"""

import pandas as pd
import streamlit as st

# User-Datenbank (aus 06_User.xlsx)
USERS = {
    # SUPER ADMIN - DEVELOPER
    "tgerkens@colle.eu": {
        "role": "superadmin",
        "region": "Alle",
        "niederlassungen": ["Ostwestfalen", "Leipzig", "Peine", "Hamburg", "Bremen", "Berlin", "Leer", "Philippsburg", "Augsburg", "Frankfurt", "Saarland"],
        "name": "T. Gerkens"
    },
    "tg1967mail@gmail.com": {  # Developer Gmail Account
        "role": "superadmin",
        "region": "Alle",
        "niederlassungen": ["Ostwestfalen", "Leipzig", "Peine", "Hamburg", "Bremen", "Berlin", "Leer", "Philippsburg", "Augsburg", "Frankfurt", "Saarland"],
        "name": "T. Gerkens (DEV)"
    },
    
    # REGION MITTE
    "lhendricks@colle.eu": {
        "role": "admin",
        "region": "Mitte",
        "niederlassungen": ["Ostwestfalen", "Leipzig", "Peine"],
        "name": "L. Hendricks"
    },
    "jmueller@colle.eu": {
        "role": "user",
        "region": "Mitte",
        "niederlassungen": ["Ostwestfalen"],
        "name": "J. Mueller"
    },
    "jblaut@colle.eu": {
        "role": "user",
        "region": "Mitte",
        "niederlassungen": ["Leipzig"],
        "name": "J. Blaut"
    },
    "mjuenemann@colle.eu": {
        "role": "user",
        "region": "Mitte",
        "niederlassungen": ["Peine"],
        "name": "M. Juenemann"
    },
    
    # REGION NORD (Platzhalter für zukünftige User)
    # Hamburg, Bremen, Berlin, Leer
    
    # REGION SÜD (Platzhalter für zukünftige User)
    # Philippsburg, Augsburg, Frankfurt, Saarland
}

# Region zu Niederlassungen Mapping
REGION_MAPPING = {
    "Mitte": ["Ostwestfalen", "Leipzig", "Peine"],
    "Nord": ["Hamburg", "Bremen", "Berlin", "Leer"],
    "Süd": ["Philippsburg", "Augsburg", "Frankfurt", "Saarland"]
}


def get_user_info(email):
    """
    Holt User-Informationen
    
    Args:
        email: User Email
    
    Returns:
        dict mit User-Info oder None
    """
    return USERS.get(email)


def is_admin(email):
    """
    Prüft ob User Admin oder SuperAdmin ist
    
    Args:
        email: User Email
    
    Returns:
        bool: True wenn Admin oder SuperAdmin
    """
    user = get_user_info(email)
    return user and user.get("role") in ["admin", "superadmin"]


def get_allowed_niederlassungen(email):
    """
    Gibt Liste erlaubter Niederlassungen zurück
    
    Args:
        email: User Email
    
    Returns:
        list: Liste der erlaubten Niederlassungen
    """
    user = get_user_info(email)
    
    if not user:
        return []
    
    return user.get("niederlassungen", [])


def get_user_region(email):
    """
    Gibt Region des Users zurück
    
    Args:
        email: User Email
    
    Returns:
        str: Region oder None
    """
    user = get_user_info(email)
    return user.get("region") if user else None


def filter_dataframe_by_user(df, email):
    """
    Filtert DataFrame basierend auf User-Rechten
    
    Args:
        df: Pandas DataFrame
        email: User Email
    
    Returns:
        Gefilterter DataFrame
    """
    if 'Niederlassung' not in df.columns:
        st.warning("⚠️ Spalte 'Niederlassung' nicht gefunden!")
        return df
    
    user = get_user_info(email)
    
    if not user:
        st.error(f"❌ User nicht gefunden: {email}")
        return pd.DataFrame()  # Leerer DataFrame
    
    allowed_nl = user.get("niederlassungen", [])
    
    if not allowed_nl:
        st.warning("⚠️ Keine Niederlassungen zugewiesen!")
        return pd.DataFrame()
    
    # Filtern
    df_filtered = df[df['Niederlassung'].isin(allowed_nl)]
    
    return df_filtered


def get_user_display_name(email):
    """
    Gibt Display-Name für User zurück
    
    Args:
        email: User Email
    
    Returns:
        str: Name + Rolle
    """
    user = get_user_info(email)
    
    if not user:
        return email
    
    name = user.get("name", email)
    role = user.get("role", "user")
    region = user.get("region", "")
    
    if role == "superadmin":
        return f"{name} (🔧 Super Admin)"
    elif role == "admin":
        return f"{name} (Admin {region})"
    else:
        return f"{name} ({region})"


def get_niederlassung_options(email):
    """
    Gibt Niederlassungs-Optionen für Dropdown zurück
    
    Args:
        email: User Email
    
    Returns:
        list: ['Gesamt'] + erlaubte Niederlassungen (für Admins/SuperAdmin)
              oder nur die eine Niederlassung (für User)
    """
    user = get_user_info(email)
    
    if not user:
        return ['Gesamt']
    
    allowed_nl = user.get("niederlassungen", [])
    role = user.get("role", "user")
    
    if role in ["admin", "superadmin"]:
        # Admin/SuperAdmin kann "Gesamt" (= alle seine Niederlassungen) wählen
        return ['Gesamt'] + sorted(allowed_nl)
    else:
        # Normal User: Nur seine Niederlassung(en)
        return sorted(allowed_nl)


def validate_user_access(email):
    """
    Validiert ob User Zugriff auf Dashboard hat
    
    Args:
        email: User Email
    
    Returns:
        (bool, str): (has_access, message)
    """
    # Domain Check
    if not email or "@" not in email:
        return False, "Ungültige Email"
    
    domain = email.split("@")[1]
    
    # Erlaubte Domains: colle.eu + gmail.com (für Developer)
    if domain not in ["colle.eu", "gmail.com"]:
        return False, f"❌ Domain '{domain}' nicht erlaubt. Nur @colle.eu und @gmail.com (Developer) haben Zugriff."
    
    # User Check
    user = get_user_info(email)
    
    if not user:
        return False, f"❌ User '{email}' ist nicht berechtigt. Bitte Admin kontaktieren."
    
    # Niederlassungen Check
    niederlassungen = user.get("niederlassungen", [])
    
    if not niederlassungen:
        return False, f"❌ Keine Niederlassungen zugewiesen für {email}"
    
    return True, "✅ Zugriff gewährt"


def get_user_statistics(email):
    """
    Gibt Statistiken über User-Zugriffe zurück (für Debug)
    
    Args:
        email: User Email
    
    Returns:
        dict mit Statistiken
    """
    user = get_user_info(email)
    
    if not user:
        return {
            "exists": False
        }
    
    return {
        "exists": True,
        "role": user.get("role"),
        "region": user.get("region"),
        "niederlassungen": user.get("niederlassungen", []),
        "niederlassungen_count": len(user.get("niederlassungen", [])),
        "is_admin": user.get("role") == "admin"
    }


def load_users_from_excel(file_path="06_User.xlsx"):
    """
    Lädt User aus Excel-Datei (für zukünftige Updates)
    
    Args:
        file_path: Pfad zur Excel-Datei
    
    Returns:
        dict: User-Dictionary
    """
    try:
        df = pd.read_excel(file_path)
        
        users = {}
        
        for idx, row in df.iterrows():
            email = row.get('User')
            
            if pd.isna(email):
                continue
            
            region = row.get('Region', '')
            niederlassung = row.get('Niederlassung', '')
            
            # Role ermitteln
            role = "admin" if "Admin" in str(region) else "user"
            
            # Region bereinigen (ohne "Admin")
            clean_region = str(region).replace("Admin ", "").strip()
            
            # Niederlassungen als Liste
            niederlassungen = [nl.strip() for nl in str(niederlassung).split(",")]
            
            users[email] = {
                "role": role,
                "region": clean_region,
                "niederlassungen": niederlassungen,
                "name": email.split("@")[0].title()
            }
        
        return users
        
    except FileNotFoundError:
        st.warning(f"⚠️ User-Datei nicht gefunden: {file_path}")
        return USERS
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der User-Datei: {e}")
        return USERS