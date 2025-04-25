import logging
import streamlit as st
from services.database import authenticate_user

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Login-Funktion
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username:")
    password = st.sidebar.text_input("Password:", type="password")

    if st.sidebar.button("Login"):
        logging.info(f"🔐 Login attempt for user: {username}")
        st.info(f"🔍 Login attempt for user: `{username}`")

        login_successful, role = authenticate_user(username, password)
        if login_successful:
            logging.info(f"✅ Login successful for user: {username} (role: {role})")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role

            st.success(f"🎉 Welcome {role}: `{username}`!")
            st.info(f"✅ You are now logged in as `{username}` with role `{role}`")
            st.rerun()
        else:
            logging.warning(f"❌ Login failed for user: {username}")
            st.error("❌ Invalid username or password.")
            st.info("🔒 Please check your credentials and try again.")

# Logout-Funktion
def logout():
    user = st.session_state.get("username", "unknown")
    logging.info(f"🚪 User '{user}' logged out.")
    st.info(f"👋 User `{user}` has been logged out.")
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["username"] = None
    st.rerun()