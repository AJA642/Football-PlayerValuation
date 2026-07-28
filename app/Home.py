import streamlit as st

from lib import config
from lib.components import balance_section_spacing, render_header, stat_card
from lib.data_loader import load_dashboard_predictions, load_results_summary

st.set_page_config(
    page_title="Performance-Based Football Player Valuation",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_header(active="Home")
balance_section_spacing()

st.title("Performance-Based Football Player Valuation")
st.subheader(
    "A Machine Learning Framework for Quantifying League and Nationality Bias "
    "in Football Market Values"
)
st.write(
    "Big 5 European leagues, 2024–25 season, 2,061 players. Position-specific "
    "machine learning models estimate market value from on-pitch performance, "
    "with SHAP explainability used to quantify the contribution of league and "
    "nationality to each estimate."
)

predictions = load_dashboard_predictions()
results_summary = load_results_summary()

best_per_position = results_summary.loc[results_summary.groupby("position")["R2"].idxmax()]
best_per_position = best_per_position.set_index("position").loc[config.POSITIONS]

algo_to_positions: dict[str, list[str]] = {}
for pos, row in best_per_position.iterrows():
    algo_to_positions.setdefault(row["algorithm"], []).append(pos)

col1, col2, col3, col4 = st.columns(4)
with col1:
    stat_card("Players Analysed", f"{len(predictions):,}")
with col2:
    stat_card("Model Configurations Trained", f"{len(results_summary)}")
with col3:
    stat_card("Positions Covered", f"{predictions['position'].nunique()}")
with col4:
    # Keyed with the same "stat-card-" prefix as stat_card() itself purely so
    # it picks up components.py's shared `[class*="st-key-stat-card-"]`
    # padding rule — this card would otherwise be the one card in the row
    # still at Streamlit's default padding, and visibly taller than its
    # three siblings.
    with st.container(border=True, key="stat-card-best-algorithm-per-position"):
        st.caption("Best Algorithm per Position")
        for algo, positions in algo_to_positions.items():
            st.markdown(f"**{algo}** — {', '.join(positions)}")

# --- Key Finding ---------------------------------------------------------
# No section heading, per spec — st.info() is already the dashboard's
# existing highlighted-callout style (the same component Bias Explorer's
# own "Insight" card uses for its dynamic strongest-league finding), reused
# here rather than inventing a new box style. The claim itself is checked
# against data/processed/dashboard/bias_summary_league.csv, not assumed:
# Premier League has the single highest mean_shap_log of any league for
# every one of the four positions (DEF 0.614, MID 0.623, FWD 0.430,
# GK 0.285) — a genuine "across all four positions" finding, not just the
# overall/pooled figure.
st.info(
    "**Key Finding:** Premier League affiliation shows the model's largest positive "
    "SHAP contribution to estimated market value, across all four positions."
)

# --- How the Framework Works ----------------------------------------------
st.subheader("How the Framework Works", anchor=False)
st.markdown(
    """
    <style>
    /* Lets the six stages wrap onto a second line on a narrow viewport
    instead of Streamlit's default (squeezing columns arbitrarily thin)
    while keeping the left-to-right reading order on wider screens. */
    .st-key-home-workflow [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        row-gap: 0.75rem;
    }
    .home-workflow-stage {
        text-align: center;
    }
    .home-workflow-stage .icon { font-size: 1.6rem; line-height: 1.3; }
    .home-workflow-stage .label {
        font-size: 0.8rem;
        color: var(--app-text-muted, rgba(250, 250, 250, 0.7));
    }
    .home-workflow-arrow {
        text-align: center;
        font-size: 1.3rem;
        color: var(--app-text-muted, rgba(250, 250, 250, 0.35));
        padding-top: 0.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
WORKFLOW_STAGES = [
    ("📊", "Performance Data"),
    ("⚙️", "Feature Engineering"),
    ("🧠", "Machine Learning Models"),
    ("💶", "Market Value Prediction"),
    ("🔍", "SHAP Explainability"),
    ("⚖️", "Bias Analysis"),
]
with st.container(key="home-workflow"):
    # Stage columns wider than arrow columns; arrows are their own narrow
    # columns rather than baked into a stage's label, so the flex-wrap rule
    # above can wrap a whole stage (with its icon and label together) onto
    # the next line instead of splitting an arrow away from its neighbour.
    widths = []
    for i in range(len(WORKFLOW_STAGES)):
        widths.append(4)
        if i < len(WORKFLOW_STAGES) - 1:
            widths.append(1)
    workflow_cols = st.columns(widths)
    col_index = 0
    for i, (icon, label) in enumerate(WORKFLOW_STAGES):
        with workflow_cols[col_index]:
            st.markdown(
                f'<div class="home-workflow-stage"><div class="icon">{icon}</div>'
                f'<div class="label">{label}</div></div>',
                unsafe_allow_html=True,
            )
        col_index += 1
        if i < len(WORKFLOW_STAGES) - 1:
            with workflow_cols[col_index]:
                st.markdown('<div class="home-workflow-arrow">→</div>', unsafe_allow_html=True)
            col_index += 1

# --- Explore the Dashboard -------------------------------------------------
st.subheader("Explore the Dashboard", anchor=False)
nav_card_cols = st.columns(len(config.PAGES))
for col, page in zip(nav_card_cols, config.PAGES):
    with col:
        # Same "stat-card-" key prefix as the KPI cards above (and
        # stat_card() itself) purely so this reuses components.py's shared
        # card padding rule — matching card styling already established on
        # this exact page, not a new design.
        card_key = "stat-card-nav-" + page["label"].lower().replace(" ", "-")
        with st.container(border=True, key=card_key):
            st.markdown(f"#### {page['icon']} {page['label']}")
            st.caption(page["description"])
            st.page_link(page["path"], label="Open →")

with st.expander("How to interpret this dashboard"):
    st.markdown(
        "- The model estimates market value based on players' observed 2024–25 "
        "characteristics\n"
        "- Estimates are not forecasts of future value\n"
        "- SHAP visualisations explain how different features contributed to "
        "the model's estimate\n"
        "- League and confederation contributions represent model-derived "
        "estimates after accounting for other features"
    )
