import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import shap
import streamlit as st

from lib import config
from lib.components import (
    balance_section_spacing,
    difference_color,
    flag_emoji,
    format_eur_short,
    logo_prefixed_heading,
    render_header,
    stat_card,
    value_ratio_color,
)
from lib.data_loader import (
    get_club_logo_data_uri,
    get_player_full_record,
    get_player_shap_row,
    get_player_valuation_history,
    get_position_base_value,
    load_predictions_with_profile,
)

st.set_page_config(
    page_title="Player Explorer", page_icon="👤", layout="wide", initial_sidebar_state="collapsed"
)
render_header(active="Player Explorer")
balance_section_spacing()
st.title("Player Explorer", anchor=False)

players = load_predictions_with_profile()

# A cross-page handoff (e.g. clicking a row in Value Finder) must always
# land on the intended player — regardless of whatever League/Club/Position
# filters were left over from a previous visit to this page in the same
# session. Reset them once per *new* handoff (tracked by player name so this
# doesn't keep clobbering a filter the user deliberately set while just
# browsing normally), before the filter widgets below are instantiated —
# session_state for a widget's key can only be set before that widget is
# created in the current run.
_incoming_player = st.session_state.get("selected_player")
if _incoming_player and st.session_state.get("_last_handoff_player") != _incoming_player:
    st.session_state["league_filter"] = "All"
    st.session_state["club_filter"] = "All"
    st.session_state["position_filter"] = "All"
    st.session_state["_last_handoff_player"] = _incoming_player

# Primary navigation is League -> Club -> Player (how users actually think
# about the dataset — "Barcelona players", "the Premier League" — rather
# than starting from Position). Position stays available but only narrows
# whatever League/Club has already selected; it doesn't drive which leagues
# or clubs are offered, and its own option list never changes.
league_label_to_raw = {config.friendly_league_label(raw): raw for raw in players["Comp"].unique()}
league_options = ["All"] + sorted(league_label_to_raw.keys())

filter_cols = st.columns([1, 1, 1, 3])
with filter_cols[0]:
    league_filter = st.selectbox("League", league_options, index=0, key="league_filter")

club_pool = players if league_filter == "All" else players[players["Comp"] == league_label_to_raw[league_filter]]
club_options = ["All"] + sorted(club_pool["Squad"].unique())
if st.session_state.get("club_filter") not in club_options:
    st.session_state["club_filter"] = "All"
with filter_cols[1]:
    club_filter = st.selectbox("Club", club_options, key="club_filter")

with filter_cols[2]:
    st.selectbox(
        "Position",
        ["All"] + config.POSITIONS,
        index=0,
        key="position_filter",
        format_func=config.friendly_position_label,
    )
position_filter = st.session_state["position_filter"]

# Single filtering pipeline — League, then Club, then Position — feeding the
# Player search dropdown below. No filter is applied more than once and no
# other section of the page re-derives this pool independently.
pool = players
if league_filter != "All":
    pool = pool[pool["Comp"] == league_label_to_raw[league_filter]]
if club_filter != "All":
    pool = pool[pool["Squad"] == club_filter]
if position_filter != "All":
    pool = pool[pool["position"] == position_filter]
pool = pool.sort_values("Player").copy()
pool["_label"] = pool["Player"] + " — " + pool["Squad"] + " (" + pool["position"] + ")"
labels = pool["_label"].tolist()

default_label = None
incoming_player = st.session_state.get("selected_player")
incoming_position = st.session_state.get("selected_player_position")
if incoming_player:
    match = pool[pool["Player"] == incoming_player]
    if incoming_position:
        position_match = match[match["position"] == incoming_position]
        if not position_match.empty:
            match = position_match
    if not match.empty:
        default_label = match.iloc[0]["_label"]
# Only pre-select a player if we arrived via a cross-page handoff (e.g. from
# Value Finder). Otherwise the search box should start blank rather than
# defaulting to the first player alphabetically.
default_index = labels.index(default_label) if default_label in labels else None

with filter_cols[3]:
    selected_label = st.selectbox(
        "Search Player",
        labels,
        index=default_index,
        placeholder="Start typing a player name or club...",
    )
if not labels:
    st.warning("No players match the selected League, Club, and Position filters.")
    st.stop()

st.divider()

if not selected_label:
    st.caption("Search for a player above to get started.")
    st.stop()

player_row = pool[pool["_label"] == selected_label].iloc[0]
player_name = player_row["Player"]
position = player_row["position"]
squad = player_row["Squad"]
full_record = get_player_full_record(player_name, position, squad)

# --- Summary row: Player Profile | Market Valuation ---------------------
# Side by side rather than two stacked full-width sections — both are
# short, and stacking them was the single biggest source of unnecessary
# scrolling on this page. Order follows the question a user actually asks
# first ("who is this, what's it worth") before performance detail/SHAP.
st.markdown(
    """
    <style>
    /* Compact vertical stack for the profile card: name prominent, each
    field on its own line with no per-field caption label (self-descriptive
    via the flag/crest/units already inline) and a tight gap between them —
    "easy to scan", not the old 7-across label/value grid. */
    .st-key-profile-summary-card [data-testid="stVerticalBlock"] { gap: 6px !important; }
    /* Hero figure for the valuation card: Model Estimated Value is the
    single most important number on this page (the model's own output),
    so it gets its own large line — Actual/Difference/Value Ratio follow
    underneath as a compact label/value list, not four equal-weight cards. */
    .valuation-hero-value {
        font-size: 2.25rem;
        font-weight: 600;
        line-height: 1.2;
    }
    .valuation-row {
        display: flex;
        justify-content: space-between;
        padding: 0.3rem 0;
        border-top: 1px solid var(--app-border, rgba(250, 250, 250, 0.15));
    }
    .valuation-row-label { color: var(--app-text-muted, rgba(250, 250, 250, 0.6)); }
    /* Fixed-width label column so profile values line up into a vertical
    column, unlike the space-between valuation rows. Built as a single
    combined markdown block below (not one st.markdown call per field) so
    the row list can't be split across separate Streamlit element wrappers
    mid-render. */
    .profile-row {
        display: flex;
        gap: 0.6rem;
        padding: 0.3rem 0;
    }
    .profile-row-label {
        flex: 0 0 132px;
        color: var(--app-text-muted, rgba(250, 250, 250, 0.6));
    }
    </style>
    """,
    unsafe_allow_html=True,
)

summary_cols = st.columns(2, gap="medium")
with summary_cols[0]:
    with st.container(border=True, key="profile-summary-card"):
        st.subheader("Player Profile", anchor=False)
        st.markdown(f"### {player_name}")

        club_html = logo_prefixed_heading(get_club_logo_data_uri(squad), squad)

        nationality = full_record["country_of_citizenship"] if full_record is not None else "—"
        flag = flag_emoji(nationality)
        nationality_html = f"{flag} {nationality}" if flag else nationality

        st.markdown(
            f"""
            <div class="profile-row"><span class="profile-row-label">Club:</span><span>{club_html}</span></div>
            <div class="profile-row"><span class="profile-row-label">Country:</span><span>{nationality_html}</span></div>
            <div class="profile-row"><span class="profile-row-label">League:</span><span>{config.friendly_league_label(player_row["Comp"])}</span></div>
            <div class="profile-row"><span class="profile-row-label">Position:</span><span>{config.POSITION_NAMES.get(position, position)}</span></div>
            <div class="profile-row"><span class="profile-row-label">Age:</span><span>{player_row["age_precise"]:.0f} years</span></div>
            <div class="profile-row"><span class="profile-row-label">Minutes Played:</span><span>{int(player_row["Min_playing_time"]):,} minutes</span></div>
            """,
            unsafe_allow_html=True,
        )

with summary_cols[1]:
    with st.container(border=True, key="valuation-summary-card"):
        st.subheader("Market Valuation", anchor=False)

        predicted = player_row["predicted_value_eur"]
        actual = player_row["actual_value_eur"]
        diff = player_row["value_gap_eur"]
        ratio = player_row["value_ratio"]
        diff_color = difference_color(diff)
        ratio_color = value_ratio_color(ratio)

        st.markdown(
            f"""
            <div class="valuation-row-label">{config.MODEL_ESTIMATED_VALUE_LABEL}</div>
            <div class="valuation-hero-value">€{predicted:,.0f}</div>
            <div class="valuation-row">
                <span class="valuation-row-label">Actual Value</span>
                <span>€{actual:,.0f}</span>
            </div>
            <div class="valuation-row">
                <span class="valuation-row-label">Difference</span>
                <span style="color:{diff_color or 'inherit'};">€{diff:+,.0f}</span>
            </div>
            <div class="valuation-row">
                <span class="valuation-row-label">Value Ratio</span>
                <span style="color:{ratio_color or 'inherit'};">{ratio:.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "The model estimates this player's market value based on their observed "
            "2024–25 characteristics. It is not a prediction of future value."
        )

st.divider()

# --- Performance Statistics ----------------------------------------------
st.header("Performance Statistics", anchor=False)
if full_record is None:
    st.warning(f"No performance record found for **{player_name}** ({squad}) in merged_dataset_2425.")
else:
    for group_name, stats in config.POSITION_STAT_GROUPS[position]:
        st.subheader(group_name, anchor=False)
        stat_cols = st.columns(len(stats))
        for col, (field, label, format_type) in zip(stat_cols, stats):
            with col:
                value = full_record.get(field)
                if pd.isna(value):
                    display_value = "—"
                elif format_type == "percent":
                    display_value = f"{value:.1f}%"
                elif format_type == "count":
                    display_value = f"{value:,.0f}"
                else:
                    display_value = f"{value:.2f}"
                stat_card(label, display_value)

st.divider()

# --- Why did the model estimate this value? -----------------------------
st.header("Why did the model estimate this value?", anchor=False)
st.write(
    "The waterfall chart below shows how each feature increased (red) or decreased "
    "(blue) the model's estimated value for this player. Together, these "
    "contributions produce the final estimate."
)

shap_row = get_player_shap_row(position, player_name, squad)
if shap_row is None:
    st.error(f"No SHAP record found for **{player_name}** ({squad}) in the {position} SHAP artefacts.")
    st.stop()

feature_labels = [config.friendly_feature_label(c) for c in shap_row["X_columns"]]

base_value = get_position_base_value(position)
explanation = shap.Explanation(
    values=shap_row["shap_values"],
    base_values=base_value,
    feature_names=feature_labels,
)

with st.spinner("Loading SHAP explanation…"):
    fig = plt.figure()
    shap.plots.waterfall(explanation, max_display=15, show=False)
    st.pyplot(fig, clear_figure=True)
st.caption(f"{config.SHAP_EUR_CAVEAT}.")

st.divider()

# --- Top SHAP Contributors ---------------------------------------------
st.header("Top SHAP Contributors", anchor=False)
contributions = pd.Series(shap_row["shap_values"], index=feature_labels).sort_values(ascending=False)
top_positive = contributions.head(5)
top_negative = contributions.tail(5).sort_values()

contrib_cols = st.columns(2)
with contrib_cols[0]:
    st.markdown("**Top Positive Contributors**")
    st.dataframe(top_positive.rename("SHAP value (log-space)").to_frame(), use_container_width=True)
with contrib_cols[1]:
    st.markdown("**Top Negative Contributors**")
    st.dataframe(top_negative.rename("SHAP value (log-space)").to_frame(), use_container_width=True)

st.divider()

# --- Transfer Value History ----------------------------------------------
st.header("Transfer Value History", anchor=False)
st.caption(
    "Historical Transfermarkt market valuations over time — distinct from the model estimate above, "
    "which is derived only from this player's observed 2024–25 performance. This chart shows what the "
    "market actually valued the player at, at each point in their career, up to June 2025."
)

valuation_history = (
    get_player_valuation_history(int(full_record["player_id_tm"])) if full_record is not None else pd.DataFrame()
)

if valuation_history.empty:
    st.info(f"No historical valuation data is available for **{player_name}**.")
else:
    valuation_history = valuation_history.copy()
    valuation_history["formatted_value"] = valuation_history["market_value_in_eur"].apply(format_eur_short)

    fig = px.line(
        valuation_history,
        x="date",
        y="market_value_in_eur",
        markers=True,
        custom_data=["formatted_value"],
    )
    fig.update_traces(hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<extra></extra>")
    fig.update_layout(
        xaxis_title="Valuation Date",
        yaxis_title="Market Value (€)",
        yaxis_tickprefix="€",
        yaxis_tickformat="~s",
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True, key="valuation_history_chart")