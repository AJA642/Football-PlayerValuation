import streamlit as st

from lib import config
from lib.components import balance_section_spacing, metrics_table_with_params, render_header, wide_divider
from lib.data_loader import (
    load_ablation_results,
    load_diagnostics_summary,
    load_results_summary,
    require_image,
)

st.set_page_config(
    page_title="Model Performance", page_icon="📊", layout="wide", initial_sidebar_state="collapsed"
)
render_header(active="Model Performance")
balance_section_spacing()

st.title("Model Performance")
st.write(
    "Position-specific models were trained with Ridge Regression, Random "
    "Forest, XGBoost and LightGBM. The best-performing algorithm per "
    "position, selected by R², was saved as the position's model."
)

diagnostics_summary = load_diagnostics_summary()
results_summary = load_results_summary()
ablation_results = load_ablation_results()

METRIC_COLUMNS = {
    "position": "Position",
    "algorithm": "Algorithm",
    "RMSE_log": "RMSE (log)",
    "MAE_log": "MAE (log)",
    "R2": "R²",
    "MAPE_eur_pct": "MAPE (%)",
    "best_params": "Best Hyperparameters",
}

st.header("Best Model per Position")
# diagnostics_summary.csv has no algorithm column of its own — the winning
# algorithm per position is selected from results_summary (max R²), the
# same values already used to build the Home page's "Best Algorithm per
# Position" card. No new metric is computed, just an existing-value lookup.
best_algorithm_per_position = (
    results_summary.loc[results_summary.groupby("position")["R2"].idxmax()]
    .set_index("position")["algorithm"]
)
diagnostics_with_algorithm = diagnostics_summary.copy()
diagnostics_with_algorithm.insert(
    1, "algorithm", diagnostics_with_algorithm["position"].map(best_algorithm_per_position)
)
st.dataframe(
    diagnostics_with_algorithm.rename(
        columns={k: v for k, v in METRIC_COLUMNS.items() if k in diagnostics_with_algorithm.columns}
    ),
    hide_index=True,
    use_container_width=True,
)
st.caption(
    "XGBoost produced the strongest performance for outfield positions, while LightGBM performed "
    "best for goalkeepers."
)

wide_divider(key="model-performance-summary-detail-divider")

st.header("Full Results — All Algorithms")
st.caption("Select a row to view its full hyperparameters below the table.")
metrics_table_with_params(results_summary, METRIC_COLUMNS, key="results_summary_table")

st.divider()

st.header("Feature Ablation Experiment")
st.caption(
    "This experiment pools all positions together (`position = ALL_ABLATION`) "
    "and is not position-specific — it tests how much predictive power is "
    "lost when advanced performance metrics are removed."
)
metrics_table_with_params(ablation_results, METRIC_COLUMNS, key="ablation_results_table")

st.divider()

st.header("Diagnostic and SHAP Summary Plots")
tabs = st.tabs(config.POSITIONS)
for position, tab in zip(config.POSITIONS, tabs):
    with tab:
        col1, col2 = st.columns(2)
        with col1:
            st.image(
                require_image(config.diagnostics_png_path(position)),
                caption=f"Diagnostics — {position}",
                use_container_width=True,
            )
        with col2:
            st.image(
                require_image(config.shap_summary_png_path(position)),
                caption=f"SHAP Summary — {position}",
                use_container_width=True,
            )
