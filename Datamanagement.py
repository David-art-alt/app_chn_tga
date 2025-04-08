import streamlit as st
from services.database import initialize_database, authenticate_user, add_user, fetch_all_users, \
    check_database_connection
from services.siedbar_layout import admin_dashboard, login, logout
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
    """Hauptsteuerungs-Logik der App."""

    if not check_database_connection():
        st.stop()

    # Weiter mit App-Logik, z. B. Login oder Dashboard
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login()  # z. B. eigene Login-Funktion
    else:
        app()  # z. B. dein Hauptdashboard

# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()