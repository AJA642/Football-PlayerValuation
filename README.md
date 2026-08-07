# Football Player Market Value Prediction & Scouting Dashboard

**MSc Data Science — Individual Project**
**University of Birmingham Dubai**
**Student:** Ashish Abraham
**Supervisor:** Panos

## Project Overview
This project investigates whether football player market values are determined 
by on-pitch performance or influenced by external factors such as league 
affiliation and nationality. Using machine learning and explainable AI, 
position-specific models are trained to predict player market values from 
performance statistics, and SHAP is used to quantify the contribution of 
league and nationality to each prediction.

## Research Questions
1. Can position-specific ML models accurately predict football player market 
values from performance statistics alone?
2. How much of a player's market value is attributable to league affiliation 
and nationality versus actual performance?

## Data Sources
- FBref (via Kaggle) — player performance statistics, 2024-25 season
- Transfermarkt — market valuations and player profiles

## Methodology
- Position-specific models: Forwards, Midfielders, Defenders, Goalkeepers
- Algorithms: Ridge Regression, Random Forest, XGBoost, LightGBM
- Explainability: SHAP (SHapley Additive Explanations)
- Feature ablation experiment to quantify value of advanced metrics

## Project Structure
notebooks/
├── 01_data_collection.ipynb
├── 02_data_cleaning_june2025.ipynb      ← canonical pipeline (live)
├── 03_data_modelling_june2025.ipynb     ← canonical pipeline (live)
└── archive/
    ├── 02_data_cleaning.ipynb           ← superseded, December 2025 cutoff — do not run
    └── 03_data_modelling.ipynb          ← superseded, December 2025 cutoff — do not run

The `_june2025`-suffixed notebooks are the live, canonical pipeline: they use
a 30 June 2025 valuation cutoff, out-of-fold evaluation, scaled Ridge, and
corrected SHAP documentation, and they are what produced everything in
`data/processed/`. The notebooks under `archive/` are the original
December-cutoff versions, kept only because they produced
`data/processed_december2025_reference/`, preserved for comparison. Each
archived notebook carries a warning cell explaining this; do not run them.

## Status
- [x] Data collection
- [x] Data cleaning and merging
- [x] Modelling
- [x] Dashboard
- [x] Dissertation
