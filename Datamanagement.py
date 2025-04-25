import streamlit as st
from services.admin import admin_dashboard
from services.database import initialize_default_users, initialize_database_if_needed
from services.siedbar_layout import login, logout

# ----------------------------
# Hauptanwendung
# ----------------------------
def app():
    """Hauptanwendung mit geschütztem Zugriff."""
    st.sidebar.title("Navigation")

    st.sidebar.markdown(f"👤 Logged in as: `{st.session_state.get('username', 'Unknown')}`")

    # Admin-spezifische Navigation
    if st.session_state.get("role") == "admin":
        selection = st.sidebar.radio("Seite auswählen", ["Home", "Admin-Dashboard"])
    else:
        st.info("🔒 Keine Admin-Berechtigung. Begrenzte Funktionalität.")
        selection = None

    # Seiteninhalte basierend auf der Auswahl
    if selection == "Admin-Dashboard":
        admin_dashboard()

    # Logout-Funktion
    st.sidebar.button("Logout", on_click=logout)


# ----------------------------
# Steuerungslogik
# ----------------------------
def main():
    """Main logic of the application."""

    st.set_page_config(page_title="IVET Datenmanagement", page_icon="📊")

    # Initialisiere DB bei Bedarf
    db_was_initialized = initialize_database_if_needed()
    if db_was_initialized:
        st.toast("📦 Datenbank wurde neu initialisiert")
        st.info("💡 Die Datenbank wurde frisch erstellt und ist bereit.")
        initialize_default_users()
    # Admin-User prüfen/erstellen


    # Login prüfen
    if not st.session_state.get("logged_in", False):
        st.info("🔐 Bitte loggen Sie sich ein, um fortzufahren.")
        login()
    else:
        app()


# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()