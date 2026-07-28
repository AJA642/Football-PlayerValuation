import plotly.express as px
import streamlit as st

from lib import config
from lib.components import balance_section_spacing, render_header, stat_card
from lib.data_loader import (
    load_bias_summary_confederation,
    load_bias_summary_league,
    load_per_player_bias,
    load_predictions_with_profile,
)

st.set_page_config(
    page_title="Bias Explorer", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed"
)
render_header(active="Bias Explorer")
balance_section_spacing()
st.title("Bias Explorer")

SMALL_SAMPLE_THRESHOLD = 20

st.write(
    "This page explores how league affiliation and nationality/confederation "
    "contributed to the model's estimated market values after accounting for "
    "player performance and the other variables included in the model."
)

league_summary = load_bias_summary_league()
confed_summary = load_bias_summary_confederation()

# The Position filter sits inline with the "League Bias" heading (left
# heading, right dropdown, one row) rather than in its own bordered box with
# a divider before the chart — it's the only control on the page, so a
# separate panel for it was more chrome than the control needed. It's
# rendered once, up front, because its value also drives the Confederation
# Bias chart further down the page.
header_col, filter_col = st.columns([4, 1])
with header_col:
    st.header("League Bias")
with filter_col:
    position_filter = st.selectbox(
        "Position",
        ["All"] + config.POSITIONS,
        index=0,
        label_visibility="collapsed",
        format_func=config.friendly_position_label,
    )

if position_filter != "All":
    league_view = league_summary[league_summary["position"] == position_filter].copy()
    confed_view = confed_summary[confed_summary["position"] == position_filter].copy()
else:
    league_view = league_summary.copy()
    confed_view = confed_summary.copy()

league_view["league_label"] = league_view["league"].map(config.friendly_league_label)
confed_view["confederation_label"] = confed_view["confederation"]


def render_bias_chart(df, category_col, category_label_col, key):
    df = df.copy()
    # Sample size moves into the hover tooltip only (not always-visible bar
    # labels) — with "All" positions selected, four grouped bars per league
    # each carrying their own text label overlapped and became unreadable.
    df["sample_note"] = df["n_players"].apply(
        lambda n: f"n={n} (small sample)" if n < SMALL_SAMPLE_THRESHOLD else f"n={n}"
    )
    if position_filter == "All":
        df = df.sort_values([category_label_col, "position"])
        fig = px.bar(
            df,
            x="mean_shap_log",
            y=category_label_col,
            color="position",
            orientation="h",
            barmode="group",
            category_orders={"position": config.POSITIONS},
            custom_data=["mean_counterfactual_eur", "sample_note"],
        )
    else:
        df = df.sort_values("mean_shap_log")
        fig = px.bar(
            df,
            x="mean_shap_log",
            y=category_label_col,
            orientation="h",
            custom_data=["mean_counterfactual_eur", "sample_note"],
        )
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>Mean SHAP Contribution (log-space): %{x:.3f}<br>"
            f"{config.SHAP_EUR_CAVEAT}: "
            "€%{customdata[0]:,.0f}<br>%{customdata[1]}<extra></extra>"
        ),
    )
    fig.update_layout(
        xaxis_title="Mean SHAP Contribution (log-space)",
        yaxis_title="",
        margin=dict(l=0, r=0, t=10, b=0),
        # Capped as well as floored — with "All" positions grouping 4 bars
        # per category, this scaled unbounded for large category counts;
        # readability doesn't need more than ~450px even then.
        height=min(450, max(280, 45 * df[category_label_col].nunique())),
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# --- League Bias ---------------------------------------------------------
# Heading already rendered above, inline with the Position filter.
render_bias_chart(league_view, "league", "league_label", key="league_bias_chart")
st.caption(
    f"Bar length: Mean SHAP Contribution (log-space). Hover for the {config.SHAP_EUR_CAVEAT.lower()} "
    "and sample size."
)
st.caption(
    "Positive values indicate that league affiliation increased the model's estimated market value "
    "after accounting for observed player performance."
)

st.divider()

# --- Confederation Bias ---------------------------------------------------
st.header("Confederation Bias")
render_bias_chart(confed_view, "confederation", "confederation_label", key="confed_bias_chart")
st.caption(
    f"Bar length: Mean SHAP Contribution (log-space). Hover for the {config.SHAP_EUR_CAVEAT.lower()} "
    "and sample size."
)

st.divider()

# --- Insight Card ---------------------------------------------------------
st.header("Insight")
position_desc = "all positions" if position_filter == "All" else f"{position_filter} players"

strongest_league = league_view.loc[league_view["mean_shap_log"].abs().idxmax()]
strongest_confed = confed_view.loc[confed_view["mean_shap_log"].abs().idxmax()]

league_direction = "boosted" if strongest_league["mean_shap_log"] > 0 else "reduced"
confed_direction = "boosted" if strongest_confed["mean_shap_log"] > 0 else "reduced"
league_name = strongest_league["league_label"]
confed_name = strongest_confed["confederation_label"]
league_position_note = f" ({strongest_league['position']})" if position_filter == "All" else ""
confed_position_note = f" ({strongest_confed['position']})" if position_filter == "All" else ""

st.info(
    f"For {position_desc}, **{league_name}**{league_position_note} showed the strongest league "
    f"effect — model estimates were {league_direction} by "
    f"{abs(strongest_league['mean_shap_log']):.3f} (log-space, n={strongest_league['n_players']}). "
    f"**{confed_name}**{confed_position_note} showed the strongest confederation effect, "
    f"{confed_direction} by {abs(strongest_confed['mean_shap_log']):.3f} "
    f"(log-space, n={strongest_confed['n_players']})."
)

st.divider()

# --- Individual Player Breakdown ------------------------------------------
st.header("Individual Player Breakdown")

per_player_bias = load_per_player_bias().copy()
players = load_predictions_with_profile().copy()

# Around 100 rows share a (Player, position) pair (players transferred
# mid-season, e.g. Kyle Walker DEF at both Manchester City and Milan).
# Neither file has a shared player ID, so pair each duplicate's occurrence
# order within its own file — same approach as load_predictions_with_profile.
per_player_bias["_occurrence"] = per_player_bias.groupby(["Player", "position"]).cumcount()
players["_occurrence"] = players.groupby(["Player", "position"]).cumcount()

player_pool = per_player_bias.merge(
    players[["Player", "position", "Squad", "_occurrence"]],
    on=["Player", "position", "_occurrence"],
    how="left",
).drop(columns=["_occurrence"]).sort_values("Player")
player_pool["_label"] = (
    player_pool["Player"] + " — " + player_pool["Squad"].fillna("Unknown Club") + " (" + player_pool["position"] + ")"
)

selected_label = st.selectbox("Search player (name or club)", player_pool["_label"].tolist())
player_row = player_pool[player_pool["_label"] == selected_label].iloc[0]

breakdown_cols = st.columns(4)
with breakdown_cols[0]:
    stat_card("League Contribution (log-space)", f"{player_row['league_shap_log']:.3f}")
with breakdown_cols[1]:
    stat_card(
        "League Contribution (€)",
        f"€{player_row['league_counterfactual_eur']:+,.0f}",
        help_text=config.SHAP_EUR_CAVEAT,
    )
with breakdown_cols[2]:
    stat_card("Confederation Contribution (log-space)", f"{player_row['confed_shap_log']:.3f}")
with breakdown_cols[3]:
    stat_card(
        "Confederation Contribution (€)",
        f"€{player_row['confed_counterfactual_eur']:+,.0f}",
        help_text=config.SHAP_EUR_CAVEAT,
    )
st.caption(
    f"League: {config.friendly_league_label(player_row['league'])} · "
    f"Confederation: {player_row['confederation']}"
)
