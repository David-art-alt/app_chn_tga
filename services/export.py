import pandas as pd
from xlsxwriter import Workbook
import io


def tga_export_to_excel(df_tga_mean, df_tga_all):
    """
    Speichert zwei DataFrames in einer Excel-Datei mit zwei Sheets und gibt einen Buffer für den Download zurück.

    Parameters:
    - df_chn: DataFrame mit den Mittelwerten der CHN-Daten
    - df_1: DataFrame mit allen Rohdaten der CHN-Analyse

    Returns:
    - io.BytesIO: Buffer mit Excel-Datei
    """

    rename_dict = {
        "Moisture": "Moisture (wt%)",
        "Va": "Volatiles ar (wt%)",
        "Aa_LTA": "Ash LTA ar (wt%)",
        "Ad_HTA": "Ash HTA ar (wt%)",
        "Vd": "Volatiles dry (wt%)",
        "FCa": "Fixed Carbon ar (wt%)"
    }

    df_mean_export = df_tga_mean.rename(columns=rename_dict)
    df_all_export = df_tga_all.rename(columns=rename_dict)

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_mean_export.to_excel(writer, sheet_name='Mean Values', index=False)
        df_all_export.to_excel(writer, sheet_name='All ELTRA TGA Data', index=False)

        # AutoFit Spaltenbreite (optional, für bessere Darstellung in Excel)
        for sheet_name, df in {'All ELTRA TGA Data': df_tga_all}.items():
            worksheet = writer.sheets[sheet_name]
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_length)

    buffer.seek(0)  # Zurück zum Anfang des Buffers für den Download
    return buffer

def chn_export_to_excel(df_chn_mean, df_chn_all):
    """
    Speichert zwei DataFrames in einer Excel-Datei mit zwei Sheets und gibt einen Buffer für den Download zurück.

    Parameters:
    - df_chn: DataFrame mit den Mittelwerten der CHN-Daten
    - df_1: DataFrame mit allen Rohdaten der CHN-Analyse

    Returns:
    - io.BytesIO: Buffer mit Excel-Datei
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_chn_mean.to_excel(writer, sheet_name='Mean Values', index=False)
        df_chn_all.to_excel(writer, sheet_name='All CHN Data', index=False)

        # AutoFit Spaltenbreite (optional, für bessere Darstellung in Excel)
        for sheet_name, df in {'All CHN Data': df_chn_all}.items():
            worksheet = writer.sheets[sheet_name]
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_length)

    buffer.seek(0)  # Zurück zum Anfang des Buffers für den Download
    return buffer