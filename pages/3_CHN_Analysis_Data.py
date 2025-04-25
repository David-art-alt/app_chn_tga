import streamlit as st
import pandas as pd
import io
from services.chn_processing import chn_process_uploaded_file, check_required_chn_headers
from services.database import fetch_all_chn_data, save_dataframe_to_chn_table

# Sicherstellen, dass ein Benutzer eingeloggt ist
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

# Initialisiere CHN-Daten im Session-State
if 'chn_data' not in st.session_state:
    st.session_state['chn_data'] = pd.DataFrame()

st.set_page_config(page_title="CHN Analysis", page_icon="📈", layout="wide")

# Datei-Upload
uploaded_files = st.file_uploader("Upload CHN files", type=["txt", "csv"], accept_multiple_files=True)

# Verarbeitung der Dateien
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        try:
            content = uploaded_file.read().decode("utf-8")
            if not check_required_chn_headers(content):
                st.error(f"❌ Invalid headers in {file_name}")
                continue

            df_chn = chn_process_uploaded_file(content)
            if df_chn is None:
                st.error(f"⚠️ Could not process {file_name}")
                continue

            # Vermeidung von Duplikaten (lokal)
            if not st.session_state['chn_data'].empty:
                df_chn = df_chn[~df_chn['sample_id'].isin(st.session_state['chn_data']['sample_id'])]

            st.session_state['chn_data'] = pd.concat([st.session_state['chn_data'], df_chn], ignore_index=True)

        except Exception as e:
            st.error(f"❌ Error in {file_name}: {e}")

# ----------------------
# Daten aus DB abrufen (join)
# ----------------------
st.sidebar.header("Filter")
all_projects = fetch_all_chn_data()['project'].dropna().unique().tolist()
proj = st.sidebar.selectbox("Project", [""] + all_projects)
filtered_data = fetch_all_chn_data(project_filter=proj)
sample_options = filtered_data['sample_id'].dropna().unique().tolist()
sid = st.sidebar.selectbox("Sample ID", [""] + sample_options, key="chn_sample_select")
if sid:
    filtered_data = filtered_data[filtered_data['sample_id'] == sid]
data = filtered_data

if data.empty:
    st.warning("⚠️ No CHN data in database.")
else:
    st.markdown("<h2 style='text-align: center;'>CHN Data</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)

# ----------------------
# Hochgeladene Daten anzeigen & speichern
# ----------------------
if st.session_state['chn_data'].empty:
    st.warning("⚠️ No uploaded CHN data.")
else:
    st.markdown("<h2 style='text-align: center;'>Uploaded CHN Data</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state['chn_data'])

    # Download-Button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state['chn_data'].to_excel(writer, sheet_name="CHN", index=False)
    output.seek(0)

    st.sidebar.download_button("📥 Download Excel", data=output, file_name="CHN_Daten.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Upload zur Datenbank
    if st.sidebar.button("📤 Upload CHN to DB"):
        success, skipped, errors, missing = save_dataframe_to_chn_table(st.session_state['chn_data'])
        if success:
            st.success(f"✅ Erfolgreich gespeichert: {success}")
            st.session_state['chn_data'] = pd.DataFrame()
            st.rerun()
        if skipped:
            st.info(f"ℹ️ Übersprungen (bereits vorhanden oder ungültig): {skipped}")
        if errors:
            st.error(f"❌ Fehler beim Speichern: {errors}")
        if missing:
            st.warning(f"⚠️ Nicht gefundene Sample IDs: {', '.join(set(missing))}")