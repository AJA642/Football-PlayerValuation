# Results Reference

Single source for every final number, table, and key finding, as currently generated in `data/processed/`. Pull numbers for the Results chapter from here, not from memory or from earlier drafts — several of these values changed across the June-cutoff migration and the Ridge-scaling/OOF fixes, and will change again if the pipeline is ever re-run (hyperparameter search is stochastic).

---

## 1. Dataset summary

| | Value |
|---|---|
| Total players | 2,061 |
| Position breakdown | DEF 778 · MID 637 · FWD 487 · GK 159 |
| League breakdown | Serie A 459 · Premier League 423 · La Liga 421 · Bundesliga 384 · Ligue 1 374 |
| Valuation cutoff | 30 June 2025 |
| Valuation date range | 2024-05-27 to 2025-06-26 |
| % of valuations within 2024-25 season window (Aug 2024–Jun 2025) | 96.99% |
| Actual value: min / 25% / median / 75% / max | €50,000 / €2,500,000 / €7,000,000 / €18,000,000 / €200,000,000 |
| Actual value: mean / std | €13,912,200 / €19,377,800 |
| Feature count | 154 (FWD, MID, DEF) · 186 (GK) |

## 2. Algorithm comparison — full results (`results_summary.csv`)

| Position | Algorithm | RMSE (log) | MAE (log) | R² | MAPE (%) |
|---|---|---|---|---|---|
| FWD | Ridge | 0.6781 | 0.4879 | 0.7416 | 91.02 |
| FWD | RandomForest | 0.7179 | 0.5291 | 0.7104 | 95.96 |
| FWD | **XGBoost** | **0.6550** | **0.4841** | **0.7589** | **78.19** |
| FWD | LightGBM | 0.6659 | 0.4826 | 0.7508 | 82.89 |
| MID | Ridge | 0.6284 | 0.4657 | 0.7371 | 66.44 |
| MID | RandomForest | 0.6758 | 0.5218 | 0.6960 | 70.01 |
| MID | XGBoost | 0.6246 | 0.4662 | 0.7403 | 62.05 |
| MID | **LightGBM** | **0.6141** | **0.4584** | **0.7490** | **60.89** |
| DEF | Ridge | 0.5882 | 0.4573 | 0.7665 | 53.77 |
| DEF | RandomForest | 0.6255 | 0.4898 | 0.7359 | 57.95 |
| DEF | **XGBoost** | **0.5653** | **0.4404** | **0.7843** | **51.35** |
| DEF | LightGBM | 0.5713 | 0.4422 | 0.7797 | 52.36 |
| GK | Ridge | 0.7535 | 0.6124 | 0.6615 | 74.67 |
| GK | RandomForest | 0.8011 | 0.6739 | 0.6174 | 82.15 |
| GK | XGBoost | 0.7403 | 0.6151 | 0.6733 | 75.69 |
| GK | **LightGBM** | **0.7240** | **0.6028** | **0.6875** | **74.07** |

**Winning algorithm per position (bold above): FWD → XGBoost, MID → LightGBM, DEF → XGBoost, GK → LightGBM.**

## 3. Winning hyperparameters

| Position | Algorithm | Hyperparameters |
|---|---|---|
| FWD | XGBoost | `subsample=1.0, n_estimators=200, max_depth=3, learning_rate=0.05, colsample_bytree=0.8` |
| MID | LightGBM | `subsample=0.8, num_leaves=15, n_estimators=500, learning_rate=0.03, colsample_bytree=0.6` |
| DEF | XGBoost | `subsample=0.8, n_estimators=300, max_depth=3, learning_rate=0.03, colsample_bytree=0.8` |
| GK | LightGBM | `subsample=0.8, num_leaves=63, n_estimators=500, learning_rate=0.01, colsample_bytree=0.6` |

Ridge's best `alpha` (post-scaling, all positions): 100.0. These values are current as of the last completed notebook run; `RandomizedSearchCV` is stochastic and a fresh run may select different values.

## 4. Feature ablation results (`ablation_results.csv`, pooled, reduced feature set)

| Algorithm | RMSE (log) | MAE (log) | R² | MAPE (%) |
|---|---|---|---|---|
| Ridge | 0.8756 | 0.6831 | 0.5249 | 105.01 |
| RandomForest | 0.8661 | 0.6781 | 0.5352 | 94.79 |
| **XGBoost** | **0.8509** | **0.6660** | **0.5514** | **96.02** |
| LightGBM | 0.8524 | 0.6653 | 0.5498 | 93.58 |

All four ablation R² values (0.52–0.55) sit well below any position-specific model's R² (0.66–0.78) — but this gap conflates two simultaneous changes (reduced feature set **and** pooled-across-positions population), not feature reduction alone (see `IMPLEMENTATION_REFERENCE.md` §6).

## 5. League bias summary (`bias_summary_league.csv`), ranked by `mean_shap_log` within position

| Position | League | n | mean_shap_log | mean_counterfactual_eur |
|---|---|---|---|---|
| DEF | Premier League | 160 | +0.6476 | +€9,287,741 |
| DEF | La Liga | 143 | −0.1460 | −€1,120,340 |
| DEF | Serie A | 179 | −0.1480 | −€1,109,047 |
| DEF | Bundesliga | 150 | −0.1514 | −€1,211,692 |
| DEF | Ligue 1 | 146 | −0.2306 | −€1,831,023 |
| FWD | Premier League | 106 | +0.5259 | +€9,877,254 |
| FWD | Serie A | 104 | −0.0984 | −€973,510 |
| FWD | Bundesliga | 83 | −0.0999 | −€939,524 |
| FWD | La Liga | 107 | −0.1093 | −€934,293 |
| FWD | Ligue 1 | 87 | −0.2516 | −€3,056,884 |
| GK | Premier League | 32 | +0.3375 | +€3,000,852 |
| GK | Serie A | 36 | −0.0787 | −€444,871 |
| GK | La Liga | 32 | −0.0811 | −€477,873 |
| GK | Ligue 1 | 28 | −0.0814 | −€527,616 |
| GK | Bundesliga | 31 | −0.0916 | −€416,866 |
| MID | Premier League | 125 | +0.6952 | +€12,473,600 |
| MID | Bundesliga | 120 | −0.1207 | −€1,140,490 |
| MID | Serie A | 140 | −0.1349 | −€1,213,749 |
| MID | Ligue 1 | 113 | −0.1910 | −€1,844,224 |
| MID | La Liga | 139 | −0.2196 | −€2,073,635 |

**Key finding: Premier League shows the model's largest positive league SHAP contribution in all four positions** — the strongest, most robust result in the bias analysis (also confirmed unchanged in rank across the December→June migration).

## 6. Confederation bias summary (`bias_summary_confederation.csv`), ranked by `mean_shap_log` within position

| Position | Confederation | n | mean_shap_log | mean_counterfactual_eur |
|---|---|---|---|---|
| DEF | UEFA | 596 | +0.000142 | +€848 |
| DEF | AFC | 12 | −0.000150 | −€1,681 |
| DEF | CONCACAF | 16 | −0.000161 | −€2,147 |
| DEF | CAF | 85 | −0.000341 | −€1,480 |
| DEF | CONMEBOL | 69 | −0.000389 | −€2,363 |
| FWD | AFC/CAF/CONCACAF/CONMEBOL/OFC/UEFA | 11/82/12/46/2/334 | 0.000000 (all) | €0 (all) |
| GK | AFC/CAF/CONMEBOL/UEFA | 3/7/10/139 | 0.000000 (all) | €0 (all) |
| MID | UEFA | 475 | +0.011410 | +€178,135 |
| MID | CONMEBOL | 51 | +0.005917 | +€181,527 |
| MID | CONCACAF | 13 | +0.002049 | +€35,625 |
| MID | AFC | 12 | +0.000310 | +€13,024 |
| MID | OFC | 1 | −0.001298 | −€3,974 |
| MID | CAF | 85 | −0.067457 | −€646,272 |

Confederation effects are an order of magnitude (DEF, MID) to several orders of magnitude (FWD, GK) smaller than league effects — consistent with the model's own dashboard commentary describing confederation contributions as much smaller in magnitude than league ones. FWD and GK show exactly zero for every confederation in the current pipeline.

## 7. Comparable players

- `comparable_players.csv`: 2,061 rows × 6 columns (`player_id`, `neighbor_1_id`…`neighbor_5_id`).
- Feature set: each position's own model features minus `league_*`, `confed_*`, `career_stage_*`, `foot_*`, `contract_months_remaining`, `missing_contract`, `height_in_cm`, `player_id_tm` — pure performance/age/playing-time signal, z-scored, Euclidean nearest-neighbours.
- Deterministic with respect to the valuation cutoff: byte-identical to the December-pipeline output despite fresh regeneration.

## 8. Undervalued Players

| Position | Flagged | Population | % |
|---|---|---|---|
| DEF | 78 | 778 | 10.0% |
| FWD | 49 | 487 | 10.1% |
| GK | 16 | 159 | 10.1% |
| MID | 64 | 637 | 10.0% |
| **Total** | **207** | **2,061** | **10.0%** |

Flag threshold: top 10% of `oof_value_ratio` (out-of-fold predicted ÷ actual), computed independently per position. Not the same ratio as the displayed "Value Ratio" column (see `IMPLEMENTATION_REFERENCE.md` §9).

## 9. Diagnostics summary (`diagnostics_summary.csv`)

Mirrors the winning algorithm's row from §2 for each position (out-of-fold RMSE/MAE/R²/MAPE) — no separate computation, same numbers as the bolded rows in the table above.
