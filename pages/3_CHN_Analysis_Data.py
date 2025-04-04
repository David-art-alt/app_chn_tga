import sqlite3
import streamlit as st
import pandas as pd
import io
from services.chn_processing import chn_process_uploaded_file, chn_calculate_mean, check_required_chn_headers
from services.export import chn_export_to_excel
from services.database import save_dataframe_to_sql, fetch_all_data, get_db_path

# Sicherstellen, dass ein Benutzer eingeloggt ist
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

# Initialisiere die CHN-Daten im Session-State (falls noch nicht vorhanden)
if 'chn_data' not in st.session_state:
    st.session_state['chn_data'] = pd.DataFrame()

# Streamlit-Seite konfigurieren
st.set_page_config(
    page_title="CHN Analysis",
    page_icon="📈",
    layout="wide"
)

# Datei-Upload-Bereich
uploaded_files = st.file_uploader(
    label="Choose one or more CHN Leco TruSpec analysis files for upload.",
    type=["txt", "csv"],
    accept_multiple_files=True
)

# Hochgeladene Dateien verarbeiten
if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name

        try:
            content = uploaded_file.read().decode("utf-8")

            # CHN-Header überprüfen
            if not check_required_chn_headers(content):
                st.error(f"❌ The file {file_name} does not contain valid CHN headers.")
                continue

            # Datei verarbeiten
            df_chn = chn_process_uploaded_file(content)
            if df_chn is None:
                st.error(f"⚠️ Processing failed for {file_name}.")
                continue

            # Vermeidung von Duplikaten basierend auf einer eindeutigen Spalte (z. B. 'sample_id')
            if not st.session_state['chn_data'].empty:
                df_chn = df_chn[~df_chn['sample_id'].isin(st.session_state['chn_data']['sample_id'])]

            # Daten hinzufügen
            st.session_state['chn_data'] = pd.concat([st.session_state['chn_data'], df_chn], ignore_index=True)
            #st.success(f"✅ File '{file_name}' successfully processed and added!")

        except Exception as e:
            st.error(f"❌ Error processing the file {file_name}: {e}")


# Bereich zum Anzeigen vorhandener Daten aus der Datenbank
# Verbindung zur SQLite-Datenbank herstellen
def get_db_connection():
    conn = sqlite3.connect(get_db_path())  # Ersetzen Sie 'your_database.db' durch den Pfad zu Ihrer Datenbank
    conn.row_factory = sqlite3.Row
    return conn


# Daten aus der Datenbank abrufen und Tabellen verknüpfen
def fetch_joined_data():
    with get_db_connection() as conn:
        query = """
        SELECT chn_data.*, samples.project
        FROM chn_data
        JOIN samples ON chn_data.sample_id = samples.sample_id
        """
        df = pd.read_sql_query(query, conn)
    return df


# Daten aus der Datenbank abrufen
data = fetch_joined_data()

if data.empty:
    st.warning("⚠️ No Data from Database available.")
else:
    # Filteroptionen in der Sidebar hinzufügen
    st.sidebar.header("Filteroptions")
    sample_id_filter = st.sidebar.text_input("Sample ID")
    project_filter = st.sidebar.text_input("Project")

    # Daten basierend auf den Filtern filtern
    if sample_id_filter:
        data = data[data['sample_id'].str.contains(sample_id_filter, case=False, na=False)]
    if project_filter:
        data = data[data['project'].str.contains(project_filter, case=False, na=False)]

    st.markdown("<h2 style='text-align: center;'>CHN Data from Database</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)

# Anzeige der hochgeladenen Daten im Session-State
if st.session_state['chn_data'].empty:
    st.warning("⚠️ No uploaded data available.")
else:
    st.markdown("<h2 style='text-align: center;'>Uploaded CHN Data</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state['chn_data'])

    # Download-Button in der Sidebar
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state['chn_data'].to_excel(writer, sheet_name="CHN_Data", index=False)
    output.seek(0)

    st.sidebar.download_button(
        label="📥 Download Uploaded-Data as Excel File",
        data=output,
        file_name="CHN_Daten.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Upload-Button für CHN-Daten zur Datenbank hinzufügen
    if st.sidebar.button("📤 Upload CHN-Data to Database"):
        try:
            # Hochgeladene Daten in die Datenbank speichern
            save_dataframe_to_sql(st.session_state['chn_data'], 'chn_data')


        except Exception as e:
            st.error(f"❌ Error uploading the data: {e}")