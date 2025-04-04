import streamlit as st
import datetime

from services.database import save_sample_data, fetch_all_samples
from services.generate_id import generate_sample_id

# Sicherstellen, dass ein Benutzer eingeloggt ist
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()  # Beendet die weitere Ausführung der Seite

# Wenn der Benutzer eingeloggt ist, wird der Rest der Seite angezeigt
st.title("Sample Registration")

with st.form("sample_form"):
    prefix = st.text_input("Sample ID Prefix", "ABC")
    sample_type = st.text_input("Sample Type")
    project = st.text_input("Project")
    sampling_date = st.date_input("Sampling Date")
    location = st.text_input("Sampling Location")
    condition = st.text_input("Sample Condition")
    responsible = st.text_input("Responsible Person")
    submitted = st.form_submit_button("Register Sample")

    if submitted:
        sample_id = generate_sample_id(prefix)

        print(f"Generated Sample ID: {sample_id}")

        registration_date = datetime.datetime.now().date()

        success = save_sample_data(sample_id, sample_type, project, registration_date, sampling_date, location, condition,
                     responsible)

        if success:
            st.success(f"Sample {sample_id} has been registered!")
        else:
            st.error(f"Failed to register sample {sample_id}. Check the logs for details.")


st.subheader("Registered Samples")
if st.button("View All Samples"):
    samples = fetch_all_samples()  # Fetch from `services.database`
    st.table(samples)
