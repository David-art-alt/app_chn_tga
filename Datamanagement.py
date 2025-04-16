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

    # Admin-spezifische Navigation
    if st.session_state.get("role") == "admin":
        selection = st.sidebar.radio("Seite auswählen", ["Home", "Admin-Dashboard"])
    else:
        selection = None

    # Seiteninhalte basierend auf der Auswahl
    if selection == "Admin-Dashboard":
        admin_dashboard()

    # Logout-Funktion anbieten
    st.sidebar.button("Logout", on_click=logout)


# ----------------------------
# Steuerungslogik
# ----------------------------
def main():
    """Main logic of the application."""

    # Initialisiere DB bei Bedarf
    db_was_initialized = initialize_database_if_needed()

    # Optional: Hinweis in Streamlit anzeigen
    if db_was_initialized:
        st.toast("📦 Datenbank wurde neu initialisiert")

    # Admin-User prüfen/erstellen
    initialize_default_users()

    # Login-Logik
    if not st.session_state.get("logged_in", False):
        login()
    else:
        app()


# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()