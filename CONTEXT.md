# Angels Academy — Session Context for Continuation

## Project Overview
Custom-branded Kolibri (v0.20.0.dev0) for Angels for Education foundation as "Angels Academy".
- **Fork:** `github.com/judicandus/kolibri`, branch `angels/main`
- **Docker:** `docker/angels/` — port 9090, rebuild: `docker compose -f ~/kolibri/docker/angels/docker-compose.yml up -d --build`
- **Production data from RPi:** mounted at `/tmp/angels-kolibri-data/`
- **Credentials:** Angels_LA / 123456 (learner), admin / admin123 (admin)
- **RPi SSH:** `ssh angels`, KOLIBRI_HOME at `/home/angels/kolibri_data`
- **Kolibri installed from source:** Dockerfile does `pip install .` (NOT from PyPI) to keep Python+JS in sync

## Key Files
- **Theme plugin:** `kolibri/plugins/angels_theme/kolibri_plugin.py` — ALL CSS/JS injection + theme config
- **Toggle JS:** `kolibri/plugins/angels_theme/static/assets/angels_theme/theme-toggle.js` — dark/light toggle
- **Static assets:** `kolibri/plugins/angels_theme/static/assets/angels_theme/` — logos, fonts, background
- **Docker:** `docker/angels/Dockerfile`, `docker/angels/docker-compose.yml`, `docker/angels/rebrand.sh`
- **README:** `README.md` — full documentation of all customizations
- **Design mockups:** `/home/judicandus/Downloads/Kolibri/2026.02.28.NovoPacote/KOLIBRI_Mokcup_Vclara.pdf` — latest spec from the team

## Technical Constraints
- **CSP:** `script-src 'self' blob:` — JS must be external files, NOT inline. CSS inline is OK (`style-src 'unsafe-inline'`).
- **CSS injection:** Python `.format()` in `kolibri_plugin.py` — literal braces must be `{{` / `}}`.
- **No upstream modifications:** All customizations via theme plugin + Docker build-time patching.
- **Dark mode mechanism:** `data-theme="dark"` attribute on `<html>`, toggled by `theme-toggle.js`, persisted in `localStorage` key `angels-theme`.
- **MutationObserver:** In `theme-toggle.js`, watches DOM for side nav styling (active links, menus).
- **Floorp MCP:** Browser automation available but screenshots/PDF reads crash the session — avoid using screenshot tool and reading PDFs.
- **JS bundles are pre-built:** The JS bundles in `kolibri/dist/` were built before and do NOT contain newer features like `brandedFooter` in SideNav. Any new UI must be done via CSS injection or `theme-toggle.js`, NOT by relying on theme config features that aren't in the built bundles. Rebuilding frontend requires: `export PATH="/tmp/node-v20.19.0-linux-x64/bin:$PATH" && source /tmp/kolibri-venv/bin/activate && KOLIBRI_RUN_MODE=dev pnpm run build`

## What Is Complete
- [x] Theme plugin with brand colors, logos, sign-in page
- [x] Open Sans font integration (woff2 bundled, weights 300/400/700 confirmed with team)
- [x] Text rebranding (Kolibri → Angels Academy) via `rebrand.sh`
- [x] Login page (high-res background, SVG logo, hidden title/footer)
- [x] Login page dark mode: logo inverts to white (`html[data-theme="dark"] .box > img.logo`), footer bar matches box blue
- [x] App bar (dark blue #213953, white text, green leaf icon, PNG icon)
- [x] Background gradients (light: linear blue, dark: radial navy)
- [x] Dark/light toggle (floating button, localStorage persistence)
- [x] Side nav full redesign (logo in header, avatar circle, Hello prefix, points pill, green icons, rounded menus)
- [x] Side nav footer: "Angels for Education" logo via CSS `::before` pseudo-element (blue in light mode, inverted white in dark mode)
- [x] Dark mode: side nav, content cards, SVGs
- [x] Dark mode: Profile page (transparent content area)
- [x] Dark mode: Downloads page (transparent content + dark bottom bar)
- [x] Dark mode: Library page filter side panel
- [x] Dark mode: TopicsPage header (transparent) + ImmersivePage toolbar (dark blue)
- [x] Home page hero card (ContinueLearning.vue) + Recently Accessed section (RecentlyAccessed.vue)
- [x] Full-bleed card images (HybridLearningContentCard, HybridLearningLessonCard, ResourceCard)
- [x] SVG logos for sidebar and login (swapped from PNG for crispness + size savings)
- [x] App bar icon stays PNG (SVG had sizing issues at 36px height)

## Current Active Work / Next Steps

### Upcoming: Search Bar on Home Page
The design mockup (`KOLIBRI_Mokcup_Vclara.pdf` page 1) shows a rounded search bar spanning the top of the home page content area, labeled "Search". The existing Library page has a search bar ("Find something to learn") that searches all available material across all classes. The user wants to explore implementing a similar search bar on the home page. This was the topic being discussed when the session ended.

**Approach considerations:**
- The Library search uses Kolibri's built-in search/filter system
- Adding a search bar to the home page could either: (a) redirect to Library with the search query pre-filled, or (b) be a CSS-only visual change that styles an existing element
- Since JS bundles can't be modified without a full rebuild, a redirect approach via CSS+JS in `theme-toggle.js` is most feasible
- Need to review the mockup PDF carefully (but NOTE: reading PDFs crashes the session — ask the user to describe the design or open it themselves)

### Previously Resolved Issues
- Card thumbnail letterboxing: CSS overrides added in theme plugin
- Dark mode thumbnail placeholder: CSS override added
- Home page hero card + recently accessed: implemented and working
- Login page logo dark/light mode: fixed (selector was `.sign-in-page .logo img`, corrected to `.box > img.logo`)
- Login footer bar dark mode: matches box blue
- Side nav footer logo: injected via CSS `::before` (brandedFooter theme config exists in code but NOT in built JS bundles)

## Color Palette Reference
| Role | Hex |
|------|-----|
| Primary (navy) | `#213953` |
| Primary dark | `#1a2e43` |
| Secondary (green) | `#a6c52e` |
| Secondary dark | `#859e25` |
| Dark bg center | `#253547` |
| Dark bg edge | `#0c131b` |
| Dark surface | `#1a2e43` |
| Dark card | `#1e3550` |
| Light text | `#e0e0e0` |
| Input border dark | `#3a5570` |
| Placeholder text | `#8899aa` |

## Side Nav Design (for reference)
- Header: X button + horizontal SVG logo via CSS `background-image` on `.side-nav-header-name` (text hidden `font-size: 0`)
- User info: CSS Grid (avatar `::before`, "Hello," prefix `b::before`, points pill)
- Active menu: green (#a6c52e) backdrop via JS (MutationObserver detects computed bg-color)
- Sub-routes (Home/Library/Bookmarks): white default, green active — JS checks font-weight
- Footer: visible, text hidden (`.side-nav-scrollable-area-footer-info { display: none }`), logo injected via `::before` pseudo-element using `background: url(...)` pointing to `logo-angels-for-education-full.svg`
- Dark mode: navy bg (#1a2e43), header (#213953), footer logo inverted to white

## Logo Files Reference
All in `kolibri/plugins/angels_theme/static/assets/angels_theme/`:
- `logo-icon-green.png` — circular green icon (app bar header + PWA icons)
- `logo-icon-green.svg` — SVG version (NOT used for app bar due to sizing issues at 36px)
- `logo-academy-horizontal-green.svg` — horizontal "Angels Academy" logo (sidebar header)
- `logo-angels-for-education-new.svg` — "Angels for Education" blue logo WITHOUT "sponsored by" text (login page)
- `logo-angels-for-education-full.svg` — "Angels for Education" blue logo WITH "sponsored by vicky" text (side nav footer)
- `login-background.jpg` — high-res login background (1.9MB, replaced from team's `bg_kolibrilogin_academy.jpg`)
- `fonts/open-sans-latin.woff2` + `fonts/open-sans-latin-ext.woff2` — variable font files (weight 300-700)

## Team Design Assets (received 2026-02-28)
Location: `/home/judicandus/Downloads/Kolibri/2026.02.28.NovoPacote/`
- `LOGO-ACADEMY-COMSOMBRA-01.svg` — full stacked logo
- `LOGO-ACADEMY-COMSOMBRA-02.svg` — horizontal "academy" logo (used for sidebar)
- `LOGO-ACADEMY-COMSOMBRA-03.svg` — icon variant
- `LOGO-ACADEMY-COMSOMBRA-04.svg` — circular green icon
- `Marca_AngelsforEducation_AZUL.svg` — blue "Angels for Education" (no "sponsored by" text)
- `Marca_AngelsforEducation_BRANCA.svg` — white version WITH "sponsored by vicky" text
- `Marca_AngelsforEducation_AZUL_completa.svg` — blue version WITH "sponsored by" (created by us from white version)
- `bg_kolibrilogin_academy.jpg` — high-res login background
- `KOLIBRI_Mokcup_Vclara.pdf` — design mockup/specifications (DO NOT read this file with tools — it crashes the session)
- `Kolibri.docx` — additional specs
