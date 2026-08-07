# Figure Captions

Ready-to-use captions for every generated figure. Grouped by figure type; one entry covers all four positions where the structure is identical. Diagnostic PNG regeneration/staleness is explicitly out of scope for this document — captions describe what each figure shows structurally, not its current freshness.

---

## SHAP Summary plots — `shap_summary_{fwd,mid,def,gk}.png`

**What it is**: A SHAP beeswarm (dot) summary plot, `shap.summary_plot(shap_values, X, max_display=15)`, showing the 15 features with the largest mean absolute SHAP contribution for that position's deployed model.

**Axes**: Y-axis lists the 15 features, ordered by importance (most important at top). X-axis is SHAP value (impact on model output, in log-market-value space) — positive values push the prediction up, negative values push it down. Each point is one player; point colour encodes that player's value for the feature (typically red = high, blue = low, on whatever scale the raw feature takes).

**Interpretation**: Read top-to-bottom for global feature importance (which stats matter most to this position's valuation model); read left-right within a row, cross-referenced with colour, for the direction of each feature's effect (e.g. a cluster of red/high-value dots sitting to the right of zero for a "goals" feature means higher goal counts push predicted value up). `league_*`/`confed_*` dummy features appearing in this plot are the same features `aggregate_bias()` sums into the league/confederation bias figures elsewhere.

**Caption template**: *"SHAP summary plot for the [position] model, showing the 15 features with the largest mean absolute contribution to predicted market value. Each point represents one player; horizontal position indicates the SHAP value (impact on the log-market-value prediction) and colour indicates that player's relative value for the feature."*

## Diagnostic panels — predicted vs. actual — `diagnostics_{pos}_pred_vs_actual.png`

**What it is**: A scatter plot of actual vs. predicted log-market-value from the position's out-of-fold cross-validated predictions, with a red dashed identity line marking perfect prediction.

**Axes**: X-axis "Actual log(market value)", Y-axis "Predicted log(market value)". Title states the position and its out-of-fold R².

**Interpretation**: Points clustering tightly along the identity line indicate accurate out-of-fold prediction; systematic curvature or fanning indicates bias or heteroscedasticity at particular value ranges. This is an out-of-fold plot — it reflects the position's cross-validated generalisation performance (the same basis as the reported R²/RMSE), not the in-sample fit the dashboard's "Model Estimated Value" is drawn from.

**Caption template**: *"Out-of-fold predicted vs. actual log-market-value for the [position] model (R²=[value]). The dashed line marks perfect prediction; deviation from it reflects genuine held-out prediction error, not in-sample fit."*

## Diagnostic panels — residuals vs. predicted — `diagnostics_{pos}_residuals_vs_predicted.png`

**What it is**: A scatter plot of residual (actual − predicted, log-space) against the predicted value, with a red dashed zero-line.

**Axes**: X-axis "Predicted log(market value)", Y-axis "Residual (actual − predicted)".

**Interpretation**: A random scatter around zero with no trend indicates no systematic bias across the predicted-value range. A funnel/fan shape indicates heteroscedasticity (larger errors at higher predicted values); a slope or curve indicates the model is systematically over- or under-predicting in some region of the value range.

**Caption template**: *"Residuals (actual minus predicted, log-space) plotted against predicted value for the [position] model's out-of-fold predictions. A patternless scatter around the zero line indicates no systematic bias across the value range."*

## Diagnostic panels — residual distribution — `diagnostics_{pos}_residual_dist.png`

**What it is**: A histogram (30 bins) of the same out-of-fold residuals, with a red dashed zero-line.

**Axes**: X-axis "Residual (actual − predicted)", Y-axis "Count". Title states the mean residual.

**Interpretation**: A roughly symmetric, zero-centred distribution indicates unbiased predictions on average. Skew indicates a systematic over- or under-prediction tendency; the title's stated mean residual quantifies this directly.

**Caption template**: *"Distribution of out-of-fold residuals for the [position] model (mean=[value]). A distribution centred near zero indicates the model is not systematically over- or under-valuing players on average."*

## Combined diagnostics image — `diagnostics_{pos}.png`

**What it is**: A single 1×3 figure combining all three panels above (predicted vs. actual, residuals vs. predicted, residual distribution) side by side. Produced by the same notebook cell that produces the three individual panels above, saved once as a matplotlib subplot grid. Not currently referenced by any dashboard page (`config.diagnostics_png_path()` is defined but unused; the dashboard reads the three separate panel files instead).

**Caption template**: *"Combined diagnostic panel for the [position] model: predicted vs. actual (left), residuals vs. predicted (centre), residual distribution (right), all computed from out-of-fold cross-validated predictions."*

## Bias Explorer — League Bias chart (dashboard-rendered, not a saved file)

**What it is**: A Plotly horizontal bar chart, rendered live from `bias_summary_league.csv` on `4_Bias_Explorer.py`, one bar per league (or per league×position when "All" positions is selected).

**Axes**: X-axis "Mean SHAP Contribution (log-space)", Y-axis league name. Hover tooltip surfaces the EUR-equivalent (`mean_counterfactual_eur`) and sample size.

**Interpretation**: Bar length/direction shows each league's average attributed contribution to predicted value after accounting for performance — positive bars mean the model associates that league with a valuation premium, negative bars a discount, holding the modelled performance features constant.

**Caption template**: *"Mean SHAP contribution of league affiliation to predicted market value, by league and position, after accounting for observed performance. Bar length indicates the model-attributed premium or discount in log-space; hover values show the SHAP-derived euro-equivalent and sample size."*

## Bias Explorer — Confederation Bias chart (dashboard-rendered, not a saved file)

**What it is**: The same chart type as League Bias, driven by `bias_summary_confederation.csv`.

**Caption template**: *"Mean SHAP contribution of nationality/confederation to predicted market value, by confederation and position, after accounting for observed performance. Confederation effects are an order of magnitude or more smaller than league effects across most positions (see RESULTS_REFERENCE.md §6)."*
