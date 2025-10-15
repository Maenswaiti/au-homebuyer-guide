import os
import requests
import pandas as pd
from io import StringIO

DATA_PATH = "data"
GEO_PATH = "geometry"
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(GEO_PATH, exist_ok=True)

SA2_GEOJSON_URL = "https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/gda94/sa2_2021_aust_simple.geojson"

def http_get(url, timeout=30):
    """Generic GET request with error handling."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        raise RuntimeError(f"GET failed {url} -> {e}")

def fetch_sa2_boundaries():
    local_path = os.path.join(GEO_PATH, "sa2_2021_simplified.geojson")
    try:
        r = http_get(SA2_GEOJSON_URL)
        with open(local_path, "wb") as f:
            f.write(r.content)
        print("✅ SA2 boundaries downloaded successfully.")
    except Exception as e:
        if os.path.exists(local_path):
            print(f"⚠️ Using cached SA2 boundaries due to: {e}")
        else:
            raise RuntimeError(f"Failed to fetch SA2 GeoJSON: {e}")

def fetch_all_datasets():
    """Fetch multiple open datasets and save them locally."""
    # --- Ownership (ABS Census)
    try:
        url = "https://raw.githubusercontent.com/pmbaumgartner/abs-data/main/ownership_sa2.csv"
        df = pd.read_csv(url)
        df.to_csv(os.path.join(DATA_PATH, "ownership.csv"), index=False)
    except Exception as e:
        print("⚠️ Failed ownership data:", e)

    # --- SEIFA (Socioeconomic Index)
    try:
        url = "https://raw.githubusercontent.com/pmbaumgartner/abs-data/main/seifa_sa2.csv"
        df = pd.read_csv(url)
        df.to_csv(os.path.join(DATA_PATH, "seifa.csv"), index=False)
    except Exception as e:
        print("⚠️ Failed SEIFA data:", e)

    # --- Vacancy rates (SQM Research public feed)
    try:
        url = "https://raw.githubusercontent.com/pmbaumgartner/abs-data/main/vacancy_sa2.csv"
        df = pd.read_csv(url)
        df.to_csv(os.path.join(DATA_PATH, "vacancy.csv"), index=False)
    except Exception as e:
        print("⚠️ Failed vacancy data:", e)

    # --- Median house prices (VIC Gov Open Data sample)
    try:
        url = "https://data.melbourne.vic.gov.au/resource/vh2v-4nfs.csv?$limit=50000"
        df = pd.read_csv(url)
        df.to_csv(os.path.join(DATA_PATH, "vic_medians.csv"), index=False)
    except Exception as e:
        print("⚠️ Failed VIC medians:", e)

    print("✅ All available datasets fetched.")
