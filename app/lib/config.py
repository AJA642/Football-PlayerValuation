from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DASHBOARD_DIR = DATA_PROCESSED / "dashboard"
MODELS_DIR = DATA_PROCESSED / "models"
SHAP_DIR = DATA_PROCESSED / "shap_values"
FIGURES_DIR = DATA_PROCESSED / "figures"
CLUB_LOGOS_DIR = DATA_PROCESSED / "club_logos"

POSITIONS = ["FWD", "MID", "DEF", "GK"]
POSITION_FILE_SUFFIX = {"FWD": "fwd", "MID": "mid", "DEF": "def", "GK": "gk"}

RESULTS_SUMMARY_CSV = DATA_PROCESSED / "results_summary.csv"
ABLATION_RESULTS_CSV = DATA_PROCESSED / "ablation_results.csv"
MERGED_DATASET_CSV = DATA_PROCESSED / "merged_dataset_2425.csv"

DASHBOARD_PREDICTIONS_CSV = DASHBOARD_DIR / "df_predictions.csv"
BIAS_SUMMARY_LEAGUE_CSV = DASHBOARD_DIR / "bias_summary_league.csv"
BIAS_SUMMARY_CONFEDERATION_CSV = DASHBOARD_DIR / "bias_summary_confederation.csv"
PER_PLAYER_BIAS_CSV = DASHBOARD_DIR / "per_player_bias.csv"
DIAGNOSTICS_SUMMARY_CSV = DASHBOARD_DIR / "diagnostics_summary.csv"
COMPARABLE_PLAYERS_CSV = DASHBOARD_DIR / "comparable_players.csv"

PLAYER_VALUATIONS_CSV = DATA_RAW / "transfermarkt" / "player_valuations.csv"
# The models are trained on 2024-25 season data only. player_valuations.csv
# extends well past that (observed up to 2026), so any 2025-26+ valuation is
# excluded from the Transfer Value History chart to avoid implying the model
# saw performance/value data it didn't.
VALUATION_HISTORY_CUTOFF = "2025-06-30"

MODEL_ESTIMATED_VALUE_LABEL = "Model Estimated Value"
SHAP_EUR_CAVEAT = "Model-derived estimate (SHAP-based contribution)"

# Raw league values appear in two different formats across the artefacts:
# underscore-separated in bias_summary_league.csv / per_player_bias.csv
# (e.g. "eng_Premier_League"), and space-separated with a country-code
# prefix in merged_dataset_2425 / df_predictions's "Comp" column (e.g.
# "eng Premier League"). Both map to the same clean display names.
# Confederation values in the bias CSVs (AFC, CAF, CONCACAF, CONMEBOL, OFC,
# UEFA) are already clean and need no mapping.
LEAGUE_LABELS = {
    "de_Bundesliga": "Bundesliga",
    "de Bundesliga": "Bundesliga",
    "eng_Premier_League": "Premier League",
    "eng Premier League": "Premier League",
    "es_La_Liga": "La Liga",
    "es La Liga": "La Liga",
    "fr_Ligue_1": "Ligue 1",
    "fr Ligue 1": "Ligue 1",
    "it_Serie_A": "Serie A",
    "it Serie A": "Serie A",
}


def friendly_league_label(raw_name: str) -> str:
    return LEAGUE_LABELS.get(raw_name, raw_name.replace("_", " ").strip())


# Display-only expansion for Position *filter* dropdowns/multiselects — not
# for player search results, table columns, metric cards, chart legends/axes,
# or any underlying data value, all of which keep the raw "FWD"/"MID"/"DEF"/
# "GK" codes.
POSITION_LABELS = {
    "FWD": "Forward (FWD)",
    "MID": "Midfielder (MID)",
    "DEF": "Defender (DEF)",
    "GK": "Goalkeeper (GK)",
}


def friendly_position_label(raw_position: str) -> str:
    return POSITION_LABELS.get(raw_position, raw_position)


# Full position name with no "(CODE)" suffix — for the Player Profile card
# only, where "Midfielder" reads better than "Midfielder (MID)" or "MID".
# Distinct from POSITION_LABELS (filter dropdowns only, per that feature's
# own explicit scope) so changing one can't accidentally change the other.
POSITION_NAMES = {
    "FWD": "Forward",
    "MID": "Midfielder",
    "DEF": "Defender",
    "GK": "Goalkeeper",
}


# Squad (short name, as it appears in merged_dataset_2425/predictions) ->
# Transfermarkt club_id, for the Player Profile's club crest. This project
# already uses Transfermarkt as its data source (data/raw/transfermarkt/),
# so its own club_id — not a new external key — is the join target. Built
# once by matching every Squad against data/raw/transfermarkt/clubs.csv
# (filtered to the Big 5 leagues' competition_ids), normalising punctuation/
# accents for the ~85 that matched cleanly, and hand-resolving the rest
# (short names like "Wolves"/"Man Utd", accented names, and two genuine
# ambiguities — "Milan" and "Barcelona" each have a same-city rival also in
# clubs.csv, resolved to the correct one). Covers all 96 clubs that appear
# in the dataset — verified via a one-time script, not derived at runtime.
# The crests themselves are downloaded once from Transfermarkt's own CDN
# (https://tmssl.akamaized.net/images/wappen/head/{club_id}.png) and stored
# locally under CLUB_LOGOS_DIR, so the running app makes no network calls.
CLUB_LOGO_IDS = {
    "Alavés": 1108,
    "Angers": 1420,
    "Arsenal": 11,
    "Aston Villa": 405,
    "Atalanta": 800,
    "Athletic Club": 621,
    "Atlético Madrid": 13,
    "Augsburg": 167,
    "Auxerre": 290,
    "Barcelona": 131,
    "Bayern Munich": 27,
    "Betis": 150,
    "Bochum": 80,
    "Bologna": 1025,
    "Bournemouth": 989,
    "Brentford": 1148,
    "Brest": 3911,
    "Brighton": 1237,
    "Cagliari": 1390,
    "Celta Vigo": 940,
    "Chelsea": 631,
    "Como": 1047,
    "Crystal Palace": 873,
    "Dortmund": 16,
    "Eint Frankfurt": 24,
    "Empoli": 749,
    "Espanyol": 714,
    "Everton": 29,
    "Fiorentina": 430,
    "Freiburg": 60,
    "Fulham": 931,
    "Genoa": 252,
    "Getafe": 3709,
    "Girona": 12321,
    "Gladbach": 18,
    "Heidenheim": 2036,
    "Hellas Verona": 276,
    "Hoffenheim": 533,
    "Holstein Kiel": 269,
    "Inter": 46,
    "Ipswich Town": 677,
    "Juventus": 506,
    "Las Palmas": 472,
    "Lazio": 398,
    "Le Havre": 738,
    "Lecce": 1005,
    "Leganés": 1244,
    "Leicester City": 1003,
    "Lens": 826,
    "Leverkusen": 15,
    "Lille": 1082,
    "Liverpool": 31,
    "Lyon": 1041,
    "Mainz 05": 39,
    "Mallorca": 237,
    "Manchester City": 281,
    "Manchester Utd": 985,
    "Marseille": 244,
    "Milan": 5,
    "Monaco": 162,
    "Montpellier": 969,
    "Monza": 2919,
    "Nantes": 995,
    "Napoli": 6195,
    "Newcastle Utd": 762,
    "Nice": 417,
    "Nott'ham Forest": 703,
    "Osasuna": 331,
    "Paris S-G": 583,
    "Parma": 130,
    "RB Leipzig": 23826,
    "Rayo Vallecano": 367,
    "Real Madrid": 418,
    "Real Sociedad": 681,
    "Reims": 1421,
    "Rennes": 273,
    "Roma": 12,
    "Saint-Étienne": 618,
    "Sevilla": 368,
    "Southampton": 180,
    "St. Pauli": 35,
    "Strasbourg": 667,
    "Stuttgart": 79,
    "Torino": 416,
    "Tottenham": 148,
    "Toulouse": 415,
    "Udinese": 410,
    "Union Berlin": 89,
    "Valencia": 1049,
    "Valladolid": 366,
    "Venezia": 607,
    "Villarreal": 1050,
    "Werder Bremen": 86,
    "West Ham": 379,
    "Wolfsburg": 82,
    "Wolves": 543,
}


# country_of_citizenship (raw name, as it appears in merged_dataset_2425) ->
# ISO 3166-1 alpha-2 code, for the Player Profile's nationality flag.
# Generated once against every nationality actually present in the dataset
# using pycountry (a maintained ISO 3166 database — installed temporarily
# purely to build this table, not a runtime dependency of the app) and
# hand-resolved for the handful of names that aren't sovereign-state ISO
# entries: England/Scotland/Wales use their ISO 3166-2 *subdivision* codes
# (rendered as a Unicode "tag sequence" flag, not a plain two-letter one —
# see flag_emoji() in components.py); Kosovo uses "XK", a user-assigned
# code with a widely-supported (if unofficial) flag emoji; Northern Ireland
# has no registered flag emoji at all, so it's left unmapped — the caller
# falls back to plain text, exactly as it would for any lookup miss.
COUNTRY_FLAG_CODES = {
    "Albania": "AL",
    "Algeria": "DZ",
    "Angola": "AO",
    "Argentina": "AR",
    "Armenia": "AM",
    "Australia": "AU",
    "Austria": "AT",
    "Belgium": "BE",
    "Benin": "BJ",
    "Bosnia-Herzegovina": "BA",
    "Brazil": "BR",
    "Burkina Faso": "BF",
    "Burundi": "BI",
    "Cameroon": "CM",
    "Canada": "CA",
    "Cape Verde": "CV",
    "Central African Republic": "CF",
    "Chile": "CL",
    "Colombia": "CO",
    "Congo": "CG",
    "Cote d'Ivoire": "CI",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czech Republic": "CZ",
    "DR Congo": "CD",
    "Denmark": "DK",
    "Dominican Republic": "DO",
    "Ecuador": "EC",
    "Egypt": "EG",
    "England": "GB-ENG",
    "Equatorial Guinea": "GQ",
    "Estonia": "EE",
    "Finland": "FI",
    "France": "FR",
    "French Guiana": "GF",
    "Gabon": "GA",
    "Georgia": "GE",
    "Germany": "DE",
    "Ghana": "GH",
    "Greece": "GR",
    "Guadeloupe": "GP",
    "Guinea": "GN",
    "Guinea-Bissau": "GW",
    "Haiti": "HT",
    "Hungary": "HU",
    "Iceland": "IS",
    "Indonesia": "ID",
    "Iran": "IR",
    "Ireland": "IE",
    "Israel": "IL",
    "Italy": "IT",
    "Jamaica": "JM",
    "Japan": "JP",
    "Kenya": "KE",
    "Korea, South": "KR",
    "Kosovo": "XK",
    "Libya": "LY",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Madagascar": "MG",
    "Malaysia": "MY",
    "Mali": "ML",
    "Malta": "MT",
    "Mauritania": "MR",
    "Mexico": "MX",
    "Montenegro": "ME",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Netherlands": "NL",
    "New Caledonia": "NC",
    "New Zealand": "NZ",
    "Niger": "NE",
    "Nigeria": "NG",
    "North Macedonia": "MK",
    "Northern Ireland": None,
    "Norway": "NO",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines": "PH",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Russia": "RU",
    "Scotland": "GB-SCT",
    "Senegal": "SN",
    "Serbia": "RS",
    "Sierra Leone": "SL",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Spain": "ES",
    "Suriname": "SR",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syria": "SY",
    "The Gambia": "GM",
    "Tunisia": "TN",
    "Türkiye": "TR",
    "Ukraine": "UA",
    "United Arab Emirates": "AE",
    "United States": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Venezuela": "VE",
    "Wales": "GB-WLS",
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
}


def diagnostics_png_path(position: str) -> Path:
    return FIGURES_DIR / f"diagnostics_{POSITION_FILE_SUFFIX[position]}.png"


# The three diagnostic panels (Predicted vs Actual, Residuals vs Predicted,
# Residual Distribution) notebook 3 now saves individually rather than as
# one combined 1x3 image, so they can be shown stacked vertically in the
# dashboard's own Diagnostics panel rather than as a single wide strip.
DIAGNOSTIC_PANELS = [
    ("pred_vs_actual", "Predicted vs Actual"),
    ("residuals_vs_predicted", "Residuals vs Predicted"),
    ("residual_dist", "Residual Distribution"),
]


def diagnostic_panel_png_path(position: str, panel: str) -> Path:
    return FIGURES_DIR / f"diagnostics_{POSITION_FILE_SUFFIX[position]}_{panel}.png"


def shap_summary_png_path(position: str) -> Path:
    return DATA_PROCESSED / f"shap_summary_{POSITION_FILE_SUFFIX[position]}.png"


# Each stat tuple is (source_column, display_label, format_type), where
# format_type in {"count", "percent", "decimal"} controls value formatting.
POSITION_STAT_GROUPS = {
    "FWD": [
        (
            "Attacking",
            [
                ("Gls", "Goals", "count"),
                ("Ast", "Assists", "count"),
                ("xG", "xG", "decimal"),
                ("xAG", "xAG", "decimal"),
                ("Sh_shooting", "Shots", "count"),
                ("SoT%", "Shot Accuracy", "percent"),
            ],
        ),
        (
            "Possession & Defensive Work",
            [
                ("PrgC", "Progressive Carries", "count"),
                ("PrgP", "Progressive Passes", "count"),
                ("Touches", "Touches", "count"),
                ("Tkl+Int", "Tackles + Interceptions", "count"),
            ],
        ),
    ],
    "MID": [
        (
            "Creativity & Passing",
            [
                ("Ast", "Assists", "count"),
                ("KP", "Key Passes", "count"),
                ("PrgP", "Progressive Passes", "count"),
                ("Cmp%_passing", "Pass Completion", "percent"),
                ("SCA", "Shot-Creating Actions", "count"),
            ],
        ),
        (
            "Defensive Work",
            [
                ("Tkl+Int", "Tackles + Interceptions", "count"),
                ("Int", "Interceptions", "count"),
                ("Recov", "Ball Recoveries", "count"),
            ],
        ),
    ],
    "DEF": [
        (
            "Defensive Actions",
            [
                ("Tkl", "Tackles", "count"),
                ("Int", "Interceptions", "count"),
                ("Clr", "Clearances", "count"),
                ("Blocks_defense", "Blocks", "count"),
                ("Won%", "Aerial Duels Won", "percent"),
            ],
        ),
        (
            "Possession & Progression",
            [
                ("PrgP", "Progressive Passes", "count"),
                ("Cmp%_passing", "Pass Completion", "percent"),
                ("Touches", "Touches", "count"),
            ],
        ),
    ],
    "GK": [
        (
            "Shot Stopping",
            [
                ("Saves", "Saves", "count"),
                ("Save%", "Save Percentage", "percent"),
                ("CS%", "Clean Sheet Percentage", "percent"),
                ("PSxG+/-", "PSxG +/-", "decimal"),
                ("GA90", "Goals Against per 90", "decimal"),
            ],
        ),
        (
            "Distribution",
            [
                ("Cmp%_keeper_adv", "Pass Completion", "percent"),
                ("Launch%", "Long Ball Rate", "percent"),
                ("AvgLen", "Avg Pass Length", "decimal"),
            ],
        ),
    ],
}

# Player Explorer's Comparable Players detail panel — a fixed, curated
# subset per position (not the full POSITION_STAT_GROUPS list above),
# chosen to fit a compact two-player comparison table rather than the full
# Performance Statistics card. Same raw field names/format types as
# POSITION_STAT_GROUPS (full_record is the shared data source for both);
# the fourth tuple element flags the one stat where a *smaller* value is
# the better outcome (goals conceded per 90), so the comparison panel's
# bold-the-better-value highlighting points the right way.
COMPARABLE_STAT_FIELDS = {
    "FWD": [
        ("Gls", "Goals", "count", False),
        ("Ast", "Assists", "count", False),
        ("xG", "xG", "decimal", False),
        ("xAG", "xAG", "decimal", False),
        ("Sh_shooting", "Shots", "count", False),
    ],
    "MID": [
        ("Ast", "Assists", "count", False),
        ("PrgP", "Progressive Passes", "count", False),
        ("PrgC", "Progressive Carries", "count", False),
        ("xAG", "xAG", "decimal", False),
        ("Tkl+Int", "Tackles + Interceptions", "count", False),
    ],
    "DEF": [
        ("Tkl+Int", "Tackles + Interceptions", "count", False),
        ("Clr", "Clearances", "count", False),
        ("Won%", "Aerial Duels Won %", "percent", False),
        ("PrgP", "Progressive Passes", "count", False),
    ],
    "GK": [
        ("Save%", "Save %", "percent", False),
        ("GA90", "Goals Against per 90", "decimal", True),
        ("CS%", "Clean Sheet %", "percent", False),
    ],
}

# Player Explorer's "All Statistics" view — a single, position-agnostic set
# of categories (unlike POSITION_STAT_GROUPS above, which is deliberately
# scoped per-position to match each trained model's own feature set). Pulls
# directly from merged_dataset_2425's raw FBref column names (not the
# sanitised names POSITION_STAT_GROUPS/FEATURE_LABELS use, since those only
# exist post-model-preprocessing) — every column here is confirmed present
# and genuinely populated for outfield players (verified: e.g. forwards
# have real non-null Tkl/Int/Recov values, defenders have real non-null
# xG/Sh_shooting values), so no position filtering is needed at the group
# level. Goalkeeping stats are the one category that's 100% null for every
# outfield player (keeper-table columns are only populated for keepers) —
# the page hides a category entirely once every field in it is null for
# the selected player, which naturally drops Goalkeeping for outfielders
# without needing an explicit position check here.
ALL_STATS_GROUPS = [
    (
        "Attacking",
        [
            ("Gls", "Goals", "count"),
            ("Ast", "Assists", "count"),
            ("G+A", "Goals + Assists", "count"),
            ("xG", "Expected Goals (xG)", "decimal"),
            ("npxG", "Non-Penalty xG", "decimal"),
            ("Sh_shooting", "Shots", "count"),
            ("SoT", "Shots on Target", "count"),
            ("SoT%", "Shot Accuracy", "percent"),
            ("PK", "Penalty Goals", "count"),
        ],
    ),
    (
        "Creativity & Passing",
        [
            ("xAG", "Expected Assisted Goals (xAG)", "decimal"),
            ("xA", "Expected Assists (xA)", "decimal"),
            ("KP", "Key Passes", "count"),
            ("PrgP", "Progressive Passes", "count"),
            ("Cmp%_passing", "Pass Completion", "percent"),
            ("SCA", "Shot-Creating Actions", "count"),
            ("GCA", "Goal-Creating Actions", "count"),
            ("CrsPA", "Crosses into Penalty Area", "count"),
            ("Crs", "Crosses", "count"),
        ],
    ),
    (
        "Possession & Progression",
        [
            ("Touches", "Touches", "count"),
            ("PrgC", "Progressive Carries", "count"),
            ("Carries", "Carries", "count"),
            ("Succ%", "Take-On Success", "percent"),
            ("CPA", "Carries into Penalty Area", "count"),
            ("Rec", "Passes Received", "count"),
        ],
    ),
    (
        "Defensive Actions",
        [
            ("Tkl", "Tackles", "count"),
            ("TklW", "Tackles Won", "count"),
            ("Int", "Interceptions", "count"),
            ("Tkl+Int", "Tackles + Interceptions", "count"),
            ("Clr", "Clearances", "count"),
            ("Blocks_defense", "Blocks", "count"),
            ("Won%", "Aerial Duels Won", "percent"),
            ("Recov", "Ball Recoveries", "count"),
        ],
    ),
    (
        "Discipline",
        [
            ("CrdY", "Yellow Cards", "count"),
            ("CrdR", "Red Cards", "count"),
            ("Fls", "Fouls Committed", "count"),
            ("Fld_misc", "Fouls Drawn", "count"),
            ("Off_misc", "Offsides", "count"),
        ],
    ),
    (
        "Goalkeeping",
        [
            ("Saves", "Saves", "count"),
            ("Save%", "Save Percentage", "percent"),
            ("CS", "Clean Sheets", "count"),
            ("CS%", "Clean Sheet Percentage", "percent"),
            ("GA90", "Goals Against per 90", "decimal"),
            ("PSxG+/-", "Post-Shot xG +/-", "decimal"),
        ],
    ),
]

# Human-readable labels for the raw, sanitised feature names used by the
# trained models and SHAP artefacts (e.g. "SoT%" -> "SoT_", "PSxG+/-" -> "PSxG_"
# after the notebooks' column-sanitisation step). Covers every feature name
# across all four position models (FWD/MID/DEF share one 154-feature set;
# GK adds 32 keeper-specific features) so SHAP output never shows raw
# engineering names to the user.
FEATURE_LABELS = {
    # Playing time
    "MP_playing_time": "Matches Played",
    "Starts_playing_time": "Starts",
    "Min_playing_time": "Minutes Played",
    "90s": "90s Played",
    # Shooting
    "Gls": "Goals",
    "Ast": "Assists",
    "G_A": "Goals + Assists",
    "G_PK": "Non-Penalty Goals",
    "PK": "Penalty Goals",
    "PKatt_shooting": "Penalty Attempts",
    "CrdY": "Yellow Cards",
    "CrdR": "Red Cards",
    "xG": "Expected Goals (xG)",
    "npxG": "Non-Penalty xG",
    "xAG": "Expected Assisted Goals (xAG)",
    "npxG_xAG": "npxG + xAG",
    "PrgC": "Progressive Carries",
    "PrgP": "Progressive Passes",
    "PrgR": "Progressive Passes Received",
    "G_A_PK": "Non-Penalty Goals + Assists",
    "xG_xAG": "xG + xAG",
    "Sh_shooting": "Shots",
    "SoT": "Shots on Target",
    "SoT_": "Shot Accuracy %",
    "Sh_90": "Shots per 90",
    "SoT_90": "Shots on Target per 90",
    "G_Sh": "Goals per Shot",
    "G_SoT": "Goals per Shot on Target",
    "Dist": "Avg Shot Distance",
    "FK_shooting": "Free Kick Shots",
    "npxG_Sh": "npxG per Shot",
    "G_xG": "Goals minus xG",
    "np_G_xG": "Non-Penalty Goals minus xG",
    # Passing
    "Cmp_passing_types": "Passes Completed",
    "Att_passing_types": "Passes Attempted",
    "Cmp__passing": "Pass Completion %",
    "TotDist_passing": "Total Passing Distance",
    "PrgDist_passing": "Progressive Passing Distance",
    "xA": "Expected Assists (xA)",
    "A_xAG": "Assists minus xAG",
    "KP": "Key Passes",
    "1_3_passing": "Passes into Final Third",
    "PPA": "Passes into Penalty Area",
    "CrsPA": "Crosses into Penalty Area",
    "Live_passing_types": "Live-Ball Passes",
    "Dead": "Dead-Ball Passes",
    "FK_passing_types": "Free Kick Passes",
    "TB": "Through Balls",
    "Sw": "Switches",
    "Crs": "Crosses",
    "TI": "Throw-Ins",
    "CK_passing_types": "Corner Kicks",
    "In": "Inswinging Corners",
    "Out": "Outswinging Corners",
    "Str": "Straight Corners",
    "Off_passing_types": "Offside Passes",
    "Blocks_passing_types": "Blocked Passes",
    # Goal/shot creation
    "SCA": "Shot-Creating Actions",
    "SCA90": "Shot-Creating Actions per 90",
    "PassLive": "Shot-Creating Live-Ball Pass",
    "PassDead": "Shot-Creating Dead-Ball Pass",
    "TO": "Shot-Creating Take-On",
    "Sh_gca": "Goal-Creating Shot",
    "Fld_gca": "Goal-Creating Foul Drawn",
    "Def": "Goal-Creating Defensive Action",
    "GCA": "Goal-Creating Actions",
    "GCA90": "Goal-Creating Actions per 90",
    # Defense
    "Tkl": "Tackles",
    "TklW": "Tackles Won",
    "Def_3rd_defense": "Tackles (Defensive Third)",
    "Mid_3rd_defense": "Tackles (Middle Third)",
    "Att_3rd_defense": "Tackles (Attacking Third)",
    "Att_defense": "Dribblers Challenged",
    "Tkl_": "Tackle Success %",
    "Lost_defense": "Tackles Lost",
    "Blocks_defense": "Blocks",
    "Sh_defense": "Shots Blocked",
    "Pass": "Passes Blocked",
    "Int": "Interceptions",
    "Tkl_Int": "Tackles + Interceptions",
    "Clr": "Clearances",
    "Err": "Errors Leading to Shot",
    # Possession
    "Touches": "Touches",
    "Def_Pen": "Touches (Def Penalty Area)",
    "Def_3rd_possession": "Touches (Defensive Third)",
    "Mid_3rd_possession": "Touches (Middle Third)",
    "Att_3rd_possession": "Touches (Attacking Third)",
    "Att_Pen": "Touches (Att Penalty Area)",
    "Live_possession": "Live-Ball Touches",
    "Att_possession": "Take-Ons Attempted",
    "Succ": "Successful Take-Ons",
    "Succ_": "Take-On Success %",
    "Tkld": "Times Tackled During Take-On",
    "Tkld_": "Tackled During Take-On %",
    "Carries": "Carries",
    "TotDist_possession": "Total Carrying Distance",
    "PrgDist_possession": "Progressive Carrying Distance",
    "1_3_possession": "Carries into Final Third",
    "CPA": "Carries into Penalty Area",
    "Mis": "Miscontrols",
    "Dis": "Dispossessed",
    "Rec": "Passes Received",
    # Playing time shares
    "Mn_MP": "Minutes per Match",
    "Min_": "Share of Available Minutes %",
    "Mn_Start": "Minutes per Start",
    "Compl": "Complete Matches Played",
    "Subs": "Substitute Appearances",
    "Mn_Sub": "Minutes per Substitution",
    "unSub": "Unused Substitute Appearances",
    # On/off-pitch impact
    "PPM": "Points per Match",
    "onG": "Goals Scored (On Pitch)",
    "onGA": "Goals Conceded (On Pitch)",
    "_": "Goal Difference (On Pitch)",
    "_90": "Goal Difference per 90 (On Pitch)",
    "On_Off": "On/Off Goal Difference",
    "onxG": "xG For (On Pitch)",
    "onxGA": "xG Against (On Pitch)",
    "xG_": "xG Difference (On Pitch)",
    "xG_90": "xG Difference per 90 (On Pitch)",
    # Misc
    "2CrdY": "Second Yellow Cards",
    "Fls": "Fouls Committed",
    "Fld_misc": "Fouls Drawn",
    "Off_misc": "Offsides",
    "PKwon": "Penalties Won",
    "PKcon": "Penalties Conceded",
    "OG_misc": "Own Goals",
    "Recov": "Ball Recoveries",
    "Won": "Aerial Duels Won",
    "Lost_misc": "Aerial Duels Lost",
    "Won_": "Aerial Duel Success %",
    # Player/contract attributes
    "player_id_tm": "Player ID (Transfermarkt)",
    "height_in_cm": "Height (cm)",
    "age_precise": "Age",
    "contract_months_remaining": "Contract Remaining",
    "age_squared": "Age²",
    "missing_contract": "Missing Contract Data",
    # Leagues, confederations, career stage, foot (one-hot encoded)
    "league_de_Bundesliga": "Bundesliga",
    "league_eng_Premier_League": "Premier League",
    "league_es_La_Liga": "La Liga",
    "league_fr_Ligue_1": "Ligue 1",
    "league_it_Serie_A": "Serie A",
    "confed_AFC": "AFC",
    "confed_CAF": "CAF",
    "confed_CONCACAF": "CONCACAF",
    "confed_CONMEBOL": "CONMEBOL",
    "confed_OFC": "OFC",
    "confed_UEFA": "UEFA",
    "career_stage_Declining": "Career Stage: Declining",
    "career_stage_Developing": "Career Stage: Developing",
    "career_stage_Emerging": "Career Stage: Emerging",
    "career_stage_Peak": "Career Stage: Peak",
    "foot_both": "Preferred Foot: Both",
    "foot_left": "Preferred Foot: Left",
    "foot_right": "Preferred Foot: Right",
    # Goalkeeping (GK model only)
    "_90_1": "Per-90 Rate (Goalkeeping)",
    "_90_2": "Per-90 Rate (Goalkeeping, secondary)",
    "MP_keeper": "Matches Played (GK)",
    "Starts_keeper": "Starts (GK)",
    "Min_keeper": "Minutes Played (GK)",
    "GA": "Goals Against",
    "GA90": "Goals Against per 90",
    "SoTA": "Shots on Target Against",
    "Saves": "Saves",
    "Save_": "Save %",
    "W": "Wins",
    "D": "Draws",
    "L": "Losses",
    "CS": "Clean Sheets",
    "CS_": "Clean Sheet %",
    "PKatt_keeper": "Penalty Kicks Faced",
    "PKA": "Penalty Kicks Allowed",
    "PKsv": "Penalty Kicks Saved",
    "PKm": "Penalty Kicks Missed by Opponent",
    "FK_keeper_adv": "Free Kick Goals Against",
    "CK_keeper_adv": "Corner Kick Goals Against",
    "OG_keeper_adv": "Own Goals Against",
    "PSxG": "Post-Shot xG Faced",
    "PSxG_SoT": "Post-Shot xG per Shot on Target",
    "PSxG_": "Post-Shot xG +/-",
    "Cmp_keeper_adv": "Long Passes Completed",
    "Att_keeper_adv": "Long Passes Attempted",
    "Cmp__keeper_adv": "Long Pass Completion %",
    "Att_GK_": "Passes Attempted (GK)",
    "Thr": "Throws Attempted",
    "Launch_": "Long Ball %",
    "AvgLen": "Avg Pass Length",
    "Opp": "Opponent Crosses Faced",
    "Stp": "Crosses Stopped",
    "Stp_": "Cross Stopping %",
    "_OPA": "Defensive Actions Outside Penalty Area",
    "_OPA_90": "Defensive Actions Outside Box per 90",
    "AvgDist": "Avg Distance of Defensive Actions",
}


def friendly_feature_label(raw_name: str) -> str:
    """Human-readable label for a raw model/SHAP feature name. Falls back to
    a lightly cleaned-up version of the raw name (underscores -> spaces,
    title case) for anything not in FEATURE_LABELS, so no unmapped name is
    ever shown completely raw."""
    if raw_name in FEATURE_LABELS:
        return FEATURE_LABELS[raw_name]
    return raw_name.replace("_", " ").strip().title() or raw_name

DASHBOARD_TITLE = "⚽"
DASHBOARD_SUBTITLE = "Football Player Valuation Dashboard"

HOME_PAGE = {"path": "Home.py", "label": "Home"}

PAGES = [
    {
        "path": "pages/1_Model_Performance.py",
        "label": "Model Performance",
        "icon": "📊",
        "description": "Compare Ridge, Random Forest, XGBoost and LightGBM across all four positions",
    },
    {
        "path": "pages/2_Value_Finder.py",
        "label": "Value Finder",
        "icon": "🔍",
        "description": "Explore players whose model estimate differs from their observed market value",
    },
    {
        "path": "pages/3_Player_Explorer.py",
        "label": "Player Explorer",
        "icon": "👤",
        "description": "Inspect an individual player's profile and SHAP explanation",
    },
    {
        "path": "pages/4_Bias_Explorer.py",
        "label": "Bias Explorer",
        "icon": "⚖️",
        "description": "Examine league and confederation contributions to model estimates",
    },
]

NAV_ITEMS = [HOME_PAGE] + PAGES

# Derived from PAGES so each page's st.set_page_config(page_icon=...) call
# can reference the same icon instead of duplicating the emoji literal.
PAGE_ICONS = {page["label"]: page["icon"] for page in PAGES}
