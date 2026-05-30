#!/bin/bash
# Rebrand "Kolibri" → "Angels Academy" in locale JSON files and HTML templates
# This script patches the installed Kolibri package files

set -euo pipefail

KOLIBRI_PKG=$(cat /tmp/kolibri_path)
LOCALE_DIR="$KOLIBRI_PKG/locale"
TEMPLATES_DIR="$KOLIBRI_PKG/core/templates/kolibri"

echo "Rebranding Kolibri → Angels Academy..."
echo "  Package: $KOLIBRI_PKG"

# --- 1. Core frontend messages (all locales) ---
# The kolibriLabel is the primary brand string used everywhere
find "$LOCALE_DIR" -name "kolibri.core.default_frontend-messages.json" -exec \
  sed -i 's/"CommonCoreStrings.kolibriLabel": "Kolibri"/"CommonCoreStrings.kolibriLabel": "Angels Academy"/g' {} +

# "Kolibri and its library will always be free"
find "$LOCALE_DIR" -name "kolibri.core.default_frontend-messages.json" -exec \
  sed -i 's/Kolibri and its library will always be free of charge/Angels Academy and its library will always be free of charge/g' {} +

# --- 2. User auth messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.user_auth.app-messages.json" -exec sh -c '
  # Title template: "{ title } - Kolibri" → "{ title } - Angels Academy"
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
  # Version text: "Kolibri {version}" → "Angels Academy {version}"
  sed -i "s/\"AuthBase.poweredBy\": \"Kolibri {version}\"/\"AuthBase.poweredBy\": \"Angels Academy {version}\"/g" "$1"
  # Restricted access
  sed -i "s/Access to Kolibri has been restricted/Access to Angels Academy has been restricted/g" "$1"
  # OIDC explanations
  sed -i "s/Kolibri is an e-learning platform/Angels Academy is an e-learning platform/g" "$1"
  sed -i "s/your Kolibri account/your Angels Academy account/g" "$1"
  # Device unusable strings
  sed -i "s/reinstall Kolibri/reinstall Angels Academy/g" "$1"
  sed -i "s/Reinstall Kolibri/Reinstall Angels Academy/g" "$1"
' _ {} \;

# --- 3. Learn messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.learn.app-messages.json" -exec sh -c '
  # Title template
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
  # "Kolibri Library" → "Angels Academy Library"
  sed -i "s/Kolibri Library/Angels Academy Library/g" "$1"
  # "Loading Kolibri libraries"
  sed -i "s/Loading Kolibri libraries/Loading Angels Academy libraries/g" "$1"
  # "Kolibri cannot connect"
  sed -i "s/Kolibri cannot connect/Angels Academy cannot connect/g" "$1"
  # "Welcome to Kolibri!"
  sed -i "s/Welcome to Kolibri!/Welcome to Angels Academy!/g" "$1"
  # "How are you using Kolibri?"
  sed -i "s/How are you using Kolibri/How are you using Angels Academy/g" "$1"
  # Mobile data strings
  sed -i "s/allow Kolibri to use/allow Angels Academy to use/g" "$1"
  sed -i "s/Allow Kolibri to use/Allow Angels Academy to use/g" "$1"
  sed -i "s/Allowing Kolibri to download/Allowing Angels Academy to download/g" "$1"
  # Version compatibility
  sed -i "s/your version of Kolibri/your version of Angels Academy/g" "$1"
  sed -i "s/version of Kolibri and/version of Angels Academy and/g" "$1"
  # "with Kolibri version"
  sed -i "s/with Kolibri version/with Angels Academy version/g" "$1"
' _ {} \;

# --- 4. Coach messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.coach.app-messages.json" -exec sh -c '
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
' _ {} \;

# --- 5. Device messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.device.app-messages.json" -exec sh -c '
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
' _ {} \;

# --- 6. Facility messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.facility.app-messages.json" -exec sh -c '
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
' _ {} \;

# --- 7. Setup wizard messages ---
find "$LOCALE_DIR" -name "kolibri.plugins.setup_wizard.app-messages.json" -exec sh -c '
  sed -i "s/{ title } - Kolibri/{ title } - Angels Academy/g" "$1"
  sed -i "s/Welcome to Kolibri/Welcome to Angels Academy/g" "$1"
' _ {} \;

# --- 8. Loading page HTML templates ---
if [ -f "$TEMPLATES_DIR/loading_page.html" ]; then
  sed -i 's/Kolibri is starting/Angels Academy is starting/g' "$TEMPLATES_DIR/loading_page.html"
  sed -i 's/Starting Kolibri/Starting Angels Academy/g' "$TEMPLATES_DIR/loading_page.html"
fi

# --- 9. Django backend string (site title fallback) ---
# The gettext string "Kolibri" in core_tags.py is the fallback for siteTitle
# Since we set siteTitle in our theme plugin, this is already handled

echo "Rebranding complete!"
