import logging
import streamlit as st
from services.database import fetch_all_users, authenticate_user, add_user

# Login-Funktion
def login():
    """Ein einfacher Login-Mechanismus für Streamlit."""
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username:")
    password = st.sidebar.text_input("Password:", type="password")

    if st.sidebar.button("Login"):
        # Authentifizieren und die Rolle abrufen
        login_true = authenticate_user(username, password)
        if login_true:
            logging.info("Login successful.")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username

            # Benutzerrolle zuweisen
            if username == "admin":  # Wenn Benutzer 'admin', dann die Rolle 'admin'
                st.session_state["role"] = "admin"
            else:  # Andernfalls die Rolle 'user'
                st.session_state["role"] = "user"

            st.success(f"Welcome {st.session_state['role']}: {username}!)")
        else:
            st.error("Invalid username or password.")

# Logout-Funktion
def logout():
    """Setzt den Login-Zustand zurück und blockiert die Applikation."""
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None  # Optional, zum Zurücksetzen des Benutzerstatus

