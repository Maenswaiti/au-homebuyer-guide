import os
import requests
import pandas as pd
import json

DATA_PATH = "data"
GEO_PATH = "geometry"
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(GEO_PATH, exist_ok=True)

SA2_REST_URL = "https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/MapServer/0/query"
G37_URL = "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/ArcGIS/rest/services/ABS_2021_Census_G37_SA2/FeatureServer/0/query"

def fetch_sa2_boundaries():
    local_geo = os.path.join(GEO_PATH, "sa2_2021_simplified.geojson")
    params = {
        "where": "1=1",
        "outFields": "SA2_CODE_2021,SA2_NAME_2021",
        "f": "geojson"
    }
    try:
        print("Fetching SA2 boundaries...")
        r = requests.get(SA2_REST_URL, params=params, timeout=60)
        r.raise_for_status()
        geojson = r.json()
        with open(local_geo, "w", encoding="utf-8") as f:
            json.dump(geojson, f)
        print("✅ Boundaries saved.")
    except Exception as e:
        if os.path.exists(local_geo):
            print("⚠️ Using existing geometry due to error:", e)
        else:
            raise RuntimeError(f"Failed to fetch boundaries: {e}")

def fetch_ownership_from_abs():
    local_own = os.path.join(DATA_PATH, "ownership.csv")
    rows = []
    offset = 0
    page_size = 2000
    while True:
        params = {
            "where": "1=1",
            "outFields": "SA2_CODE_2021,O_Tot,O_Mortgage,O_Owned",
            "returnGeometry": "false",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        }
        r = requests.get(G37_URL, params=params, timeout=60)
        r.raise_for_status()
        js = r.json()
        feats = js.get("features", [])
        if not feats:
            break
        for ft in feats:
            a = ft["attributes"]
            rows.append({
                "sa2_code21": str(a.get("SA2_CODE_2021")),
                "o_tot": a.get("O_Tot"),
                "o_mortgage": a.get("O_Mortgage"),
                "o_owned": a.get("O_Owned"),
            })
        offset += len(feats)
        if len(feats) < page_size:
            break

    df = pd.DataFrame(rows)
    df["ownership_pct"] = ((df["o_mortgage"].fillna(0) + df["o_owned"].fillna(0))
                           / df["o_tot"].replace({0: pd.NA})) * 100
    df = df[["sa2_code21", "ownership_pct"]]
    df.to_csv(local_own, index=False)
    print("✅ Ownership saved.")

def fetch_all_datasets():
    fetch_sa2_boundaries()
    fetch_ownership_from_abs()
    # You should provide your own CSVs for these or replace URLs accordingly:
    # e.g. fetch a SEIFA CSV, vacancy CSV, and median price CSV.
    # For now, skip or leave local sample if they exist.
    print("✅ fetch_all_datasets done.")
