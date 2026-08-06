import streamlit as st

from lib import config
from lib.components import balance_section_spacing, render_header, stat_card
from lib.data_loader import load_dashboard_predictions, load_results_summary

st.set_page_config(
    page_title="Performance-Based Football Player Valuation",
    page_icon=config.DASHBOARD_TITLE,
    layout="wide",
    initial_sidebar_state="collapsed",
)
render_header(active="Home")
balance_section_spacing()

# Shared typography for every "research landing page" section added below
# (Research Context, Research Question, How the Framework Works, Explore
# the Dashboard) — one place for the centered-heading/muted-subtext/
# constrained-prose rhythm so each section is built the same way rather
# than re-deriving slightly different CSS per section. KPI cards, Key
# Finding banner, and the nav cards keep their own pre-existing styling
# untouched elsewhere in this file, per spec.
st.markdown(
    """
    <style>
    /* One shared spacing rhythm for every major section boundary on the
    page (Research Context -> Research Question -> KPIs -> Key Finding ->
    Framework -> interpretation expander -> Explore), so gaps read as
    consistent rather than each transition having its own ad-hoc size. */
    .home-section { margin-bottom: 3rem; }
    .section-heading {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .section-subtext {
        text-align: center;
        max-width: 46rem;
        margin: 0 auto 1.25rem auto;
        color: var(--app-text-muted, rgba(250, 250, 250, 0.65));
        line-height: 1.5;
    }
    /* Prose blocks (Research Context / Research Question): now centred
    per explicit request ("everything centre aligned... text... ")
    overriding the earlier left-aligned-for-readability choice — still
    capped to ~800px so lines don't stretch edge-to-edge on this page's
    wide, near-full-bleed layout, and the whole block is centred on the
    page via auto margins. */
    .prose-block {
        max-width: 50rem;
        margin: 0 auto;
        text-align: center;
        font-size: 1rem;
        line-height: 1.65;
        color: rgba(250, 250, 250, 0.88);
    }
    /* The Research Question keeps the accent treatment it already had
    (left rule + faint tint, now the design system's orange rather than
    the old red) — applied to the whole centered/constrained prose box
    instead of a full-bleed block, so it stays a single self-contained
    callout rather than a stripe running to the page edge. */
    .prose-block-accent {
        border-left: 3px solid var(--app-accent);
        background: var(--app-accent-subtle);
        padding: 1rem 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero -------------------------------------------------------------
with st.container(key="home-hero"):
    st.title("Performance-Based Football Player Valuation")
    st.subheader(
        "A Machine Learning Framework for Quantifying League and Nationality Bias "
        "in Football Market Values"
    )
    st.markdown(
        '<div class="prose-block" style="text-align: center; margin-top: 0.5rem;">'
        "Big 5 European leagues, 2024–25 season, 2,061 players. Position-specific "
        "machine learning models estimate market value from on-pitch performance, "
        "with SHAP explainability used to quantify the contribution of league and "
        "nationality to each estimate."
        "</div>",
        unsafe_allow_html=True,
    )
st.markdown(
    """
    <style>
    /* Centers the hero block's own heading levels (st.title/st.subheader)
    without a global rule — text-align inherits down to their rendered
    <h1>/<h2> elements from this one keyed ancestor. The description below
    them is centered directly via its own inline style above, since it's
    already a plain div rather than a Streamlit heading element. */
    /* st.title() renders <h1>, st.subheader() renders <h3> (not <h2>) in
    this Streamlit version — verified live rather than assumed, since the
    wrong tag silently matches nothing. */
    .st-key-home-hero h1, .st-key-home-hero h3 { text-align: center; }
    /* Title -> subtitle was landing flush against each other (measured
    live: 0px gap) — the title needs its own breathing room below it,
    distinct from (and a bit smaller than) the subtitle -> intro-paragraph
    gap, so the hero itself reads as a calm sequence rather than two
    headings stacked directly on top of one another. */
    .st-key-home-hero h1 {
        margin-bottom: 1rem;
    }
    /* The hero-to-"Research Context" transition was landing on the
    page's generic top-level block gap (measured live: 8px) rather than
    the deliberate ~3rem/44px rhythm every later section boundary uses
    (Research Context -> Research Question, measured live: 44px, via
    .home-section's own margin-bottom) — the one genuinely compressed gap
    in this section, and the specific complaint this fixes. Set slightly
    larger than that 3rem reference (not identical to it) rather than
    reusing .home-section's own margin-bottom rule: this is the single
    biggest structural break in the section (end of the hero, start of
    the first body heading), so it earns a touch more room than the
    body-to-body transitions below it — proportional, not mechanical. */
    .st-key-home-hero {
        margin-bottom: 3.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Research Context ---------------------------------------------------
# Merges the former "The Problem" / "The Approach" pair into one section —
# motivation and method read as a single continuous idea rather than two
# separate stops, ahead of the Research Question below.
st.markdown(
    '<div class="home-section">'
    '<div class="section-heading">Research Context</div>'
    '<div class="prose-block">'
    "Football players with similar on-pitch performance often receive markedly "
    "different market values. This project investigates how much of that "
    "variation can be explained by observed performance and how much remains "
    "associated with league affiliation and nationality using explainable "
    "machine learning."
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Research Question ---------------------------------------------------
st.markdown(
    '<div class="home-section">'
    '<div class="section-heading">The Research Question</div>'
    '<div class="prose-block prose-block-accent">'
    "To what extent can football player market value be explained by observed "
    "performance, and how much additional contribution is associated with league "
    "affiliation and nationality after accounting for performance?"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Dataset & Models (KPI cards) -----------------------------------------
# Left exactly as it already was — content, styling, and position unchanged
# per spec, sitting directly after the Research Question in the page's
# narrative flow.
predictions = load_dashboard_predictions()
results_summary = load_results_summary()

best_per_position = results_summary.loc[results_summary.groupby("position")["R2"].idxmax()]
best_per_position = best_per_position.set_index("position").loc[config.POSITIONS]

algo_to_positions: dict[str, list[str]] = {}
for pos, row in best_per_position.iterrows():
    algo_to_positions.setdefault(row["algorithm"], []).append(pos)

st.markdown(
    """
    <style>
    /* "Best Algorithm per Position" card: two stacked algo entries, each
    styled to echo st.metric's own bold-value/muted-label pairing (used by
    the other three KPI cards) rather than two plain equal-weight markdown
    lines. Sized well under st.metric's 36px value so two entries plus
    their position captions still fit inside this card's existing height
    (measured against the other cards, unchanged). */
    .algo-per-position {
        margin-top: 0.1rem;
        /* Explicit, not inherited: this card's own text-align:center
        (set on the outer card container by the KPI-row rule further
        below) never actually reaches these divs — Streamlit's own
        [data-testid="stMarkdownContainer"] machinery resets text-align
        back to left partway down the DOM chain between the card and this
        content, confirmed live via getComputedStyle at every level.
        Setting it directly here, on the actual content wrapper, is what
        makes centring reliable regardless of that reset. */
        text-align: center;
    }
    .algo-row + .algo-row {
        margin-top: 0.15rem;
    }
    .algo-name {
        /* This card's own "KPI value" — its 3 siblings use st.metric,
        which the shared [data-testid="stMetricValue"] rule already colours
        with the accent; matched here explicitly since this 4th card is
        hand-built HTML rather than st.metric. */
        font-size: 1.15rem;
        font-weight: 600;
        line-height: 1.2;
        color: var(--app-accent);
    }
    .algo-positions {
        font-size: 0.75rem;
        color: var(--app-text-muted);
        line-height: 1.2;
    }
    /* Same "centred content block, not a responsive dashboard grid"
    treatment as the workflow card grid below: capped width + centred,
    rather than 4 equal flex columns stretching to the page's full,
    near-edge-to-edge width. Gap tightened to match. */
    .st-key-home-kpi-row {
        max-width: 62rem;
        margin: 0 auto 3rem auto;
    }
    .st-key-home-kpi-row [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }
    /* Centre-aligns every KPI card's own content. text-align:center on
    the card correctly reaches st.metric's VALUE (confirmed live: its
    testid is a plain full-width display:block element, text-align just
    works) but was silently doing nothing for st.metric's own LABEL —
    [data-testid="stMetricLabel"] is display:grid, and text-align has no
    effect on how a grid lays out its content; the label's <p> was
    measured sitting flush at the grid container's own left edge despite
    text-align:center being set on every ancestor. justify-items:center
    is the grid equivalent of text-align:center here. The 4th card's own
    st.caption() label ("Best Algorithm per Position") is a separate
    case: a plain st.caption() call, which — like every other raw
    st.markdown/st.caption content on this page — does NOT reliably
    inherit text-align from an ancestor this far up the DOM, so it needs
    its own explicit rule the same way .algo-per-position/.nav-card-title/
    .nav-card-desc did. */
    .st-key-home-kpi-row [class*="st-key-stat-card-"] {
        text-align: center;
    }
    .st-key-home-kpi-row [data-testid="stMetricLabel"] {
        justify-items: center;
        /* The real fix, found only by inspecting computed widths live:
        this grid's single implicit column track was itself auto-sized to
        its content (measured 98px inside a 207px-wide label), so neither
        justify-items:center nor a child's width:100% had any free space
        to work with — a width:100% child inside an auto-sized track just
        resolves back to content width, a known CSS grid circularity.
        Sizing the column track itself to 100% is what actually gives
        justify-items something real to centre within. */
        grid-template-columns: 100%;
    }
    .st-key-home-kpi-row [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] {
        text-align: center;
    }
    .st-key-home-kpi-row [data-testid="stCaptionContainer"] {
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.container(key="home-kpi-row"):
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
            # Matches the other three KPI cards' one-big-value hierarchy
            # (st.metric's bold value + muted label) instead of two equal-weight
            # markdown lines — the algorithm name is the "value", the positions
            # it won on are a small caption underneath, same visual role as
            # st.metric's own label but placed after rather than before.
            rows_html = []
            for algo, positions in algo_to_positions.items():
                rows_html.append(
                    f'<div class="algo-row">'
                    f'<div class="algo-name">{algo}</div>'
                    f'<div class="algo-positions">{", ".join(positions)}</div>'
                    f"</div>"
                )
            st.markdown(
                f'<div class="algo-per-position">{"".join(rows_html)}</div>',
                unsafe_allow_html=True,
            )

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
st.markdown(
    """
    <style>
    /* Restrained, premium callout treatment (design system spec): a dark
    amber-tinted background rather than Streamlit's default saturated blue
    info box, with an accent border instead of a filled/loud background —
    scoped to this one banner (via the keyed container below) rather than
    every st.info() on the site, since Value Finder/Bias Explorer/Player
    Explorer use the same component for unrelated, lower-emphasis
    messages. Size/text content untouched — colour and centring only. */
    .st-key-home-key-finding [data-testid="stAlertContainer"] {
        background-color: #2A1B0D !important;
        border: 1px solid var(--app-accent) !important;
        justify-content: center !important;
    }
    /* Default info-alert icon is Streamlit's own blue — recoloured to the
    accent so nothing blue survives in a banner that's otherwise entirely
    black/white/orange. */
    .st-key-home-key-finding [data-testid="stAlertContainer"] svg {
        fill: var(--app-accent) !important;
    }
    .st-key-home-key-finding [data-testid="stMarkdownContainer"] p {
        text-align: center !important;
        color: var(--app-text) !important;
    }
    /* Only the "**Key Finding:**" label itself carries the accent — the
    rest of the sentence stays plain white body text, so the callout reads
    as restrained rather than fully orange. */
    .st-key-home-key-finding [data-testid="stMarkdownContainer"] strong {
        color: var(--app-accent) !important;
    }
    /* Same shared rhythm as every other major section boundary. */
    .st-key-home-key-finding {
        margin-bottom: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.container(key="home-key-finding"):
    st.info(
        "**Key Finding:** Premier League affiliation shows the model's largest positive "
        "SHAP contribution to estimated market value, across all four positions."
    )

# --- How the Framework Works ----------------------------------------------
# The visual centerpiece of the page: a 3x2 grid of individually bordered
# cards (one per pipeline stage) replaces the old single-row icon+arrow
# strip. Each card reuses the exact same st.container(border=True) card
# component as every other card on this page (KPI/nav cards, via the
# shared "stat-card-" key prefix) rather than a hand-rolled look-alike, so
# it's guaranteed to match, not just resemble, the existing style.
st.markdown(
    '<div class="home-section">'
    '<div class="section-heading">How the Framework Works</div>'
    '<div class="section-subtext">A six-stage pipeline that turns raw performance data into '
    "explainable, bias-quantified market value estimates.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    /* Capped and centered like the prose blocks above — at full page
    width the 3 cards per row stretched out with a lot of empty interior
    padding and wide gaps, reading as sparse rather than as a tight card
    grid. Narrower ceiling makes each card content-hugging (closer to a
    reference card grid's proportions) while leaving the now-larger empty
    margin on both sides of the page, which is the intended trade. */
    .st-key-home-workflow {
        max-width: 62rem;
        margin: 0 auto 3rem auto;
    }
    /* Lets each row of 3 cards wrap onto more rows on a narrow viewport
    instead of Streamlit's default (squeezing columns arbitrarily thin) —
    same trick used elsewhere on this page for the KPI/nav rows. Gap
    tightened from Streamlit's default so cards sit close together rather
    than floating with wide gutters between them. */
    .st-key-home-workflow [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
        row-gap: 0.75rem;
        gap: 0.75rem;
    }
    /* Equal card heights regardless of description length: st.columns()
    already stretches each column wrapper to match the tallest one in its
    row, but each card's own height still defaults to its content size
    unless told to fill that stretched wrapper — same two-part fix used
    for Player Explorer's Profile/Valuation/Statistics row (:has() reaches
    the intermediate "stLayoutWrapper" div Streamlit inserts between the
    card and the column, [class*=...] matches all 6 workflow cards'
    per-instance keys at once). */
    [data-testid="stLayoutWrapper"]:has(> [class*="st-key-stat-card-workflow-"]) {
        height: 100% !important;
    }
    [class*="st-key-stat-card-workflow-"] {
        height: 100% !important;
        box-sizing: border-box !important;
    }
    /* Flex column so step label / icon / title / description stack with
    identical internal rhythm across all 6 cards regardless of how much
    any one description wraps — each part below gets a reserved min-height
    (sized for its longest real case: "Machine Learning Models" needs 2
    title lines, the longest description needs 2 desc lines) so the icon
    and title always land at the same vertical position card-to-card, not
    just the overall card height matching via the row-stretch trick above. */
    .workflow-card {
        text-align: center;
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    .workflow-step-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--app-text-muted);
        margin-bottom: 0.5rem;
    }
    /* Icon-in-circle treatment: the icons are emoji (full-colour glyphs
    that ignore CSS `color`, so the glyph itself can't literally be
    recoloured orange) — the accent is instead carried by a bright, fully
    solid orange circle behind each one (an explicit request to replace
    the earlier subtle/dark tinted version, which read as too muted to
    actually draw the eye). Reused as-is for Explore the Dashboard's card
    icons below via the same class names, so both sections share one
    identical icon treatment rather than two similar-but-different ones. */
    .workflow-icon-circle {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--app-accent-subtle);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.5rem auto;
    }
    .workflow-icon {
        font-size: 1.5rem;
        line-height: 1;
        /* Belt-and-braces: the emoji is already visually centred by its
        parent circle's flexbox (justify-content:center positions it
        regardless of text-align), confirmed live — this is here purely
        so the icon's own computed text-align reads "center" too rather
        than an inherited "left", for full consistency with every other
        centred element on the page. */
        text-align: center;
    }
    .workflow-title {
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.3;
        margin-bottom: 0.35rem;
        min-height: 2.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--app-text);
    }
    .workflow-desc {
        font-size: 0.85rem;
        line-height: 1.45;
        color: var(--app-text-muted);
        min-height: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# Icons unchanged from the earlier icon-consistency fix (🤖/🏷️ replaced the
# two full-colour emoji that stood out against the rest of the set) — kept
# exactly as they were, only the surrounding layout changes here.
WORKFLOW_STEPS = [
    ("📊", "Performance Data", "Collects 2024–25 performance statistics from the Big Five European leagues."),
    ("⚙️", "Feature Engineering", "Creates position-specific features for modelling."),
    ("🤖", "Machine Learning Models", "Trains and evaluates four candidate algorithms."),
    ("🏷️", "Market Value Prediction", "Generates model-estimated player market values."),
    ("🔍", "SHAP Explainability", "Explains each feature's contribution to a prediction."),
    ("⚖️", "Bias Analysis", "Quantifies league and nationality contributions to value."),
]
with st.container(key="home-workflow"):
    for row_start in (0, 3):
        workflow_cols = st.columns(3)
        for offset, col in enumerate(workflow_cols):
            step_num = row_start + offset + 1
            icon, title, description = WORKFLOW_STEPS[row_start + offset]
            with col:
                with st.container(border=True, key=f"stat-card-workflow-{step_num}"):
                    st.markdown(
                        '<div class="workflow-card">'
                        f'<div class="workflow-step-label">Step {step_num}</div>'
                        f'<div class="workflow-icon-circle"><span class="workflow-icon">{icon}</span></div>'
                        f'<div class="workflow-title">{title}</div>'
                        f'<div class="workflow-desc">{description}</div>'
                        "</div>",
                        unsafe_allow_html=True,
                    )

# Placed before "Explore the Dashboard" rather than after it — a reader
# should know how to interpret an estimate before being pointed at the
# pages that show one, not as an afterthought below the exit links.
st.markdown(
    """
    <style>
    /* Tightens the gap between the four bullets — this is the only
    st.expander on the site, so a global stExpander selector is safe here
    without a keyed wrapper. Streamlit's own per-item spacing comes from
    each <li>'s margin, not a list-level gap. */
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] ul li {
        margin-bottom: 0.15rem;
    }
    /* Bullet text centred per explicit request that literally everything
    on this page be centre-aligned — supersedes an earlier, more specific
    "keep the bullets left-aligned for readability" instruction. The
    list-style position stays at its default (bullet glyphs sit just left
    of each line's own centred text rather than in one straight column),
    which is the expected look for a centred list rather than a bug. */
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] ul {
        text-align: center;
    }
    /* Centers only the expander's own heading row (chevron + label move
    together, centered as a unit) — the bullet list revealed on expand is
    untouched (still left-aligned via the default block above) since it's
    a separate element, not part of the summary row this rule targets. */
    /* Streamlit nests the icon+label wrapper 2 levels deep inside
    <summary> (span > div), and BOTH levels default to flex-grow: 1 —
    each one fills all remaining width in its own parent regardless of
    justify-content on an ancestor, so every level has to be shrunk back
    to content width before centering the outermost <summary> has any
    visible effect. */
    [data-testid="stExpander"] summary {
        justify-content: center;
    }
    [data-testid="stExpander"] summary * {
        flex-grow: 0 !important;
        width: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
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

# --- Explore the Dashboard -------------------------------------------------
st.markdown(
    '<div class="home-section" style="margin-top: 3rem;">'
    '<div class="section-heading">Explore the Dashboard</div>'
    '<div class="section-subtext">Navigate to each component of the framework — model performance, '
    "value estimates, individual player profiles, and league/nationality bias.</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    /* Now built from the exact same icon-circle -> title -> description
    pattern as "How the Framework Works" (an explicit request to make the
    two sections match, reusing .workflow-icon-circle/.workflow-icon
    directly rather than a similar-but-separate copy) instead of the
    former inline "#### icon Label" heading + st.caption. "Visit Page →" uses
    the design system's accent colour instead of the default link/body
    colour, so it reads as the card's call-to-action without becoming a
    button (no background, no border). A subtle hover brightening
    (accent -> accent-hover) reinforces it's the interactive element in
    the card, distinct from the card's own neutral hover lift. All
    scoped to nav cards only via the "stat-card-nav-" key prefix, so
    KPI cards elsewhere are untouched. */
    [class*="st-key-stat-card-nav-"] [data-testid="stPageLink"] a {
        color: var(--app-accent) !important;
        transition: color 150ms ease;
    }
    [class*="st-key-stat-card-nav-"] [data-testid="stPageLink"] a:hover {
        color: var(--app-accent-hover) !important;
    }
    /* Same centred, capped-width treatment as the KPI row and workflow
    grid above — these 4 cards were stretching to the page's full width
    otherwise, the one remaining section still behaving like a responsive
    dashboard grid instead of a compact, centred content block. */
    .st-key-home-explore-row {
        max-width: 62rem;
        margin: 0 auto;
    }
    .st-key-home-explore-row [data-testid="stHorizontalBlock"] {
        gap: 0.75rem;
    }
    /* Equal card heights: same two-part fix used for the workflow grid
    (the intermediate "stLayoutWrapper" div Streamlit inserts between each
    card and its column also has to be told to fill the already-equal,
    row-stretched column). Card content then becomes a flex column, all
    centred, with "Visit Page →" pushed to a shared baseline via margin-top:
    auto rather than sitting wherever its own content ends. */
    [data-testid="stLayoutWrapper"]:has(> [class*="st-key-stat-card-nav-"]) {
        height: 100% !important;
    }
    [class*="st-key-stat-card-nav-"] {
        height: 100% !important;
        box-sizing: border-box !important;
        text-align: center;
    }
    [class*="st-key-stat-card-nav-"][data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
    }
    /* Title/description reuse the workflow cards' own reserved-height
    approach (sized for this row's own longest cases: "Model Performance"
    needs 2 title lines, the Model Performance description needs 3 desc
    lines) so all four cards' icon/title/description land at consistent
    positions regardless of how much any one wraps. text-align:center set
    explicitly on both — same reason as .algo-per-position above: the
    card's own text-align:center (set on the outer stVerticalBlock) does
    not reliably reach content this deep in Streamlit's own markdown DOM,
    so it's not enough on its own, confirmed live via getComputedStyle.
    (.nav-card-title's justify-content:center already visually centred
    its own single line via flexbox regardless, but multi-line
    .nav-card-desc genuinely needed this to stop wrapping left-aligned.) */
    .nav-card-title {
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.3;
        margin-bottom: 0.35rem;
        min-height: 2.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: var(--app-text);
    }
    .nav-card-desc {
        font-size: 0.85rem;
        line-height: 1.45;
        color: var(--app-text-muted);
        min-height: 4.1rem;
        text-align: center;
    }
    /* margin-top: auto has to land on the flex item itself — the direct
    stElementContainer child that wraps stPageLink, not stPageLink itself
    (nested a level deeper, so it isn't a flex item of the card's own
    flex column and margin:auto on it alone did nothing). stPageLink is
    always the card's 2nd/last stElementContainer (icon+title+description
    markdown, then the link). */
    [class*="st-key-stat-card-nav-"] > [data-testid="stElementContainer"]:last-child {
        margin-top: auto !important;
        /* The actual fix for centring "Visit Page →": this element (not
        stPageLink or its inner <a>, both measured shrink-wrapped to their
        own ~59px text width with no free space to redistribute) is the
        one true full-width flex item in the card's column — forcing it
        to stretch and flex-centre its content is what centres the link,
        rather than any text-align/justify-content set on the already-
        content-sized elements further down. */
        width: 100% !important;
        display: flex !important;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with st.container(key="home-explore-row"):
    nav_card_cols = st.columns(len(config.PAGES))
    for col, page in zip(nav_card_cols, config.PAGES):
        with col:
            # Same "stat-card-" key prefix as the KPI cards above (and
            # stat_card() itself) purely so this reuses components.py's shared
            # card padding rule — matching card styling already established on
            # this exact page, not a new design.
            card_key = "stat-card-nav-" + page["label"].lower().replace(" ", "-")
            with st.container(border=True, key=card_key):
                st.markdown(
                    f'<div class="workflow-icon-circle"><span class="workflow-icon">{page["icon"]}</span></div>'
                    f'<div class="nav-card-title">{page["label"]}</div>'
                    f'<div class="nav-card-desc">{page["description"]}</div>',
                    unsafe_allow_html=True,
                )
                st.page_link(page["path"], label="Visit Page →")
