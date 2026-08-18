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
    page_title="Model Performance",
    page_icon=config.PAGE_ICONS["Model Performance"],
    layout="wide",
    initial_sidebar_state="collapsed",
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
# diagnostics_summary.csv has no algorithm column — the winner per position
# is looked up from results_summary (max R²), the same values behind the
# Home page's Best Algorithm card. No new metric computed here.
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
    width="stretch",
)
_algo_position_groups: dict[str, list[str]] = {}
for _pos in config.POSITIONS:
    _algo_position_groups.setdefault(best_algorithm_per_position[_pos], []).append(_pos)
st.caption(
    "Best algorithm by position: "
    + "; ".join(f"{algo} ({', '.join(positions)})" for algo, positions in _algo_position_groups.items())
    + "."
)

wide_divider(key="model-performance-summary-detail-divider")

st.header("Full Results — All Algorithms")
st.caption("Select a row to view its full hyperparameters below the table.")
metrics_table_with_params(results_summary, METRIC_COLUMNS, key="results_summary_table")

st.divider()

st.header("Feature Ablation Experiment")
st.caption(
    "This experiment pools all positions together (`position = ALL_ABLATION`) "
    "and uses a reduced feature set restricted to metrics also available in "
    "the 2025-26 season. Because both change at once, the gap versus the "
    "position-specific models above reflects the combined effect of losing "
    "the advanced metrics and moving to a pooled population — not the "
    "feature reduction in isolation."
)
ablation_display = ablation_results.copy()
ablation_display["position"] = ablation_display["position"].replace(
    "ALL_ABLATION", "All Positions (Pooled)"
)
metrics_table_with_params(ablation_display, METRIC_COLUMNS, key="ablation_results_table")

st.divider()

st.header("Diagnostic and SHAP Summary Plots")
st.caption("Diagnostic plots and SHAP summaries are shown for the final selected model only.")
st.markdown(
    """
    <style>
    /* Diagnostics/SHAP Summary as equal companion panels, matching the
    bordered-card treatment used elsewhere (e.g. Player Explorer). Identical
    padding/border on both means their top edges align by construction. */
    [class*="st-key-diag-panel-"], [class*="st-key-shap-panel-"] {
        padding-top: 16px !important;
        padding-bottom: 16px !important;
    }
    /* Gap sized (measured, not guessed) so the Diagnostics card's total
    height matches SHAP Summary's at the 35/65 split — at 10px this card
    came out ~29px shorter, so +14.5px per gap (×2) closes the difference.
    Compound selector (no space): key class and stVerticalBlock testid are
    on the same element here, not parent/descendant — a descendant-combinator
    version silently matched nothing and left the gap at Streamlit's default. */
    [class*="st-key-diag-panel-"][data-testid="stVerticalBlock"] {
        gap: 25px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
tabs = st.tabs(config.POSITIONS)
for position, tab in zip(config.POSITIONS, tabs):
    with tab:
        # 35/65, not even — Diagnostics' three stacked plots are narrow, but
        # SHAP needs real width to stay readable. 30/70 was tried first and
        # measured; it overcorrected, leaving SHAP taller than Diagnostics,
        # so 35/65 was derived from that measurement to balance both panels.
        diag_col, shap_col = st.columns([35, 65])
        with diag_col:
            with st.container(border=True, key=f"diag-panel-{position}"):
                st.subheader("Diagnostics")
                st.caption("Prediction quality and residual behaviour")
                for panel, _panel_label in config.DIAGNOSTIC_PANELS:
                    st.image(
                        require_image(config.diagnostic_panel_png_path(position, panel)),
                        width="stretch",
                    )
        with shap_col:
            with st.container(border=True, key=f"shap-panel-{position}"):
                st.subheader("SHAP Summary")
                st.caption("Top 15 most influential features")
                st.image(
                    require_image(config.shap_summary_png_path(position)),
                    width="stretch",
                )
