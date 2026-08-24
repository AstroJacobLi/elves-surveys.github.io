# ELVES Surveys Website Design Review Checklist

This document turns the August 2026 design review into an implementation checklist. Work through it in order: fix functional responsive issues first, then establish the shared design system, then polish individual pages.

## Design direction

The site currently feels visually heavy because several emphasis signals are stacked together: large headings, `650–750` font weights, pill-shaped controls, borders, tinted card backgrounds, and shadows. The goal is a lighter scientific-data portal with:

- Clear information hierarchy and comfortable long-form reading.
- Consistent left edges, baselines, and vertical rhythm.
- Fewer framed surfaces and fewer pill-shaped elements.
- Restrained color used for survey identity and interaction, not decoration everywhere.
- Consistent behavior across desktop, tablet, and mobile.

Do not make all text smaller or center-align everything. Body copy should remain approximately `16px`; most of the improvement should come from reducing display sizes, font weights, visual chrome, and density.

## Recommended implementation order

1. Fix the P0 responsive and semantic problems.
2. Introduce shared typography and surface tokens.
3. Simplify the global header, footer, cards, buttons, and tags.
4. Polish the homepage and shared survey template.
5. Simplify Papers and Team.
6. Improve Catalogs and the standalone Explorer.
7. Run the final cross-page visual and accessibility checks.

## P0: functional and structural fixes

### Mobile data documentation

- [ ] Keep schema tables accessible below `860px`.
  - Current issue: `src/styles/global.css` hides every `.data-table-wrap` below `860px`, but `src/pages/catalogs/[survey]/index.astro` has no card fallback for Columns, Files, or Fields.
  - Do not apply the generic table-hiding rule to documentation/schema tables.
  - Prefer a horizontally scrollable table or a dedicated responsive schema layout.
  - Acceptance: every column name, type, unit, and description remains readable at 390px viewport width.

### Team page hierarchy

- [ ] Add a single visible `h1` to `/team/`.
  - Current issue: the page starts with `h2 Core Members` and has no `h1`.
  - Add a compact Team hero consistent with Papers and survey pages, or promote the page heading to `h1`.
  - Acceptance: generated `dist/team/index.html` contains exactly one `h1`, followed by logical `h2`/`h3` levels.

### Header and footer responsiveness

- [ ] Prevent the desktop navigation from wrapping awkwardly between approximately 861px and 1100px.
  - Move to the compact/mobile navigation earlier, reduce spacing, or provide a proper menu.
  - Acceptance: the logo and navigation remain optically aligned at 1024px, 900px, and 768px without a partially wrapped desktop nav.
- [ ] Make the mobile footer stack intentionally.
  - Current issue: the media query sets `grid-template-columns`, but `.site-footer__inner` remains `display:flex`.
  - Use `flex-direction: column` or switch it to grid.
  - Acceptance: both footer lines align cleanly at 390px without squeezing or excessive separation.

### Anchor positioning

- [ ] Account for the sticky header when navigating to in-page anchors.
  - Replace the current small `scroll-margin-top` with a value that clears the full sticky header, approximately `88–104px` depending on the final header.
  - Check survey `#data` links and all catalog product anchors.

### Explorer mobile layout

- [ ] Create a real mobile layout for `public/explorer/elves-dwarf/index.html`.
  - The current `900px` breakpoint only widens the right panel and hides the dock; the top bar and 250px left rail can still overflow.
  - Reduce the mobile top bar to brand, host selector, and menu.
  - Move secondary controls and filters into a drawer or sheet.
  - Ensure controls have approximately `40–44px` touch targets.
  - Acceptance: no horizontal overflow and no inaccessible controls at 390px and 768px.

## P1: shared design system

### Typography

- [ ] Define one responsive type scale in `src/styles/global.css`.
  - Suggested desktop page/display `h1`: `clamp(2.4rem, 4vw, 3.2rem)`.
  - Suggested `h2`: approximately `1.7–1.9rem`.
  - Suggested `h3`: approximately `1.05–1.15rem`.
  - Keep body copy near `1rem` with approximately `1.6` line height.
  - Use slightly smaller values for compact page heroes where appropriate.
- [ ] Reduce common font weights.
  - General headings: approximately `580–600`.
  - Buttons and important links: approximately `600`.
  - Eyebrows, tags, metadata, and filters: approximately `600–650`, not `700–750` everywhere.
- [ ] Remove inline typography from `src/pages/index.astro`.
  - Move the homepage `h1`, lede, and section-heading sizes into named CSS classes.
  - Acceptance: responsive media rules control these elements without inline overrides.
- [ ] Fix the homepage acronym line height.
  - Current `.acronym-phrase` uses `line-height: 0.5` on desktop.
  - Use approximately `1.1–1.2`, especially when the phrase wraps.
  - Reduce the base phrase weight and use moderate emphasis only on the acronym letters.
- [ ] Limit long prose to roughly `68–75ch`.
  - Apply this to survey overviews, page introductions, and explanatory text.

### Alignment and spacing

- [ ] Establish a consistent content grid.
  - Hero copy, section headings, cards, tables, figures, and captions should share stable left edges.
  - Center only diagrams, loading states, and content that genuinely benefits from centering.
- [ ] Normalize section spacing.
  - Define standard compact, normal, and major section gaps.
  - Avoid cases where `page-section--compact` has more padding than a normal section unless the name and behavior are clarified.
- [ ] Align split headings by text baseline rather than relying only on `align-items:end`.
- [ ] Review mobile spacing separately; do not simply reuse large desktop section padding after collapsing to one column.

### Surfaces, cards, and controls

- [ ] Reduce the default card shadow substantially or remove it.
  - Prefer a thin border, subtle tinted background, or very soft shadow—not all three.
- [ ] Reduce nested framed surfaces.
  - Avoid a bordered card containing multiple bordered stat chips, pills, callouts, and divided footers.
- [ ] Reduce pill usage.
  - Keep pills for selected filters, compact statuses, or genuinely categorical tags.
  - Render ordinary links, counts, and metadata as text where possible.
- [ ] Standardize buttons.
  - Use one primary, one secondary, and one quiet/text-link style.
  - Reduce button font weight to approximately `600`.
  - Preserve at least 44px target size for primary navigation actions.
- [ ] Use sentence case consistently in headings and controls unless a true proper noun requires otherwise.

## P2: global navigation and footer

- [ ] Rebalance the header wordmark and navigation.
  - Consider reducing the desktop icon from 60px and the wordmark weight from 700.
  - Ensure the header does not dominate compact pages.
- [ ] Evaluate whether `Data` should be a first-class navigation destination.
  - `/catalogs/` is currently discoverable mainly through Documentation links in product tables.
  - If it is not added to the main nav, provide a prominent, consistent Data documentation link on every survey page.
- [ ] Make active navigation states lighter.
  - The active item should be recognizable without looking like another large button.
- [ ] Ensure the Explorer dropdown remains keyboard accessible after any navigation redesign.
- [ ] Keep footer alignment and spacing consistent with the main content container.

## P2: homepage (`/`)

Files: `src/pages/index.astro`, `src/components/AcronymReveal.astro`, `src/components/LocalVolumeMap.astro`, `src/components/SurveyCard.astro`.

### Hero

- [ ] Reduce the homepage title slightly and rely on the shared type scale.
- [ ] Remove the inline `font-family: sans-serif` override around `ELVES` unless there is a deliberate brand reason for it.
- [ ] Make the acronym expansion a quiet explanatory line rather than a second headline.
- [ ] Keep the introductory paragraph at normal readable body size; do not make it tiny to compensate for the large heading.
- [ ] Slightly reduce the Local Volume map and optically center it against the copy column.
- [ ] Keep the map legend aligned with the map and avoid switching alignment without a clear reason on mobile.

### Survey cards

- [ ] Simplify the three survey cards.
  - Remove the large shadow.
  - Use a white or nearly white background.
  - Preserve survey identity with a small accent line, dot, or restrained border color.
  - Replace nested statistic boxes with a simple two-column statistic row.
- [ ] Ensure titles, descriptions, statistics, and actions align across all three cards.
- [ ] Check that cards remain balanced when one survey has a different number of statistics.

### Featured papers

- [ ] Create a lighter homepage variant of the paper card.
  - Show title, authors/year, one short summary, and one primary link.
  - Avoid reproducing the full bibliography card with all badges and actions.

### Data access

- [ ] Reduce duplication between survey cards and the three Data access cards.
  - Consider a compact three-column link strip instead of another row of large bordered cards.
- [ ] Make Documentation a visible action where released documentation exists.

### Contact and citation

- [ ] Change `Contact and Citation` to sentence case if the rest of the site uses sentence case.
- [ ] Collapse BibTeX behind a `Show BibTeX`/`details` interaction instead of showing a large code block by default.
- [ ] Keep the citation text and copy action visually subordinate to primary page content.

## P2: survey pages (`/elves/`, `/elves-dwarf/`, `/elves-field/`)

Files: `src/pages/[slug]/index.astro`, `src/components/DataProducts.astro`, `src/components/PaperList.astro`.

### Survey hero

- [ ] Reduce survey-page `h1` and lede sizes by roughly 10–15% from their current values.
- [ ] Top-align hero copy and metadata instead of using bottom alignment.
- [ ] Simplify the metadata presentation.
  - Avoid a tall left border that must visually align with variable-height copy.
  - Use a compact definition list or simple statistic row.

### Overview

- [ ] Remove redundant hierarchy between `Survey snapshot` and `Overview`, or make the eyebrow much quieter.
- [ ] Constrain overview prose to a readable line length.
- [ ] On ELVES-Dwarf, center the scientific figure within its content area while keeping the caption left-aligned with the image.
- [ ] Confirm the wide figure scroll behavior remains discoverable and does not cause page-level horizontal scrolling.

### Papers and data products

- [ ] Use the same lighter paper-card treatment defined for the Papers page.
- [ ] Keep released data prominent, but render unreleased products as a compact `Planned products` list.
- [ ] Do not show full rows of `[Pending]` placeholders in production-facing tables.
- [ ] Align Papers and Data products section spacing and heading structure.

## P2: Papers (`/papers/`)

Files: `src/pages/papers/index.astro`, `src/components/PaperList.astro`.

- [ ] Remove hierarchy duplication among `Papers`, `All papers`, and `Filtered bibliography`.
- [ ] Simplify the filter panel.
  - Remove or soften the outer framed panel.
  - Reduce filter-button weight.
  - Use compact select controls on small screens if the pill rows become crowded.
- [ ] Simplify each paper entry.
  - Title and authors/year should be the primary hierarchy.
  - Use normal roman text for descriptions; do not italicize every summary.
  - Keep at most one subtle accent such as a left rule.
  - Combine type, citation count, and survey associations into quiet metadata.
  - Reserve button styling for ADS and Published Version actions.
- [ ] Reduce paper title size and weight slightly.
- [ ] Consider separators and whitespace instead of a complete border around every paper.
- [ ] Acceptance: scanning 8–10 papers should not look like scanning a stack of independent dashboard widgets.

## P2: Team (`/team/`)

Files: `src/pages/team/index.astro`, `src/components/TeamMemberCard.astro`.

- [ ] Add the page-level `h1` described in P0.
- [ ] Use a consistent portrait-friendly image ratio, such as `4:5` or near-square.
- [ ] Support per-person `object-position` where needed so faces are not cropped poorly.
- [ ] Remove or substantially soften card shadows.
- [ ] Test three columns versus four columns at wide desktop sizes; choose the layout with better breathing room and name wrapping.
- [ ] Left-align role text with the rest of the card.
- [ ] Use `margin-top:auto` if roles or tags should align along the card bottoms.
- [ ] Replace the collaborator flex list with `repeat(auto-fit, minmax(...))` grid so the final row remains orderly.
- [ ] Ensure email addresses wrap without changing card widths or alignment.

## P2: Catalog landing page (`/catalogs/`)

File: `src/pages/catalogs/index.astro`.

- [ ] Reduce repetition between the hero title and `Documented surveys` section heading.
- [ ] Make released surveys and their available products easy to scan without a large card for sparse content.
- [ ] Keep version, release date, and format metadata visually quiet.
- [ ] Provide a clear route back to the relevant survey page.

## P2: Catalog detail page (`/catalogs/elves-dwarf/`)

Files: `src/pages/catalogs/[survey]/index.astro`, `src/components/FootprintViewer.astro`.

- [ ] Replace the large row of bold product pills with a lighter table of contents.
  - Consider a sticky side TOC on desktop and a compact jump menu on mobile.
- [ ] Reorganize each product section in this order:
  1. Description and release facts.
  2. Primary download action.
  3. Quick read/example code.
  4. Column or field documentation.
  5. Viewer and individual files where relevant.
- [ ] Reduce visual competition among facts, download buttons, code blocks, viewers, tables, and file lists.
- [ ] Make schema tables less than the current generic `940px` minimum where possible.
- [ ] Consider combining Type and Unit into a compact metadata column on smaller desktop/tablet widths.
- [ ] Keep the column filter visually aligned with the table heading.
- [ ] Reduce bold text in the Footprint Viewer controls and legend.
- [ ] Preserve keyboard focus states and table-region accessibility.

## P2: standalone Explorer

File: `public/explorer/elves-dwarf/index.html`.

- [ ] Add a visible `Back to ELVES Surveys` link or make the brand clickable.
- [ ] Retain the specialized dark map interface, but connect it to the main-site brand through logo, color, and navigation.
- [ ] Reduce glass-panel shadow strength so the sky map remains the visual focus.
- [ ] Increase tiny labels and controls where feasible; several are currently approximately `9.5–12.5px`.
- [ ] Ensure active states do not rely only on color.
- [ ] Add safe-area padding for modern mobile devices.
- [ ] Test loading, empty, failed-network, and no-cutout states.

## Content cleanup that affects visual polish

- [ ] Replace or hide production-facing placeholder strings such as `[Version pending]`, `[Download link pending]`, and `[Citation text pending]`.
- [ ] Present unavailable releases as planned work rather than broken-looking data rows.
- [ ] Review capitalization across headings: `Core Members`, `Contact and Citation`, and similar labels should follow one convention.
- [ ] Keep labels short enough that buttons and pills do not wrap unpredictably.

## Final validation checklist

### Viewports

- [ ] Desktop: 1440px wide.
- [ ] Small laptop: 1024px wide.
- [ ] Tablet: 768px wide.
- [ ] Mobile: 390px wide.
- [ ] Narrow mobile: 320px wide where practical.

### Pages

- [ ] `/`
- [ ] `/elves/`
- [ ] `/elves-dwarf/`
- [ ] `/elves-field/`
- [ ] `/papers/`
- [ ] `/team/`
- [ ] `/catalogs/`
- [ ] `/catalogs/elves-dwarf/`
- [ ] `/explorer/elves-dwarf/`

### Quality gates

- [ ] Run `npm run build` successfully.
- [ ] Confirm exactly one `h1` per main Astro page.
- [ ] Confirm no page-level horizontal scrolling at the target viewports.
- [ ] Confirm all schema documentation remains available on mobile.
- [ ] Confirm sticky navigation does not cover anchor targets.
- [ ] Confirm keyboard access to navigation, Explorer menu, paper filters, citation tabs, tables, and Footprint Viewer controls.
- [ ] Confirm visible focus indicators on all interactive controls.
- [ ] Confirm touch targets are appropriately sized on mobile.
- [ ] Test `prefers-reduced-motion: reduce`.
- [ ] Compare all pages together before accepting page-specific CSS; the shared design system should remain consistent.

## Suggested definition of done

The redesign is complete when the site feels calmer without losing scientific clarity: body text remains readable, headings no longer dominate, cards do not look nested, metadata stays subordinate, all pages align to a consistent grid, mobile documentation is fully usable, and the Explorer remains powerful without becoming a navigation or responsive dead end.
