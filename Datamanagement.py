import streamlit as st
from services.admin import admin_dashboard
from services.database import initialize_database, authenticate_user, add_user, check_database_connection, \
    initialize_default_users
from services.siedbar_layout import login, logout
import os


# ----------------------------
# Hauptanwendung
# ----------------------------

def app():
    """Hauptanwendung mit geschütztem Zugriff."""
    st.sidebar.title("Navigation")

    # Admin-spezifische Navigation
    if st.session_state.get("role") == "admin":
        selection = st.sidebar.radio("Seite auswählen",
                                     ["Home", "Admin-Dashboard"])
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

    # Check if the database is connected and initialized
    db_status = check_database_connection()
    if db_status == "connection_error":
        st.error("❌ Verbindung zur Datenbank konnte nicht hergestellt werden. "
                 "Überprüfen Sie die DATABASE_URI und stellen Sie sicher, dass die Datenbank verfügbar ist.")
        st.stop()
    elif db_status == "not_initialized":
        st.warning("⚠️ Die Datenbank scheint nicht initialisiert zu sein. Initialisiere nun...")
        initialize_database()
        initialize_default_users()
        st.success("✅ Die Datenbank wurde erfolgreich initialisiert. Bitte starten Sie die Anwendung neu!")
        st.stop()

    # Check if the user is logged in, otherwise call the login function
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login()  # Zeigt den Login-Bereich an
    else:
        app()  # Startet das Haupt-Dashboard


# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()
