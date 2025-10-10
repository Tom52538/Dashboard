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
