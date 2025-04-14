####################################################################################
import os
import logging
import pandas as pd
import bcrypt
from dotenv import load_dotenv
from supabase import create_client
import streamlit as st

# Logging-Konfiguration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Lade Umgebungsvariablen
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Benutzerfunktionen
def add_user(username, password, role):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    data = {"username": username, "password": hashed_pw, "role": role}
    response = supabase.table("users").insert(data).execute()
    if response.error:
        logging.error(f"❌ Error adding user: {response.error}")
        return False
    return True

def authenticate_user(username, password):
    response = supabase.table("users").select("*").eq("username", username).execute()
    if not response.error and response.data:
        user = response.data[0]
        stored_pw = user["password"]
        if bcrypt.checkpw(password.encode(), stored_pw.encode()):
            return True, user["role"]
    return False, None

# Initialisierung
def initialize_default_users():
    response = supabase.table("users").select("*").eq("username", "admin").execute()
    if not response.error and not response.data:
        add_user("admin", "admin", "admin")
        logging.info("✅ Default admin user created")

# Sample speichern
def save_sample_data(sample_id, sample_type, project, registration_date, sampling_date, location, condition, responsible):
    data = {
        "sample_id": sample_id,
        "sample_type": sample_type,
        "project": project,
        "registration_date": registration_date,
        "sampling_date": sampling_date,
        "sampling_location": location,
        "sample_condition": condition,
        "responsible_person": responsible
    }
    response = supabase.table("samples").insert(data).execute()
    if response.error:
        logging.error(f"❌ Error saving sample: {response.error}")
        return False
    return True

def fetch_all_users():
    response = supabase.table("users").select("username, role").execute()
    if response.error:
        logging.error(f"❌ Error fetching users: {response.error}")
        return []
    return [(user["username"], user["role"]) for user in response.data]

def fetch_all_samples():
    response = supabase.table("samples").select("*").execute()
    if response.error or not response.data:
        logging.error(f"❌ Error fetching samples: {response.error}")
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def fetch_all_data(table_name):
    response = supabase.table(table_name).select("*").execute()
    if response.error or not response.data:
        logging.error(f"❌ Error fetching {table_name}: {response.error}")
        return pd.DataFrame()
    return pd.DataFrame(response.data)

def check_existing_data(new_df: pd.DataFrame, table_name, unique_cols):
    existing = fetch_all_data(table_name)
    if existing.empty:
        return False
    if all(col in existing.columns for col in unique_cols):
        merged = new_df.merge(existing, on=unique_cols, how="inner")
        return not merged.empty
    return False

def save_dataframe_to_supabase(df: pd.DataFrame, table_name):
    data = df.to_dict(orient='records')
    response = supabase.table(table_name).insert(data).execute()
    if response.error:
        logging.error(f"❌ Error saving to {table_name}: {response.error}")
        return False
    logging.info(f"✅ {len(data)} rows saved to {table_name}.")
    return True