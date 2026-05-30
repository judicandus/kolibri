# Angels Academy — Kolibri Customization

Custom-branded version of [Kolibri](https://learningequality.org/kolibri/) for the **Angels for Education** foundation. This fork rebrands the platform as **Angels Academy** with a custom visual identity, dark/light theme toggle, redesigned UI components, and a fully custom home screen experience.

Based on Kolibri **v0.19.1**.

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 20.x + pnpm (for development builds)

### Build & Run
```bash
docker compose -f docker/angels/docker-compose.yml up -d --build
```
Access at **http://localhost:9090**

### Using Production Data (from Raspberry Pi)
```bash
# Copy data from the RPi
scp -r angels:/home/angels/kolibri_data/* /tmp/angels-kolibri-data/

# The docker-compose.yml mounts /tmp/angels-kolibri-data as KOLIBRI_HOME
docker compose -f docker/angels/docker-compose.yml up -d --build
```

### Default Test Credentials
- **Admin:** admin / admin123
- **Test learner (from RPi data):** Angels_LA / 123456

---

## What Was Customized

### 1. Theme Plugin (`kolibri/plugins/angels_theme/`)
A Kolibri plugin that replaces the default theme. It consists of:

- **`kolibri_plugin.py`** — Three registered hooks:
  - `AngelsThemePlugin` — Plugin base class
  - `AngelsThemeHeadHook` — Injects CSS (~950 lines covering fonts, gradients, dark mode, side nav redesign, full-bleed card images, search bar, library filters, quiz/PDF/EPUB dark mode) and JS (theme toggle) into the `<head>` of every page
  - `AngelsThemeHook` — Theme configuration (colors, logos, sign-in page, app bar, side nav, favicon)

- **Static assets** (`static/assets/angels_theme/`):
  - `fonts/open-sans-latin.woff2`, `fonts/open-sans-latin-ext.woff2` — Open Sans font
  - `logo-icon-green.png` / `logo-icon-green.svg` — Green leaf icon (app bar, PWA)
  - `logo-icon-favicon.svg` — SVG favicon
  - `logo-academy-horizontal-green.png` / `.svg` — Horizontal logo (side nav header)
  - `logo-angels-for-education.svg` / `*-new.svg` / `*-full.svg` — Foundation logos (login page, side nav footer)
  - `login-background.jpg` — Login page background image
  - `logo-angels-horizontal-dark.png`, `logo-icon-dark.png` — Dark variants
  - `theme-toggle.js` — Dark/light mode toggle logic with MutationObserver

### 2. Home Screen Redesign (Vue Component Modifications)
The learner home page was significantly reworked:

#### a. "Continue Learning" Hero Card (`ContinueLearning.vue`)
- **Before:** A grid of small ResourceCards for in-progress content
- **After:** A single full-width hero card showing the most recent active lesson
- Features: full-bleed thumbnail background, gradient overlay, lesson title, class name, learning activity label, progress bar
- Receives the most recent lesson via prop from the HomePage

#### b. "Recently Accessed" Section (`RecentlyAccessed.vue` — NEW file)
- Extracted from the original ContinueLearning component into its own dedicated component
- Shows up to 4 ResourceCards in a grid for the most recently accessed content
- Filters out the `__class_thumb__` marker activity (see below)

#### c. "Your Classes" with Thumbnail Images (`YourClasses/index.vue`)
- Class cards now display a background thumbnail image
- Since Kolibri has no native way to assign images to classes, a convention is used: a special content node titled `__class_thumb__` is added to a lesson within the class
- The component searches the class's lessons for this marker, extracts its thumbnail URL, and displays it as the card's background image
- The `__class_thumb__` activity is automatically filtered from all student-facing views

#### d. HomePage Orchestration (`HomePage/index.vue`)
- Computes `recentResources` from class lesson resources, filtering out `__class_thumb__` markers
- Passes the most recent active lesson to the ContinueLearning hero card
- Passes recently accessed resources to the RecentlyAccessed section

#### e. Lesson Playlist Filtering (`LessonPlaylistPage.vue`)
- Filters out `__class_thumb__` content nodes from lesson content listings so students never see the marker activity

### 3. Full-Bleed Card Images (CSS in `kolibri_plugin.py`)
Three card types were converted from showing small thumbnails to full-bleed background images:

#### a. HybridLearningContentCard (Library / Topics grids)
- `span.thumbnail` set to `position: static` so the `<img>` (already `position: absolute`) escapes to the card-link container
- Gradient overlay on `.text` with white title text and text-shadow
- Header bar hidden

#### b. HybridLearningLessonCard (Lesson playlist page)
- Same technique: static thumbnail span, absolute image covers the card
- `::after` gradient overlay, white text, object-position at 75% center

#### c. ResourceCard (Home page "Recently accessed")
- Most complex due to deeply nested KFixedGrid structure
- All wrapper elements inside KFixedGrid forced to `position: static` via `*:not(img)` wildcard selector (excluding the img itself)
- Image escapes through multiple DOM layers to position relative to the card-link
- Card fixed at 200px height; gradient overlay via `::after` pseudo-element
- Activity label grid item hidden; text content positioned above gradient with `z-index: 5`

### 4. Text Rebranding (`docker/angels/rebrand.sh`)
A build-time script that patches Kolibri's locale JSON files, replacing "Kolibri" with "Angels Academy" across:
- Core frontend messages (kolibriLabel)
- User auth messages (titles, version text, access restrictions, OIDC)
- Learn plugin messages (library, loading, welcome, mobile data)
- Coach, Device, Facility, Setup wizard title templates
- Loading page HTML template

### 5. Dark/Light Theme Toggle
- Floating circular button at bottom-right corner (z-index 9999)
- Persists selection in `localStorage` (`angels-theme` key)
- Uses `data-theme="dark"` attribute on `<html>` element
- External JS file (required by CSP `script-src 'self'`)
- `MutationObserver` watches DOM changes to re-style dynamic elements (side nav links, active menus)

### 6. Side Navigation Redesign
- **Header:** Close button + horizontal logo (CSS `background-image` on `.side-nav-header-name`)
- **User info area:** CSS Grid with green avatar circle (CSS `::before`), "Hello," prefix in green, username, points pill
- **Menu items:** Rounded corners, green SVG icons
- **Active menu:** Green background — handled via JS detecting computed `background-color`
- **Footer:** Angels for Education logo (SVG), inverted to white in dark mode
- **Dark mode:** Navy background (`#1a2e43`), header slightly lighter (`#213953`)

### 7. Dark Mode — Comprehensive Page Overrides
All major Kolibri views have dark mode CSS:
- **General:** Background gradients, transparent content wrappers, light text
- **Profile / Downloads pages:** Transparent content area, dark bottom bar
- **Library page:** Dark filter side panel with styled inputs, buttons, checkboxes
- **Content/Quiz pages:** Dark toolbar, dark page container, transparent exercise area, styled Perseus quiz choices with green selected state
- **PDF viewer:** Dark sidebar, dark controls bar, dark bookmark items
- **EPUB viewer:** Dark sidebar, top/bottom bars, navigation pane
- **Search results:** Dark filter chips

### 8. AppBar Search Bar
- Fixed-position search bar styled as a translucent pill (`rgba(255, 255, 255, 0.15)`) in the app bar
- White text and placeholder, rounded corners, focus state with increased opacity

### 9. Library Side Panel Filter Hiding
- Keywords heading, search box, and language/level/accessibility selectors hidden via CSS

### 10. Docker Environment (`docker/angels/`)
- **`Dockerfile`** — Installs Kolibri from the built wheel, copies the theme plugin, runs rebranding, provisions a test facility
- **`docker-compose.yml`** — Maps port 9090→8080, mounts `/tmp/angels-kolibri-data` as KOLIBRI_HOME
- **`rebrand.sh`** — Build-time text replacement script
- **`update_thumbnails.py`** — Script to update content node thumbnails in the database (copies images into Kolibri content storage, updates File records)
- **`generate_images.py`** — Gemini API script used to generate horizontal thumbnail images
- Environment variables disable the default theme and enable `angels_theme`

---

## `__class_thumb__` Convention (Class Thumbnail Images)

Since Kolibri has no native way to assign thumbnail images to classes/classrooms, a convention was created:

1. In Kolibri Studio, create a content node with the exact title `__class_thumb__`
2. Assign the desired class card image as this content node's thumbnail
3. Add this content node to any lesson within the class
4. The system automatically:
   - Uses this thumbnail as the class card background on the home page
   - Filters `__class_thumb__` from all student-facing content lists (Recently Accessed, Lesson Playlist)

---

## Design Specifications

### Color Palette
- **Primary (dark blue):** `#213953` — App bar, dark mode surfaces
- **Primary dark:** `#1a2e43` — Side nav, card backgrounds
- **Secondary (green):** `#a6c52e` — Leaf icons, points, active menu, accents
- **Secondary dark:** `#859e25` — Hover states
- **Dark mode center:** `#253547` — Radial gradient center
- **Dark mode edge:** `#0c131b` — Radial gradient edge
- **Light text:** `#e0e0e0` — Dark mode text
- **Input border (dark):** `#3a5570`

### Font
**Open Sans** (300–700 weight), bundled as woff2. Fallbacks: Noto Sans, sans-serif. VideoJS icon font explicitly preserved.

### Login Page
Custom background image, Angels for Education SVG logo, Kolibri footer and "Powered by" text hidden.

### Home Screen Layout
1. **Your classes** — Class cards with `__class_thumb__` background images
2. **Continue learning from your classes** — Full-width hero card with lesson thumbnail, gradient overlay, progress bar
3. **Recently accessed** — 4 ResourceCards with full-bleed thumbnail backgrounds

---

## Files Modified (Beyond Theme Plugin)

These upstream Kolibri files were modified for the home screen customizations:

- `kolibri/plugins/learn/frontend/views/HomePage/index.vue` — Added recent resources computation, `__class_thumb__` filtering, lesson prop for hero card
- `kolibri/plugins/learn/frontend/views/HomePage/ContinueLearning.vue` — Replaced multi-card grid with single hero card component
- `kolibri/plugins/learn/frontend/views/HomePage/RecentlyAccessed.vue` — **NEW** — Extracted recently accessed section into dedicated component
- `kolibri/plugins/learn/frontend/views/YourClasses/index.vue` — Added `__class_thumb__` thumbnail extraction and class card background images
- `kolibri/plugins/learn/frontend/views/classes/LessonPlaylistPage.vue` — Filter `__class_thumb__` from lesson content list
- `kolibri/plugins/learn/frontend/views/cards/LessonCard/index.vue` — Reads thumbnail from embedded `resource.contentnode.thumbnail` instead of separate API call
- `kolibri/utils/build_config/default_plugins.py` — Registered `angels_theme` plugin

---

## Project Structure

```
kolibri/
├── kolibri/plugins/angels_theme/
│   ├── __init__.py
│   ├── kolibri_plugin.py              # Plugin hooks (theme config + ~950 lines CSS + JS injection)
│   └── static/assets/angels_theme/
│       ├── fonts/
│       │   ├── open-sans-latin.woff2
│       │   └── open-sans-latin-ext.woff2
│       ├── login-background.jpg
│       ├── logo-angels-for-education.svg
│       ├── logo-angels-for-education-new.svg
│       ├── logo-angels-for-education-full.svg
│       ├── logo-academy-horizontal-green.png
│       ├── logo-academy-horizontal-green.svg
│       ├── logo-icon-green.png
│       ├── logo-icon-green.svg
│       ├── logo-icon-favicon.svg
│       ├── logo-angels-horizontal-dark.png
│       ├── logo-icon-dark.png
│       └── theme-toggle.js
├── kolibri/plugins/learn/frontend/views/
│   ├── HomePage/
│   │   ├── index.vue                  # Modified: home screen orchestration
│   │   ├── ContinueLearning.vue       # Modified: hero card
│   │   └── RecentlyAccessed.vue       # NEW: recently accessed section
│   ├── YourClasses/index.vue          # Modified: class card thumbnails
│   └── classes/LessonPlaylistPage.vue # Modified: __class_thumb__ filter
├── docker/angels/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── rebrand.sh
│   ├── update_thumbnails.py           # DB thumbnail update script
│   └── generate_images.py             # Gemini API image generation
├── README.md                          # This file
└── WORKFLOW.md                        # Development workflow (Portuguese)
```

---

## Data Architecture & Deployment

### KOLIBRI_HOME Mount Points

The `KOLIBRI_HOME` environment variable determines where Kolibri stores its database, content files, and configuration. **The path differs between environments:**

- **Dockerfile build-time:** `KOLIBRI_HOME=/kolibrihome` — used during `docker build` for provisioning the test facility
- **Local development (docker-compose):** Volume mount `/tmp/angels-kolibri-data:/kolibrihome` — matches Dockerfile default
- **Production (docker-compose):** Environment override `KOLIBRI_HOME=/kolibri_data`, volume mount `/home/angels/kolibri_data:/kolibri_data`

When running containers manually with `docker run`, you must mount the volume to the correct container path:
```bash
# Local (matches Dockerfile KOLIBRI_HOME)
docker run -v /tmp/angels-kolibri-data:/kolibrihome ...

# Production uses docker-compose which handles the override automatically
```

### Content Storage & Cloudflare Caching

Kolibri stores content files (thumbnails, videos, exercises) under `KOLIBRI_HOME/content/storage/` using a content-addressable scheme: `content/storage/X/Y/XYHASH.ext` where X and Y are the first two characters of the file's MD5 hash.

Kolibri serves these files with aggressive cache headers:
```
cache-control: public, max-age=315360000, immutable
```

This means Cloudflare CDN (which proxies app.angelsforedu.org) will cache these files for up to 10 years and never revalidate. **After any deployment that updates content files (thumbnails, etc.), you must purge the Cloudflare cache.** See `PUBLISH.md` Step 7 for instructions.

### SQLite WAL Mode

Kolibri uses SQLite in WAL (Write-Ahead Logging) mode. The database consists of three files:
- `db.sqlite3` — main database file
- `db.sqlite3-wal` — write-ahead log (uncommitted transactions)
- `db.sqlite3-shm` — shared memory index

**When copying databases between environments, always copy all three files.** Copying only `db.sqlite3` can silently lose data that exists only in the WAL file. Before transferring, checkpoint the WAL:
```bash
python3 -c "import sqlite3; c=sqlite3.connect('db.sqlite3'); c.execute('PRAGMA wal_checkpoint(TRUNCATE)'); c.close()"
```

### LessonCard Thumbnail Fix

The `LessonCard` component (`kolibri/plugins/learn/frontend/views/cards/LessonCard/index.vue`) was modified to read thumbnails directly from the embedded `resource.contentnode.thumbnail` data in the lesson object, rather than making a separate API call via `ContentNodeResource.fetchLessonResources()`. The lesson data from `useLearnerResources().getClassActiveLessons()` already includes embedded contentnode objects with thumbnail URLs, so no additional API call is needed. The component also skips any resource titled `__class_thumb__` (the class thumbnail marker convention).

## Technical Notes

- **CSP constraint:** Kolibri enforces `script-src 'self' blob:` — all JavaScript must be in external files, not inline `<script>` tags. CSS inline is allowed (`style-src 'unsafe-inline'`).
- **CSS injection approach:** All custom styles are injected via a Python format string in `AngelsThemeHeadHook.head_html`. Literal braces in CSS must be escaped as `{{` / `}}` because of Python `.format()`.
- **CSS specificity for full-bleed cards:** The ResourceCard required a wildcard `*:not(img)` selector to force all KFixedGrid wrapper elements to `position: static` while preserving `position: absolute` on the img. This allows the thumbnail image to escape through multiple nested Vue component DOM layers.
- **Theme toggle mechanism:** The `data-theme` attribute on `<html>` drives all dark mode CSS selectors. A `MutationObserver` watches the entire DOM to re-style dynamically rendered Vue components.
- **Upstream modifications:** Most customizations live in the theme plugin (no upstream conflict). However, 5 Vue files in `kolibri/plugins/learn/` were directly modified for the home screen redesign — these will need manual rebasing when updating from upstream.

---

## Pending / Known Issues

- [ ] Light mode styling for side navigation active links (currently JS-driven only in dark mode)
- [ ] Responsive behavior on smaller screens (mobile side panel modal)
- [ ] Coach, Facility, Device admin pages — dark mode not yet reviewed
- [ ] RTL (right-to-left) language support testing
- [ ] Additional text rebranding that may have been missed in less common UI paths

---

## Upstream

This is a fork of [learningequality/kolibri](https://github.com/learningequality/kolibri) (v0.19.1).
See the upstream repository for Kolibri's own documentation, contribution guidelines, and license.
