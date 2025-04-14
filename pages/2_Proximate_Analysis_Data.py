import streamlit as st
import pandas as pd
import io
from services.eltra_tga_processing import check_required_tga_headers, tga_process_uploaded_file
from services.export import chn_export_to_excel
from services.database import save_dataframe_to_supabase, fetch_all_data

# Sicherstellen, dass ein Benutzer eingeloggt ist
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("You must be logged in to access this page.")
    st.stop()

# Initialisiere TGA-Daten im Session-State
if 'tga_data' not in st.session_state:
    st.session_state['tga_data'] = pd.DataFrame()

st.set_page_config(
    page_title="ELTRA TGA Analysis",
    page_icon="📈",
    layout="wide"
)

# Datei-Upload
uploaded_files = st.file_uploader(
    label="Choose one or more ELTRA TGA analysis files for upload.",
    type=["txt", "csv"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name

        try:
            content = uploaded_file.read().decode("utf-8")

            if not check_required_tga_headers(content):
                st.error(f"❌ The file {file_name} does not contain valid ELTRA TGA headers.")
                continue

            df_tga = tga_process_uploaded_file(content)
            if df_tga is None:
                st.error(f"⚠️ Processing failed for {file_name}.")
                continue

            # Duplikate lokal vermeiden
            if not st.session_state['tga_data'].empty:
                df_tga = df_tga[~df_tga['sample_id'].isin(st.session_state['tga_data']['sample_id'])]

            st.session_state['tga_data'] = pd.concat([st.session_state['tga_data'], df_tga], ignore_index=True)

        except Exception as e:
            st.error(f"❌ Error processing the file {file_name}: {e}")


# 🔍 Supabase-Query für Join
def fetch_joined_data():
    df_tga = fetch_all_data("eltra_tga_data")
    df_samples = fetch_all_data("samples")

    if df_tga.empty or df_samples.empty:
        return pd.DataFrame()

    return df_tga.merge(df_samples[['sample_id', 'project']], on='sample_id', how='left')


# 🗂 Daten aus Supabase anzeigen
data = fetch_joined_data()

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

    st.markdown("<h2 style='text-align: center;'>TGA Data from Supabase</h2>", unsafe_allow_html=True)
    st.dataframe(data, height=400)


# 📤 Hochgeladene Daten anzeigen & speichern
if st.session_state['tga_data'].empty:
    st.warning("⚠️ No uploaded data available.")
else:
    st.markdown("<h2 style='text-align: center;'>Uploaded ELTRA TGA Data</h2>", unsafe_allow_html=True)
    st.dataframe(st.session_state['tga_data'])

    # Download-Button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        st.session_state['tga_data'].to_excel(writer, sheet_name="ELTRA_TGA_Data", index=False)
    output.seek(0)

    st.sidebar.download_button(
        label="📥 Download Uploaded-Data as Excel File",
        data=output,
        file_name="TGA_Daten.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.sidebar.button("📤 Upload TGA-Data to Database"):
        try:
            save_dataframe_to_supabase(st.session_state['tga_data'], "eltra_tga_data")
            st.success("✅ Data uploaded to Supabase.")
        except Exception as e:
            st.error(f"❌ Error uploading the data: {e}")