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

# Temporary session state to store successful registration result
if "sample_registered" not in st.session_state:
    st.session_state.sample_registered = False
    st.session_state.sample_label_text = ""
    st.session_state.sample_id = ""

@st.dialog("Register New Sample")
def register_sample_dialog():
    if not st.session_state.sample_registered:
        with st.form("sample_form"):
            prefix = st.text_input("Sample ID Prefix", "ABC")
            sample_type = st.text_input("Sample Type", help="Min. 3 characters required")
            project = st.text_input("Project")
            sampling_date = st.date_input("Sampling Date")
            location = st.text_input("Sampling Location")
            condition = st.text_input("Sample Condition")
            responsible = st.text_input("Responsible Person", help="Min. 6 characters required")

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
                    st.session_state.sample_registered = True
                    st.session_state.sample_id = sample_id
                    st.session_state.sample_label_text = f"""
                                                **Sample ID**: `{sample_id}`  
                                                **Type**: `{sample_type}`  
                                                **Project**: `{project}`  
                                                **Sampling Date**: `{sampling_date}`  
                                                **Location**: `{location}`  
                                                **Condition**: `{condition}`  
                                                **Responsible**: `{responsible}`  
                                                """
                else:
                    st.error("❌ Sample could not be registered.")
    else:
        st.success(f"✅ Sample `{st.session_state.sample_id}` has been registered!")

        st.markdown("---")
        st.markdown("### 🏷️ Sample Label")
        st.code(st.session_state.sample_label_text, language="markdown")
        if st.download_button("⬇️ Download Label & Enter", st.session_state.sample_label_text, file_name=f"{st.session_state.sample_id}_label.txt"):
            st.session_state.sample_registered = False
            st.rerun()
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
# Combined Sidebar: Filter and Download Label
# -------------------------------
st.sidebar.header("Filter and Download Options")

project_list = fetch_all_samples()['project'].dropna().unique().tolist()
project_filter = st.sidebar.selectbox("Project Filter", [""] + project_list)

# Hole gefilterte Sample-Daten
data = fetch_all_samples(project_filter=project_filter)

if data.empty:
    st.warning("⚠️ No Data from Database available.")
else:
    st.markdown("<h2 style='text-align: center;'>Registered Samples</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)

sample_options = data['sample_id'].tolist()
selected_sample = st.sidebar.selectbox("Select Sample ID", [""] + sample_options, key="download_sample_select")

label_text = ""

if selected_sample:
    sample_row = data[data['sample_id'] == selected_sample].iloc[0]
    label_text = f"""
    **Sample ID**: `{sample_row.get('sample_id', 'N/A')}`  
    **Type**: `{sample_row.get('sample_type', 'N/A')}`  
    **Project**: `{sample_row.get('project', 'N/A')}`  
    **Sampling Date**: `{sample_row.get('sampling_date', 'N/A')}`  
    **Location**: `{sample_row.get('sampling_location', 'N/A')}`  
    **Condition**: `{sample_row.get('sample_condition', 'N/A')}`  
    **Responsible**: `{sample_row.get('responsible_person', 'N/A')}`
    """

st.sidebar.download_button(
    label="⬇️ Download Label",
    data=label_text if label_text != "" else "No sample selected",
    file_name=f"{sample_row.get('sample_id', 'sample')}_label.txt" if selected_sample else "sample_label.txt"
)