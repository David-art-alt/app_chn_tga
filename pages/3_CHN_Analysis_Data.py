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
uploaded_file = st.file_uploader("Upload CHN files", type=["txt", "csv"], accept_multiple_files=False)

if uploaded_file:
    # Lösche die vorherigen Daten im Session-State, bevor neue hochgeladen werden
    st.session_state['chn_data'] = pd.DataFrame()


    file_name = uploaded_file.name
    try:
        content = uploaded_file.read().decode("utf-8")
        if not check_required_chn_headers(content):
            st.error(f"❌ Invalid headers in {file_name}")

        df_chn = chn_process_uploaded_file(content)
        if df_chn is None:
            st.error(f"⚠️ Could not process {file_name}")

        # Setze den Session-State mit den neuen Daten (überschreibe die alten Daten)
        st.session_state['chn_data'] = df_chn

    except Exception as e:
        st.error(f"❌ Error in {file_name}: {e}")
# ----------------------
# Daten aus DB abrufen (join)
# ----------------------
st.sidebar.header("Filter")

# Sicherstellen, dass wir Daten von der DB abrufen können und sie existieren
try:
    all_chn_data = fetch_all_chn_data()

    if all_chn_data is None or all_chn_data.empty:
        st.warning("⚠️ No CHN data found in the database.")
        data = pd.DataFrame()  # Leerer DataFrame, wenn keine Daten vorhanden sind
    else:
        # Fetch all projects for selectbox, falls vorhanden
        proj_chn = all_chn_data['project'].dropna().unique().tolist()

        # Filter by selected project
        proj = st.sidebar.selectbox("Project", [""] + proj_chn)
        filtered_data = all_chn_data[all_chn_data['project'] == proj] if proj else all_chn_data
        sample_options = filtered_data['sample_id'].dropna().unique().tolist()

        sid = st.sidebar.selectbox("Sample ID", [""] + sample_options, key="chn_sample_select")
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
    st.warning("⚠️ No CHN data available for the selected filter.")
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

    # Upload to Database
    if st.sidebar.button("📤 Upload CHN to DB"):
        success, skipped, errors, missing = save_dataframe_to_chn_table(st.session_state['chn_data'])
        if success:
            st.success(f"✅ Successfully saved: {success}")
            st.session_state['chn_data'] = pd.DataFrame()
            st.rerun()
        if skipped:
            st.info(f"ℹ️ Skipped (already present or invalid): {skipped}")
        if errors:
            st.error(f"❌ Upload Error: {errors}")
        if missing:
            st.warning(f"⚠️ Sample IDs are not registered: {', '.join(set(missing))}")