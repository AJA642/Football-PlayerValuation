import base64
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from lib import config


def _fail(path: Path, error: Exception):
    st.error(f"Failed to load required artefact: `{path}`\n\n{error}")
    st.stop()


@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as e:  # noqa: BLE001 - surfaced to the user via st.error
        _fail(path, e)


@st.cache_resource(show_spinner=False)
def load_shap(position: str) -> dict:
    suffix = config.POSITION_FILE_SUFFIX[position]
    path = config.SHAP_DIR / f"shap_values_{suffix}.pkl"
    try:
        return joblib.load(path)
    except Exception as e:  # noqa: BLE001
        _fail(path, e)


def load_results_summary() -> pd.DataFrame:
    return load_csv(config.RESULTS_SUMMARY_CSV)


def load_ablation_results() -> pd.DataFrame:
    return load_csv(config.ABLATION_RESULTS_CSV)


def load_merged_dataset() -> pd.DataFrame:
    return load_csv(config.MERGED_DATASET_CSV)


def load_dashboard_predictions() -> pd.DataFrame:
    return load_csv(config.DASHBOARD_PREDICTIONS_CSV)


def load_bias_summary_league() -> pd.DataFrame:
    return load_csv(config.BIAS_SUMMARY_LEAGUE_CSV)


def load_bias_summary_confederation() -> pd.DataFrame:
    return load_csv(config.BIAS_SUMMARY_CONFEDERATION_CSV)


def load_per_player_bias() -> pd.DataFrame:
    return load_csv(config.PER_PLAYER_BIAS_CSV)


def load_diagnostics_summary() -> pd.DataFrame:
    return load_csv(config.DIAGNOSTICS_SUMMARY_CSV)


def load_comparable_players() -> pd.DataFrame:
    return load_csv(config.COMPARABLE_PLAYERS_CSV)


@st.cache_data(show_spinner=False)
def get_league_shap_by_player(position: str) -> pd.DataFrame:
    """Per-player league SHAP contribution (log-space) and its euro
    counterfactual for one position, with Squad attached so a comparable-
    player row (identified by Player+Squad, per comparable_players.csv) can
    look up its own league contribution. per_player_bias.csv has no Squad
    of its own and ~50 rows share a (Player, position) pair (mid-season
    transfers), so Squad is joined back on via the same occurrence-index
    pairing Bias Explorer's Individual Player Breakdown already uses for
    the identical problem.

    league_counterfactual_eur is read directly from per_player_bias.csv
    (computed in notebooks/03_data_modelling.ipynb's aggregate_bias via
    re-predicting each player with their league one-hot features zeroed
    out, then back-transforming both predictions from log-space and
    differencing in euro-space) — never derived here by exponentiating
    league_shap_log directly, which would not equal the same figure."""
    bias = load_per_player_bias()
    bias = bias[bias["position"] == position]
    bias = add_occurrence_index(bias, ["Player", "position"])

    profile = load_predictions_with_profile()
    profile = profile[profile["position"] == position]
    profile = add_occurrence_index(profile, ["Player", "position"])

    merged = bias.merge(
        profile[["Player", "position", "_occurrence", "Squad"]],
        on=["Player", "position", "_occurrence"],
        how="left",
    )
    return merged[["Player", "Squad", "league", "league_shap_log", "league_counterfactual_eur"]]


def add_occurrence_index(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Tags each row with its occurrence index within its own `group_cols`
    group (e.g. (Player, position)) as a new `_occurrence` column, on a copy
    of `df`. Lets duplicate-keyed rows — e.g. a player transferred mid-season
    has two rows for the same position — be joined Nth-occurrence-to-Nth-
    occurrence across two files that share no player ID, instead of
    cross-joining and inflating the row count. Exact for the common
    single-row case; a stable (if unverifiable) pairing for genuine
    duplicates."""
    df = df.copy()
    df["_occurrence"] = df.groupby(group_cols).cumcount()
    return df


@st.cache_data(show_spinner=False)
def load_predictions_with_profile() -> pd.DataFrame:
    """`dashboard/df_predictions.csv` joined with player profile columns
    (Squad, Comp, age_precise, Min_playing_time) from merged_dataset_2425.

    Some (Player, position) pairs are not unique — a handful of players
    were transferred mid-season and have two rows (e.g. Kyle Walker, DEF,
    at both Manchester City and Milan). Neither file carries a shared
    player ID, so a plain merge on (Player, position) would cross-join
    those pairs and inflate the row count. Instead each duplicate's
    occurrence order within its own file is used as an extra join key
    (see `add_occurrence_index`), pairing the Nth duplicate in one file
    with the Nth duplicate in the other — exact for the ~98% of players
    with a single row, and a stable (if unverifiable) pairing for the rest.
    """
    predictions = add_occurrence_index(load_dashboard_predictions(), ["Player", "position"])
    merged = add_occurrence_index(load_merged_dataset(), ["Player", "position_group"])

    profile_columns = [
        "Player",
        "position_group",
        "_occurrence",
        "Squad",
        "Comp",
        "age_precise",
        "Min_playing_time",
        "country_of_citizenship",
        "confederation",
        "foot",
    ]
    joined = predictions.merge(
        merged[profile_columns],
        left_on=["Player", "position", "_occurrence"],
        right_on=["Player", "position_group", "_occurrence"],
        how="left",
    )
    return joined.drop(columns=["_occurrence", "position_group"])


@st.cache_data(show_spinner=False)
def get_position_base_value(position: str) -> float:
    """The SHAP base value (expected log-market-value) for a position's model.

    Not stored in the saved artefacts. The additive property of SHAP values
    means, for any row, base_value = model_output_log - sum(shap_values).
    model_output_log is recovered from the saved `predicted_value_eur` via
    ln(), since the training target was log_market_value = ln(market value)
    (verified against merged_dataset_2425's own log_market_value column).
    base_value is a single dataset-level constant, so it's derived from a
    sample of rows and averaged to smooth out floating-point noise, rather
    than trusting any one row. No SHAP values are recomputed.
    """
    shap_obj = load_shap(position)
    lookup = shap_obj["lookup"]
    shap_values = shap_obj["shap_values"]
    predictions = load_dashboard_predictions()
    predictions = predictions[predictions["position"] == position]

    sample_size = min(50, len(lookup))
    implied_bases = []
    for i in range(sample_size):
        player = lookup.iloc[i]["Player"]
        squad = lookup.iloc[i]["Squad"]
        match = predictions[predictions["Player"] == player]
        if len(match) != 1:
            continue
        y_pred_log = np.log(match.iloc[0]["predicted_value_eur"])
        implied_bases.append(y_pred_log - shap_values[i].sum())
    return float(np.mean(implied_bases))


def get_player_shap_row(position: str, player: str, squad: str) -> dict | None:
    """SHAP values for one player, matched by (Player, Squad) in that
    position's saved `lookup` — verified unique within each position."""
    shap_obj = load_shap(position)
    lookup = shap_obj["lookup"]
    match = lookup[(lookup["Player"] == player) & (lookup["Squad"] == squad)]
    if match.empty:
        return None
    idx = match.index[0]
    return {"shap_values": shap_obj["shap_values"][idx], "X_columns": shap_obj["X_columns"]}


def get_player_full_record(player: str, position: str, squad: str) -> pd.Series | None:
    """A player's full row from merged_dataset_2425, matched exactly by
    (Player, position, Squad) — unambiguous once Squad is known, unlike the
    bulk join in `load_predictions_with_profile` which can't use Squad
    since it isn't yet available on the predictions side at that point."""
    merged = load_merged_dataset()
    match = merged[
        (merged["Player"] == player) & (merged["position_group"] == position) & (merged["Squad"] == squad)
    ]
    if match.empty:
        return None
    return match.iloc[0]


@st.cache_data(show_spinner=False)
def load_player_valuations() -> pd.DataFrame:
    """Raw Transfermarkt valuation history, one row per valuation event
    across ~656k rows for all players (not just this project's ~2,061).
    Keyed by `player_id` (Transfermarkt ID) — the same ID present in
    merged_dataset_2425 as `player_id_tm`/`tm_player_id` (verified: 100% of
    merged_dataset_2425's player_id_tm values exist in this file's
    player_id column)."""
    return load_csv(config.PLAYER_VALUATIONS_CSV)


def get_player_valuation_history(player_id_tm: int) -> pd.DataFrame:
    """A single player's market value history, sorted chronologically and
    cut off at config.VALUATION_HISTORY_CUTOFF (the models are trained on
    2024-25 data only, so later valuations are excluded rather than shown
    alongside a model estimate they couldn't have informed). Returns an
    empty DataFrame if the player has no valuation history at all, or none
    before the cutoff — the caller is responsible for the "no data" message,
    this function only filters."""
    valuations = load_player_valuations()
    history = valuations[valuations["player_id"] == player_id_tm][["date", "market_value_in_eur"]].copy()
    history["date"] = pd.to_datetime(history["date"])
    history = history[history["date"] <= pd.Timestamp(config.VALUATION_HISTORY_CUTOFF)]
    return history.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def get_club_logo_data_uri(squad: str) -> str | None:
    """A club's crest as a base64 data URI, ready to drop straight into an
    `<img src=...>`, or None if unavailable — callers must fall back to
    text-only (a missing crest is expected for any Squad not in
    config.CLUB_LOGO_IDS, and is never an error).

    Reads a local file only; no network request happens here or anywhere
    else in the running app. The files themselves (data/processed/
    club_logos/{club_id}.png) were downloaded once from Transfermarkt's own
    CDN by a one-time data-prep script, the same way every other processed/
    artefact in this project was produced ahead of time rather than
    fetched live."""
    club_id = config.CLUB_LOGO_IDS.get(squad)
    if club_id is None:
        return None
    path = config.CLUB_LOGOS_DIR / f"{club_id}.png"
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def require_image(path: Path) -> str:
    if not path.exists():
        _fail(path, FileNotFoundError("Image file not found"))
    return str(path)
