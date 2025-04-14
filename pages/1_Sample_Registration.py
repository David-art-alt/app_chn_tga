import streamlit as st
import datetime
from services.database import save_sample_data, fetch_all_samples
from services.generate_id import generate_sample_id

# -------------------------------
# Login-Check
# -------------------------------
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

st.set_page_config(layout="wide")

# -------------------------------
# Dialog: Sample registrieren
# -------------------------------
@st.dialog("Register New Sample")
def register_sample_dialog():
    with st.form("sample_form"):
        prefix = st.text_input("Sample ID Prefix", "ABC")
        sample_type = st.text_input("Sample Type", help="Min. 3 characters required")
        project = st.text_input("Project")
        sampling_date = st.date_input("Sampling Date")
        location = st.text_input("Sampling Location")
        condition = st.text_input("Sample Condition")
        responsible = st.text_input("Responsible Person", help="Min. 3 characters required")

        submitted = st.form_submit_button("Register Sample")

        if submitted:
            errors = []

            if not sample_type or len(sample_type.strip()) < 3:
                errors.append("Sample Type must contain at least 3 characters.")
            if not responsible or len(responsible.strip()) < 3:
                errors.append("Responsible Person must contain at least 3 characters.")

            if errors:
                for e in errors:
                    st.error(e)
                return

            sample_id = generate_sample_id(prefix)
            registration_date = datetime.datetime.now().date()

            success = save_sample_data(
                sample_id, sample_type, project, registration_date,
                sampling_date, location, condition, responsible
            )

            if success:
                st.success(f"✅ Sample `{sample_id}` has been registered!")
                st.rerun()
            else:
                st.error("❌ Sample could not be registered.")

# -------------------------------
# Button zentriert + Styling
# -------------------------------
st.markdown(
    """
    <style>
    .stButton button {
        background-color: #f0f0f5;
        border: 1px solid #d6d6d6;
        color: black;
        width: 100%;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }
    .stButton button:hover {
        background-color: #e1e1eb;
        border-color: #c0c0c8;
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.button("➕ Register New Sample"):
    register_sample_dialog()

# -------------------------------
# Samples anzeigen
# -------------------------------
data = fetch_all_samples()

if data.empty:
    st.warning("⚠️ No Data from Database available.")
else:
    st.sidebar.header("Filteroptions")
    sample_id_filter = st.sidebar.text_input("Sample ID")
    project_filter = st.sidebar.text_input("Project")

    if sample_id_filter:
        data = data[data['sample_id'].str.contains(sample_id_filter, case=False, na=False)]
    if project_filter:
        data = data[data['project'].str.contains(project_filter, case=False, na=False)]

    st.markdown("<h2 style='text-align: center;'>Registered Samples from Supabase</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)