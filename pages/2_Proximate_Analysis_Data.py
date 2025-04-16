
import streamlit as st
import pandas as pd
import io
from services.eltra_tga_processing import check_required_tga_headers, tga_process_uploaded_file
from services.export import chn_export_to_excel
from services.database import save_dataframe_to_tga_table, fetch_all_data, Sample, EltraTGAData

# Login prüfen
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

# Session-State vorbereiten
if 'tga_data' not in st.session_state:
    st.session_state['tga_data'] = pd.DataFrame()

st.set_page_config(page_title="ELTRA TGA Analysis", page_icon="🔥", layout="wide")

# Datei-Upload
uploaded_files = st.file_uploader("Upload ELTRA TGA files", type=["txt", "csv"], accept_multiple_files=True)

# Datei-Verarbeitung
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        try:
            content = uploaded_file.read().decode("utf-8")

            if not check_required_tga_headers(content):
                st.error(f"❌ Invalid headers in {file_name}")
                continue

            df_tga = tga_process_uploaded_file(content)
            if df_tga is None:
                st.error(f"⚠️ Could not process {file_name}")
                continue

            # Duplikate lokal vermeiden
            if not st.session_state['tga_data'].empty:
                df_tga = df_tga[~df_tga['sample_id'].isin(st.session_state['tga_data']['sample_id'])]

            st.session_state['tga_data'] = pd.concat([st.session_state['tga_data'], df_tga], ignore_index=True)

        except Exception as e:
            st.error(f"❌ Error in {file_name}: {e}")

# Daten aus DB (Join)
def fetch_joined_data():
    df_tga = fetch_all_data(EltraTGAData)
    df_samples = fetch_all_data(Sample)

    if df_tga.empty or df_samples.empty:
        return pd.DataFrame()

    return df_tga.merge(df_samples[['sample_id', 'project']], on='sample_id', how='left')

# Anzeigen & Filtern
data = fetch_joined_data()
if data.empty:
    st.warning("⚠️ No TGA data in database.")
else:
    st.sidebar.header("Filter")
    sid = st.sidebar.text_input("Sample ID")
    proj = st.sidebar.text_input("Project")

    if sid:
        data = data[data['sample_id'].str.contains(sid, case=False, na=False)]
    if proj:
        data = data[data['project'].str.contains(proj, case=False, na=False)]

    st.markdown("<h2 style='text-align: center;'>TGA Data from Database</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)

# Hochgeladene Daten anzeigen
if st.session_state['tga_data'].empty:
    st.warning("⚠️ No uploaded TGA data.")
else:
    st.markdown("<h2 style='text-align: center;'>Uploaded TGA Data</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state['tga_data'])

    # Excel-Download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state['tga_data'].to_excel(writer, sheet_name="TGA", index=False)
    output.seek(0)

    st.sidebar.download_button("📥 Download Excel", data=output, file_name="TGA_Daten.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 📤 Upload TGA-Daten in die Datenbank
    if st.sidebar.button("📤 Upload TGA to DB"):
        try:
            success, skipped, errors = save_dataframe_to_tga_table(st.session_state['tga_data'])

            if success:
                st.success(f"✅ {success} neue Datensätze gespeichert.")
            if skipped:
                st.info(f"⏭️ {skipped} Datensätze übersprungen (Duplikate oder fehlende Sample IDs).")
            if errors:
                st.warning(f"⚠️ {errors} Fehler beim Speichern der Daten. Details siehe Log.")
            if not any([success, skipped, errors]):
                st.info("ℹ️ Keine Daten wurden verarbeitet.")

        except Exception as e:
            st.error(f"❌ Upload fehlgeschlagen: {e}")