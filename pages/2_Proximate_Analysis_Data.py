
import streamlit as st
import pandas as pd
import io
from services.eltra_tga_processing import check_required_tga_headers, tga_process_uploaded_file
from services.database import save_dataframe_to_tga_table,fetch_all_eltra_tga_data

# Login prüfen
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

# Session-State vorbereiten
if 'tga_data' not in st.session_state:
    st.session_state['tga_data'] = pd.DataFrame()

st.set_page_config(page_title="ELTRA TGA Analysis", page_icon="🔥", layout="wide")

# Datei-Upload
uploaded_file = st.file_uploader("Upload ELTRA TGA files", type=["txt", "csv"], accept_multiple_files=False)

# Datei-Verarbeitung
if uploaded_file:

    file_name = uploaded_file.name
    try:
        content = uploaded_file.read().decode("utf-8")

        if not check_required_tga_headers(content):
            st.error(f"❌ Invalid headers in {file_name}")


        df_tga = tga_process_uploaded_file(content)
        if df_tga is None:
            st.error(f"⚠️ Could not process {file_name}")

        # Duplikate lokal vermeiden
        if not st.session_state['tga_data'].empty:
            df_tga = df_tga[~df_tga['sample_id'].isin(st.session_state['tga_data']['sample_id'])]

            # Setze den Session-State mit den neuen Daten (überschreibe die alten Daten)
            st.session_state['chn_data'] = df_tga

    except Exception as e:
        st.error(f"❌ Error in {file_name}: {e}")

# ----------------------
# Daten aus DB abrufen (join)
# ----------------------
st.sidebar.header("Filter")

# Sicherstellen, dass wir Daten von der DB abrufen können und sie existieren
try:
    all_tga_data = fetch_all_eltra_tga_data()

    if all_tga_data is None or all_tga_data.empty:
        st.warning("⚠️ No ELTRA TGA data found in the database.")
        data = pd.DataFrame()  # Leerer DataFrame, wenn keine Daten vorhanden sind
    else:
        # Fetch all projects for selectbox, falls vorhanden
        proj_tga = all_tga_data['project'].dropna().unique().tolist()

        # Filter by selected project
        proj = st.sidebar.selectbox("Project", [""] + proj_tga)
        filtered_data = all_tga_data[all_tga_data['project'] == proj] if proj else all_tga_data
        sample_options = filtered_data['sample_id'].dropna().unique().tolist()

        sid = st.sidebar.selectbox("Sample ID", [""] + sample_options, key="tga_sample_select")
        if sid:
            filtered_data = filtered_data[filtered_data['sample_id'] == sid]
        data = filtered_data

except Exception as e:
    st.error(f"❌ Error fetching data from database: {e}")
    data = pd.DataFrame()  # Leerer DataFrame, wenn ein Fehler auftritt

# ----------------------
# Anzeige der gefilterten Daten
# ----------------------
if data.empty:
    st.warning("⚠️ No ELTRA-TGA data available for the selected filter.")
else:
    st.markdown("<h2 style='text-align: center;'>ELTRA TGA Data</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)

# ----------------------
# Hochgeladene Daten anzeigen & speichern
# ----------------------
if st.session_state['tga_data'].empty:
    st.warning("⚠️ No uploaded ELTRA TGA data.")
else:
    st.markdown("<h2 style='text-align: center;'>Uploaded ELTRA TGA Data</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state['tga_data'])

    # Download-Button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state['tga_data'].to_excel(writer, sheet_name="ELTRA TGA", index=False)
    output.seek(0)

    st.sidebar.download_button("📥 Download Excel", data=output, file_name="ELTRA_TGA_Daten.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Upload to Database
    if st.sidebar.button("📤 Upload ELTRA TGA to DB"):
        success, skipped, errors, missing = save_dataframe_to_tga_table(st.session_state['tga_data'])
        if success:
            st.success(f"✅ Successfully saved: {success}")
            st.session_state['tga_data'] = pd.DataFrame()
            st.rerun()
        if skipped:
            st.info(f"ℹ️ Skipped (already present or invalid): {skipped}")
        if errors:
            st.error(f"❌ Upload Error: {errors}")
        if missing:
            st.warning(f"⚠️ Sample IDs are not registered: {', '.join(set(missing))}")