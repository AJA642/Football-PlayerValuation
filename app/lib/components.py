import ast
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from lib import config


def _fix_dropdown_chevron_toggle():
    """Makes every selectbox/multiselect chevron a true open/close toggle.

    Investigated first, live, before writing anything: clicking the (now
    correctly rotated) chevron while open does fire BaseWeb's own close
    logic — `aria-expanded` on the combobox `<input>` does flip to "false"
    at click time — but the same click's mousedown also refocuses that
    input, and BaseWeb reopens the menu on focus. Net effect: the click
    closes and reopens within the same interaction, which reads as "nothing
    happened." This is a BaseWeb focus/click race, not something our own
    CSS or a page's widget code is causing — confirmed by reproducing it
    with a plain click and no custom JS at all.

    `aria-expanded` is a genuine, stable ARIA attribute (not an
    emotion-hash class), so it's used here too: a single document-level
    mousedown listener, capture phase (fires before BaseWeb's own delegated
    handlers get a chance to run), that only acts when the click lands on
    a dropdown's own chevron *and* that dropdown is currently open. In that
    one case it stops the event outright and blurs the input directly,
    bypassing the focus-reopen race entirely. A click on a closed dropdown,
    or anywhere else on the page (including the options list, which BaseWeb
    renders in a portal outside the `[data-baseweb="select"]` subtree so it
    never matches this selector), is untouched and behaves exactly as
    before. Idempotent (guarded so a rerun never attaches a second copy).
    """
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
    """The app's only header and only navigation surface: one single-row top
    bar with logo (left), page tabs (centre), and an empty spacer zone
    (right). The spacer has no content — it exists purely so the centre zone
    is genuinely centred on the full row: zone 1 and zone 3 are forced to
    equal width (`flex: 1 1 0` on both), so whatever space the centre zone's
    own content doesn't need is split evenly on either side, regardless of
    how wide the logo is. Replaces Streamlit's native header/toolbar
    entirely rather than sitting below it.

    Every nav item — including the active one — is rendered as a real
    st.page_link with identical structure, so padding/height/line-height/
    border-radius are guaranteed identical by construction. The active item
    is picked out purely via an href attribute selector that only changes
    font weight, never layout or colour — a bold-text state instead of a
    tinted-background "pill", per user preference.

    The sidebar itself is never created server-side (see
    .streamlit/config.toml's showSidebarNavigation=false) — nothing here
    hides it after the fact."""
    active_href = "" if active == "Home" else active.replace(" ", "_")
    st.markdown(
        f"""
        <style>
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

        /* Bordered "card" containers — stat_card() and colored_metric() —
        keyed per-instance (`st-key-stat-card-<label>` /
        `st-key-colored-metric-<label>`) so this substring selector reaches
        every card on every page without touching unrelated bordered
        containers (e.g. Value Finder's Filters panel, handled on its own
        page). Streamlit's default is 15px all round; only the vertical
        component is reduced here (~13% less), width/padding-inline stays. */
        [class*="st-key-stat-card-"], [class*="st-key-colored-metric-"] {{
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
            color: rgba(255, 255, 255, 0.65);
            white-space: nowrap;
            padding-left: 0.6rem;
            border-left: 1px solid rgba(255, 255, 255, 0.15);
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
        }}
        /* Active nav item: underline only — no background tint, no colour
        change, no weight change. Uses text-decoration (hugs the text
        itself) rather than border-bottom, which would span the link's full
        padded clickable box and look like a bracket around the whole tab
        rather than a line under the word. Scoped to the nav zone (col 2)
        only. The logo's own st.page_link also points at Home.py, so on the
        Home page its href is the same empty string as the Home tab's — an
        unscoped selector here was underlining the logo too. */
        .st-key-topbar [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) [data-testid="stPageLink"] a[href="{active_href}"] {{
            background: transparent;
            color: inherit;
            font-weight: 400;
            text-decoration: underline;
            text-underline-offset: 4px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="topbar"):
        # zone_cols[2] is intentionally left empty — a pure symmetry spacer
        # so zone_cols[1] centres on the full row (see the CSS above). The
        # ratio passed to st.columns() here is moot; the CSS's `!important`
        # flex rules are what actually size all three zones.
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
    """Breathing room around section dividers so a page with several stacked
    sections (e.g. Player Explorer) doesn't run sections together, without
    altering section order or content. 1.1rem — down from an earlier 1.75rem
    that, combined with the page-wide gap in render_header(), read as too
    loose for a dashboard that's meant to feel dense."""
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
    """A divider deliberately exempt from balance_section_spacing()'s global
    margin — for the rare case where a specific divider is separating two
    genuinely distinct ideas (e.g. Model Performance's summary-vs-detail
    split between "Best Model per Position" and "Full Results") and earns
    more visual weight than the standard inter-section gap. Needs its own
    keyed container: `[data-testid="stMainBlockContainer"] hr` alone can't
    be overridden per-instance, only page-wide."""
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
    """A container `key` that's both a valid Streamlit key and, via
    Streamlit's own `st-key-<key>` class convention, targetable by a CSS
    substring selector — e.g. `[class*="st-key-stat-card-"]` reaches every
    stat_card() on a page regardless of its label, without relying on
    Streamlit's unstable emotion-hash classes (there is no other stable hook:
    a bordered st.container() and a plain one share the exact same
    data-testid, differing only in an internal emotion class)."""
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", label).strip("-")
    return f"{prefix}-{safe}"


def stat_card(label: str, value: str, help_text: str | None = None):
    with st.container(border=True, key=_css_safe_key("stat-card", label)):
        st.metric(label, value, help=help_text)


def format_eur_short(value: float) -> str:
    """Compact euro formatting for chart axes/tooltips (€1.2M, €35M, €900K),
    distinct from the full comma-formatted euros used in metric cards
    elsewhere (e.g. "€17,960,778") — a value-history chart with many points
    needs shorter labels than a single-value stat card does."""
    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:,.0f}"


_TAG_BASE = 0xE0000  # Unicode tag-character block, used only for the
# England/Scotland/Wales subdivision flags below (see flag_emoji).


def flag_emoji(country_name: str) -> str:
    """Unicode flag for a nationality (e.g. "France" -> "🇫🇷"), or "" if
    the country isn't in config.COUNTRY_FLAG_CODES — callers should just
    display the plain name in that case, the same graceful-fallback
    behaviour as a missing club logo.

    Two encodings, both real Unicode mechanisms (no image assets):
    - Ordinary ISO 3166-1 alpha-2 codes ("FR") become a pair of Regional
      Indicator Symbols (U+1F1E6-based), the standard flag-emoji encoding.
    - The three UK home nations aren't alpha-2 codes at all
      (COUNTRY_FLAG_CODES stores "GB-ENG" etc. for them) — they render via
      the separate "tag sequence" mechanism: the black-flag base character
      followed by invisible tag characters spelling the region code, which
      is how 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (England) etc. are actually defined.
    """
    code = config.COUNTRY_FLAG_CODES.get(country_name)
    if not code:
        return ""
    if "-" in code:
        region = code.replace("-", "").lower()
        tags = "".join(chr(_TAG_BASE + ord(c)) for c in region)
        return "\U0001f3f4" + tags + "\U000e007f"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def logo_prefixed_heading(logo_data_uri: str | None, text: str) -> str:
    """Markdown-heading-compatible HTML: a small inline crest immediately
    before `text`, sized and vertically aligned to sit on the same line as
    the surrounding "####"-style profile values — or, if no logo is
    available, just `text` unchanged so the caller's existing rendering
    (`st.markdown(f"#### {...}")`) doesn't need a separate no-logo code
    path. Callers must still pass unsafe_allow_html=True."""
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
    """Consistent Value Ratio colour threshold, shared across every page
    that shows a Value Ratio: >1.10 green (model estimate well above actual
    value), <0.90 red (well below), otherwise the theme's neutral text
    colour (no override).

    The value is rounded to 2 decimal places *before* the threshold check,
    matching the 2-decimal precision every page actually displays (e.g.
    f"{ratio:.2f}"). Thresholding the raw float instead would let a value
    like 0.898039 — which displays as "0.90" — read as red, contradicting
    a number that looks like it's sitting right on the boundary."""
    if value is None or (isinstance(value, float) and value != value):  # NaN check without pandas
        return ""
    rounded = round(value, 2)
    if rounded > 1.10:
        return VALUE_RATIO_GREEN
    if rounded < 0.90:
        return VALUE_RATIO_RED
    return ""


def value_ratio_style(value: float) -> str:
    """CSS declaration string for a pandas Styler.map cell, using the same
    thresholds as value_ratio_color."""
    color = value_ratio_color(value)
    return f"color: {color}; font-weight: 600;" if color else ""


def difference_color(value: float) -> str:
    """Sign-based colour for a currency delta (e.g. Value Finder's
    Difference column) — the same green/red palette as Value Ratio, but
    keyed on sign alone rather than reusing the ratio's >1.10/<0.90
    magnitude thresholds, since a euro delta isn't the same kind of number
    as a ratio."""
    if value is None or (isinstance(value, float) and value != value):
        return ""
    if value > 0:
        return VALUE_RATIO_GREEN
    if value < 0:
        return VALUE_RATIO_RED
    return ""


def difference_style(value: float) -> str:
    """CSS declaration string for a pandas Styler.map cell, using the same
    thresholds as difference_color."""
    color = difference_color(value)
    return f"color: {color}; font-weight: 600;" if color else ""


def colored_metric(label: str, value_text: str, color: str = ""):
    """A st.metric look-alike whose value can be colour-overridden (st.metric
    itself has no API for colouring the main value, only its delta line).
    Used for Value Ratio cards so the colour matches value_ratio_color's
    thresholds consistently with the coloured table cells elsewhere. Wrapped
    in the same bordered container as stat_card for visual consistency."""
    value_style = f"color: {color};" if color else ""
    with st.container(border=True, key=_css_safe_key("colored-metric", label)):
        st.markdown(
            f"""
            <div data-testid="stMetric">
                <div style="font-size: 0.875rem; color: var(--app-text-muted, rgba(250, 250, 250, 0.6));">{label}</div>
                <div style="font-size: 2.25rem; font-weight: 600; line-height: 1.2; {value_style}">
                    {value_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def metrics_table_with_params(df, rename_map: dict, key: str):
    """Render a metrics table; if a `best_params` column is present, let the
    user select a row to view its full hyperparameters below the table.
    The raw hyperparameter string is never shown inline in the grid —
    only in the detail panel below, once a row is selected."""
    has_params = "best_params" in df.columns
    visible_columns = [c for c in df.columns if c != "best_params"]
    display_df = df[visible_columns].rename(columns=rename_map)

    if not has_params:
        st.dataframe(display_df, hide_index=True, use_container_width=True)
        return

    event = st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
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