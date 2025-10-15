# AU Homebuyer Guide (Production)

A production-ready Streamlit app that evaluates suburbs (SA2) across Australia using full public datasets.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data pipeline
Use `scripts/fetch_full_data.py --all` to fetch and normalize datasets to `data/processed/`:
- `abs_g37_ownership_sa2.csv`
- `seifa_irsad_sa2.csv`
- `sa2_boundaries_2021.geojson`
- `medians_sales_sa2.csv`
- `medians_rent_sa2.csv`
- `vacancy_sa2.csv`

If some state medians or vacancy need credentials, place CSVs under `data/raw/` and re-run `--medians` or `--vacancy`.
