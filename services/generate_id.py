import datetime
import logging
from services.database import fetch_all_samples  # Holt alle Samples aus Supabase

def generate_sample_id(prefix: str) -> str:
    """
    Generiert eine eindeutige Sample-ID im Format PREFIX_JAHR_XXXX basierend auf existierenden IDs in Supabase.
    """
    try:
        # Aktuelles Jahr zweistellig, z. B. "24" für 2024
        year = datetime.datetime.now().strftime("%y")

        # Alle bisherigen Sample-IDs laden
        samples_df = fetch_all_samples()

        # Filter auf IDs mit dem gleichen Jahr
        mask = samples_df['sample_id'].str.contains(f"_{year}_", na=False)
        relevant_ids = samples_df.loc[mask, 'sample_id']

        # Extrahiere die laufenden Nummern (XXXX) aus den IDs
        counters = []
        for sid in relevant_ids:
            try:
                counters.append(int(sid.split('_')[-1]))
            except (ValueError, IndexError):
                continue

        # Nächste freie Nummer bestimmen
        next_counter = max(counters) + 1 if counters else 1

        # Neue Sample-ID generieren
        sample_id = f"{prefix}_{year}_{next_counter:04d}"
        return sample_id

    except Exception as e:
        logging.error(f"❌ Error generating sample ID: {e}")
        raise RuntimeError(f"Fehler bei der ID-Generierung: {e}")