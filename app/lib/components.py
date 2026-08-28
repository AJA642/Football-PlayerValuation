import ast
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from lib import config


def _fix_dropdown_chevron_toggle():
    """Makes every selectbox/multiselect chevron a true open/close toggle."""
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            if (doc.__fpvdChevronToggleFixInstalled) return;
            doc.__fpvdChevronToggleFixInstalled = true;
            doc.addEventListener('mousedown', function(e) {
                const icon = e.target.closest && e.target.closest('[data-baseweb="select"] svg[data-baseweb="icon"]');
                if (!icon) return;
                const root = icon.closest('[data-baseweb="select"]');
                const input = root && root.querySelector('input[aria-expanded]');
                if (input && input.getAttribute('aria-expanded') === 'true') {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    input.blur();
                }
            }, true);
        })();
        </script>
        """,
        height=0,
    )


def render_header(active: str):
    active_href = "" if active == "Home" else active.replace(" ", "_")
    st.markdown(
        f"""
        <style>
        /* --- Design system tokens ------------------------------------
        Single source of truth for the "premium/restrained, orange-accent"
        identity, defined once here (render_header runs on every page) so
        every page inherits it instead of redefining colours locally.
        var(--app-text-muted, ...) / var(--app-border, ...) were already
        used as CSS custom properties with inline rgba fallbacks across
        Home.py and Player_Explorer.py *before* this redesign, but the
        properties themselves were never actually defined anywhere — every
        one of those usages was silently falling back to its inline rgba
        default. Defining them here retargets all of those existing call
        sites app-wide without editing each page. */
        :root {{
            --app-bg: #0B0B0B;
            --app-card-bg: #171717;
            --app-border: #2A2A2A;
            --app-border-hover: #3D3D3D;
            --app-text: #FFFFFF;
            --app-text-muted: #A3A3A3;
            --app-accent: #FF7A00;
            --app-accent-hover: #FF8C1A;
            --app-accent-subtle: rgba(255, 122, 0, 0.12);
        }}

        /* Every bordered st.container() across all 5 pages, reached via
        the "st-key-" prefixes already established for each one (stat
        cards, nav cards, workflow cards, Player Explorer's Profile/
        Valuation/Statistics cards, Model Performance's Diagnostics/SHAP
        panels, Value Finder's Filters panel) — one shared card treatment
        instead of restyling each page's cards independently. Hover is
        intentionally a neutral brighter border + slight lift, not an
        orange border: orange is reserved for genuinely interactive
        elements (links, active states), not every static info card. */
        [class*="st-key-stat-card-"],
        [class*="st-key-profile-summary-card"],
        [class*="st-key-valuation-summary-card"],
        [class*="st-key-perf-stats-col"],
        [class*="st-key-diag-panel-"],
        [class*="st-key-shap-panel-"],
        [class*="st-key-vf-filters-panel"] {{
            background-color: var(--app-card-bg) !important;
            border-color: var(--app-border) !important;
            border-radius: 10px !important;
            transition: transform 180ms ease, border-color 180ms ease;
        }}
        [class*="st-key-stat-card-"]:hover,
        [class*="st-key-profile-summary-card"]:hover,
        [class*="st-key-valuation-summary-card"]:hover,
        [class*="st-key-perf-stats-col"]:hover,
        [class*="st-key-diag-panel-"]:hover,
        [class*="st-key-shap-panel-"]:hover,
        [class*="st-key-vf-filters-panel"]:hover {{
            border-color: var(--app-border-hover) !important;
            transform: translateY(-2px);
        }}

        /* st.metric's big value is the "KPI number" everywhere it's used
        (Home's KPI row, Value Finder's/Bias Explorer's breakdown cards) —
        one rule makes every KPI number orange app-wide, per the design
        brief's explicit "KPI numbers" accent guidance, without touching
        each page. The label above it is untouched (stays white/muted),
        so only the number itself carries the accent. */
        [data-testid="stMetricValue"] {{
            color: var(--app-accent) !important;
        }}

        /* Default alert treatment (st.info/st.warning) — Streamlit's own
        colours (a saturated blue/yellow) are the last surviving non-
        monochrome, non-accent colour on the dashboard otherwise: Value
        Finder's "no players match" message, Bias Explorer's Insight box,
        Player Explorer's "no valuation data"/"select a comparable player"
        messages all use st.info() for genuinely neutral messaging, not a
        highlighted callout, so they get the same restrained charcoal-card
        treatment as everything else rather than their own colour. Home's
        Key Finding banner is the one deliberate exception — it has its
        own more specific `.st-key-home-key-finding` rules (same
        !important tier, higher specificity) that win over this default. */
        [data-testid="stAlertContainer"] {{
            background-color: var(--app-card-bg) !important;
            border: 1px solid var(--app-border) !important;
        }}
        [data-testid="stAlertContainer"] svg {{
            fill: var(--app-text-muted) !important;
        }}
        [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] p {{
            color: var(--app-text) !important;
        }}

        /* Streamlit's native header (the "⋮" settings menu, Deploy button,
        theme toggle, etc.) is replaced outright by the custom top bar below
        rather than living alongside it — hidden completely, not just
        shrunk, per the "single top bar" requirement. Its theme toggle is
        not replaced by a custom one; the top bar's third zone is an empty
        symmetry spacer (see render_header's docstring), not a toggle slot. */
        [data-testid="stHeader"] {{
            display: none;
        }}
        /* With the native header gone there is nothing left to clear, so
        the block container can sit almost flush against the viewport top —
        only a small breathing-room gap remains. Side padding is reduced
        from Streamlit's default 5rem/side to reclaim ~6% more horizontal
        width for tables/charts (measured: 80px/side at a 1600px viewport,
        i.e. 10% of width, dropping to 32px/side i.e. 4% — a 6-point gain). */
        [data-testid="stMainBlockContainer"] {{
            padding-top: 0.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}

        /* Every selectbox/multiselect's dropdown chevron points down even
        while the menu is open — BaseWeb never rotates or swaps the icon
        itself, it only flips the input's `aria-expanded` attribute (checked
        live: same <svg>, same <path>, same "open" title, in both states).
        `:has()` lets a state on the descendant input drive a style on the
        descendant icon, scoped to BaseWeb's own stable, public attributes
        (`data-baseweb`, `aria-expanded`) — not Streamlit's unstable
        per-build emotion-hash classes, and not a per-page override, so this
        one rule covers every dropdown on every page. Closing via the
        chevron already worked before this change (BaseWeb's own
        outside-click/toggle handling, untouched here) — this only fixes
        which way the icon points. */
        [data-baseweb="select"]:has(input[aria-expanded="true"]) svg[data-baseweb="icon"] {{
            transform: rotate(180deg);
        }}

        /* Shared top-level page rhythm: the gap between every direct
        top-level block (H1 title, description, first divider, first
        section...) on every page, since this one flex `gap` is what
        actually produces that spacing in this Streamlit version — content
        elements themselves have zero margin and rely entirely on it.
        Scoped with a direct-child combinator so only the page's outermost
        content flow is affected, not nested column/container layouts
        elsewhere (which have their own, separate stVerticalBlock). Reduced
        from Streamlit's default 16px to 12px (25% less) — this single rule
        is what tightens title -> description -> divider -> first section on
        every page, and every section-to-section transition on pages with
        several stacked sections (e.g. Player Explorer), without per-page
        tweaks. */
        [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{
            gap: 12px !important;
        }}

        /* Bordered "card" containers — every stat_card() — keyed per-instance
        (`st-key-stat-card-<label>`) so this substring selector reaches every
        card on every page without touching unrelated bordered containers
        (e.g. Value Finder's Filters panel, handled on its own page).
        Streamlit's default is 15px all round; only the vertical component
        is reduced here (~13% less), width/padding-inline stays. */
        [class*="st-key-stat-card-"] {{
            padding-top: 13px !important;
            padding-bottom: 13px !important;
        }}

        /* Streamlit adds a hover-visible "link to heading" icon (the chain
        link) next to every st.title/header/subheader by default. Purely
        cosmetic chrome, not content — hidden globally here since
        render_header() runs on every page, rather than passing anchor=False
        to every heading call across all five page files individually. */
        [data-testid="stHeaderActionElements"] {{
            display: none !important;
        }}

        /* The divider directly under the navbar, in its own keyed container
        so this rule can't accidentally hide a page's own section dividers.
        (An earlier version tried `.dashboard-header hr` — that never
        matched anything: st.markdown's raw <div> open/close tags each
        become their own isolated element in Streamlit's DOM, they don't
        actually wrap the widgets rendered in between.) Selector includes
        the block-container ancestor to out-specify balance_section_spacing()'s
        `[data-testid="stMainBlockContainer"] hr` rule — both are !important,
        same specificity otherwise, and that one was winning the tie by
        loading later in the page script. */
        [data-testid="stMainBlockContainer"] .st-key-topbar-divider hr {{
            margin: 0 0 0.125rem !important;
        }}

        /* Three-zone flex row: logo (col 1) and the empty spacer (col 3)
        are forced to equal width via matching flex-grow, whatever that
        width ends up being — not sized to col 1's own content. That's what
        makes col 2 (nav) genuinely centred on the full row: the space
        col 2's content doesn't use is split evenly on both sides, so a
        wide logo doesn't push the centre zone off-centre. Re-balances at
        any viewport width, no fixed widths or transforms involved. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type {{
            display: flex;
            align-items: center;
            width: 100%;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(1) {{
            flex: 1 1 0 !important;
            width: auto !important;
            /* Never shrinks past its own content's width (the brand text
            is nowrap) — below that, col 2 gives up room instead, same as
            any narrow-viewport flex layout. Without this floor, matching
            col 1's grow/shrink to col 3's forces the logo text to overflow
            into the nav zone once the row gets tight. */
            min-width: max-content !important;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) {{
            flex: 0 1 auto !important;
            width: auto !important;
            min-width: 0 !important;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(3) {{
            flex: 1 1 0 !important;
            width: auto !important;
            min-width: 0 !important;
        }}

        .st-key-topbar [data-testid="stPageLink"] {{
            margin: 0;
        }}
        /* Brand block (logo + subtitle): laid out as its own inline flex
        row so the two pieces sit side by side rather than stacking, and
        kept deliberately modest (nav is the visual focus, not the brand —
        the page already has a large hero title of its own on every page).
        Scoped via the child combinator to the outer zone columns only, so
        it can't coincidentally match a same-numbered nested nav column. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(1) [data-testid="stVerticalBlock"] {{
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 0.6rem;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(1) [data-testid="stElementContainer"] {{
            width: auto !important;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(1) [data-testid="stPageLink"] a {{
            padding: 0.2rem 0;
            font-size: 1rem;
            font-weight: 500;
            /* Streamlit renders an icon-only page_link label (our logo is
            just "⚽") with its own subtle grey "chip" background — a
            different auto-generated style than the plain-text nav links
            get. Neutralised here so the logo sits flush in the bar rather
            than looking like a button. */
            background: transparent !important;
        }}
        .brand-subtitle {{
            font-size: 0.85rem;
            font-weight: 400;
            color: var(--app-text-muted);
            white-space: nowrap;
            padding-left: 0.6rem;
            border-left: 1px solid var(--app-border);
        }}
        /* The nav zone's own content is plain sequential st.page_link calls
        (no nested columns — those turned out to size by percentage, not by
        content, which made the leading/trailing spacer trick unreliable:
        measured 16px vs 172px for two columns given the *same* ratio).
        Forcing this block into a row keeps the links inline; col 2 itself
        is already sized and positioned to be centred on the full row (see
        the column rules above), so no additional transform is needed here. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stVerticalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            gap: 2rem;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stElementContainer"] {{
            width: auto !important;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a {{
            justify-content: center;
            border-radius: 0.5rem;
            white-space: nowrap;
            font-size: 0.9rem;
            font-weight: 400;
            padding: 0.4rem 0.5rem;
            line-height: 1.5;
            transition: color 150ms ease;
            /* Real <a> tags otherwise pick up the browser's own default
            (unvisited-blue/visited-purple) link colour once a page has
            actually been visited this session — visible here as a stray
            blue/purple tint that has nothing to do with the design
            system. Forcing the theme's own text colour keeps every
            inactive tab neutral white regardless of visited state.
            :link/:visited explicitly repeated (not just the bare
            selector) because a browser's built-in :visited rule has
            higher specificity than a plain element+attribute selector
            and was winning the tie despite !important on the plain
            selector alone. */
            color: var(--app-text) !important;
        }}
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a:link,
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a:visited {{
            color: var(--app-text) !important;
        }}
        /* Inactive links pick up the accent on hover — active tab is
        excluded (its href already matches active_href above, and this
        selector's specificity is lower than that rule's) so the current
        page's own link doesn't flicker between two accent treatments. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a:hover {{
            color: var(--app-accent-hover);
        }}
        /* Active nav item: accent-coloured text + underline, still no
        background tint or weight change — one of the design system's
        explicit "orange is reserved for" cases (active navigation state).
        Uses text-decoration (hugs the text itself) rather than
        border-bottom, which would span the link's full padded clickable
        box and look like a bracket around the whole tab rather than a
        line under the word. Scoped to the nav zone (col 2) only. The
        logo's own st.page_link also points at Home.py, so on the Home
        page its href is the same empty string as the Home tab's — an
        unscoped selector here was colouring the logo too. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a[href="{active_href}"] {{
            background: transparent;
            /* !important: the :link/:visited browser-default override
            above also uses !important (needed to beat the UA stylesheet's
            own :visited rule), which otherwise wins this tie regardless
            of source order since importance is checked before order. */
            color: var(--app-accent) !important;
            font-weight: 500;
            text-decoration: underline;
            text-underline-offset: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="topbar"):
        zone_cols = st.columns([1, 6, 1])
        with zone_cols[0]:
            st.page_link(config.HOME_PAGE["path"], label=config.DASHBOARD_TITLE)
            st.markdown(
                f'<span class="brand-subtitle">{config.DASHBOARD_SUBTITLE}</span>',
                unsafe_allow_html=True,
            )
        with zone_cols[1]:
            for item in config.NAV_ITEMS:
                st.page_link(item["path"], label=item["label"])
    with st.container(key="topbar-divider"):
        st.divider()

    _fix_dropdown_chevron_toggle()


def balance_section_spacing():
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] hr {
            margin: 1.1rem 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def wide_divider(key: str):
    with st.container(key=key):
        st.divider()
    st.markdown(
        f"""
        <style>
        [data-testid="stMainBlockContainer"] .st-key-{key} hr {{
            margin: 1.75rem 0 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _css_safe_key(prefix: str, label: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", label).strip("-")
    return f"{prefix}-{safe}"


def stat_card(label: str, value: str, help_text: str | None = None):
    with st.container(border=True, key=_css_safe_key("stat-card", label)):
        st.metric(label, value, help=help_text)


def format_eur_short(value: float) -> str:
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:,.0f}"


_TAG_BASE = 0xE0000  # Unicode tag-character block, used only for the
# England/Scotland/Wales subdivision flags below (see flag_emoji).


def flag_emoji(country_name: str) -> str:
    code = config.COUNTRY_FLAG_CODES.get(country_name)
    if not code:
        return ""
    if "-" in code:
        region = code.replace("-", "").lower()
        tags = "".join(chr(_TAG_BASE + ord(c)) for c in region)
        return "\U0001f3f4" + tags + "\U000e007f"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def logo_prefixed_heading(logo_data_uri: str | None, text: str) -> str:
    if not logo_data_uri:
        return text
    return (
        f'<img src="{logo_data_uri}" style="height:22px;width:auto;'
        f'vertical-align:middle;border-radius:2px;margin-right:0.4rem;"/>'
        f"{text}"
    )

VALUE_RATIO_GREEN = "#22c55e"
VALUE_RATIO_RED = "#ef4444"


def value_ratio_color(value: float) -> str:
    if value is None or (isinstance(value, float) and value != value):  # NaN check without pandas
        return ""
    rounded = round(value, 2)
    if rounded > 1.10:
        return VALUE_RATIO_GREEN
    if rounded < 0.90:
        return VALUE_RATIO_RED
    return ""


def value_ratio_style(value: float) -> str:
    color = value_ratio_color(value)
    return f"color: {color}; font-weight: 600;" if color else ""


def difference_color(value: float) -> str:
    if value is None or (isinstance(value, float) and value != value):
        return ""
    if value > 0:
        return VALUE_RATIO_GREEN
    if value < 0:
        return VALUE_RATIO_RED
    return ""


def difference_style(value: float) -> str:
    color = difference_color(value)
    return f"color: {color}; font-weight: 600;" if color else ""


def metrics_table_with_params(df, rename_map: dict, key: str):
    has_params = "best_params" in df.columns
    visible_columns = [c for c in df.columns if c != "best_params"]
    display_df = df[visible_columns].rename(columns=rename_map)

    if not has_params:
        st.dataframe(display_df, hide_index=True, width="stretch")
        return

    event = st.dataframe(
        display_df,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )

    selected_rows = event.selection.rows if event and event.selection else []
    if selected_rows:
        row = df.iloc[selected_rows[0]]
        label_bits = [str(row[c]) for c in ("position", "algorithm") if c in df.columns]
        st.caption(f"Hyperparameters — {' / '.join(label_bits)}")
        try:
            params = ast.literal_eval(row["best_params"])
            st.code(json.dumps(params, indent=2), language="json")
        except (ValueError, SyntaxError):
            st.code(row["best_params"])
    else:
        st.caption("Select a row above to view its full hyperparameters.")