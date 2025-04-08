import pandas as pd
import streamlit as st
import re


def check_required_tga_headers(file_data: str) -> bool:
    """
    Checks the content of a single ELTRA TGA file to ensure it contains expected identifiers.

    Args:
        file_data (str): The content of the file as a decoded UTF-8 string.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    expected_identifiers = [
        "Tga Version:",
        "Analyse durchgeführt:",
        "Benutzer:",
        "Caption:",
        "Applikation:"
    ]

    try:
        lines = [line.strip() for line in file_data.splitlines()]
        top_lines = lines[:10]  # Only check the first 10 lines

        missing = [idf for idf in expected_identifiers if not any(line.startswith(idf) for line in top_lines)]

        if missing:
            return False
        return True

    except Exception:
        return False


def tga_process_uploaded_file(file_content: str) -> pd.DataFrame | None:
    """
    Processes the content of a single ELTRA TGA result file and returns a cleaned DataFrame,
    including the 'analysis_date' extracted from the header.

    Args:
        file_content (str): The decoded content of the uploaded file.

    Returns:
        pd.DataFrame | None: Processed data or None if an error occurred.
    """
    try:
        lines = file_content.splitlines()
        data = []
        columns = None
        expected_num_columns = None
        analysis_date_str = None

        # 1. Extrahiere Datum aus Kopfbereich
        for line in lines[:15]:  # Nur in den ersten Zeilen suchen
            if line.strip().startswith("Analyse durchgeführt:"):
                raw_date = line.split("Analyse durchgeführt:")[1].strip()
                analysis_date_str = raw_date
                break

        if not analysis_date_str:
            st.warning("⚠️ No 'Analyse durchgeführt:' date found.")
            analysis_date_str = ""

        for line in lines:
            if "N ," in line and "Id" in line:
                columns = [col.strip() for col in line.split(',')]
                expected_num_columns = len(columns)
                continue

            if any(keyword in line for keyword in ["Gruppe", "MW:", "STD:"]):
                continue

            values = line.split(',')
            if columns and len(values) == expected_num_columns:
                data.append([val.strip() for val in values])

        if not columns or not data:
            st.error("❌ No valid data structure found in the uploaded TGA file.")
            return None

        df = pd.DataFrame(data, columns=columns)

        # Typkonvertierung
        if "N" in df.columns:
            df["N"] = pd.to_numeric(df["N"], errors="coerce", downcast="integer")
        if "Id" in df.columns:
            df["Id"] = df["Id"].astype(str)

        for col in df.columns[2:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Relevante Spalten auswählen und umbenennen
        df_tga_all = df[['Id', 'Moisture', 'Va', 'Aa_LTA', 'Aa_HTA', 'Vd', 'Ad_LTA', 'Ad_HTA', 'FCa']].copy()
        df_tga_all.rename(columns={
            'Id': 'sample_id',
            'Va': 'Volatiles_ar',
            'Vd': 'Volatiles_db',
            'Aa_LTA': 'Ash_LTA_ar',
            'Aa_HTA': 'Ash_HTA_ar',
            'Ad_LTA': 'Ash_LTA_db',
            'Ad_HTA': 'Ash_HTA_db',
            'FCa': 'Fixed_C_ar'
        }, inplace=True)

        # Neue Spalte mit dem Analysedatum einfügen
        df_tga_all["analysis_date"] = analysis_date_str
        # Spalten in gewünschter Reihenfolge ordnen
        df_tga_all = df_tga_all[
            ['sample_id', 'analysis_date', 'Moisture', 'Volatiles_ar', 'Ash_LTA_ar', 'Ash_HTA_ar',
             'Volatiles_db', 'Ash_LTA_db', 'Ash_HTA_db', 'Fixed_C_ar']
        ].copy()

        # Nach sample_id sortieren
        df_tga_all = df_tga_all.sort_values(by='sample_id', ascending=True)
        return df_tga_all

    except Exception as e:
        st.error(f"❌ Error while processing the TGA file: {e}")
        return None

def extract_description_from_file(file_path: str) -> str:
    """
    Extracts the descriptive text from an ELTRA TGA file.
    (Text between the beginning and the line 'Temperaturkalibration:')
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    match = re.search(r"^(.*?)(?=Temperaturkalibration:)", content, re.DOTALL | re.MULTILINE)
    if match:
        description = match.group(1).strip()
        return description
    else:
        return "❌ No descriptive text found."



def tga_calculate_mean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the mean values of numeric columns for each group in the 'Id' column.

    Args:
        df (pd.DataFrame): DataFrame containing ELTRA TGA data.

    Returns:
        pd.DataFrame: DataFrame with mean values per ID.
    """
    if df is None or df.empty:
        st.error("❌ Error: Empty or invalid DataFrame provided.")
        return pd.DataFrame()

    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    print(df)
    if "sample_id" in df.columns:
        df_mean = df.groupby("sample_id")[numeric_cols].mean().reset_index()
        st.write("✅ Mean values calculated successfully.")
        return df_mean
    else:
        st.error("❌ Error: 'sample_id' column not found.")
        return pd.DataFrame()

