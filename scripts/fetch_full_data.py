#!/usr/bin/env python3

"""
Fetch and normalize full datasets.

Outputs (in ../data/processed):
  - abs_g37_ownership_sa2.csv
  - seifa_irsad_sa2.csv
  - sa2_boundaries_2021.geojson
  - medians_sales_sa2.csv
  - medians_rent_sa2.csv
  - vacancy_sa2.csv
"""

import pathlib, time
import pandas as pd
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

def http_get(url, params=None, headers=None, max_retries=5, backoff=1.5):
    last = None
    for i in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=60)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last = repr(e)
        time.sleep(backoff ** i + 0.1)
    raise RuntimeError(f"GET failed {url} params={params} last={last}")

SA2_GEOJSON_URL = "https://static-data-assets.s3.ap-southeast-2.amazonaws.com/asgs_2021_sa2_simple.geojson"
def fetch_sa2_boundaries():
    r = http_get(SA2_GEOJSON_URL)
    (RAW/"sa2_boundaries_2021.geojson").write_bytes(r.content)
    (PROCESSED/"sa2_boundaries_2021.geojson").write_bytes(r.content)

G37_URL = "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/ArcGIS/rest/services/ABS_2021_Census_G37_SA2/FeatureServer/0/query"
def fetch_abs_g37_owner():
    fields = ["SA2_CODE_2021","O_Tot","O_Mortgage","O_Owned"]
    params = dict(where="1=1", outFields=",".join(fields), returnGeometry="false", f="json", resultOffset=0, resultRecordCount=2000, outSR=4326)
    out_rows = []
    while True:
        js = http_get(G37_URL, params=params).json()
        feats = js.get("features", [])
        if not feats: break
        for ft in feats:
            at = ft["attributes"]
            out_rows.append({k.lower(): at.get(k) for k in fields})
        params["resultOffset"] += len(feats)
        if len(feats) < params["resultRecordCount"]:
            break
    df = pd.DataFrame(out_rows).rename(columns={"sa2_code_2021":"sa2_code21"})
    df["ownership_pct"] = ((df["o_owned"].fillna(0)+df["o_mortgage"].fillna(0)) / df["o_tot"].replace({0: pd.NA})) * 100
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    df[["sa2_code21","ownership_pct"]].to_csv(PROCESSED/"abs_g37_ownership_sa2.csv", index=False)

SEIFA_URL = "https://services-ap1.arcgis.com/ypkPEy1AmwPKGNNv/ArcGIS/rest/services/SEIFA_2021_IRSAD_SA2/FeatureServer/0/query"
def fetch_seifa_irsad():
    fields = ["SA2_CODE_2021","IRSAD_Score","IRSAD_Rank_National"]
    params = dict(where="1=1", outFields=",".join(fields), returnGeometry="false", f="json", resultOffset=0, resultRecordCount=2000, outSR=4326)
    rows = []
    while True:
        js = http_get(SEIFA_URL, params=params).json()
        feats = js.get("features", [])
        if not feats: break
        for ft in feats:
            at = ft["attributes"]
            rows.append({
                "sa2_code21": str(at.get("SA2_CODE_2021")),
                "irsad_score": at.get("IRSAD_Score"),
                "irsad_rank": at.get("IRSAD_Rank_National"),
            })
        params["resultOffset"] += len(feats)
        if len(feats) < params["resultRecordCount"]:
            break
    pd.DataFrame(rows).to_csv(PROCESSED/"seifa_irsad_sa2.csv", index=False)

def build_state_medians():
    # Expect CSVs in data/raw with columns: sa2_code21, median_price and/or median_rent
    import pandas as pd, os
    sales_frames, rent_frames = [], []
    for fn in os.listdir(RAW):
        if not fn.lower().endswith(".csv"): continue
        df = pd.read_csv(RAW/fn)
        cols = {c.lower().strip(): c for c in df.columns}
        if "sa2_code21" not in cols: continue
        if "median_price" in cols:
            sales_frames.append(pd.DataFrame({
                "sa2_code21": df[cols["sa2_code21"]].astype(str),
                "median_price": pd.to_numeric(df[cols["median_price"]], errors="coerce")
            }))
        if "median_rent" in cols:
            rent_frames.append(pd.DataFrame({
                "sa2_code21": df[cols["sa2_code21"]].astype(str),
                "median_rent": pd.to_numeric(df[cols["median_rent"]], errors="coerce")
            }))
    if sales_frames:
        pd.concat(sales_frames, ignore_index=True).to_csv(PROCESSED/"medians_sales_sa2.csv", index=False)
    if rent_frames:
        pd.concat(rent_frames, ignore_index=True).to_csv(PROCESSED/"medians_rent_sa2.csv", index=False)

def build_vacancy():
    import pandas as pd
    p = RAW/"vacancy.csv"
    if not p.exists(): return
    df = pd.read_csv(p, dtype={"sa2_code21":"string"})
    df["sa2_code21"] = df["sa2_code21"].astype(str)
    if "vacancy_pct" not in df.columns and "vacancy" in df.columns:
        df["vacancy_pct"] = pd.to_numeric(df["vacancy"], errors="coerce")*100
    df[["sa2_code21","vacancy_pct"]].dropna().to_csv(PROCESSED/"vacancy_sa2.csv", index=False)

if __name__ == "__main__":
    fetch_sa2_boundaries()
    fetch_abs_g37_owner()
    fetch_seifa_irsad()
    build_state_medians()
    build_vacancy()
