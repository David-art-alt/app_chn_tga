from services.database import fetch_all_samples
import datetime
import logging

def generate_sample_id(prefix: str) -> str:
    try:
        year = datetime.datetime.now().strftime("%y")
        samples_df = fetch_all_samples()

        if samples_df.empty or "sample_id" not in samples_df.columns:
            next_counter = 1
        else:
            # Filter auf IDs mit dem gleichen Jahr
            mask = samples_df['sample_id'].str.contains(f"_{year}_", na=False)
            relevant_ids = samples_df.loc[mask, 'sample_id']

            if relevant_ids.empty:
                next_counter = 1
            else:
                counters = relevant_ids.str.extract(r"_(\d{2})_(\d+)")[1]
                counters = counters.dropna().astype(int)
                next_counter = counters.max() + 1 if not counters.empty else 1

        sample_id = f"{prefix}_{year}_{next_counter:05d}"
        return sample_id

    except Exception as e:
        logging.error(f"❌ Error generating sample ID: {e}")
        raise RuntimeError(f"Fehler bei der ID-Generierung: {e}")