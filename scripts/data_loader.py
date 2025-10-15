import os
import geopandas as gpd
import pandas as pd

DATA_PATH = "data"
GEO_PATH = "geometry/sa2_2021_simplified.geojson"

def load_sa2_geojson():
    return gpd.read_file(GEO_PATH)

def load_ownership_sample():
    f = os.path.join(DATA_PATH, "ownership.csv")
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["sa2_code21", "ownership_pct"])

def load_seifa_sample():
    f = os.path.join(DATA_PATH, "seifa.csv")
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["sa2_code21", "irsad_rank"])

def load_vacancy_sample():
    f = os.path.join(DATA_PATH, "vacancy.csv")
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["sa2_code21", "vacancy_rate"])

def load_vic_medians_sample():
    f = os.path.join(DATA_PATH, "vic_medians.csv")
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=["postcode", "median_price"])

def load_all_data():
    geo = load_sa2_geojson()
    own = load_ownership_sample()
    seifa = load_seifa_sample()
    vac = load_vacancy_sample()
    med = load_vic_medians_sample()
    return geo, own, seifa, vac, med
