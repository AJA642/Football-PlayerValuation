import math

import streamlit as st

from lib import config
from lib.components import balance_section_spacing, difference_style, render_header, value_ratio_style
from lib.data_loader import load_predictions_with_profile

st.set_page_config(
    page_title="Value Finder", page_icon="🔍", layout="wide", initial_sidebar_state="collapsed"
)
render_header(active="Value Finder")
balance_section_spacing()

# This filter panel is a compact control surface, not prose — tighter than
# the standard bordered-card padding (components.py already trims that
# globally) and tighter than the standard inter-section divider gap, since
# neither of those defaults were tuned with a dense, all-controls panel
# like this one in mind.
st.markdown(
    """
    <style>
    .st-key-vf-filters-panel {
        padding-top: 0.75rem !important;
        padding-bottom: 0.75rem !important;
    }
    .st-key-vf-filters-panel [data-testid="stVerticalBlock"] {
        gap: 8px !important;
    }
    [data-testid="stMainBlockContainer"] .st-key-vf-filters-results-divider hr {
        margin: 0.5rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Value Finder")
st.write(
    "Compare each player's actual 2024–25 market value against the "
    f"{config.MODEL_ESTIMATED_VALUE_LABEL.lower()} derived from their observed "
    "performance. Select a player to open their full profile in Player Explorer."
)

players = load_predictions_with_profile()

with st.container(border=True, key="vf-filters-panel"):
    st.subheader("Filters")
    # Same League -> Club -> Position ordering/hierarchy as Player Explorer.
    # These are multiselects (not Player Explorer's single "All"-or-one
    # selectbox), so the cascade works slightly differently: Club's option
    # list is scoped to whichever League(s) are currently selected, and any
    # already-picked club that falls outside a newly-narrowed League
    # selection is dropped from the selection instead of the whole field
    # resetting to a single default.
    filter_row1 = st.columns(3)
    with filter_row1[0]:
        league_label_to_raw = {
            config.friendly_league_label(raw): raw for raw in sorted(players["Comp"].unique())
        }
        selected_league_labels = st.multiselect(
            "League", options=sorted(league_label_to_raw.keys()), key="vf_league_filter"
        )
        leagues = [league_label_to_raw[label] for label in selected_league_labels]

    club_pool = players if not leagues else players[players["Comp"].isin(leagues)]
    club_options = sorted(club_pool["Squad"].unique())
    valid_prior_clubs = [c for c in st.session_state.get("vf_club_filter", []) if c in club_options]
    if st.session_state.get("vf_club_filter") != valid_prior_clubs:
        st.session_state["vf_club_filter"] = valid_prior_clubs
    with filter_row1[1]:
        clubs = st.multiselect("Club", options=club_options, key="vf_club_filter")

    with filter_row1[2]:
        positions = st.multiselect(
            "Position", options=config.POSITIONS, format_func=config.friendly_position_label
        )

    filter_row2 = st.columns([1, 1, 1, 1])
    with filter_row2[0]:
        age_min, age_max = math.floor(players["age_precise"].min()), math.ceil(players["age_precise"].max())
        age_range = st.slider("Age", min_value=age_min, max_value=age_max, value=(age_min, age_max))
    with filter_row2[1]:
        value_min, value_max = float(players["actual_value_eur"].min()), float(players["actual_value_eur"].max())
        value_range = st.slider(
            "Market value range (€)",
            min_value=value_min,
            max_value=value_max,
            value=(value_min, value_max),
            format="€%,.0f",
        )
    with filter_row2[2]:
        minutes_min = st.slider(
            "Minimum minutes played",
            min_value=0,
            max_value=int(players["Min_playing_time"].max()),
            value=0,
        )
    with filter_row2[3]:
        # A compact control surface, not prose — this sits in the same row
        # as the sliders rather than on its own line. st.slider's own label
        # sits above the track, so a leading spacer of the same height lines
        # the checkbox up with the sliders' tracks instead of their labels.
        st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
        show_undervalued_only = st.checkbox("Show undervalued players only", value=False)

with st.container(key="vf-filters-results-divider"):
    st.divider()
st.header("Results")

filtered = players.copy()
if leagues:
    filtered = filtered[filtered["Comp"].isin(leagues)]
if clubs:
    filtered = filtered[filtered["Squad"].isin(clubs)]
if positions:
    filtered = filtered[filtered["position"].isin(positions)]
filtered = filtered[filtered["age_precise"].between(*age_range)]
filtered = filtered[filtered["actual_value_eur"].between(*value_range)]
filtered = filtered[filtered["Min_playing_time"] >= minutes_min]
if show_undervalued_only:
    filtered = filtered[filtered["undervalued_flag"]]

# No explicit ordering existed before — players with the largest
# model-vs-actual discrepancy (in either direction) are the whole point of
# this page, so that's the default sort rather than incidental CSV row order.
filtered = filtered.sort_values("value_ratio", ascending=False).reset_index(drop=True)

st.caption(
    f"{len(filtered):,} of {len(players):,} players match the current filters. "
    "Undervalued players are highlighted in green."
)

if filtered.empty:
    st.info("No players match the current filters. Try widening your filters.")
    st.stop()

DISPLAY_COLUMNS = {
    "Player": "Player",
    "Squad": "Club",
    "Comp": "League",
    "position": "Position",
    "actual_value_eur": "Actual Value",
    "predicted_value_eur": config.MODEL_ESTIMATED_VALUE_LABEL,
    "value_gap_eur": "Difference",
    "value_ratio": "Value Ratio",
}
display_df = filtered[list(DISPLAY_COLUMNS.keys())].rename(columns=DISPLAY_COLUMNS)
display_df["League"] = display_df["League"].map(config.friendly_league_label)
undervalued_mask = filtered["undervalued_flag"].to_numpy()


def _highlight_undervalued(row):
    is_undervalued = undervalued_mask[display_df.index.get_loc(row.name)]
    style = "background-color: rgba(34, 197, 94, 0.18)" if is_undervalued else ""
    return [style] * len(row)


styled_df = (
    display_df.style.apply(_highlight_undervalued, axis=1)
    .map(value_ratio_style, subset=["Value Ratio"])
    .map(difference_style, subset=["Difference"])
)

event = st.dataframe(
    styled_df,
    hide_index=True,
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Actual Value": st.column_config.NumberColumn(format="€%,.0f"),
        config.MODEL_ESTIMATED_VALUE_LABEL: st.column_config.NumberColumn(
            format="€%,.0f",
            help=f"{config.MODEL_ESTIMATED_VALUE_LABEL} — derived from observed 2024–25 performance, not a forecast.",
        ),
        "Difference": st.column_config.NumberColumn(
            format="€%+,.0f",
            help=f"{config.MODEL_ESTIMATED_VALUE_LABEL} minus Actual Value.",
        ),
        "Value Ratio": st.column_config.NumberColumn(
            format="%.2f",
            help=f"{config.MODEL_ESTIMATED_VALUE_LABEL} ÷ Actual Value.",
        ),
    },
    key="value_finder_table",
)

selected_rows = event.selection.rows if event and event.selection else []
if selected_rows:
    selected_player_row = filtered.iloc[selected_rows[0]]
    st.session_state["selected_player"] = selected_player_row["Player"]
    st.session_state["selected_player_position"] = selected_player_row["position"]
    st.switch_page("pages/3_Player_Explorer.py")
