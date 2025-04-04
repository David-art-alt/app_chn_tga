import streamlit as st
from services.eltra_tga_processing import result_files_to_df, tga_calculate_mean, check_file_content_results
from services.export import tga_export_to_excel
from services.database import check_existing_data, save_dataframe_to_sql, fetch_all_data
import pandas as pd

# Sicherstellen, dass ein Benutzer eingeloggt ist
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()  # Beendet die weitere Ausführung der Seite

# Seitenkonfiguration
st.set_page_config(
    page_title="ELTRA TGA Analyzer",
    page_icon="📊",
    layout="wide"
)

# Seitentitel
st.title("ELTRA TGA Analysis")

# Initialisiere Session-Status für den Download-Button
if "download_ready" not in st.session_state:
    st.session_state["download_ready"] = False
    st.session_state["download_buffer"] = None

# Datei-Upload-Bereich
uploaded_files = st.file_uploader(
    label="Select one or more ELTRA TGA analysis files",
    type=["txt", "csv"],
    accept_multiple_files=True
)

# Hauptlogik: Verarbeite hochgeladene Dateien
if uploaded_files:  # Gehe nur weiter, wenn Dateien hochgeladen werden
    st.write("🔍 Starting file validation...")

    # Temporäre Pfade für hochgeladene Dateien
    temp_file_paths = []
    status_messages = []

    for uploaded_file in uploaded_files:
        temp_path = f"{uploaded_file.name}"
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_file_paths.append(temp_path)
        except Exception as e:
            st.error(f"❌ Error while saving the file '{uploaded_file.name}': {e}")
            continue  # Fahre mit verbleibenden Dateien fort, wenn ein Fehler auftritt

    # Dateien auf Gültigkeit prüfen
    valid_files = check_file_content_results(temp_file_paths)

    # Validierungsergebnisse anzeigen
    for file in temp_file_paths:
        if file in valid_files:
            status_messages.append(f"✅ File '{file}' is valid.")
        else:
            status_messages.append(f"❌ File '{file}' is invalid or could not be verified.")

    # Zeige Validierungsstatus für jede Datei
    for msg in status_messages:
        st.write(msg)

    # Weiterverarbeitung nur für gültige Dateien
    if valid_files:
        dfs_all = result_files_to_df(valid_files)

        if dfs_all:
            # Mittelwerte und Gesamtdaten kombinieren
            dfs_mean = [tga_calculate_mean(df) for df in dfs_all]
            df_combined_all = pd.concat(dfs_all, ignore_index=True)
            df_combined_mean = pd.concat(dfs_mean, ignore_index=True)

            # Berechnungsergebnisse anzeigen
            st.subheader("Mean values by ID")
            st.dataframe(df_combined_mean)

            st.subheader("All ELTRA TGA Data")
            st.dataframe(df_combined_all)

            # Excel-Export vorbereiten
            buffer = tga_export_to_excel(df_combined_mean, df_combined_all)

            # Update Session-State mit Download-Daten
            st.session_state["download_ready"] = True
            st.session_state["download_buffer"] = buffer

            st.success("🎉 Data is ready for download!")

            # Datenbank-Upload-Sektion
            st.subheader("Upload to Database")
            if st.button("Save Processed Data to Database"):
                try:
                    if not check_existing_data(df_combined_all, "eltra_tga_data"):
                        save_dataframe_to_sql(df_combined_all, "eltra_tga_data")
                        st.success("Data successfully saved to the database!")
                    else:
                        st.warning("Data already exists in the database!")
                except Exception as e:
                    st.error(f"❌ Error during database operation: {e}")
        else:
            st.error("No valid data could be processed.")
    else:
        st.error("No valid files found. Please check your input files.")

# Platzhalter für den Download-Bereich
if st.session_state.get("download_ready") and st.session_state["download_buffer"]:
    with st.sidebar:  # Download-Button in der Seitenleiste
        st.download_button(
            label="📥 Download Excel File",
            data=st.session_state["download_buffer"],
            file_name="ELTRA_TGA_Analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Bereich zum Anzeigen vorhandener Daten aus der Datenbank
st.subheader("ELTRA TGA Proximate Analysis Data of Registered Samples")
if st.button("View TGA Data"):
    samples = fetch_all_data('eltra_tga_data')
    if not samples.empty:
        st.table(samples)
    else:
        st.warning("No data available in the database!")
