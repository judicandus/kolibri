FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy entire source tree (includes pre-built frontend bundles + our Vue/CSS changes)
COPY . /kolibri-src/

# Install Python dependencies then Kolibri from source
# This ensures Python code, templates, JS bundles, and locale files are all from the same version
RUN pip install --no-cache-dir -r /kolibri-src/requirements/base.txt && \
    pip install --no-cache-dir /kolibri-src/

# Find where kolibri is installed (for rebrand script)
RUN KOLIBRI_PKG=$(python -c "import kolibri; import os; print(os.path.dirname(kolibri.__file__))") && \
    echo "$KOLIBRI_PKG" > /tmp/kolibri_path

# Rebrand "Kolibri" → "Angels Academy" in locale files and templates
COPY docker/angels/rebrand.sh /tmp/rebrand.sh
RUN chmod +x /tmp/rebrand.sh && /tmp/rebrand.sh && rm /tmp/rebrand.sh

# Environment variables
ENV KOLIBRI_HOME=/kolibrihome
ENV KOLIBRI_HTTP_PORT=8080
ENV KOLIBRI_PLUGIN_DISABLE=kolibri.plugins.default_theme
ENV KOLIBRI_PLUGIN_ENABLE=kolibri.plugins.angels_theme
ENV KOLIBRI_LANG=en

# Create KOLIBRI_HOME
RUN mkdir -p /kolibrihome

# Provision a test facility automatically
RUN kolibri manage migrate --no-input && \
    kolibri manage provisiondevice \
        --facility "Angels Academy Test" \
        --preset formal \
        --superusername admin \
        --superuserpassword admin123 \
        --language_id en \
        --verbosity 0 \
        --noinput

EXPOSE 8080

CMD ["kolibri", "start", "--foreground"]
