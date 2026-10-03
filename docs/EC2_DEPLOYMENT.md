# Single-EC2 evaluation deployment

This is a **domain-free evaluation runbook**, not a public launch plan. It keeps
the three web ports on the EC2 loopback interface and uses an SSH tunnel from
the evaluator's computer. Do not put candidate PII, passwords, or a real
customer workload on an untrusted public HTTP endpoint.

There is no claim that any EC2 instance is free. Eligibility/credits, public
IPv4, EBS, snapshots and egress can all cost money. Check the AWS account's
current pricing and limits before creating resources. This document does not
create AWS resources.

## What is included

`compose.ec2.yml` runs the existing backend image, Celery worker, PostgreSQL,
Redis, client Next app and admin Next app. PostgreSQL and Redis have no host
ports. The app ports bind to `127.0.0.1` only:

* client: EC2 `127.0.0.1:3000`
* admin: EC2 `127.0.0.1:3001`
* API: EC2 `127.0.0.1:8000`

The backend image is expected to be the existing `backend/Dockerfile` image
(already non-root); the two Next images are expected to use their existing
`production` Dockerfile targets (already run as the `node` user). Compose uses
modest Gunicorn/Celery concurrency and `init: true` for Python services.

## Inputs and image preparation

On a build machine, inspect the target architecture (`uname -m`) and build for
the instance architecture. For an x86_64 instance, for example:

```sh
docker buildx build --platform linux/amd64 -f backend/Dockerfile \
  -t htf-backend:ec2 --load backend
docker buildx build --platform linux/amd64 -f client-web/Dockerfile \
  --target production \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  --build-arg NEXT_PUBLIC_ADMIN_URL=http://localhost:3001 \
  --build-arg NEXT_PUBLIC_AUTH_MODE=clerk \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" \
  -t htf-client:ec2 --load client-web
docker buildx build --platform linux/amd64 -f admin-web/Dockerfile \
  --target production \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  --build-arg NEXT_PUBLIC_AUTH_MODE=clerk \
  --build-arg NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" \
  -t htf-admin:ec2 --load admin-web
```

Use a private registry or `docker save`/`scp`/`docker load` to transfer these
images; do not put secrets in Docker build arguments. The public Clerk key is
intended to be public, but the Clerk secret is runtime-only and is never a
build argument or image layer. Adapt the platform to `linux/arm64` when the
instance is ARM64. Building both Next apps beside PostgreSQL/Celery on a small
instance is intentionally avoided.

On the EC2 host:

```sh
git clone <your-private-repository> htf
cd htf
cp infra/ec2/.env.example infra/ec2/.env
chmod 600 infra/ec2/.env
# Edit infra/ec2/.env locally on the host; use unique secret values.
docker load -i /path/to/htf-images.tar       # if not using a registry
docker compose --env-file infra/ec2/.env -f compose.ec2.yml config --quiet
docker compose --env-file infra/ec2/.env -f compose.ec2.yml up -d postgres redis
docker compose --env-file infra/ec2/.env -f compose.ec2.yml run --rm backend python manage.py migrate --noinput
docker compose --env-file infra/ec2/.env -f compose.ec2.yml up -d backend worker client-web admin-web
```

Set `BACKEND_IMAGE`, `CLIENT_IMAGE` and `ADMIN_IMAGE` to the transferred image
tags. Set a strong random `DJANGO_SECRET_KEY` (50+ characters), a unique
PostgreSQL password, and the Clerk **development** issuer/JWKS settings and
publishable key. Supply `CLERK_SECRET_KEY` for the protected Next.js auth proxy;
it is injected only at container runtime, never into client code or build arguments.
Never commit `infra/ec2/.env` or copy an existing root `.env` into the image.

## Domain-free evaluation through SSH

Configure the Clerk development instance's allowed origins/redirects for
`http://localhost:3000` and, if evaluating admin, `http://localhost:3001`.
Verify that the installed Clerk flow supports localhost origins. A bare EC2 IP
is not a substitute for a supported Clerk hostname.

From the evaluator computer, keep this tunnel open:

```sh
ssh -N \
  -L 3000:127.0.0.1:3000 \
  -L 3001:127.0.0.1:3001 \
  -L 8000:127.0.0.1:8000 \
  ec2-user@<instance-public-ip-or-hostname>
```

Then use `http://localhost:3000` and `http://localhost:3001`. The API is
`http://localhost:8000/health/`; it is reachable only through the tunnel.
This is a private evaluation path, not HTTPS and not a public launch.

## Operations

```sh
docker compose --env-file infra/ec2/.env -f compose.ec2.yml ps
docker compose --env-file infra/ec2/.env -f compose.ec2.yml logs --tail=100 backend worker
curl -fsS http://127.0.0.1:8000/health/
docker compose --env-file infra/ec2/.env -f compose.ec2.yml exec backend \
  python manage.py check
```

The defaults are one Gunicorn worker and one Celery worker. Size memory for
PostgreSQL, Redis, the worker and both Next runtimes together; do not assume a
1 GB/free micro instance can safely run all six services. Reduce scope or use
more memory based on observed usage before handling real data.

Run migrations deliberately after reviewing the release and before exposing a
new evaluation build:

```sh
docker compose --env-file infra/ec2/.env -f compose.ec2.yml exec backend \
  python manage.py migrate --noinput
```

Take a backup before migrations. The manual scripts are intentionally not
scheduled:

```sh
# Use storage outside this repository; the first argument must be absolute.
sh infra/ec2/backup-postgres.sh /var/backups/htf/before-migration.dump
# Recovery requires an explicitly named isolated database and strong confirmation:
sh infra/ec2/restore-postgres.sh /var/backups/htf/before-migration.dump htf_restore_20261003
# Type exactly: RESTORE htf_restore_20261003
```

Copy dumps off-instance and protect them separately. Do not store dumps in the
repository. Test recovery on a disposable database before relying on it.

## SSH and firewall guidance

Use an instance security group with TCP 22 restricted to the operator's fixed
IP/CIDR where possible. Do not open 3000, 3001, 8000, 5432 or 6379. Do not add
HTTP/HTTPS rules for this evaluation path. Use key-based SSH, disable password
authentication and root login in `sshd_config`, patch the host, and remove
unused keys. A public IP is only for SSH transport here; services remain
loopback-bound.

## Production/domain cutover requirements

Before real users or candidate PII, use a trusted HTTPS hostname and a
supported TLS reverse proxy, with only 80/443 exposed as needed. Configure
Clerk production keys, allowed origins, redirect URLs, and issuer/JWKS values
for that hostname; use production Django settings and a deliberate
`CSRF_TRUSTED_ORIGINS`/`DJANGO_ALLOWED_HOSTS` list. Review secure-cookie,
HTTPS redirect, HSTS, proxy-header, rate-limit, backup, monitoring and secret
rotation behavior. The current production settings force HTTPS, so they are
not interchangeable with this localhost HTTP tunnel without a trusted TLS
proxy. Use a separate production env file and image release process.

## Compatibility items to resolve in the main application/config work

* The domain-free path uses the planned `config.settings.evaluation` settings
  to keep DEBUG off, require PostgreSQL and a strong secret, allow localhost,
  and avoid the production `SECURE_SSL_REDIRECT` loop over an HTTP SSH tunnel.
  This is evaluation-only; it must not be used for a public deployment.
* Next `NEXT_PUBLIC_API_URL` is a build-time value in the existing Dockerfiles;
  domain-free images must be built with `http://localhost:8000`. A later domain
  cutover requires rebuilding both Next images with the HTTPS API URL.
* `NEXT_PUBLIC_ADMIN_URL` is likewise a frontend build-time compatibility input;
  rebuild the relevant Next image when changing it. Build evaluation images
  with `http://localhost:3001`.
* `WHATSAPP_BUSINESS_NUMBER` is backend runtime configuration. Leave it empty
  until the owner supplies the configured business number; never invent one.
* Confirm Clerk development localhost origins and backend issuer/JWKS values
  in the Clerk dashboard; this cannot be verified offline or from Compose.
* S3, Resend, OmniRoute and Clerk provider credentials are optional integration
  inputs and remain unset until deliberately configured. No paid service or
  AWS resource is provisioned by this runbook.

## Verification

Before starting, validate interpolation without changing state:

```sh
docker compose --env-file infra/ec2/.env -f compose.ec2.yml config --quiet
```

After startup, verify `ps`, the backend health endpoint, backend/worker logs,
and the frontend pages through the SSH tunnel. The main combined checks should
also run the repository's frontend builds and backend tests; this deployment
file does not replace application-level verification.
