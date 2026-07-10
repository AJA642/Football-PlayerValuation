**MSc Data Science — Project**
**University of Birmingham Dubai**
**Student:** Ashish Abraham

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
