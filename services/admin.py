import streamlit as st
from services.database import fetch_all_users, add_user

# Admin-Bereich
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Welcome to the Admin Dashboard. Here you can manage users.")

    # Form: Add a new user
    with st.form("Add New User"):
        new_username = st.text_input("Username:")
        new_password = st.text_input("Password:", type="password")
        role = st.selectbox("Role", options=["user", "admin"])
        submitted = st.form_submit_button("Add User")

        if submitted:
            users = fetch_all_users()
            if new_username in [user[0] for user in users]:
                st.warning(f"The username '{new_username}' already exists. Please choose a different one.")
            else:
                add_user(new_username, new_password, role)
                st.success(f"User '{new_username}' has been successfully added.")

    # Display the user list
    st.subheader("User List")
    users = fetch_all_users()
    if users:
        for user in users:
            st.write(f"Username: {user[0]}, Role: {user[1]}")
    else:
        st.info("No users found.")


