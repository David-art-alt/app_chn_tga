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

    # Button immer anzeigen, aber keinen Download ermöglichen, wenn keine Sample ID ausgewählt wurde
    st.markdown(
        f"""
              <style>
              .stButton button {{
                  background-color: #f0f0f5;
                  border: 1px solid #d6d6d6;
                  color: black;
                  width: 100%;  /* Macht den Button genauso breit wie das Eingabefeld */
                  padding: 10px 20px;
                  border-radius: 5px;
                  font-size: 16px;
                  font-weight: 500;
                  transition: background-color 0.3s ease;
              }}
              .stButton button:hover {{
                  background-color: #e1e1eb;
                  border-color: #c0c0c8;
                  color: black;
              }}
              
              </style>
              """, unsafe_allow_html=True
    )


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

