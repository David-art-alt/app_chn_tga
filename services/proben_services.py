import sqlite3
import datetime


def generate_proben_id(prefix: str) -> str:
    conn = sqlite3.connect("probenverwaltung.db")
    cursor = conn.cursor()

    year = datetime.datetime.now().strftime("%y")
    cursor.execute(
        f"SELECT Proben_ID FROM haupttabelle WHERE Proben_ID LIKE '{prefix}_{year}_%' ORDER BY Proben_ID DESC LIMIT 1")
    result = cursor.fetchone()

    if result:
        last_id = int(result[0].split('_')[-1])
        new_id = last_id + 1
    else:
        new_id = 1

    conn.close()
    return f"{prefix}_{year}_{new_id:04d}"
