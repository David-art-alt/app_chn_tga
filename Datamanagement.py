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

    # Admin-specific navigation
    if st.session_state.get("role") == "admin":
        selection = st.sidebar.radio("Select Page", ["Home", "Admin-Dashboard"])
    else:
        st.info("🔒 No admin privileges. Limited functionality.")
        selection = None

    # Seiteninhalte basierend auf der Auswahl
    if selection == "Admin-Dashboard":
        admin_dashboard()

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
              .stTextInput input {{
                  width: 100%;  /* Macht das Eingabefeld genauso breit wie den Button */
                  padding: 10px 20px;
                  border-radius: 5px;
                  border: 1px solid #d6d6d6;
                  font-size: 16px;
                  font-weight: 500;
              }}
              </style>
              """, unsafe_allow_html=True
    )

    # Logout-Button
    st.sidebar.button("Logout", on_click=logout)


# ----------------------------
# Steuerungslogik
# ----------------------------
def main():
    """Main logic of the application."""

    st.set_page_config(page_title="IVET Data Management", page_icon="📊")
    st.markdown("<h2 style='text-align: center;'>IVET DATA MANAGEMENT</h2>", unsafe_allow_html=True)
    # Initialisiere DB bei Bedarf
    db_was_initialized = initialize_database_if_needed()
    if db_was_initialized:
        st.toast("📦 Database has been reinitialized")
        st.info("💡 The database has been freshly created and is ready.")
        initialize_default_users()
     # Check/create admin user

    # Check login
    if not st.session_state.get("logged_in", False):
        st.info("🔐 Please log in to continue.")
        login()
    else:
        app()


# ----------------------------
# Startpunkt
# ----------------------------
if __name__ == "__main__":
    main()