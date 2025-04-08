import pandas as pd
import streamlit as st
import csv
from io import StringIO


def chn_process_uploaded_file(content: str) -> pd.DataFrame | None:
    """
    Liest eine CHN-Analyzedatei ein und verarbeitet sie minimal.
    """

    try:
        #print("📂 Datei wird eingelesen...")
        #print(repr(content))  # Zeigt das genaue Trennzeichen

        # Verwende StringIO, um den Textinhalt wie eine Datei zu behandeln
        df_chn_all = pd.read_csv(StringIO(content), sep='\t', encoding='utf-8', engine='python')
        #print(df_chn_all)

        # Entferne führende Leerzeichen in Spaltennamen
        df_chn_all.columns = df_chn_all.columns.str.strip()

        # Wähle nur die relevanten Spalten
        required_columns = ['sample_id', 'Analysis Date', 'Carbon %', 'Hydrogen %', 'Nitrogen %']
        df_chn_all = df_chn_all[required_columns]
        df_chn_all.rename(columns={
            'Analysis Date': 'analysis_date',
            'Carbon %': 'carbon_percentage',
            'Hydrogen %': 'hydrogen_percentage',
            'Nitrogen %': 'nitrogen_percentage'
        }, inplace=True)

        # Konvertiere numerische Spalten
        for col in ['carbon_percentage', 'hydrogen_percentage', 'nitrogen_percentage']:
            df_chn_all[col] = pd.to_numeric(df_chn_all[col], errors='coerce')

        # Sortiere nach 'sample_id'
        df_chn_all = df_chn_all.sort_values(by='sample_id', ascending=True)

        # Zeige die ersten Zeilen zur Überprüfung
        #print(df_chn_all.head())

        return df_chn_all

    except Exception as e:
        st.error(f"❌ Fehler beim Einlesen der Datei: {e}")
        return None

def chn_calculate_mean(df_chn_all: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet die Mittelwerte der numerischen Spalten für jede Gruppe in der 'Name'-Spalte.

    Parameters:
    df_chn_all (pd.DataFrame): Ein DataFrame mit den Spalten 'Name' und numerischen Werten.

    Returns:
    pd.DataFrame: Ein DataFrame mit den Mittelwerten für jede Gruppe in 'Name'.
    """
    # Gruppieren nach 'Name' und Mittelwerte berechnen
    df_chn_mean = df_chn_all.drop(columns=['analysis_date']).groupby('sample_id').mean().reset_index()
    #print(df_chn_mean)
    return df_chn_mean



def check_required_chn_headers(file_data: str) -> bool:
    """
    Validates whether the uploaded CHN analysis file contains all required headers.

    Args:
        file_data (str): The raw content of the file as a UTF-8 decoded string.

    Returns:
        bool: True if all required headers are found in any row, False otherwise.
    """
    required_headers = [
        "sample_id",
        "Comments",
        "Mass",
        "Nitrogen %",
        "Carbon %",
        "Hydrogen %",
        "Analysis Date"
    ]

    try:
        reader = csv.reader(file_data.splitlines(), delimiter="\t")

        for row in reader:
            if all(header in row for header in required_headers):
                return True  # All headers found
        return False  # No matching header row found

    except Exception:
        return False


