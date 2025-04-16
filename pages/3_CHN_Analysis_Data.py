import streamlit as st
import pandas as pd
import io
from services.chn_processing import chn_process_uploaded_file, check_required_chn_headers
from services.export import chn_export_to_excel
from services.database import fetch_all_data, save_dataframe_to_chn_table  # <-- neue Funktion!
from services.database import CHNData
from services.database import Sample

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
def fetch_joined_data():
    df_chn = fetch_all_data(CHNData)
    df_samples = fetch_all_data(Sample)

    if df_chn.empty or df_samples.empty:
        return pd.DataFrame()

    return df_chn.merge(df_samples[['sample_id', 'project']], on='sample_id', how='left')

# ----------------------
# Daten anzeigen & filtern
# ----------------------
data = fetch_joined_data()
if data.empty:
    st.warning("⚠️ No CHN data in database.")
else:
    st.sidebar.header("Filter")
    sid = st.sidebar.text_input("Sample ID")
    proj = st.sidebar.text_input("Project")

    if sid:
        data = data[data['sample_id'].str.contains(sid, case=False, na=False)]
    if proj:
        data = data[data['project'].str.contains(proj, case=False, na=False)]

    st.markdown("<h2 style='text-align: center;'>CHN Data from Database</h2>", unsafe_allow_html=True)
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

        st.success(f"✅ Erfolgreich gespeichert: {success}")
        if skipped:
            st.info(f"ℹ️ Übersprungen (bereits vorhanden oder ungültig): {skipped}")
        if errors:
            st.error(f"❌ Fehler beim Speichern: {errors}")
        if missing:
            st.warning(f"⚠️ Nicht gefundene Sample IDs: {', '.join(set(missing))}")