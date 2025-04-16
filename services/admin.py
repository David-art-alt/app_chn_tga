import streamlit as st
from services.database import fetch_all_users, add_user, update_user_role, delete_user

def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Welcome to the Admin Dashboard. Here you can manage users.")

    # Benutzerliste abrufen
    users = fetch_all_users()
    existing_usernames = {user[0] for user in users}

    # ---------------------------
    # Add New User
    # ---------------------------
    with st.form("Add New User"):
        new_username = st.text_input("Username:")
        new_password = st.text_input("Password:", type="password")
        role = st.selectbox("Role", options=["user", "admin"])
        submitted = st.form_submit_button("Add User")

        if submitted:
            if new_username in existing_usernames:
                st.warning(f"The username '{new_username}' already exists.")
            else:
                success = add_user(new_username, new_password, role)
                if success:
                    st.success(f"User '{new_username}' has been added.")
                    st.rerun()
                else:
                    st.error("❌ Could not add user. Check logs for details.")

    # ---------------------------
    # Update Role
    # ---------------------------
    st.write("Change Role of Existing User")
    if users:
        selected_user = st.selectbox("Select User", [user[0] for user in users], key="update_role")
        new_role = st.selectbox("New Role", ["user", "admin"], key="role_select")
        if st.button("Update Role"):
            update_user_role(selected_user, new_role)
            st.success(f"✅ Role updated for {selected_user} to {new_role}")
            st.rerun()

    # ---------------------------
    # Delete User
    # ---------------------------
    st.write("Delete a User")
    if users:
        user_to_delete = st.selectbox("Select User to Delete", [user[0] for user in users], key="delete_user")
        if st.button("Delete User"):
            delete_user(user_to_delete)
            st.success(f"🗑️ User {user_to_delete} has been deleted.")
            st.rerun()

    # ---------------------------
    # User List
    # ---------------------------
    st.subheader("User List")
    users = fetch_all_users()
    if users:
        for user in users:
            st.write(f"👤 Username: `{user[0]}` | Role: `{user[1]}`")
    else:
        st.info("No users found.")