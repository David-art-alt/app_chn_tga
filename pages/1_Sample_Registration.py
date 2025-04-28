import streamlit as st
import pandas as pd
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

# Fehlerbehandlung für Datenabruf
try:
    all_samples_data = fetch_all_samples()

    # Überprüfen, ob Daten existieren
    if all_samples_data is None or all_samples_data.empty:
        st.warning("⚠️ No ELTRA TGA data found in the database.")
        data = pd.DataFrame()  # Leerer DataFrame, wenn keine Daten vorhanden sind
    else:
        # Filter anzeigen, auch wenn keine Daten existieren
        st.sidebar.header("Filter and Download Options")

        # Projektfilter
        proj_tga = all_samples_data['project'].dropna().unique().tolist()
        proj = st.sidebar.selectbox("Project", [""] + proj_tga)

        # Filter anwenden, wenn Projekt ausgewählt
        filtered_data = all_samples_data[all_samples_data['project'] == proj] if proj else all_samples_data

        # Sample ID Filter
        sample_options = filtered_data['sample_id'].dropna().unique().tolist()
        sample_id = st.sidebar.selectbox("Sample ID", [""] + sample_options)

        # Filter anwenden, wenn Sample ID ausgewählt
        if sample_id:
            filtered_data = filtered_data[filtered_data['sample_id'] == sample_id]

        # Anzeige der gefilterten Daten oder der Warnung
        if filtered_data.empty:
            st.warning("⚠️ No data available for the selected filter.")
        else:
            st.markdown("<h2 style='text-align: center;'>Registered Samples</h2>", unsafe_allow_html=True)
            st.dataframe(filtered_data, height=400)

        # Wenn eine Sample ID ausgewählt wurde, anzeigen und Download ermöglichen
        if sample_id:
            # Nur wenn die sample_id gültig ist, sample_row definieren
            sample_row = filtered_data[filtered_data['sample_id'] == sample_id].iloc[0]
            label_text = f"""
            **Sample ID**: `{sample_row['sample_id'] if 'sample_id' in sample_row else 'N/A'}`  
            **Type**: `{sample_row['sample_type'] if 'sample_type' in sample_row else 'N/A'}`  
            **Project**: `{sample_row['project'] if 'project' in sample_row else 'N/A'}`  
            **Sampling Date**: `{sample_row['sampling_date'] if 'sampling_date' in sample_row else 'N/A'}`  
            **Location**: `{sample_row['sampling_location'] if 'sampling_location' in sample_row else 'N/A'}`  
            **Condition**: `{sample_row['sample_condition'] if 'sample_condition' in sample_row else 'N/A'}`  
            **Responsible**: `{sample_row['responsible_person'] if 'responsible_person' in sample_row else 'N/A'}`
            """
            file_name = f"{sample_row['sample_id']}_label.txt"  # Gültigen Dateinamen setzen
            ID = f"Download Label {file_name}"
        else:
            label_text = "No sample selected. Please choose a Sample ID to download the label."
            file_name = "NO_label.txt"  # Default-Dateiname, wenn keine Sample ID gewählt wurde
            ID = "Select ID for Download"

        # Immer den Download-Button anzeigen, aber den Download nur aktivieren, wenn file_name gültig ist
        if file_name != "NO_label.txt":
            st.sidebar.download_button(
                label=f"⬇️ {ID}",
                data=label_text,
                file_name=f"{file_name if file_name else 'sample_label.txt'}"
                # Default-Dateiname, wenn keine Sample ID gewählt wurde
            )
        else:
            # Button immer anzeigen, aber keinen Download ermöglichen, wenn keine Sample ID ausgewählt wurde
            st.markdown(
                f"""
                    <style>
                    .stButton button {{
                        background-color: #f0f0f5;
                        border: 1px solid #d6d6d6;
                        color: black;
                        width: 100%;
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
            st.sidebar.button(f"⬇️ {ID}", disabled=True)  # Zeigt den Button an, aber er ist inaktiv

except Exception as e:
    st.error(f"❌ Error fetching data from database: {e}")
    all_samples_data = pd.DataFrame()  # Leerer DataFrame, wenn ein Fehler auftritt