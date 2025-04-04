from typing import List, Union
import pandas as pd
import streamlit as st
import re

def check_file_content_results(file_paths: Union[str, List[str]]) -> List[str]:
    """
    Checks the contents of one or multiple text files to ensure they match a predefined format.

    Criteria:
    - Each file must contain expected identifiers in the first lines.

    Args:
        file_paths (Union[str, List[str]]): A single file path or a list of file paths.

    Returns:
        List[str]: A list of paths to valid files.
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    expected_identifiers = [
        "Tga Version:",
        "Analyse durchgeführt:",
        "Benutzer:",
        "Caption:",
        "Applikation:"
    ]

    valid_files = []

    print("\n🔍 Starting validation of result files...\n")

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            lines = [line.strip() for line in lines]

            missing_identifiers = [idf for idf in expected_identifiers if not any(line.startswith(idf) for line in lines[:10])]

            if missing_identifiers:
                print(f"❌ File '{file_path}' is invalid. Missing identifiers: {', '.join(missing_identifiers)}")
            else:
                print(f"✅ File '{file_path}' is valid.")
                valid_files.append(file_path)

        except FileNotFoundError:
            print(f"❌ Error: File '{file_path}' not found. Please check the file path.")
        except Exception as e:
            print(f"⚠️ An error occurred in file '{file_path}': {e}")

    print("\n🔍 Validation completed.")
    print(f"✅ Validated files: {len(valid_files)} / {len(file_paths)}\n")

    return valid_files


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


def result_files_to_df(file_paths: List[str]) -> List[pd.DataFrame]:
    """
    Reads a list of text files, extracts relevant measurement data, and converts data types
    based on column names: 'N' to int, 'Id' to str, and all other numeric columns to float.
    Ignores lines containing 'Gruppe', 'MW:', and 'STD:'.

    Args:
        file_paths (List[str]): List of paths to measurement files.

    Returns:
        List[pd.DataFrame]: A list of DataFrames with the extracted data.
    """
    dataframes = []
    status_messages = []

    for file_path in file_paths:
        data = []
        columns = None
        expected_num_columns = None

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if "N ," in line and "Id" in line:
                        columns = [col.strip() for col in line.split(',')]
                        expected_num_columns = len(columns)
                        continue

                    if any(keyword in line for keyword in ["Gruppe", "MW:", "STD:"]):
                        continue

                    values = line.split(',')
                    if len(values) == expected_num_columns:
                        data.append([val.strip() for val in values])

            if columns:
                df = pd.DataFrame(data, columns=columns)

                if "N" in df.columns:
                    df["N"] = df["N"].astype(int)
                if "Id" in df.columns:
                    df["Id"] = df["Id"].astype(str)
                for col in df.columns[2:]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                df_tga_all = df[['Id', 'Moisture', 'Va', 'Aa_LTA', 'Aa_HTA', 'Vd', 'Ad_LTA', 'Ad_HTA', 'FCa']]
                df_tga_all.rename(columns={'Id': 'sample_id', 'Moisture': 'Moisture','Va': 'Volatiles_ar', 'Vd':'Volatiles_db', 'Aa_LTA': 'Ash_LTA_ar',
                                           'Aa_HTA': 'Ash_HTA_ar', 'Ad_LTA': 'Ash_HTA_db', 'Ad_HTA': 'Ash_LTA_db', 'FCa': 'Fixed_C_ar'})
                dataframes.append(df_tga_all)
                status_messages.append(f"✅ File '{file_path}' successfully processed.")
            else:
                status_messages.append(f"❌ Error: No header found in file '{file_path}'.")

        except FileNotFoundError:
            status_messages.append(f"❌ Error: File '{file_path}' not found.")
        except Exception as e:
            status_messages.append(f"⚠️ An error occurred in file '{file_path}': {e}")

    st.write("\n".join(status_messages))

    return dataframes


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
