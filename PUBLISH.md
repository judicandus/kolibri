# Publishing Angels Academy to Production

**Production server:** `ssh angels` (app.angelsforedu.org)
**Architecture:** ARM64 (aarch64) — images must be built with `--platform linux/arm64`
**Local dev:** AMD64 (x86_64), Docker on port 9090
**Production Docker:** `kolibri-angels:latest`, port 8080, data at `/home/angels/kolibri_data`

---

## Prerequisites

On the local machine:

- Docker with `buildx` and ARM64 emulation support (QEMU)
- SSH access configured as `angels` in `~/.ssh/config`
- Frontend already built: `pnpm run build`

Verify buildx ARM64 support:

```bash
docker buildx create --name arm64builder --platform linux/arm64 --use 2>/dev/null
docker buildx inspect --bootstrap | grep -i platform
# Should list linux/arm64
```

---

## Option A: Full Deployment (Code + Database Overwrite)

Use this when the local database has changes that must go to production (e.g., updated thumbnails, new content, modified user data).

### 1. Build the frontend

```bash
pnpm run build
```

### 2. Build the ARM64 Docker image

```bash
docker buildx build \
  --platform linux/arm64 \
  -t kolibri-angels:latest \
  -f docker/angels/Dockerfile \
  --output type=docker,dest=/tmp/kolibri-angels-arm64.tar \
  .

gzip /tmp/kolibri-angels-arm64.tar
```

### 3. Back up current production data

```bash
ssh angels "docker stop kolibri && \
  rsync -a \
    --exclude='sessions/' \
    --exclude='process_cache/' \
    --exclude='server.pid' \
    /home/angels/kolibri_data/ /home/angels/kolibri_data_backup/ && \
  docker start kolibri && \
  echo 'Backup done'"
```

### 4. Transfer the image and data

```bash
# Image
scp /tmp/kolibri-angels-arm64.tar.gz angels:/home/angels/

# Data (from the local Docker volume mount)
rsync -az \
  --exclude='sessions*' \
  --exclude='process_cache/' \
  --exclude='server.pid' \
  /tmp/angels-kolibri-data/ angels:/home/angels/kolibri_data_new/
```

### 5. Deploy

```bash
ssh angels "
  docker stop kolibri && docker rm kolibri &&

  # Load new image
  gunzip -c /home/angels/kolibri-angels-arm64.tar.gz | docker load &&

  # Swap data
  mv /home/angels/kolibri_data /home/angels/kolibri_data_old &&
  mv /home/angels/kolibri_data_new /home/angels/kolibri_data &&

  # Create sessions database (excluded from rsync, must be recreated)
  python3 -c \"
import sqlite3
conn = sqlite3.connect('/home/angels/kolibri_data/sessions.sqlite3')
conn.execute('''CREATE TABLE IF NOT EXISTS kolibriauth_session (
    session_key varchar(40) NOT NULL PRIMARY KEY,
    session_data text NOT NULL,
    expire_date datetime NOT NULL,
    user_id char(32) NULL
)''')
conn.execute('CREATE INDEX IF NOT EXISTS kolibriauth_session_expire_date_idx ON kolibriauth_session (expire_date)')
conn.execute('CREATE INDEX IF NOT EXISTS kolibriauth_session_user_id_idx ON kolibriauth_session (user_id)')
conn.commit()
conn.close()
\" &&

  # Checkpoint any stale WAL journal
  python3 -c \"
import sqlite3
conn = sqlite3.connect('/home/angels/kolibri_data/db.sqlite3')
conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
conn.close()
\" &&
  rm -f /home/angels/kolibri_data/db.sqlite3-wal /home/angels/kolibri_data/db.sqlite3-shm &&

  cd /home/angels && docker compose up -d &&
  echo 'Deployed'
"
```

### 6. Verify

```bash
ssh angels "sleep 10 && curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/"
# Should print 302
```

### 7. Purge Cloudflare CDN Cache

Kolibri serves static content (thumbnails, JS bundles) with `cache-control: public, max-age=315360000, immutable` (10-year cache). Cloudflare will keep serving the old cached versions until explicitly purged.

**Via Cloudflare Dashboard:**
1. Go to https://dash.cloudflare.com → angelsforedu.org → Caching → Configuration
2. Click **Purge Everything** → Confirm

**Via Cloudflare API** (if `CF_API_TOKEN` is set — requires Zone:Cache Purge permission):
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

To find the zone ID, run:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=angelsforedu.org" \
  -H "Authorization: Bearer $CF_API_TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])"
```

> **Warning:** After purging, the first requests to each resource will be slower as Cloudflare re-fetches from origin. This is expected and only affects the first visitor per resource.

### 8. Verify (after cache purge)

Check that Cloudflare is serving the new files (look for `cf-cache-status: MISS` on first request, then `HIT` on subsequent):
```bash
curl -sI "https://app.angelsforedu.org/content/storage/5/d/5d5f5d51ccfb0026971ce08445fb7677.png" | grep -iE 'cf-cache|content-length|cache-control'
```

Also do a hard refresh (Ctrl+Shift+R) in the browser to bypass local browser cache.

### 9. Clean up (after confirming everything works)

```bash
ssh angels "rm -rf /home/angels/kolibri_data_old /home/angels/kolibri_data_backup \
  /home/angels/kolibri-angels-arm64.tar.gz"
```

### Rollback

If the new version doesn't work:

```bash
ssh angels "
  docker stop kolibri && docker rm kolibri &&
  rm -rf /home/angels/kolibri_data &&
  mv /home/angels/kolibri_data_backup /home/angels/kolibri_data &&
  docker tag kolibri-angels:old-arm64 kolibri-angels:latest &&
  cd /home/angels && docker compose up -d
"
```

---

## Option B: Code-Only Deployment (Keep Production Database)

Use this when only the application code changed (Vue components, theme CSS, Python backend) but the production database and content should be preserved.

### 1. Build the frontend

```bash
pnpm run build
```

### 2. Build the ARM64 Docker image

```bash
docker buildx build \
  --platform linux/arm64 \
  -t kolibri-angels:latest \
  -f docker/angels/Dockerfile \
  --output type=docker,dest=/tmp/kolibri-angels-arm64.tar \
  .

gzip /tmp/kolibri-angels-arm64.tar
```

### 3. Transfer the image

```bash
scp /tmp/kolibri-angels-arm64.tar.gz angels:/home/angels/
```

### 4. Back up and deploy

```bash
ssh angels "
  # Tag current image for rollback
  docker tag kolibri-angels:latest kolibri-angels:previous &&

  # Stop and remove container
  docker stop kolibri && docker rm kolibri &&

  # Load new image (overwrites kolibri-angels:latest)
  gunzip -c /home/angels/kolibri-angels-arm64.tar.gz | docker load &&

  # Run migrations (new code may require schema changes)
  # Start a temporary container to run migrations against the existing data
  docker run --rm \
    -v /home/angels/kolibri_data:/kolibri_data \
    -e KOLIBRI_HOME=/kolibri_data \
    kolibri-angels:latest \
    kolibri manage migrate --no-input &&

  # Ensure sessions database exists and has the required table
  python3 -c \"
import sqlite3, os
db_path = '/home/angels/kolibri_data/sessions.sqlite3'
conn = sqlite3.connect(db_path)
conn.execute('''CREATE TABLE IF NOT EXISTS kolibriauth_session (
    session_key varchar(40) NOT NULL PRIMARY KEY,
    session_data text NOT NULL,
    expire_date datetime NOT NULL,
    user_id char(32) NULL
)''')
conn.execute('CREATE INDEX IF NOT EXISTS kolibriauth_session_expire_date_idx ON kolibriauth_session (expire_date)')
conn.execute('CREATE INDEX IF NOT EXISTS kolibriauth_session_user_id_idx ON kolibriauth_session (user_id)')
conn.commit()
conn.close()
\" &&

  # Start
  cd /home/angels && docker compose up -d &&
  echo 'Deployed'
"
```

### 5. Verify

```bash
ssh angels "sleep 10 && curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/"
# Should print 302
```

### 6. Clean up

```bash
ssh angels "rm -f /home/angels/kolibri-angels-arm64.tar.gz"
```

### Rollback

```bash
ssh angels "
  docker stop kolibri && docker rm kolibri &&
  docker tag kolibri-angels:previous kolibri-angels:latest &&
  cd /home/angels && docker compose up -d
"
```

---

## Known Gotchas

**ARM64 requirement.** The production server is ARM64. A standard `docker build` on an AMD64 machine produces an image that will fail with `exec format error`. Always use `docker buildx build --platform linux/arm64`.

**KOLIBRI_HOME paths differ between local and production.** This is the most common source of deployment confusion:
- **Dockerfile default:** `KOLIBRI_HOME=/kolibrihome` (used during image build for provisioning)
- **Local docker-compose:** mounts `/tmp/angels-kolibri-data:/kolibrihome` (matches Dockerfile default)
- **Production docker-compose:** overrides with `KOLIBRI_HOME=/kolibri_data`, mounts `/home/angels/kolibri_data:/kolibri_data`

When running `docker run` manually (without docker-compose), you must mount the volume to match the KOLIBRI_HOME the container expects. For local: `-v /tmp/angels-kolibri-data:/kolibrihome`. For production: use docker-compose which handles the override.

**Cloudflare CDN cache.** Kolibri sets `cache-control: public, max-age=315360000, immutable` on all `/content/storage/` files. After deploying updated thumbnails or content, you **must** purge the Cloudflare cache (see Step 7 in Option A). Without purging, Cloudflare will serve stale files for up to 10 years.

**Sessions database.** Kolibri stores sessions in a separate `sessions.sqlite3` file (not in the main `db.sqlite3`). This file must contain the `kolibriauth_session` table. If it's missing or empty, every request will return HTTP 500. The deploy scripts above handle this automatically.

**WAL journal files.** SQLite WAL files (`db.sqlite3-wal`, `db.sqlite3-shm`) from a different Kolibri version or architecture can cause `no such table` errors even when the table exists. Always checkpoint and remove WAL files when transferring databases between environments. When copying a SQLite database, **always copy all three files** (`db.sqlite3`, `db.sqlite3-wal`, `db.sqlite3-shm`) together — copying only the main file may lose uncommitted WAL data.

**Frontend build required.** The Docker image copies pre-built webpack bundles from the source tree. If you change any Vue/JS/CSS files, you must run `pnpm run build` before building the Docker image. Without this step, the old bundles will be packaged.

**Facility name.** The Dockerfile provisions a test facility "Angels Academy Test". In a full deployment (Option A), the production facility comes from the transferred database, not from the Dockerfile. In a code-only deployment (Option B), the existing production facility is preserved.
