# Implementation Reference

How the system currently works, end to end. Describes only what exists in the repository as of the live pipeline (`notebooks/01_data_collection.ipynb`, `notebooks/02_data_cleaning_june2025.ipynb`, `notebooks/03_data_modelling_june2025.ipynb`, `app/`). The archived December-cutoff notebooks (`notebooks/archive/`) and `data/processed_december2025_reference/` are historical reference material, not part of the live pipeline, and are not described here except where directly relevant.

---

## 1. Dataset characteristics

- **Population**: 2,061 players, Big 5 European leagues, 2024-25 season.
- **Position split**: DEF 778, MID 637, FWD 487, GK 159.
- **League split**: Serie A 459, Premier League 423, La Liga 421, Bundesliga 384, Ligue 1 374.
- **Target**: `log_market_value` = `log1p(market_value_in_eur)`, where `market_value_in_eur` is each player's most recent Transfermarkt valuation on or before **30 June 2025** (see §5).
- **Actual value range**: €50,000–€200,000,000 (mean €13.9M, median €7.0M, heavily right-skewed — this is why the target is log-transformed).
- **Sources**: FBref via Kaggle (`data/raw/fbref_kaggle/players_data-2024_2025.csv`, performance statistics) and Transfermarkt (`data/raw/transfermarkt/`, valuations and player profiles). A separate 6-season FBref scrape exists for descriptive/EDA use only and never feeds the models.

## 2. Data collection — `notebooks/01_data_collection.ipynb`

- Step 1–3: scrapes FBref across 6 seasons and all stat types for EDA use; determines which scraped stat categories are actually usable (most FBref pages load via JavaScript and can't be scraped this way, so the scrape is descriptive-only).
- Step 4: inventories the Kaggle FBref datasets (`players_data-2024_2025.csv` primary, `players_data-2025_2026.csv` for the ablation's reduced feature set).
- Step 5–6: loads Transfermarkt valuations/injuries, checks for unresolved Git LFS pointer files.
- Step 7: final inventory printout confirming all raw sources are present before notebook 2 runs.
- Not cutoff-dependent — this notebook's outputs are identical regardless of the December/June cutoff choice, and it is not re-run as part of the June pipeline; its outputs in `data/raw/` and `data/external/` predate and are shared by both.

## 3. Preprocessing & feature engineering — `notebooks/02_data_cleaning_june2025.ipynb`

29 steps, in order:

1. **Load** the Kaggle 2024-25 and 2025-26 FBref files.
2. **Resolve suffix-duplicate columns** (2024-25 file merges 10 FBref stat tables per player, producing `_stats_shooting`/`_stats_defense`/etc. suffix collisions) — classified as true duplicate / partial match / ambiguous.
3–5. Resolve ambiguous columns against FBref's own source-table schema, empirically sanity-check the resolution, apply it.
6. Standardise remaining suffix naming.
7. **Minimum minutes filter**: drop players with fewer than 3×90s (270 minutes) — too little playing time for meaningful per-90 stats.
8. Position cleaning (map raw FBref positions to the four modelling groups).
9–15. **Build the FBref ↔ Transfermarkt player mapping**: accent-mismatch checks, first-pass matching, birth-year disambiguation, then fuzzy name matching (via `fuzzy_match_name`) for unmatched players, sanity-checked against birth year before being applied. No pre-built mapping file exists for this season; the mapping is built from scratch every run.
16. **Join Transfermarkt market valuations** (see §5 — this is the cutoff-dependent step).
17. Filter to rows with a valid target variable (a valuation within the window).
18. Player profile features from Transfermarkt (age, contract, nationality, height, foot).
19. **Feature engineering**: `age_precise` and `contract_months_remaining` computed relative to a **fixed** `REFERENCE_DATE = 2025-01-01` (independent of both the season window and each player's own valuation date — deliberately not tied to the valuation cutoff), `missing_contract` flag, `career_stage` bucketing.
20. **League encoding**: one-hot (`league_*`), not ordinal.
21–25. **Nationality → confederation mapping**: explored, mapped, patched for missing values, 2 remaining players resolved manually, then one-hot encoded (`confed_*`).
26. **Split by position** into `df_fwd`, `df_mid`, `df_def`, `df_gk`.
27. Drop position-irrelevant columns.
28. **Build the ablation dataframe** (`df_ablation`) — all positions pooled, restricted to the ~20-column reduced feature set also present in the 2025-26 Kaggle file (used to measure how much the advanced FBref metrics add over basic stats).
29. **Save**: `merged_dataset_2425.csv`, `df_{fwd,mid,def,gk}.csv`, `df_ablation.csv` to `PROCESSED_DIR` (see §14 for the actual promoted location).

`league_*`, `confed_*`, `contract_months_remaining`, `career_stage_*`, `foot_*`, and `height_in_cm` are all retained as **direct model input features** in the final `X` used for training — not held out for a separate post-hoc analysis. This is why SHAP can attribute a league/confederation contribution at all (§10): those columns are literal one-hot inputs the model was trained on.

## 4. Feature matrix construction — `prepare_features()` (notebook 3, Step 2)

Shared by every position. Given a position's dataframe:
- Extracts `y = log_market_value` and a `lookup` table (`Player`, `Squad`, `Comp`, `Nation`).
- Fills `contract_months_remaining` NaNs with the position's own median, flags them via `missing_contract`.
- One-hot encodes `career_stage` and `foot`.
- Drops identifier/target/leakage-adjacent columns: `Player, Squad, Nation, Pos, Comp, tm_player_id, player_id, market_value_in_eur, date, nation_code, confederation, date_of_birth, contract_expiration_date, Born, position_group, log_market_value, match_method, country_of_citizenship, Age`.
- Fills remaining NaNs (rate/ratio columns first, with 0 = zero-denominator; then any stragglers).
- Sanitises column names, deduplicating any that collide after sanitisation (GK's raw columns produce a genuine post-sanitisation collision, handled explicitly).

**Resulting feature count: 154 columns for FWD/MID/DEF, 186 for GK** (goalkeepers carry additional keeper-specific stat columns that outfield positions don't have).

## 5. The June 2025 cutoff — exact implementation

Notebook 2, Step 16:
```python
val_window = df_valuations[(df_valuations['date'] >= '2024-01-01') & (df_valuations['date'] <= '2025-06-30')].copy()
val_latest = val_window.sort_values('date').groupby('player_id').tail(1)
```
Each player's target is their **latest Transfermarkt valuation on or before 30 June 2025** (lower bound `2024-01-01` unchanged from the original design). This replaced an earlier version of the same line with an upper bound of `2025-12-31` (the December cutoff, preserved in `notebooks/archive/02_data_cleaning.ipynb` and `data/processed_december2025_reference/`).

Effect on the dataset: the player population and every non-target feature are **identical** between the December and June cutoffs (verified: 2,061 players, same position/league breakdown, byte-identical `X` on every column except `date`/`market_value_in_eur`/`log_market_value`) — only the target value itself changes. 96.99% of June-cutoff valuation dates fall within the nominal 2024-25 season window (Aug 2024–Jun 2025); 3.0% predate it.

## 6. Model training — `train_position()` (notebook 3, Section 3)

One call per position (`FWD`, `MID`, `DEF`, `GK`):

- **Algorithms compared**: Ridge Regression (wrapped in `Pipeline([('scaler', StandardScaler()), ('ridge', Ridge(random_state=42))])`), Random Forest, XGBoost, LightGBM. Ridge is the only one requiring explicit scaling; the three tree ensembles are scale-invariant.
- **Stratification**: target `y` is bucketed into 5 quantile bins via `pd.qcut(y, q=5, labels=False, duplicates='drop')` (`make_strat_bins`), used only to stratify the CV split — not as a model input.
- **CV**: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`, folds materialized once per position (`cv_folds = list(skf.split(X, bins))`) and reused for both tuning and evaluation.
- **Hyperparameter tuning**: `RandomizedSearchCV(n_iter=25, cv=cv_folds, scoring='neg_root_mean_squared_error', random_state=42)` per algorithm.
- **Non-nested CV**: the same 5 folds serve both the `RandomizedSearchCV` search and the final `cross_val_predict`-based evaluation — the reported R²/RMSE for the winning hyperparameter combination is not from a held-out set independent of the search that chose it. Documented as a limitation in `LIMITATION_REFERENCE.md`; its bias magnitude has not been empirically bounded (would require a full nested-CV re-run, not performed).
- **Selection**: within each position, the algorithm with the lowest `RMSE_log` from `cross_val_predict` is selected (mathematically equivalent to maximum R² for a fixed target — verified to select the identical algorithm either way, in every position).
- **Final fit**: the winning model is then refit via `best_model.fit(X, y)` on **100% of the position's data** and saved to `data/processed/models/best_model_{pos}.pkl`. This full-data-fit model is what SHAP explains (§10) and what every dashboard "Model Estimated Value" displays (§9) — it is not the same object as any individual fold's model from the CV step above.

Ablation (Section 4) repeats the identical procedure on the pooled, reduced-feature `df_ablation` (`position = 'ALL_ABLATION'` in `ablation_results.csv`), saved as `best_model_ablation.pkl`. Because both the feature set and the population change simultaneously, the ablation's R² gap versus the position-specific models reflects the combined effect of both — not feature reduction in isolation (documented in the ablation section's own markdown and repeated in `app/pages/1_Model_Performance.py`'s caption).

## 7. Final models and hyperparameters

See `RESULTS_REFERENCE.md` for the complete current numbers. Summary: FWD → XGBoost, MID → LightGBM, DEF → XGBoost, GK → LightGBM. Hyperparameters are re-searched (not fixed) on every full notebook run and will change if the notebook is re-executed, even with identical data, due to `RandomizedSearchCV`'s stochastic search — the values in `results_summary.csv` are current only as of the last completed run and are not hardcoded anywhere.

## 8. Evaluation metrics — `eval_metrics()`

Computed in both log-space and EUR-space from `(y_true_log, y_pred_log)`:
- `RMSE_log`, `MAE_log`, `R2` — computed directly in log-space (the space the model was actually optimised in).
- `MAPE_eur_pct` — mean absolute percentage error after back-transforming both `y_true` and `y_pred` via `expm1`.

All of `results_summary.csv`, `ablation_results.csv`, and `diagnostics_summary.csv` (and the diagnostic plots — predicted-vs-actual, residuals-vs-predicted, residual distribution) are built from **out-of-fold** predictions (`cross_val_predict`), never from the full-data-fit model's own in-sample output. This is the "evaluation" side of the OOF/final-model split described in §9.

## 9. OOF vs. final-model prediction methodology — Section 6 & 7 (notebook 3)

Two structurally different prediction sources exist, used for two different purposes, both persisted:

| Source | Computed | Stored as | Used for |
|---|---|---|---|
| **Out-of-fold** (`cv_predictions[position]`, Section 6) | `cross_val_predict(model, X, y, cv=cv_folds)` — each player's prediction comes from a fold that held them out | `oof_predicted_value_eur`, `oof_value_ratio` in `df_predictions.csv`; also the sole basis for `results_summary.csv`/`diagnostics_summary.csv`/the diagnostic plots | `undervalued_flag` threshold **only** — top 10% of `oof_value_ratio` within each position |
| **Final model** (`model.predict(X)`, Section 7) | The same fully-fitted `best_model` object used for SHAP (§10), predicting on the data it was fit on | `predicted_value_eur`, `value_gap_eur`, `value_ratio` in `df_predictions.csv` | Every displayed "Model Estimated Value" / Difference / Value Ratio, throughout the dashboard |

Rationale for the split: SHAP (§10) can only explain a single fitted model's own output — `cross_val_predict`'s output isn't the output of any one model (different rows come from different fold-specific fits), so it has no SHAP decomposition. Displaying the final model's own prediction keeps every "Model Estimated Value" reconcilable with its own SHAP waterfall (verified exactly, see `EVIDENCE_MATRIX.md`). The tradeoff: `predicted_value_eur` carries the same in-sample optimism that motivated computing `oof_predicted_value_eur` in the first place — it is not a held-out estimate and can run high for statistical outliers within a position. `undervalued_flag` avoids this by using the OOF ratio exclusively; the dashboard's Value Finder caption states this explicitly (§14).

`undervalued_flag` threshold: `oof_value_ratio >= oof_value_ratio.quantile(0.90)`, computed independently per position (so GK and FWD, with very different value distributions, are each compared only against their own population).

## 10. SHAP methodology — Section 5 (notebook 3)

- **Explainer**: `shap.TreeExplainer(model)` for XGBoost/LightGBM/RandomForest; `shap.LinearExplainer(model, X)` for Ridge (never actually the deployed model in any position, kept for completeness).
- Computed once per position on the full-data-fit model against its own full `X` — `explainer.shap_values(X)`. Saved to `data/processed/shap_values/shap_values_{pos}.pkl` as a dict: `{'shap_values': array, 'X_columns': list, 'lookup': DataFrame}`.
- **League/confederation bias quantification** (`aggregate_bias()`, Section 5 cont.): for each player, sums the SHAP values across all `league_*` columns into `league_shap_log`, and across all `confed_*` columns into `confed_shap_log` — the model's own attributed contribution of that player's league/confederation dummy variables to its own prediction, in log-space. These are the **primary, exact** metrics (guaranteed additive by TreeSHAP).
- **EUR-denominated columns** (`league_counterfactual_eur`, `confed_counterfactual_eur`): computed as `back_transform(full_pred_log) - back_transform(full_pred_log - player_league_shap)` — a **SHAP-value subtraction and nonlinear back-transform**, not a re-prediction with the league/confed feature actually changed to a different value. The docstring and inline comments explicitly describe this as a SHAP-derived attribution, not a "true" or "proper" counterfactual (corrected from an earlier version that used that language) — an actual zero-out-and-repredict intervention would produce materially different (and less trustworthy, due to out-of-distribution extrapolation for tree models on an all-zero one-hot row) numbers, empirically checked during that correction.
- **App-side reconstruction** (`app/lib/data_loader.py::get_position_base_value()`): SHAP's `base_value` (the model's expected output before any feature contributions) is not saved to the pickle. It is recovered algebraically from a 50-player sample: `base_value = ln(predicted_value_eur) - shap_values.sum()`, averaged. This is exact **only** because `predicted_value_eur` is the final model's own in-sample prediction (§9) — the same quantity SHAP was computed against.

## 11. League/confederation bias — dashboard-facing artefacts

`bias_summary_league.csv` / `bias_summary_confederation.csv`: `per_player_bias` grouped by `(position, league)` / `(position, confederation)`, reporting `n_players`, `mean_shap_log`, `mean_abs_shap_log`, `mean_counterfactual_eur`. `mean_shap_log`/`mean_abs_shap_log` are the primary reported metrics; `mean_counterfactual_eur` is explicitly labelled dashboard-only/model-estimated in the notebook's own comments, not an observed market premium.

## 12. Comparable-player methodology — Section 9 (notebook 3)

- Starts from each position's own model feature matrix `X` (the exact one the model trained on), then **excludes** everything not football-performance/age/playing-time signal: `league_*`, `confed_*`, `career_stage_*`, `foot_*` (prefix exclusions), and `contract_months_remaining`, `missing_contract`, `height_in_cm`, `player_id_tm` (exact-name exclusions).
- Remaining columns are z-scored (`StandardScaler`), and `NearestNeighbors(n_neighbors=6, metric='euclidean')` finds each player's 5 nearest teammates-in-position by Euclidean distance in that standardized space (6 requested, self at distance 0 dropped).
- Saved as `comparable_players.csv`: `player_id` (`"{Player} — {Squad}"`) plus `neighbor_1_id`…`neighbor_5_id`.
- Because the excluded columns are exactly the ones affected by the valuation cutoff and target-source choices, this artefact is deterministic with respect to those choices — confirmed byte-identical between the December and June pipelines despite being freshly regenerated (not carried over) each run.
- Verification cells (Section 9 cont.) sanity-check neighbour distances against the average random-pair distance, and manually spot-check a few players' neighbours against raw stats.

## 13. Value Finder methodology

`app/pages/2_Value_Finder.py`, built on `load_predictions_with_profile()` (joins `df_predictions.csv` with profile columns from `merged_dataset_2425.csv` by `(Player, position, occurrence-index)`, since ~50 mid-season-transfer duplicates share no player ID across the two files). Displays `actual_value_eur`, `predicted_value_eur` (final-model), `value_gap_eur`, `value_ratio` (both final-model-derived) as sortable/filterable table columns; highlights rows where `undervalued_flag` is true (OOF-derived, §9) in green. `oof_predicted_value_eur`/`oof_value_ratio` are never rendered as table columns (`DISPLAY_COLUMNS` is an explicit allowlist) — a caption below the results count states that the Undervalued highlighting uses a different, cross-validated basis than the visible Value Ratio column.

## 14. Dashboard architecture

- **Pages**: `Home.py` (landing/KPIs), `1_Model_Performance.py`, `2_Value_Finder.py`, `3_Player_Explorer.py`, `4_Bias_Explorer.py`, all under `app/pages/`.
- **Shared libs**: `app/lib/config.py` (all paths, labels, and static lookup dicts — single source of truth for where every artefact lives), `app/lib/data_loader.py` (all CSV/pickle loading, wrapped in `@st.cache_data`/`@st.cache_resource`), `app/lib/components.py` (shared UI components/styling).
- **Data root**: `config.DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"` — the single path every dashboard artefact is read from. `data/processed_december2025_reference/` is never referenced anywhere in `app/`.
- **Promotion note**: the notebooks write to a staging directory (`../data/processed_june2025/` from their own location), not directly to `data/processed/`. Promotion to the live path is a manual, undocumented-in-repo step (not a notebook cell or script) — done once per full pipeline re-run.
- **Static assets not produced by the notebooks**: `club_logos/` (downloaded once from Transfermarkt, cutoff-independent) and, currently, the diagnostic panel PNGs consumed by `1_Model_Performance.py` (`config.diagnostic_panel_png_path()`) — the notebook's Section 6 plotting code produces one combined 3-panel image per position (`diagnostics_{pos}.png`, unused by any page), not the three separate panel files the dashboard actually reads. Both are carried over from `data/processed_december2025_reference/` during promotion rather than being notebook outputs of the June pipeline. Out of scope for this document per instruction — noted here only as an architectural fact, not a finding.

## 15. Libraries and versions (installed, `venv/`)

| Package | Version |
|---|---|
| Python | 3.14.6 |
| streamlit | 1.58.0 |
| pandas | 3.0.3 |
| numpy | 2.4.6 |
| scikit-learn | 1.9.0 |
| xgboost | 3.3.0 |
| lightgbm | 4.6.0 |
| shap | 0.52.0 |
| plotly | 6.8.0 |
| matplotlib | 3.11.0 |
| joblib | 1.5.3 |
| scipy | 1.18.0 |

No `requirements.txt` or `pyproject.toml` exists in the repository; the above reflects what is actually installed in `venv/` at the time of writing, not a pinned/declared dependency set.

## 16. Dependency graph

```
notebooks/01_data_collection.ipynb
  → data/raw/{fbref_kaggle,transfermarkt}/*.csv   (inputs to notebook 2; not cutoff-dependent)

notebooks/02_data_cleaning_june2025.ipynb  (Steps 1–29)
  reads:  data/raw/fbref_kaggle/players_data-2024_2025.csv, players_data-2025_2026.csv
          data/raw/transfermarkt/player_valuations.csv, players.csv
  writes: merged_dataset_2425.csv, df_{fwd,mid,def,gk}.csv, df_ablation.csv
          → data/processed_june2025/ (staged) → promoted to data/processed/

notebooks/03_data_modelling_june2025.ipynb
  Step 1–3   reads df_{fwd,mid,def,gk}.csv, df_ablation.csv
             writes best_model_{fwd,mid,def,gk}.pkl (models/)
  Checkpoint writes results_summary.csv
  Section 4  writes best_model_ablation.pkl, ablation_results.csv
  Section 5  reads best_model_{pos}.pkl
             writes shap_values_{pos}.pkl (shap_values/), shap_summary_{pos}.png (figures)
             writes bias_summary_league.csv, bias_summary_confederation.csv,
                    per_player_bias.csv (dashboard/)
  Section 6  reads best_model_{pos}.pkl
             writes diagnostics_summary.csv (dashboard/), diagnostics_{pos}.png (figures, unused by app/)
  Section 7  reads best_model_{pos}.pkl, cv_predictions (in-memory from Section 6)
             writes df_predictions.csv (root and dashboard/)
  Section 8  verifies all of the above exist; re-saves df_predictions.csv
  Section 9  reads df_{fwd,mid,def,gk}.csv (X only, via prepare_features)
             writes comparable_players.csv (dashboard/)

data/processed/  (promoted)
  ├── merged_dataset_2425.csv ──────────► Home.py (KPI count via df_predictions instead),
  │                                        3_Player_Explorer.py (profile columns, Transfer Value History)
  ├── df_{fwd,mid,def,gk}.csv ──────────► (notebook-internal only; not read by app/)
  ├── results_summary.csv ─────────────► Home.py, 1_Model_Performance.py
  ├── ablation_results.csv ────────────► 1_Model_Performance.py
  ├── models/best_model_{pos}.pkl ─────► (not loaded directly by app/; consumed via the CSVs/pickles below)
  ├── shap_values/shap_values_{pos}.pkl ► 3_Player_Explorer.py (waterfall, get_position_base_value)
  ├── figures/shap_summary_{pos}.png ──► 1_Model_Performance.py
  ├── figures/diagnostics_{pos}_*.png ─► 1_Model_Performance.py
  └── dashboard/
      ├── df_predictions.csv ──────────► Home.py, 2_Value_Finder.py, 3_Player_Explorer.py
      ├── bias_summary_league.csv ─────► 4_Bias_Explorer.py
      ├── bias_summary_confederation.csv ► 4_Bias_Explorer.py
      ├── per_player_bias.csv ─────────► 3_Player_Explorer.py, 4_Bias_Explorer.py
      ├── diagnostics_summary.csv ─────► 1_Model_Performance.py
      └── comparable_players.csv ──────► 3_Player_Explorer.py
```
