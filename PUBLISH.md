# Publishing Angels Academy to Production

**Production server:** `ssh hetzner` (app.angelsforedu.org — 65.109.103.48)
**Architecture:** AMD64 (x86_64) — images built natively on the server
**Runtime:** K3s (Kubernetes) with containerd, Traefik ingress
**K8s namespace:** `kolibri`
**Local dev:** AMD64 (x86_64), Docker on port 9090
**Source on server:** `/mnt/data/starters/kolibri/`
**Persistent data:** PVC `kolibri-data` (20Gi, `local-path` storageclass)

---

## Prerequisites

On the local machine:

- Node.js 20.19.x (install via `nvm install 20.19.3 && nvm use 20.19.3`)
- pnpm 10.4.1
- SSH access configured as `hetzner` in `~/.ssh/config`

---

## Standard Deployment (Code Update)

Use this for any code change (Vue components, theme CSS, Python backend).

### 1. Build the frontend locally

```bash
source ~/.nvm/nvm.sh && nvm use 20.19.3
pnpm run build
```

### 2. Sync source code to Hetzner

```bash
rsync -avz \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.tox' \
  /home/judicandus/kolibri/ hetzner:/mnt/data/starters/kolibri/
```

> **Note:** `kolibri/dist/` must be included (do not exclude it — the build process requires it).

### 3. Build the Docker image on Hetzner

```bash
ssh hetzner "cd /mnt/data/starters/kolibri && \
  docker build -t kolibri-angels:latest -f docker/angels/Dockerfile ."
```

The build is native AMD64 — no cross-compilation needed.

### 4. Import image into K3s containerd

K3s uses containerd, not Docker. The image must be imported:

```bash
ssh hetzner "docker save kolibri-angels:latest > /tmp/kolibri-angels.tar && \
  sudo k3s ctr images import /tmp/kolibri-angels.tar && \
  rm /tmp/kolibri-angels.tar"
```

> `sudo k3s ctr images import` is configured as NOPASSWD on Hetzner.

### 5. Rollout the new deployment

```bash
ssh hetzner "kubectl rollout restart deployment kolibri -n kolibri"
```

Wait for the rollout to complete:

```bash
ssh hetzner "kubectl rollout status deployment kolibri -n kolibri --timeout=120s"
```

### 6. Verify

```bash
# From the server (internal)
ssh hetzner "curl -sk -o /dev/null -w '%{http_code}' https://app.angelsforedu.org/"
# Should print 302

# From outside
curl -s -o /dev/null -w '%{http_code}' https://app.angelsforedu.org/
# Should print 302
```

Check pod logs if something looks wrong:

```bash
ssh hetzner "kubectl logs deployment/kolibri -n kolibri --tail=50"
```

### 7. Purge Cloudflare CDN Cache (if static assets changed)

Kolibri serves static content with `cache-control: public, max-age=315360000, immutable` (10-year cache). After updating thumbnails, JS bundles, or CSS, purge the Cloudflare cache.

**Via Cloudflare Dashboard:**
1. Go to https://dash.cloudflare.com → angelsforedu.org → Caching → Configuration
2. Click **Purge Everything** → Confirm

**Via Cloudflare API** (if `CF_API_TOKEN` is set):
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```

Then do a hard refresh (Ctrl+Shift+R) in the browser.

---

## Full Deployment (Code + Database Overwrite)

Use this when the local database has changes that must go to production (e.g., updated thumbnails, new content, modified user data).

Follow steps 1–4 above, then instead of a simple rollout restart:

### 5. Back up the current production data

```bash
ssh hetzner "kubectl exec -n kolibri deployment/kolibri -- \
  cp -a /kolibri_data /kolibri_data_backup"
```

### 6. Scale down, swap data, scale up

```bash
# Scale down
ssh hetzner "kubectl scale deployment kolibri -n kolibri --replicas=0 && \
  kubectl rollout status deployment kolibri -n kolibri --timeout=60s"

# Transfer data (rsync from local Docker volume to server, then copy into PVC)
rsync -az \
  --exclude='sessions*' \
  --exclude='process_cache/' \
  --exclude='server.pid' \
  /tmp/angels-kolibri-data/ hetzner:/tmp/kolibri_data_new/

# Scale back up (pod will use the existing PVC)
ssh hetzner "kubectl scale deployment kolibri -n kolibri --replicas=1 && \
  kubectl rollout status deployment kolibri -n kolibri --timeout=120s"
```

### 7. Verify and clean up

Follow steps 6–7 from the standard deployment above.

### Rollback

```bash
ssh hetzner "kubectl exec -n kolibri deployment/kolibri -- \
  rm -rf /kolibri_data && \
  mv /kolibri_data_backup /kolibri_data"

ssh hetzner "kubectl rollout restart deployment kolibri -n kolibri"
```

---

## K8s Infrastructure Reference

The following resources already exist in the `kolibri` namespace:

```
deployment.apps/kolibri        # 1 replica, image: kolibri-angels:latest (imagePullPolicy: Never)
service/kolibri                # ClusterIP on port 8080
ingress/kolibri                # Traefik, host: app.angelsforedu.org, TLS via Let's Encrypt
persistentvolumeclaim/kolibri-data  # 20Gi RWO (local-path), mounted at /kolibri_data
```

### Key deployment environment variables

```yaml
KOLIBRI_HOME: /kolibri_data
KOLIBRI_HTTP_PORT: "8080"
KOLIBRI_PLUGIN_DISABLE: kolibri.plugins.default_theme
KOLIBRI_PLUGIN_ENABLE: kolibri.plugins.angels_theme
ALLOWED_HOSTS: '["app.angelsforedu.org", "localhost", "127.0.0.1"]'
```

### Useful commands

```bash
# View pod logs
ssh hetzner "kubectl logs -n kolibri -l app=kolibri --tail=100 -f"

# Open a shell in the pod
ssh hetzner "kubectl exec -n kolibri deployment/kolibri -it -- /bin/bash"

# Check pod status and events
ssh hetzner "kubectl describe pod -n kolibri -l app=kolibri"

# View current deployment YAML
ssh hetzner "kubectl get deployment kolibri -n kolibri -o yaml"
```

---

## Known Gotchas

**Native AMD64 build.** Unlike the old Raspberry Pi deployment, the Hetzner server is x86_64. Build the image directly on the server — no `docker buildx --platform linux/arm64` needed.

**K3s uses containerd, not Docker.** After building with `docker build`, you must import the image into containerd via `sudo k3s ctr images import`. The deployment uses `imagePullPolicy: Never`, so K3s will only use locally available images.

**KOLIBRI_HOME paths differ between build and runtime:**
- **Dockerfile default:** `KOLIBRI_HOME=/kolibrihome` (used during image build for provisioning)
- **K8s deployment:** `KOLIBRI_HOME=/kolibri_data` (overridden via env var, PVC mounted at `/kolibri_data`)

**Cloudflare CDN cache.** Kolibri sets `cache-control: public, max-age=315360000, immutable` on all `/content/storage/` files. After deploying updated thumbnails or content, you **must** purge the Cloudflare cache. Without purging, Cloudflare will serve stale files for up to 10 years.

**Sessions database.** Kolibri stores sessions in a separate `sessions.sqlite3` file. This file must contain the `kolibriauth_session` table. If it's missing, every request returns HTTP 500. The Dockerfile handles this during build; manual data transfers must ensure it exists.

**WAL journal files.** SQLite WAL files from a different Kolibri version can cause errors. When transferring databases between environments, checkpoint first:
```sql
PRAGMA wal_checkpoint(TRUNCATE);
```
Then remove `*.sqlite3-wal` and `*.sqlite3-shm` files.

**Frontend build required.** The Docker image copies pre-built webpack bundles from the source tree. If you change any Vue/JS/CSS files, you must run `pnpm run build` before syncing to Hetzner. Without this step, the old bundles will be packaged.

**Node.js version.** The frontend build requires Node.js 20.19.x. Using Node 22 causes `node-sass` runtime errors. Always activate the correct version first:
```bash
source ~/.nvm/nvm.sh && nvm use 20.19.3
```

**Facility name.** The Dockerfile provisions a test facility "Angels Academy Test". In a full deployment (code + database), the production facility comes from the transferred database. In a code-only deployment, the existing production facility is preserved.

**sudo is restricted on Hetzner.** The `judicandus` user has passwordless sudo only for specific commands. `sudo k3s ctr images import *` is one of them. Other `sudo` operations require a password.
