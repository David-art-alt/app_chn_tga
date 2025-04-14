import streamlit as st
from services.admin import admin_dashboard
from services.database import initialize_default_users
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

    # Initialisiere Standard-Admin (falls nicht vorhanden)
    initialize_default_users()

    # Login prüfen oder Login anzeigen
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login()
    else:
        app()


# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()