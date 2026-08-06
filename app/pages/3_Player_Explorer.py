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
    value_ratio_color,
)
from lib.data_loader import (
    get_club_logo_data_uri,
    get_league_shap_by_player,
    get_player_full_record,
    get_player_shap_row,
    get_player_valuation_history,
    get_position_base_value,
    load_comparable_players,
    load_predictions_with_profile,
)

st.set_page_config(
    page_title="Player Explorer",
    page_icon=config.PAGE_ICONS["Player Explorer"],
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_header(active="Player Explorer")
balance_section_spacing()
st.title("Player Explorer")

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

# Shrink the page title once a player is selected — the filters above it
# stay the same size, but the title itself is pure chrome at this point
# (the player's own name becomes the focal heading below), so freeing up
# its vertical space lets more of the profile/valuation/stats row show
# without scrolling. Left at full size on the blank, no-selection state.
st.markdown(
    """
    <style>
    [data-testid="stMain"] h1 { font-size: 1.5rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

player_row = pool[pool["_label"] == selected_label].iloc[0]
player_name = player_row["Player"]
position = player_row["position"]
squad = player_row["Squad"]
full_record = get_player_full_record(player_name, position, squad)

# --- Summary row: Player Profile | Market Valuation | Performance Stats --
# Three columns rather than a two-column summary followed by a full-width
# statistics section — this puts "who is this, what's it worth, how did
# they play" side by side as one scannable row, with no page-length scroll
# needed to reach the stats. Performance Statistics gets 2x the width of
# the other two (it holds far more content: several categories of stats
# vs. a handful of profile/valuation fields).
st.markdown(
    """
    <style>
    /* Even more breathing room than the app-wide card default (13px) — all
    three cards share the same padding now that Statistics is boxed too,
    so the three columns read as one consistent, bordered set.
    Equal column heights: st.columns() already stretches each stColumn
    wrapper to match the tallest one (confirmed via measurement — all
    three wrappers report the same height regardless of content), but each
    card's own height defaults to its content size, leaving empty space
    below the shorter cards instead of visibly filling the stretched
    column. height: 100% makes each card fill that already-equal wrapper —
    but only once the intermediate "stLayoutWrapper" div Streamlit inserts
    between the card and the column is also told to stretch (it defaults
    to auto/content-sized too, breaking the 100% chain otherwise); :has()
    scopes that fix to just these three wrappers, not every stLayoutWrapper
    on the page. */
    [data-testid="stLayoutWrapper"]:has(> .st-key-profile-summary-card),
    [data-testid="stLayoutWrapper"]:has(> .st-key-valuation-summary-card),
    [data-testid="stLayoutWrapper"]:has(> .st-key-perf-stats-col) {
        height: 100% !important;
    }
    .st-key-profile-summary-card, .st-key-valuation-summary-card, .st-key-perf-stats-col {
        padding-top: 20px !important;
        padding-bottom: 20px !important;
        height: 100% !important;
        box-sizing: border-box !important;
    }
    /* Player Profile as a premium summary card, not a dense list: each
    field below the name on its own line, no per-field caption label
    (self-descriptive via the flag/crest/units already inline). Gap between
    the name and the field rows widened to
    22px. Compound selector (no space) — the key class and the
    stVerticalBlock testid are on the same element here, not a
    parent/descendant pair. */
    .st-key-profile-summary-card[data-testid="stVerticalBlock"] { gap: 22px !important; }
    /* Market Valuation as a premium summary card, matching Player Profile's
    added breathing room: heading -> hero figure -> Actual/Difference/Value
    Ratio -> disclaimer caption all get even more room to separate, rather
    than reading as one dense block. Compound selector (no space) for the
    same reason as Player Profile's — the key class and stVerticalBlock
    testid land on the same element. */
    .st-key-valuation-summary-card[data-testid="stVerticalBlock"] { gap: 26px !important; }
    /* Hero figure for the valuation card: Model Estimated Value is the
    single most important number on this page (the model's own output),
    so it gets its own large line — Actual/Difference/Value Ratio follow
    underneath as a compact label/value list, not four equal-weight cards. */
    .valuation-hero-value {
        font-size: 2.25rem;
        font-weight: 600;
        line-height: 1.2;
        margin-top: 0.4rem;
        margin-bottom: 0.6rem;
    }
    .valuation-row {
        display: flex;
        justify-content: space-between;
        padding: 0.8rem 0;
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
        gap: 0.75rem;
        padding: 0.75rem 0;
        line-height: 1.5;
    }
    .profile-row-label {
        flex: 0 0 132px;
        color: var(--app-text-muted, rgba(250, 250, 250, 0.6));
    }
    /* Performance Statistics as a compact label/value table instead of a
    grid of bordered metric boxes — dense reference data (a dozen-plus
    stats per player) reads faster as a scannable table than as tiles, and
    it's what lets this column stay visually balanced with Player Profile/
    Market Valuation at equal column width. Each row gets the same
    right-aligned, subtle-separator treatment as the valuation card above,
    for a consistent look across the whole row. */
    .st-key-perf-stats-col .stat-table-row {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.25rem 0;
        border-top: 1px solid var(--app-border, rgba(250, 250, 250, 0.15));
    }
    .st-key-perf-stats-col .stat-table-label { color: var(--app-text-muted, rgba(250, 250, 250, 0.6)); }
    .st-key-perf-stats-col .stat-table-value {
        font-variant-numeric: tabular-nums;
        font-weight: 500;
        text-align: right;
        white-space: nowrap;
    }
    /* Tightened category-heading spacing so the table reads as one
    continuous, scannable block rather than several separated mini-cards.
    margin-bottom applies to every heading in this column, but margin-top
    is scoped to .stat-category-heading only (not the plain h3 rule) —
    applying it to every h3 here also pushed down the card-level "Statistics
    (24-25 Season)" heading itself, 10px lower than "Player Profile"/"Market
    Valuation"'s headings in the other two columns and breaking the
    three-column top alignment. */
    .st-key-perf-stats-col [data-testid="stVerticalBlock"] { gap: 4px !important; }
    .st-key-perf-stats-col h3 { margin-bottom: 0px !important; }
    /* Category headings (Shot Stopping, Distribution, Attacking, etc.) sized
    down a step below the card-level "Performance Statistics (2024-25
    Season)" heading, which stays at the same size as "Player Profile"/
    "Market Valuation". Rendered as a plain <h3 class="stat-category-heading">
    (not st.subheader()) specifically so this class can target them without
    touching that first, card-level heading — each st.subheader/markdown
    heading gets its own wrapper div, so a sibling-position selector
    (:not(:first-of-type)) can't tell them apart; a dedicated class can. */
    .stat-category-heading { font-size: 1.15rem !important; margin-top: 10px !important; }
    /* All Statistics can run to 6 categories / ~35 rows — far more than
    Model Features' 2 categories / 8-10 stats. Rather than let that grow
    this card (and, via the equal-height row, Player Profile/Market
    Valuation along with it), the stat rows scroll within a fixed-height
    region instead. 480px was chosen by measuring Model Features' own
    tallest case (FWD, 10 stats, renders at 466px) and adding headroom —
    so Model Features itself never reaches the scrollbar, confirmed via
    scrollHeight vs clientHeight, not assumed. */
    .stat-scroll-area {
        max-height: 480px;
        overflow-y: auto;
    }
    /* Segmented control sized down to match this card's compact scale —
    Streamlit's default is sized for full-width, standalone use. */
    .st-key-perf-stats-col [data-testid="stSegmentedControl"] button {
        padding: 0.25rem 0.75rem !important;
        font-size: 0.85rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

summary_cols = st.columns(3, gap="medium")
with summary_cols[0]:
    with st.container(border=True, key="profile-summary-card"):
        st.subheader("Player Profile")
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
        st.subheader("Market Valuation")

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

with summary_cols[2]:
    with st.container(border=True, key="perf-stats-col"):
        st.subheader("Performance Statistics (2024–25 Season)")
        if full_record is None:
            st.warning(f"No performance record found for **{player_name}** ({squad}) in merged_dataset_2425.")
        else:
            stats_view = st.segmented_control(
                "Statistics view",
                options=["Model Features", "All Statistics"],
                default="Model Features",
                label_visibility="collapsed",
                key="stats_view_toggle",
            )
            # segmented_control returns None if the user clicks the already-
            # selected option (deselecting it) — treated as staying on the
            # default rather than showing neither view.
            if not stats_view:
                stats_view = "Model Features"

            if stats_view == "Model Features":
                st.caption("Statistics used by the position-specific machine learning model.")
            else:
                st.caption(
                    "Complete 2024–25 seasonal statistics for player exploration. "
                    "These statistics were not necessarily used by the model."
                )

            # Fixed-height scroll region (not content-driven) so toggling to
            # the much longer All Statistics view can never grow this card
            # taller than Model Features already does — Profile/Valuation
            # sit in the same equal-height row (see the height:100% rule
            # above) and must stay unaffected by which view is selected.
            stats_rows_html = []
            if stats_view == "Model Features":
                for group_name, stats in config.POSITION_STAT_GROUPS[position]:
                    stats_rows_html.append(f'<h3 class="stat-category-heading">{group_name}</h3>')
                    for field, label, format_type in stats:
                        value = full_record.get(field)
                        if pd.isna(value):
                            display_value = "—"
                        elif format_type == "percent":
                            display_value = f"{value:.1f}%"
                        elif format_type == "count":
                            display_value = f"{value:,.0f}"
                        else:
                            display_value = f"{value:.2f}"
                        stats_rows_html.append(
                            f'<div class="stat-table-row">'
                            f'<span class="stat-table-label">{label}</span>'
                            f'<span class="stat-table-value">{display_value}</span>'
                            f"</div>"
                        )
            else:
                # All Statistics: every meaningful (non-null) stat across a
                # fixed set of football categories, regardless of position or
                # whether the model actually used that feature. A category is
                # dropped entirely if every field in it is null for this
                # player (e.g. Goalkeeping for an outfield player — verified
                # those columns are 100% null for non-keepers, not just
                # sparsely populated, so this never hides genuine data).
                for group_name, stats in config.ALL_STATS_GROUPS:
                    group_rows = []
                    for field, label, format_type in stats:
                        value = full_record.get(field)
                        if pd.isna(value):
                            continue
                        if format_type == "percent":
                            display_value = f"{value:.1f}%"
                        elif format_type == "count":
                            display_value = f"{value:,.0f}"
                        else:
                            display_value = f"{value:.2f}"
                        group_rows.append(
                            f'<div class="stat-table-row">'
                            f'<span class="stat-table-label">{label}</span>'
                            f'<span class="stat-table-value">{display_value}</span>'
                            f"</div>"
                        )
                    if group_rows:
                        stats_rows_html.append(f'<h3 class="stat-category-heading">{group_name}</h3>')
                        stats_rows_html.extend(group_rows)

            st.markdown(
                f'<div class="stat-scroll-area">{"".join(stats_rows_html)}</div>',
                unsafe_allow_html=True,
            )

st.divider()

# --- Comparable Players ---------------------------------------------------
# Reads the precomputed nearest-neighbour artifact (notebooks/
# 03_data_modelling.ipynb, Section 9) rather than computing similarity
# here — the neighbour search itself is unbiased and unchanged by this
# page; only which neighbour feeds the interpretive sentence below is
# selected here, and only for that sentence, never for the table (the
# table always shows all 5 real nearest neighbours regardless of league).
st.header("Comparable Players")
st.markdown(
    """
    <style>
    /* Tightened section rhythm: overview table -> "Compare with" selector
    -> comparison panel now read as one cohesive block instead of three
    visually separate sections. Scoped to this section's own keyed
    container (compound selector — the key class and stVerticalBlock
    testid land on the same element, same pattern used elsewhere on this
    page) so it doesn't touch spacing anywhere else. */
    .st-key-comparable-players-section[data-testid="stVerticalBlock"] {
        gap: 6px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
comparable_players_section = st.container(key="comparable-players-section")
with comparable_players_section:
    st.write(
        "Comparable players are identified using standardized performance, age, and "
        "playing-time metrics within the same position."
    )
    st.caption(
        "League, nationality/confederation, market value, contract length, and career "
        "stage are excluded from the similarity calculation."
    )

    comparable_players = load_comparable_players()
    selected_player_id = f"{player_name} — {squad}"
    comp_row = comparable_players[comparable_players["player_id"] == selected_player_id]

    if comp_row.empty:
        st.info(f"No comparable-players data available for **{player_name}** ({squad}).")
    else:
        comp_row = comp_row.iloc[0]
        neighbor_ids = [
            comp_row[col]
            for col in ("neighbor_1_id", "neighbor_2_id", "neighbor_3_id", "neighbor_4_id", "neighbor_5_id")
            if col in comp_row.index and pd.notna(comp_row[col])
        ]

        league_shap_by_player = get_league_shap_by_player(position)

        def _neighbor_details(neighbor_id: str):
            # comparable_players.csv builds player_id as "{Player} — {Squad}"
            # (em dash) — Squad names never contain that exact separator, so a
            # single split is unambiguous.
            n_name, n_squad = neighbor_id.split(" — ", 1)
            profile_match = players[
                (players["position"] == position) & (players["Player"] == n_name) & (players["Squad"] == n_squad)
            ]
            if profile_match.empty:
                return None
            profile_row = profile_match.iloc[0]
            bias_match = league_shap_by_player[
                (league_shap_by_player["Player"] == n_name) & (league_shap_by_player["Squad"] == n_squad)
            ]
            league_shap_log = bias_match.iloc[0]["league_shap_log"] if not bias_match.empty else None
            return {
                "name": n_name,
                "squad": n_squad,
                "league_raw": profile_row["Comp"],
                "actual_value_eur": profile_row["actual_value_eur"],
                "league_shap_log": league_shap_log,
            }

        RANK_LABELS = ["Closest Match", "2nd Closest", "3rd Closest", "4th Closest", "5th Closest"]

        ranked_neighbors = []
        for rank, neighbor_id in enumerate(neighbor_ids, start=1):
            details = _neighbor_details(neighbor_id)
            if details is not None:
                ranked_neighbors.append((rank, details))

        # Selected player's own league/SHAP figures — needed by both the detail
        # panel below and the cross-league sentence further down, so computed
        # once here rather than twice.
        selected_league_raw = player_row["Comp"]
        selected_bias_match = league_shap_by_player[
            (league_shap_by_player["Player"] == player_name) & (league_shap_by_player["Squad"] == squad)
        ]
        selected_league_shap_log = (
            selected_bias_match.iloc[0]["league_shap_log"] if not selected_bias_match.empty else None
        )

        comp_table = pd.DataFrame(
            [
                {
                    "Match Rank": RANK_LABELS[rank - 1],
                    "Player": details["name"],
                    "Club": details["squad"],
                    "League": config.friendly_league_label(details["league_raw"]),
                    "Actual Value": details["actual_value_eur"],
                }
                for rank, details in ranked_neighbors
            ]
        )

        # Note: st.dataframe's own row height (~35px, glide-data-grid
        # canvas-rendered) isn't reachable via CSS or a public per-row
        # height option in this Streamlit version — a shorter `height=`
        # here would only add a scrollbar over the same fixed row size,
        # not shrink the rows, so it's left at its default. The vertical
        # win in this section comes from the tightened gaps around the
        # table (see .st-key-comparable-players-section above) and the
        # comparison panel's own tighter row padding below.
        st.dataframe(
            comp_table,
            hide_index=True,
            width="stretch",
            column_config={
                "Actual Value": st.column_config.NumberColumn(format="€%,.0f"),
            },
        )

        # --- Detail panel: pick one of the 5 neighbours to compare in full ---
        # Keyed per selected-player so switching players resets any stale
        # comparison choice from a previous player's neighbour list, rather
        # than silently carrying an unrelated selection over.
        neighbor_options = [f"{details['name']} — {details['squad']}" for _, details in ranked_neighbors]
        chosen_label = st.selectbox(
            "Compare with",
            options=neighbor_options,
            index=None,
            placeholder="Select a comparable player to inspect in detail…",
            key=f"comparable_player_select_{selected_player_id}",
        )

        if not chosen_label:
            st.info("Select a comparable player above to compare their performance profile.")
        else:
            chosen_details = next(
                details
                for _, details in ranked_neighbors
                if f"{details['name']} — {details['squad']}" == chosen_label
            )

            selected_full_record = full_record
            comparable_full_record = get_player_full_record(
                chosen_details["name"], position, chosen_details["squad"]
            )

            def _format_stat(record, field, format_type):
                if record is None:
                    return None, "—"
                value = record.get(field)
                if pd.isna(value):
                    return None, "—"
                if format_type == "percent":
                    return value, f"{value:.1f}%"
                if format_type == "count":
                    return value, f"{value:,.0f}"
                return value, f"{value:.2f}"

            def _factual_display(record, field, formatter):
                if record is None:
                    return "—"
                value = record.get(field)
                if pd.isna(value):
                    return "—"
                return formatter(value)

            selected_league_label_detail = config.friendly_league_label(selected_league_raw)
            comparable_league_label = config.friendly_league_label(chosen_details["league_raw"])

            comparable_bias_match = league_shap_by_player[
                (league_shap_by_player["Player"] == chosen_details["name"])
                & (league_shap_by_player["Squad"] == chosen_details["squad"])
            ]
            comparable_league_shap_log = (
                comparable_bias_match.iloc[0]["league_shap_log"] if not comparable_bias_match.empty else None
            )
            selected_league_counterfactual_eur = (
                selected_bias_match.iloc[0]["league_counterfactual_eur"] if not selected_bias_match.empty else None
            )
            comparable_league_counterfactual_eur = (
                comparable_bias_match.iloc[0]["league_counterfactual_eur"]
                if not comparable_bias_match.empty
                else None
            )

            def _league_effect_cell(counterfactual_eur, shap_log):
                if counterfactual_eur is None or pd.isna(counterfactual_eur):
                    return '<span class="compare-value">—</span>'
                primary = f"€{counterfactual_eur:+,.0f}"
                secondary = f"{shap_log:+.3f} log-space" if shap_log is not None and not pd.isna(shap_log) else ""
                return (
                    f'<span class="compare-value">{primary}'
                    f'<span class="compare-value-secondary">{secondary}</span></span>'
                )

            rows_html = [
                '<div class="compare-row compare-row-header">'
                '<span class="compare-metric-label">Metric</span>'
                f'<span class="compare-value">{player_name}</span>'
                f'<span class="compare-value">{chosen_details["name"]}</span>'
                "</div>",
                '<div class="compare-row">'
                '<span class="compare-metric-label">League</span>'
                f'<span class="compare-value">{selected_league_label_detail}</span>'
                f'<span class="compare-value">{comparable_league_label}</span>'
                "</div>",
                '<div class="compare-row">'
                '<span class="compare-metric-label">Actual Value</span>'
                f'<span class="compare-value">€{player_row["actual_value_eur"]:,.0f}</span>'
                f'<span class="compare-value">€{chosen_details["actual_value_eur"]:,.0f}</span>'
                "</div>",
                '<div class="compare-row">'
                '<span class="compare-metric-label">League Effect</span>'
                f"{_league_effect_cell(selected_league_counterfactual_eur, selected_league_shap_log)}"
                f"{_league_effect_cell(comparable_league_counterfactual_eur, comparable_league_shap_log)}"
                "</div>",
                # Explanatory note sits directly beneath the League Effect row,
                # ahead of the causality disclaimer at the bottom of the panel
                # — this one clarifies why the euro figure isn't a simple
                # function of the log-space value alone, not whether the
                # effect is causal (that's the separate st.caption below).
                '<div class="compare-note">League Effect is shown in both euro and log-space terms. '
                "The euro-denominated contribution depends on each player's overall model estimate, "
                "so players in the same league may still display different euro contributions even "
                "when their underlying log-space SHAP values are similar.</div>",
                '<div class="compare-row">'
                '<span class="compare-metric-label">Age</span>'
                f'<span class="compare-value">'
                f'{_factual_display(selected_full_record, "age_precise", lambda v: f"{v:.0f} years")}</span>'
                f'<span class="compare-value">'
                f'{_factual_display(comparable_full_record, "age_precise", lambda v: f"{v:.0f} years")}</span>'
                "</div>",
                '<div class="compare-row">'
                '<span class="compare-metric-label">Contract Remaining (months)</span>'
                f'<span class="compare-value">'
                f'{_factual_display(selected_full_record, "contract_months_remaining", lambda v: f"{v:.0f}")}</span>'
                f'<span class="compare-value">'
                f'{_factual_display(comparable_full_record, "contract_months_remaining", lambda v: f"{v:.0f}")}</span>'
                "</div>",
            ]

            for field, label, format_type, lower_is_better in config.COMPARABLE_STAT_FIELDS[position]:
                selected_raw, selected_display = _format_stat(selected_full_record, field, format_type)
                comparable_raw, comparable_display = _format_stat(comparable_full_record, field, format_type)

                selected_cls = comparable_cls = ""
                if selected_raw is not None and comparable_raw is not None and selected_raw != comparable_raw:
                    selected_wins = (
                        selected_raw < comparable_raw if lower_is_better else selected_raw > comparable_raw
                    )
                    selected_cls = "compare-value-better" if selected_wins else ""
                    comparable_cls = "" if selected_wins else "compare-value-better"

                rows_html.append(
                    '<div class="compare-row">'
                    f'<span class="compare-metric-label">{label}</span>'
                    f'<span class="compare-value {selected_cls}">{selected_display}</span>'
                    f'<span class="compare-value {comparable_cls}">{comparable_display}</span>'
                    "</div>"
                )

            st.markdown(
                """
                <style>
                /* Comparison detail panel: same label/value row rhythm as the
                Performance Statistics table above (border-top separators,
                muted labels, tabular-nums values) rather than a nested card —
                a plain 3-column grid reads as one continuous panel instead of
                a table-within-a-table. Row padding tightened (was 0.5rem) so
                the panel reads as compact rather than airy, matching the
                rest of this section. */
                .compare-row {
                    display: grid;
                    grid-template-columns: 1.2fr 1fr 1fr;
                    gap: 0.75rem;
                    padding: 0.3rem 0;
                    border-top: 1px solid var(--app-border, rgba(250, 250, 250, 0.15));
                    align-items: center;
                }
                .compare-row-header {
                    border-top: none;
                    padding-bottom: 0.4rem;
                    color: var(--app-text-muted, rgba(250, 250, 250, 0.6));
                    font-size: 0.85rem;
                }
                .compare-metric-label { color: var(--app-text-muted, rgba(250, 250, 250, 0.6)); }
                .compare-value {
                    font-variant-numeric: tabular-nums;
                    text-align: right;
                }
                .compare-value-better { font-weight: 700; }
                .compare-value-secondary {
                    display: block;
                    font-size: 0.75rem;
                    font-weight: 400;
                    color: var(--app-text-muted, rgba(250, 250, 250, 0.55));
                    margin-top: 0.1rem;
                }
                /* League Effect explanatory note — no border/label columns,
                just a short muted line spanning the panel's own width. */
                .compare-note {
                    font-size: 0.75rem;
                    line-height: 1.45;
                    color: var(--app-text-muted, rgba(250, 250, 250, 0.55));
                    padding: 0.15rem 0 0.4rem 0;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("".join(rows_html), unsafe_allow_html=True)
            st.caption(
                "League Effect reflects the model-attributed contribution of league affiliation after "
                "accounting for observed player performance. It should not be interpreted as a causal effect."
            )

        # Interpretive sentence: first cross-league neighbour in rank order
        # (neighbor_1 checked first, since ranked_neighbors preserves rank
        # order), or omitted entirely if all 5 share the selected player's
        # league. This selection only decides which neighbour's numbers appear
        # in the sentence — it has no effect on the table above.
        cross_league_neighbor = next(
            (details for _, details in ranked_neighbors if details["league_raw"] != selected_league_raw),
            None,
        )

        if (
            cross_league_neighbor is not None
            and selected_league_shap_log is not None
            and cross_league_neighbor["league_shap_log"] is not None
        ):
            cross_league_neighbor_league = config.friendly_league_label(cross_league_neighbor["league_raw"])
            selected_league_label = config.friendly_league_label(selected_league_raw)
            st.markdown(
                f"**Cross-league insight:** {cross_league_neighbor['name']} has one of the closest "
                f"performance profiles to {player_name}. The model attributes different league "
                f"contributions ({cross_league_neighbor_league}: {cross_league_neighbor['league_shap_log']:+.3f} "
                f"vs {selected_league_label}: {selected_league_shap_log:+.3f})."
            )

st.divider()

# --- Transfer Value History ----------------------------------------------
st.header("Transfer Value History")
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
    st.plotly_chart(fig, width="stretch", key="valuation_history_chart")

st.divider()

# --- Why did the model estimate this value? -----------------------------
# Waterfall (left) and Top Positive/Negative Contributors (right, stacked)
# merged into one two-column row rather than two stacked full-width
# sections — they're explaining the same SHAP breakdown from two angles
# (visual + tabular), so reading them side by side needs less scrolling
# and reads as one analysis instead of two separate ones.
st.header("Why did the model estimate this value?")
st.write(
    "SHAP values show how each feature increased (red) or decreased (blue) the "
    "model's estimated value for this player, together producing the final estimate."
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

contributions = pd.Series(shap_row["shap_values"], index=feature_labels).sort_values(ascending=False)
top_positive = contributions.head(5)
top_negative = contributions.tail(5).sort_values()

st.markdown(
    """
    <style>
    /* The contributor tables (stacked) are much shorter than the tall
    waterfall figure beside them — center them vertically in the row
    instead of leaving all the leftover space stranded below them. */
    .st-key-shap-row [data-testid="stHorizontalBlock"] { align-items: center; }
    /* Tight, consistent gap between the two stacked tables (and between
    each table and its label above it) so the pair reads as one panel
    rather than two loosely related blocks. */
    .st-key-shap-row [data-testid="stVerticalBlock"] { gap: 6px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="shap-row"):
    # 55/45 — widened from the prior 50/50 per feedback that the
    # contributor column felt cramped, while keeping the waterfall as the
    # dominant element rather than an even split.
    waterfall_col, contrib_col = st.columns([55, 45])
    with waterfall_col:
        with st.spinner("Loading SHAP explanation…"):
            fig = plt.figure()
            shap.plots.waterfall(explanation, max_display=15, show=False)
            st.pyplot(fig, clear_figure=True)
        # No caption here any more — it only restated what the paragraph
        # above the two columns already says (this chart is the SHAP-based
        # explanation), and unlike the SHAP_EUR_CAVEAT's other uses
        # elsewhere (e.g. league/confederation contribution cards), no EUR
        # figure appears on this chart for the caveat to actually qualify.
    with contrib_col:
        st.markdown("**Top Positive Contributors**")
        st.dataframe(top_positive.rename("SHAP value (log-space)").to_frame(), width="stretch")
        st.markdown("**Top Negative Contributors**")
        st.dataframe(top_negative.rename("SHAP value (log-space)").to_frame(), width="stretch")