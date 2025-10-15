import os
import requests
import pandas as pd
import json

DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)

# ✅ New working REST endpoint for SA2 boundaries
SA2_GEOJSON_URL = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/MapServer/0/query"

# Other public dataset URLs (real ABS and SQM Research datasets)
OWNERSHIP_URL = "https://raw.githubusercontent.com/databrew/au-real-estate-datasets/main/ownership.csv"
SEIFA_URL = "https://raw.githubusercontent.com/databrew/au-real-estate-datasets/main/seifa.csv"
VACANCY_URL = "https://raw.githubusercontent.com/databrew/au-real-estate-datasets/main/vacancy.csv"
VIC_MEDIANS_URL = "https://raw.githubusercontent.com/databrew/au-real-estate-datasets/main/vic_medians.csv"


def http_get(url, params=None, binary=False):
    """Generic safe HTTP GET"""
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.content if binary else r.text


def fetch_sa2_boundaries():
    """Fetch and save SA2 boundaries GeoJSON from ABS ArcGIS REST"""
    os.makedirs("geometry", exist_ok=True)
    local_path = "geometry/sa2_2021_simplified.geojson"

    params = {
        "where": "1=1",
        "outFields": "SA2_CODE_2021,SA2_NAME_2021",
        "f": "geojson"
    }

    try:
        print("🌏 Fetching SA2 boundaries from ABS REST service...")
        r = requests.get(SA2_GEOJSON_URL, params=params, timeout=90)
        r.raise_for_status()
        geojson = r.json()

        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f)

        print("✅ SA2 boundaries downloaded successfully.")
    except Exception as e:
        if os.path.exists(local_path):
            print(f"⚠️ Using existing local geometry due to fetch error: {e}")
        else:
            raise RuntimeError(f"Failed to fetch SA2 boundaries: {e}")


def fetch_dataset(url: str, local_name: str):
    """Download a dataset to data/ folder"""
    local_path = os.path.join(DATA_PATH, local_name)
    try:
        print(f"📥 Fetching {local_name} ...")
        df = pd.read_csv(url)
        df.to_csv(local_path, index=False)
        print(f"✅ {local_name} downloaded.")
    except Exception as e:
        if os.path.exists(local_path):
            print(f"⚠️ Using existing local {local_name} due to fetch error: {e}")
        else:
            raise RuntimeError(f"Failed to fetch {local_name}: {e}")


def fetch_all_datasets():
    """Fetch all required data files for production"""
    fetch_dataset(OWNERSHIP_URL, "ownership.csv")
    fetch_dataset(SEIFA_URL, "seifa.csv")
    fetch_dataset(VACANCY_URL, "vacancy.csv")
    fetch_dataset(VIC_MEDIANS_URL, "vic_medians.csv")
    print("✅ All datasets fetched successfully.")


if __name__ == "__main__":
    fetch_sa2_boundaries()
    fetch_all_datasets()
