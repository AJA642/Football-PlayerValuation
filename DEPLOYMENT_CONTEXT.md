# Project Context: Football Player Valuation Dashboard — Deployment Brief

Written for a fresh chat that will help deploy this project online. Read this file first.

## What this is

A Streamlit dashboard (`app/Home.py` + 4 pages under `app/pages/`) that presents the
output of an MSc dissertation project: a machine-learning model that estimates
football player market values from 2024–25 performance data, with SHAP-based
explainability. The ML work (data collection, cleaning, modelling) lives in
`notebooks/01_data_collection.ipynb`, `02_data_cleaning.ipynb`, `03_data_modelling.ipynb`.
The dashboard only *reads* precomputed artifacts produced by those notebooks — it does
not train or retrain anything at runtime.

Pages:
- `app/pages/1_Model_Performance.py` — results tables, feature ablation, diagnostic/SHAP
  summary plots (static PNGs) per position (FWD/MID/DEF/GK).
- `app/pages/2_Value_Finder.py` — value-ratio search/filter tool.
- `app/pages/3_Player_Explorer.py` — per-player profile, comparables, and a **live**
  matplotlib SHAP waterfall plot (the only page that renders matplotlib live rather than
  from a saved image — relevant if deploy-time cold starts are slow).
- `app/pages/4_Bias_Explorer.py` — league/nationality bias analysis.

## Local environment (what currently works)

- macOS, Python **3.14.6** (only Python version installed on this machine), venv at
  `venv/` (not committed to git).
- No `requirements.txt` exists yet. Key package versions currently installed (from
  `pip freeze` in `venv/`): `streamlit==1.58.0`, `pandas==3.0.3`, `numpy==2.4.6`,
  `scikit-learn==1.9.0`, `shap==0.52.0`, `xgboost==3.3.0`, `lightgbm==4.6.0`,
  `matplotlib==3.11.0`, `plotly==6.8.0`. 152 packages total in the venv.
- Launched locally via `.claude/launch.json` → `venv/bin/streamlit run app/Home.py
  --server.headless true --server.port 8511`.
- `.streamlit/config.toml` is committed and sets a dark custom theme; sidebar nav is
  disabled (custom top navbar instead, in `lib/components.py`).

## Data — the critical deployment blocker

`data/` is **entirely gitignored** (`.gitignore` excludes `data/`, `venv/`,
`__pycache__/`, `.env`, `private_notes/`, `.claude/`). The GitHub repo
(`AJA642/Football-PlayerValuation`, remote `origin`) currently has **only 21 files
tracked** — no data, no venv. There's also a second remote, `gitlab` (University of
Birmingham GitLab), likely the submission repo.

The app reads data relative to project root via `app/lib/config.py`:
```python
APP_DIR = Path(__file__).resolve().parent.parent   # .../app
PROJECT_ROOT = APP_DIR.parent                        # repo root
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
```
Local `data/` breakdown: `raw/` is 342MB (likely not needed at runtime — check whether
`data_loader.py` reads from `raw/` or only `processed/`), `processed/` is only 10MB,
plus smaller `processed_june2025/` (8.6MB) and `processed_december2025_reference/`
(7.5MB) folders. Total `data/` is 368MB.

**Before deploying, a fresh session needs to:**
1. Confirm exactly which files under `data/` the app actually reads at runtime (grep
   `app/lib/data_loader.py` and `app/lib/config.py` for every path used) — it's likely
   only a small subset of the 368MB, possibly just `data/processed/` and the SHAP
   `.pkl` files.
2. Decide how that subset reaches the deployed app, since it isn't in git. Options:
   bundle it into the repo (fine if it's just the ~10–30MB actually needed), use Git
   LFS, or fetch it from external storage (S3/GDrive/HF datasets) at startup.

## Platform choice — Vercel is not a natural fit

Vercel is built for serverless functions and static/Next.js-style frontends, not
long-running stateful Python server processes like Streamlit. Streamlit needs a
persistent WebSocket connection, which Vercel's serverless model doesn't support well.
A new chat should weigh this explicitly before building toward Vercel specifically.
Better-matched options for a Streamlit app: **Streamlit Community Cloud** (free, built
for exactly this, deploys straight from the GitHub repo), **Render**, **Railway**, or
**Fly.io** (all support persistent Python web services). If the user wants a true
custom frontend/Vercel setup instead, that would mean rebuilding the UI in a JS
framework and serving the model via a separate API — a much bigger rewrite, not a
deployment task.

## Known performance characteristics worth carrying over

- Cold start is slow: heavy ML imports (pandas, sklearn, shap, xgboost, lightgbm) plus
  matplotlib's first-use font-cache build can take noticeably long on a fresh process —
  observed 280–500+ seconds for individual imports in one cold-start diagnostic on this
  machine. A deployed environment should be checked for the same issue; it may need a
  warm-up request or a platform with fast/persistent processes rather than
  spin-down-on-idle serverless behavior.
- `app/pages/1_Model_Performance.py` renders all 4 position tabs' content on every page
  load (Streamlit tabs aren't lazy) — roughly 2.9MB of PNGs decoded per load.
- `app/pages/3_Player_Explorer.py`'s live SHAP waterfall (matplotlib) is the slowest
  interactive element on the site.

## Suggested first steps for the deployment chat

1. Read `app/lib/data_loader.py` and `app/lib/config.py` in full to map every data file
   the app touches.
2. Generate a real `requirements.txt` (not committed yet) via
   `venv/bin/pip freeze > requirements.txt`, then trim it to actual imports rather than
   shipping all 152 resolved packages if that matters for deploy speed.
3. Confirm with the user which platform to target (recommend Streamlit Community Cloud
   as the default, given this is literally a Streamlit app) before writing deploy
   config.
4. Decide the data-bundling strategy (above) before pushing anything live.
