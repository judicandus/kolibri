from django.templatetags.static import static
from django.utils.safestring import mark_safe

from kolibri.core import theme_hook
from kolibri.core.hooks import FrontEndBaseHeadHook
from kolibri.plugins import KolibriPluginBase
from kolibri.plugins.hooks import register_hook


class AngelsThemePlugin(KolibriPluginBase):
    pass


@register_hook
class AngelsThemeHeadHook(FrontEndBaseHeadHook):
    """Inject Open Sans font, background gradient, leaf icon fix, dark/light toggle."""

    @property
    def head_html(self):
        latin = static("assets/angels_theme/fonts/open-sans-latin.woff2")
        latin_ext = static("assets/angels_theme/fonts/open-sans-latin-ext.woff2")
        toggle_js = static("assets/angels_theme/theme-toggle.js")
        logo_url = static("assets/angels_theme/logo-academy-horizontal-green.png")
        favicon_url = static("assets/angels_theme/logo-icon-favicon.svg")
        return mark_safe(
            """
<link rel="icon" type="image/svg+xml" href="{favicon_url}">
<style>
/* --- Open Sans Font --- */
@font-face {{
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300 700;
  font-stretch: 100%;
  font-display: swap;
  src: url({latin_ext}) format('woff2');
  unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7,
    U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F,
    U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F,
    U+A720-A7FF;
}}
@font-face {{
  font-family: 'Open Sans';
  font-style: normal;
  font-weight: 300 700;
  font-stretch: 100%;
  font-display: swap;
  src: url({latin}) format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6,
    U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122,
    U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}}
body, button, input, select, textarea {{
  font-family: 'Open Sans', 'Noto Sans', sans-serif !important;
}}
/* Restore VideoJS icon font for media player controls */
[class*="vjs-icon"]::before {{
  font-family: VideoJS !important;
}}

/* --- AppBar: hide the plugin title text ("Learn") next to the logo --- */
.app-bar .k-toolbar-brand + span {{
  display: none !important;
}}
/* --- AppBar: make the logo larger --- */
.app-bar .k-toolbar-brand img {{
  max-height: 48px !important;
  max-width: 64px !important;
}}

/* --- AppBar points: pill style matching side nav --- */
.app-bar span:has(> .points-description) {{
  display: inline-flex !important;
  align-items: center;
  background-color: #1a2e43 !important;
  border-radius: 20px;
  padding: 4px 14px 4px 8px;
  margin-right: 8px;
  vertical-align: middle;
  position: relative;
  top: -1px;
}}
.app-bar .points-description {{
  color: #ffffff !important;
  font-weight: bold;
  font-size: 14px;
  margin-left: 6px;
}}
.app-bar span:has(> .points-description) svg {{
  fill: #a6c52e !important;
  width: 18px !important;
  height: 18px !important;
}}

/* --- Background gradient (light theme default) --- */
html:not([data-theme="dark"]) {{
  background: linear-gradient(135deg, #e8eef5 0%, #f5f7fa 50%, #e0e8f0 100%) !important;
  min-height: 100vh;
}}
html:not([data-theme="dark"]) body,
html:not([data-theme="dark"]) .scrolling-pane,
html:not([data-theme="dark"]) .main-wrapper {{
  background: transparent !important;
}}

/* --- Dark theme overrides --- */
html[data-theme="dark"] {{
  background: radial-gradient(ellipse at center, #253547 0%, #0c131b 100%) !important;
  min-height: 100vh;
}}
html[data-theme="dark"] body,
html[data-theme="dark"] .scrolling-pane,
html[data-theme="dark"] .main-wrapper {{
  background: transparent !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .card-main-wrapper,
html[data-theme="dark"] .box {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}

/* --- Profile & Downloads pages: make the main content wrapper transparent --- */
html[data-theme="dark"] #main.main-wrapper {{
  background-color: transparent !important;
  background: transparent !important;
}}
/* KPageContainer inner wrapper */
html[data-theme="dark"] .main-wrapper > div {{
  background-color: transparent !important;
}}
/* Profile/Downloads table text */
html[data-theme="dark"] .main-wrapper th,
html[data-theme="dark"] .main-wrapper td,
html[data-theme="dark"] .main-wrapper h1,
html[data-theme="dark"] .main-wrapper h2,
html[data-theme="dark"] .main-wrapper p,
html[data-theme="dark"] .main-wrapper span,
html[data-theme="dark"] .main-wrapper a,
html[data-theme="dark"] .main-wrapper label {{
  color: #e0e0e0 !important;
}}

/* --- Downloads page: BottomAppBar dark mode --- */
html[data-theme="dark"] .bottom {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}

/* --- Library page: SearchFiltersPanel (side-panel) dark mode --- */
html[data-theme="dark"] .side-panel {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .side-panel h2,
html[data-theme="dark"] .side-panel label,
html[data-theme="dark"] .side-panel span,
html[data-theme="dark"] .side-panel p,
html[data-theme="dark"] .side-panel a {{
  color: #e0e0e0 !important;
}}
/* Search input box in side panel */
html[data-theme="dark"] .side-panel input {{
  background-color: #253547 !important;
  color: #e0e0e0 !important;
  border-color: #3a5570 !important;
}}
html[data-theme="dark"] .side-panel input::placeholder {{
  color: #8899aa !important;
}}
/* Category list buttons in side panel */
html[data-theme="dark"] .side-panel button {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .side-panel button:hover {{
  background-color: #253547 !important;
}}
/* Dropdown selects in side panel */
html[data-theme="dark"] .side-panel select,
html[data-theme="dark"] .side-panel .ui-select {{
  background-color: #253547 !important;
  color: #e0e0e0 !important;
  border-color: #3a5570 !important;
}}
/* Checkbox styling */
html[data-theme="dark"] .side-panel .ui-checkbox__checkmark-background {{
  border-color: #8899aa !important;
}}
/* Side panel SVG icons */
html[data-theme="dark"] .side-panel svg {{
  fill: #e0e0e0 !important;
}}
html[data-theme="dark"] .content-card {{
  background-color: #1e3550 !important;
  color: #e0e0e0 !important;
}}
/* Section header icons and general SVG icons → white in dark mode */
html[data-theme="dark"] .main-wrapper svg,
html[data-theme="dark"] .scrolling-pane svg {{
  fill: #e0e0e0 !important;
}}
/* Keep AppBar icons unchanged (they're already on dark background) */
html[data-theme="dark"] .app-bar [aria-label="Points earned"] svg {{
  fill: #a6c52e !important;
}}

/* ===== SIDE NAV REDESIGN (both modes) ===== */

/* Replace header title text with logo image */
.side-nav-header {{
  display: flex !important;
  align-items: center !important;
}}
.side-nav-header-name {{
  font-size: 0 !important;
  line-height: 0 !important;
  display: block !important;
  flex: 1;
  height: 48px;
  background: url('{logo_url}') left center / contain no-repeat;
  margin-left: 4px;
}}
/* Hide the original logo in the scrollable area (now in header) */
.side-nav .logo {{
  display: none !important;
}}

/* Side nav footer: show logo, hide text */
.side-nav-scrollable-area-footer {{
  display: block !important;
  text-align: center;
}}
.side-nav-scrollable-area-footer-info {{
  display: none !important;
}}
.side-nav-scrollable-area-footer::before {{
  content: '';
  display: block;
  width: 80%;
  height: 64px;
  margin: 0 auto 8px;
  background: url('{sidenav_footer_logo}') center / contain no-repeat;
}}
html[data-theme="dark"] .side-nav-scrollable-area-footer::before {{
  filter: brightness(0) invert(1);
}}

/* Hide username and role lines */
.side-nav .user-information p {{
  display: none !important;
}}

/* User info: avatar left, text right in column, points far right */
.side-nav .user-information {{
  display: grid !important;
  grid-template-columns: 40px 1fr auto;
  grid-template-rows: auto auto;
  align-items: center;
  column-gap: 12px;
  row-gap: 0;
  padding-right: 16px;
  margin-top: 16px !important;
  margin-left: 16px !important;
}}
/* Avatar circle */
.side-nav .user-information::before {{
  content: '';
  display: block;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #a6c52e url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>') center/24px no-repeat;
  flex-shrink: 0;
  grid-row: 1 / 3;
  grid-column: 1;
}}
/* "Hello," on first line */
.side-nav .user-information b {{
  grid-column: 2;
  grid-row: 1 / 3;
  line-height: 1.3;
}}
.side-nav .user-information b::before {{
  content: 'Hello,';
  display: block;
  color: #a6c52e;
  font-weight: normal;
  font-size: 13px;
}}
/* Points badge: dark blue pill, no border */
.side-nav .points-wrapper {{
  float: none !important;
  display: inline-flex !important;
  align-items: center;
  background-color: #213953 !important;
  border: none !important;
  border-radius: 20px;
  padding: 4px 14px 4px 6px;
  margin: 0 !important;
  grid-column: 3;
  grid-row: 1 / 3;
}}
.side-nav .points-wrapper .icon-wrapper {{
  background-color: transparent !important;
  width: 28px !important;
  height: 28px !important;
}}
.side-nav .points-wrapper .icon-wrapper svg {{
  fill: #a6c52e !important;
  width: 22px !important;
  height: 22px !important;
}}
.side-nav .points-wrapper .description {{
  color: #ffffff !important;
  font-weight: bold;
  font-size: 14px;
}}

/* Active menu item: green background, rounded */
.side-nav .core-menu-option {{
  border-radius: 8px !important;
}}

/* Menu icons: green */
.side-nav .ui-menu svg {{
  fill: #a6c52e !important;
}}

/* Bottom menu items (My downloads, Profile, Sign out, Change language): bold white */
html[data-theme="dark"] .side-nav .core-menu-option {{
  color: #ffffff !important;
  font-weight: bold !important;
}}

/* Sub-route links: base white in dark mode (JS handles active=green) */
html[data-theme="dark"] .side-nav .link {{
  color: #ffffff !important;
  text-decoration: none !important;
}}

/* ===== SIDE NAV: DARK MODE ===== */
html[data-theme="dark"] .side-nav {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .side-nav-header {{
  background-color: #213953 !important;
  color: #ffffff !important;
}}
html[data-theme="dark"] .side-nav .ui-menu {{
  background-color: #1a2e43 !important;
}}
html[data-theme="dark"] .side-nav .ui-menu-option:hover {{
  background-color: #253547 !important;
}}
html[data-theme="dark"] .side-nav .user-information b {{
  color: #ffffff !important;
}}
html[data-theme="dark"] .side-nav svg {{
  fill: #e0e0e0 !important;
}}
/* Keep green for menu icons and points leaf */
html[data-theme="dark"] .side-nav .ui-menu svg,
html[data-theme="dark"] .side-nav .points-wrapper .icon-wrapper svg {{
  fill: #a6c52e !important;
}}

/* ============================================================
   FULL-BLEED CARD IMAGES
   Core technique: span.thumbnail becomes position:static so
   the <img> (already position:absolute) escapes to the
   card-link container and covers the entire card.
   ============================================================ */

/* --- 1. HybridLearningContentCard (Library / Topics grids) ---
   Structure: div.card.drop-shadow > a.card.card-link >
              [div.header-bar + span.thumbnail + div.text]
*/
.drop-shadow > .card-link {{
  position: relative !important;
  overflow: hidden !important;
  height: 200px !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-end !important;
}}
.drop-shadow > .card-link > .header-bar {{
  display: none !important;
}}
.drop-shadow > .card-link span.thumbnail {{
  position: static !important;
  background-color: transparent !important;
  height: 0 !important;
  padding: 0 !important;
}}
.drop-shadow > .card-link span.thumbnail > img.image,
.drop-shadow > .card-link span.thumbnail > img {{
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  object-fit: cover !important;
  object-position: 75% center !important;
  margin: 0 !important;
  z-index: 1 !important;
}}
/* Text overlay at bottom */
.drop-shadow > .card-link > .text {{
  position: relative !important;
  z-index: 5 !important;
  height: auto !important;
  padding-bottom: 12px !important;
}}
.drop-shadow > .card-link > .text::before {{
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 200%;
  background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.65) 100%);
  z-index: -1;
  pointer-events: none;
}}
.drop-shadow > .card-link > .text .title {{
  color: #ffffff !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
}}
/* Hide thumbnail placeholder icon when image present */
.drop-shadow > .card-link span.thumbnail .icon {{
  z-index: 0 !important;
}}

/* --- 2. HybridLearningLessonCard (Lesson playlist page) ---
   Structure: div.card.drop-shadow > a.card.card-content >
              [div.thumbnail + h3.title + LearningActivityLabel + div.footer]
*/
.drop-shadow > .card-content {{
  position: relative !important;
  overflow: hidden !important;
  height: auto !important;
  min-height: 156px !important;
}}
.drop-shadow > .card-content > .thumbnail {{
  position: static !important;
  display: block !important;
  width: auto !important;
  margin: 0 !important;
}}
.drop-shadow > .card-content > .thumbnail span.thumbnail {{
  position: static !important;
  background-color: transparent !important;
  height: 0 !important;
  padding: 0 !important;
}}
.drop-shadow > .card-content > .thumbnail span.thumbnail > img.image,
.drop-shadow > .card-content > .thumbnail span.thumbnail > img {{
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  object-fit: cover !important;
  object-position: 75% center !important;
  margin: 0 !important;
  z-index: 1 !important;
}}
.drop-shadow > .card-content > .title,
.drop-shadow > .card-content > .title * {{
  position: relative !important;
  z-index: 5 !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
}}
.drop-shadow > .card-content > .title {{
  margin-top: 80px !important;
}}
.drop-shadow > .card-content > .learning-activity-label,
.drop-shadow > .card-content > .learning-activity-label * {{
  z-index: 5 !important;
  color: #ffffff !important;
}}
.drop-shadow > .card-content > .learning-activity-label svg {{
  fill: #ffffff !important;
}}
.drop-shadow > .card-content > .footer,
.drop-shadow > .card-content > .footer * {{
  position: relative !important;
  z-index: 5 !important;
  color: #ffffff !important;
}}
.drop-shadow > .card-content > .footer svg {{
  fill: #ffffff !important;
}}
/* Gradient overlay for lesson cards */
.drop-shadow > .card-content::after {{
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 70%;
  background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.6) 100%);
  z-index: 2;
  pointer-events: none;
}}
.drop-shadow > .card-content > .title,
.drop-shadow > .card-content > .learning-activity-label,
.drop-shadow > .card-content > .footer {{
  z-index: 5 !important;
}}

/* --- 2b. BaseCard/LessonCard with thumbnail (Class assignments page) ---
   Structure: a.card-link.card-link-with-thumbnail >
              [img.card-thumbnail + div + div.progress]
*/
.card-link-with-thumbnail {{
  position: relative !important;
  overflow: hidden !important;
  min-height: 180px !important;
}}
/* Gradient overlay */
.card-link-with-thumbnail::after {{
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 70%;
  background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.65) 100%);
  z-index: 2;
  pointer-events: none;
}}
/* Push content to bottom */
.card-link-with-thumbnail > div:first-of-type {{
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-end !important;
  flex: 1 !important;
  position: relative !important;
  z-index: 5 !important;
}}
/* Title: white, bold, shadow */
.card-link-with-thumbnail .title,
.card-link-with-thumbnail .title * {{
  color: #ffffff !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
}}
/* Progress: white */
.card-link-with-thumbnail .progress,
.card-link-with-thumbnail .progress * {{
  position: relative !important;
  z-index: 5 !important;
  color: #ffffff !important;
}}
.card-link-with-thumbnail .progress svg {{
  fill: #ffffff !important;
}}

/* --- 3. ResourceCard (Home page "Recently accessed" vertical) ---
   Structure: div.resource-card-outer > a.card-link.base-card >
              [div > KFixedGrid + collectionTitle + h3.title] + div.progress
*/
.resource-card-outer {{
  border-radius: 12px !important;
  overflow: hidden !important;
}}
.resource-card-outer .card-link {{
  position: relative !important;
  overflow: hidden !important;
  padding: 0 !important;
  height: 200px !important;
}}
.resource-card-outer span.thumbnail {{
  position: static !important;
  background-color: transparent !important;
  border-radius: 0 !important;
  overflow: visible !important;
  /* Remove the 16:9 placeholder padding so it doesn't push the title off-card */
  height: 0 !important;
  padding: 0 !important;
}}
.resource-card-outer span.thumbnail > img.image,
.resource-card-outer span.thumbnail > img {{
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  object-fit: cover !important;
  object-position: 75% center !important;
  margin: 0 !important;
  z-index: 1 !important;
  display: block !important;
}}
/* Content wrapper: flex pushes text to bottom */
.resource-card-outer .card-link > div:first-child {{
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-end !important;
  flex: 1 !important;
  padding: 0 !important;
  position: static !important;
}}
/* Gradient overlay */
.resource-card-outer .card-link::after {{
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 50%;
  background: linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.7) 100%);
  z-index: 3;
  pointer-events: none;
}}
/* KFixedGrid: collapse to zero height, let img escape to card-link */
.resource-card-outer .card-link > div:first-child > div:first-child {{
  height: 0 !important;
  margin: 0 !important;
  overflow: visible !important;
}}
/* All wrappers inside KFixedGrid: ensure no positioned ancestors (except img) */
.resource-card-outer .card-link > div:first-child > div:first-child *:not(img) {{
  position: static !important;
  overflow: visible !important;
}}
/* Hide the activity label grid item */
.resource-card-outer .card-link > div:first-child > div:first-child .pure-g > div:last-child {{
  display: none !important;
}}
/* Text content: above gradient */
.resource-card-outer .card-link > div:first-child > div:nth-child(2),
.resource-card-outer .card-link > div:first-child > h3 {{
  position: relative !important;
  z-index: 5 !important;
  padding: 0 16px !important;
  margin-bottom: 4px !important;
}}
.resource-card-outer .title {{
  color: #ffffff !important;
  font-weight: 700 !important;
  text-shadow: 0 1px 3px rgba(0,0,0,0.5) !important;
  margin: 0 !important;
  height: auto !important;
}}
/* Collection title (class name) */
.resource-card-outer .card-link > div:first-child > div:nth-child(2),
.resource-card-outer .card-link > div:first-child > div:nth-child(2) * {{
  color: rgba(255,255,255,0.8) !important;
}}
/* Progress area */
.resource-card-outer .progress {{
  position: relative !important;
  z-index: 6 !important;
  padding: 4px 16px 12px !important;
}}
.resource-card-outer .progress,
.resource-card-outer .progress * {{
  color: #ffffff !important;
}}
.resource-card-outer .progress svg {{
  fill: #ffffff !important;
}}
/* Topic bar: hide on full-bleed cards */
.resource-card-outer .topic-bar {{
  z-index: 10 !important;
}}
/* ResourceCard padding adjustment */
.resource-card-outer .resource-card {{
  padding-top: 0 !important;
}}

/* --- Dark mode: fallback for no-image cards --- */
html[data-theme="dark"] .drop-shadow > .card-link,
html[data-theme="dark"] .drop-shadow > .card-content,
html[data-theme="dark"] .resource-card-outer .card-link {{
  background-color: #1a2e43 !important;
}}

/* --- TopicsPage (learning path) header: dark mode --- */
html[data-theme="dark"] .header {{
  background-color: transparent !important;
}}
html[data-theme="dark"] .header h1,
html[data-theme="dark"] .header span,
html[data-theme="dark"] .header a,
html[data-theme="dark"] .header p {{
  color: #e0e0e0 !important;
}}
/* ===== CONTENT / QUIZ PAGE: DARK MODE ===== */

/* LearningActivityBar / default toolbar: dark bg, white text & icons */
html[data-theme="dark"] .k-toolbar--type-default {{
  background-color: #213953 !important;
  color: #ffffff !important;
}}
html[data-theme="dark"] .k-toolbar--type-default .k-toolbar-title {{
  color: #ffffff !important;
}}
html[data-theme="dark"] .k-toolbar--type-default svg {{
  fill: #ffffff !important;
}}

/* ImmersiveToolbar (type-clear): white text & icons */
html[data-theme="dark"] .k-toolbar--type-clear.k-toolbar--text-color-black {{
  color: #ffffff !important;
}}
html[data-theme="dark"] .k-toolbar--type-clear.k-toolbar--text-color-black .k-toolbar-title {{
  color: #ffffff !important;
}}
html[data-theme="dark"] .k-toolbar--type-clear svg {{
  fill: #ffffff !important;
}}

/* Content area wrapper (overrides inline background-color: white) */
html[data-theme="dark"] .main .content {{
  background-color: transparent !important;
  color: #e0e0e0 !important;
}}

/* KPageContainer: dark background, light text */
html[data-theme="dark"] .page-container {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
  box-shadow: none !important;
}}
html[data-theme="dark"] .page-container h1,
html[data-theme="dark"] .page-container h2,
html[data-theme="dark"] .page-container h3,
html[data-theme="dark"] .page-container p,
html[data-theme="dark"] .page-container label {{
  color: #e0e0e0 !important;
}}

/* Quiz: BaseToolbar "Get N correct" bar → dark blue */
html[data-theme="dark"] .base-toolbar {{
  background-color: #213953 !important;
  color: #e0e0e0 !important;
  box-shadow: none !important;
}}
html[data-theme="dark"] .base-toolbar span {{
  color: #e0e0e0 !important;
}}

/* Quiz: content-wrapper (question area) → transparent */
html[data-theme="dark"] .content-wrapper {{
  background-color: transparent !important;
}}

/* Quiz: Perseus exercise div (scoped background: white) → transparent */
html[data-theme="dark"] .perseus {{
  background: transparent !important;
}}

/* Quiz: BottomAppBar attempts container → dark */
html[data-theme="dark"] .bottom.attempts-container {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .bottom.attempts-container .overall-status,
html[data-theme="dark"] .bottom.attempts-container .overall-status-text,
html[data-theme="dark"] .bottom.attempts-container .completed,
html[data-theme="dark"] .bottom.attempts-container .current-status {{
  color: #e0e0e0 !important;
}}

/* Perseus answer choices: override inline dark text color */
html[data-theme="dark"] .perseus-root .description {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .perseus-root .paragraph {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .perseus-root .perseus-renderer {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .perseus-root .instructions {{
  color: #b0bec5 !important;
}}
/* Perseus choice icon circles (A, B, C, D) */
html[data-theme="dark"] .perseus-root [data-testid="choice-icon__library-choice-icon"] {{
  border-color: rgba(224, 224, 224, 0.64) !important;
  color: rgba(224, 224, 224, 0.64) !important;
}}
/* Perseus choice separator/border */
html[data-theme="dark"] .perseus-root .perseus-widget-radio li {{
  border-color: #3a5570 !important;
}}
/* Perseus selected answer: green-tinted dark background */
html[data-theme="dark"] .perseus-root .perseus-widget-radio li.perseus-radio-selected {{
  background-color: rgba(166, 197, 46, 0.15) !important;
  border-color: #a6c52e !important;
  border-radius: 8px;
}}
/* Selected answer text → white */
html[data-theme="dark"] .perseus-root .perseus-widget-radio li.perseus-radio-selected .description,
html[data-theme="dark"] .perseus-root .perseus-widget-radio li.perseus-radio-selected .paragraph,
html[data-theme="dark"] .perseus-root .perseus-widget-radio li.perseus-radio-selected span {{
  color: #ffffff !important;
}}
/* Selected choice icon (A/B/C/D circle) → green instead of blue */
html[data-theme="dark"] .perseus-root .perseus-widget-radio li.perseus-radio-selected [data-testid="choice-icon__library-choice-icon"] {{
  background-color: #a6c52e !important;
  border-color: #a6c52e !important;
  color: #1a2e43 !important;
}}

/* ===== PDF VIEWER: DARK MODE ===== */

/* PDF sidebar (table of contents) */
html[data-theme="dark"] .pdf-sidebar {{
  background: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .pdf-sidebar a,
html[data-theme="dark"] .pdf-sidebar button,
html[data-theme="dark"] .pdf-sidebar span,
html[data-theme="dark"] .pdf-sidebar li {{
  color: #e0e0e0 !important;
}}
/* PDF controls bar */
html[data-theme="dark"] .fullscreen-header.pdf-controls-container,
html[data-theme="dark"] .pdf-controls-container {{
  background-color: #213953 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .pdf-controls-container svg {{
  fill: #e0e0e0 !important;
}}
html[data-theme="dark"] .pdf-controls-container button,
html[data-theme="dark"] .pdf-controls-container span,
html[data-theme="dark"] .pdf-controls-container input {{
  color: #e0e0e0 !important;
}}
/* Bookmark items in sidebar */
html[data-theme="dark"] .bookmark-item {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .bookmark-item:hover {{
  background-color: #253547 !important;
}}

/* Perseus / exercise content */
html[data-theme="dark"] .framework-perseus,
html[data-theme="dark"] .perseus-root {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .framework-perseus fieldset {{
  border-color: #3a5570 !important;
}}

/* Quiz BottomAppBar answered text */
html[data-theme="dark"] .bottom .answered {{
  color: #e0e0e0 !important;
}}

/* QuizReport: header row, exercise container, try selector */
html[data-theme="dark"] .page-status {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .exercise-container {{
  background-color: transparent !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .try-selection {{
  background-color: #253547 !important;
  color: #e0e0e0 !important;
}}

/* ===== EPUB VIEWER: DARK MODE ===== */

/* Outer wrapper */
html[data-theme="dark"] .epub-viewer {{
  background-color: #1a2e43 !important;
}}
/* Table-of-contents sidebar */
html[data-theme="dark"] .epub-viewer .side-bar {{
  background-color: #1a2e43 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .epub-viewer .side-bar a,
html[data-theme="dark"] .epub-viewer .side-bar button,
html[data-theme="dark"] .epub-viewer .side-bar span,
html[data-theme="dark"] .epub-viewer .side-bar li {{
  color: #e0e0e0 !important;
}}
/* Top bar & bottom bar */
html[data-theme="dark"] .epub-viewer .top-bar,
html[data-theme="dark"] .epub-viewer .bottom-bar {{
  background-color: #213953 !important;
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .epub-viewer .top-bar svg,
html[data-theme="dark"] .epub-viewer .bottom-bar svg {{
  fill: #e0e0e0 !important;
}}
/* Content border */
html[data-theme="dark"] .epub-viewer .epub-viewer-content {{
  border-color: #3a5570 !important;
}}
/* Navigation + content pane background */
html[data-theme="dark"] .epub-viewer .navigation-and-epubjs,
html[data-theme="dark"] .epub-viewer .epubjs-parent,
html[data-theme="dark"] .epub-viewer .epubjs-navigation {{
  background-color: #1a2e43 !important;
}}

/* --- Theme toggle button --- */
.angels-theme-toggle {{
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: #213953;
  color: #ffffff;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.3s;
}}
.angels-theme-toggle:hover {{
  background: #1a2e43;
}}
html[data-theme="dark"] .angels-theme-toggle {{
  background: #a6c52e;
  color: #1a2e43;
}}
html[data-theme="dark"] .angels-theme-toggle:hover {{
  background: #859e25;
}}

/* Login page logo: invert to white in dark mode */
html[data-theme="dark"] .box > img.logo {{
  filter: brightness(0) invert(1) !important;
}}
/* Login page footer bar: match box background in dark mode */
html[data-theme="dark"] .fh .footer-cell {{
  background-color: #213953 !important;
}}
/* Side nav footer logo: invert to white in dark mode */
html[data-theme="dark"] .side-nav-scrollable-area-footer-logo {{
  filter: brightness(0) invert(1) !important;
}}

/* ===== SEARCH BAR IN APP BAR ===== */
.angels-search-bar {{
  position: fixed;
  display: flex;
  align-items: center;
  padding: 0 12px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  transition: background 0.2s, border-color 0.2s;
  z-index: 100;
  box-sizing: border-box;
}}
.angels-search-bar:focus-within {{
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.4);
}}
.angels-search-icon {{
  display: flex;
  align-items: center;
  margin-right: 8px;
  flex-shrink: 0;
}}
.angels-search-input {{
  flex: 1;
  border: none !important;
  background: transparent !important;
  color: #ffffff !important;
  font-size: 14px;
  font-family: 'Open Sans', 'Noto Sans', sans-serif !important;
  outline: none !important;
  width: 100%;
  padding: 0 !important;
  margin: 0 !important;
  height: auto !important;
}}
.angels-search-input::placeholder {{
  color: rgba(255, 255, 255, 0.6) !important;
}}
/* Dark mode: slightly different tint */
html[data-theme="dark"] .angels-search-bar {{
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}}
html[data-theme="dark"] .angels-search-bar:focus-within {{
  background: rgba(255, 255, 255, 0.18);
}}

/* ===== SEARCH RESULT TAGS: dark mode readability ===== */
html[data-theme="dark"] .filter-chip {{
  background-color: #253547 !important;
}}
html[data-theme="dark"] .filter-chip .filter-chip-text {{
  color: #e0e0e0 !important;
}}
html[data-theme="dark"] .filter-chip svg {{
  fill: #e0e0e0 !important;
}}

/* ===== LIBRARY SIDE PANEL: Hide Keywords + SearchBox + Selectors ===== */
/* Keywords heading (direct h2 child of the filter content div) */
.side-panel > div > div > h2 {{
  display: none !important;
}}
/* SearchBox form */
.side-panel .search-box {{
  display: none !important;
}}
/* Language / Level / Accessibility selectors (KSelect) */
.side-panel .ui-select {{
  display: none !important;
}}
</style>

<script src="{toggle_js}"></script>
""".format(
                latin=latin, latin_ext=latin_ext, toggle_js=toggle_js,
                logo_url=logo_url, favicon_url=favicon_url,
                sidenav_footer_logo=static("assets/angels_theme/logo-angels-for-education-full.svg")
            )
        )


@register_hook
class AngelsThemeHook(theme_hook.ThemeHook):
    @property
    def theme(self):
        return {
            # Browser tab title
            "siteTitle": "Angels Academy",
            # Brand color scales generated from primary (#213953) and secondary (#a6c52e)
            # Use https://materialpalettes.com/ to fine-tune
            "brandColors": {
                "primary": {
                    "v_100": "#d4dce4",
                    "v_200": "#a9b9c9",
                    "v_300": "#7e96ae",
                    "v_400": "#537393",
                    "v_500": "#213953",
                    "v_600": "#1a2e43",
                },
                "secondary": {
                    "v_100": "#eef5d5",
                    "v_200": "#d6e89e",
                    "v_300": "#bfdb67",
                    "v_400": "#b3d44b",
                    "v_500": "#a6c52e",
                    "v_600": "#859e25",
                },
            },
            # Sign-in page configuration
            "signIn": {
                "background": static("assets/angels_theme/login-background.jpg"),
                "topLogo": {
                    "src": static(
                        "assets/angels_theme/logo-angels-for-education-new.svg"
                    ),
                    "style": "padding-left: 48px; padding-right: 48px; margin-bottom: 8px; margin-top: 16px; max-height: 120px;",
                    "alt": "Angels for Education",
                },
                "title": "Angels Academy",
                "showTitle": False,
                "showKolibriFooterLogo": False,
                "showPoweredBy": False,
            },
            # App bar (top navigation bar)
            "appBar": {
                "background": "#213953",
                "textColor": "#ffffff",
                "topLogo": {
                    "src": static("assets/angels_theme/logo-icon-green.png"),
                    "style": "max-height: 48px; margin-right: 8px",
                    "alt": "Angels Academy",
                },
            },
            # Side navigation menu
            "sideNav": {
                "title": "",
                "topLogo": {
                    "src": static(
                        "assets/angels_theme/logo-academy-horizontal-green.svg"
                    ),
                    "style": "max-height: 48px; margin: 12px auto; display: block",
                    "alt": "Angels Academy",
                },
                "showKolibriFooterLogo": False,
            },
            # Favicon and PWA icons
            "logos": [
                {
                    "src": static("assets/angels_theme/logo-icon-favicon.svg"),
                    "content_type": "image/svg+xml",
                    "size": "512x512",
                },
                {
                    "src": static("assets/angels_theme/logo-icon-green.png"),
                    "content_type": "image/png",
                    "size": "192x192",
                },
            ],
        }
