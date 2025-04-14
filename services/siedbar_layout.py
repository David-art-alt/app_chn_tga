import logging
import streamlit as st
from services.database import authenticate_user

# Login-Funktion
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username:")
    password = st.sidebar.text_input("Password:", type="password")

    if st.sidebar.button("Login"):
        login_successful, role = authenticate_user(username, password)
        if login_successful:
            logging.info("✅ Login successful.")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role

            st.success(f"Welcome {role}: {username}!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password.")

# Logout-Funktion
def logout():
    """Setzt den Login-Zustand zurück und blockiert die Applikation."""
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None
    st.rerun()  # Sofort zurück zur Login-Seite