# Restore inquiries frontend — verification and merge gate

Date: 2026-10-03 (Asia/Kolkata).

## Versions and decision

- Tested feature: `feature/restore-inquiries-frontend`, source commit `15f448c`.
- Compared main: `aa35099` (also `origin/main` after fetch).
- Starting feature working tree was clean; it was already checked out.
- **Feature works with a fresh database, but merging is blocked.** Existing-data
  migration and the combined main/feature source both fail checks. Main was not
  modified or pushed.

## Feature-only results

| Check | Actual result |
| --- | --- |
| Backend pytest in Docker/PostgreSQL | 186 passed |
| Django system check | Passed |
| All migrations against fresh PostgreSQL | Passed |
| Fresh-database migration drift check | No changes detected |
| Client helper tests | 13 passed |
| Admin helper/contract tests | 8 passed |
| Both apps: typecheck, lint, production build | Passed |
| Public client Playwright browser checks | 3 passed |
| Docker build/start | All six services started |

The first Playwright run could not launch because its Chromium binary was not
installed. `npx playwright install chromium` resolved that environment prerequisite;
the subsequent run passed all three cases. Tests cover landing plan links, mobile
navigation/FAQ/overflow, and public/protected-page separation. They deliberately
disable Clerk and are **not authenticated customer/operator journeys**.

The host checks used Node 26.0.0; Docker uses Node 22. The fresh PostgreSQL checks
used the branch's real backend image, not a SQLite substitute. Providers are
mocked by the backend suite. No messages, payments, AI requests, or customer
state changes were performed.

## Running test environment

An isolated Compose project named `htf-restore-test` is running:

| Component | Address |
| --- | --- |
| Candidate | http://localhost:13000 |
| Admin | http://localhost:13001 |
| API | http://localhost:18000 |
| Health | http://localhost:18000/health/ |

It has separate PostgreSQL and Redis volumes. The legacy database on the default
stack was preserved; no tables or migration records were reset or faked. The
verification overlay disables S3 credentials, Resend, OmniRoute, and Sentry.
Clerk still uses the existing development configuration. This is a local-only
test topology, not a production configuration.

Actual isolated HTTP results:

- API health and `/api/v1/public/contact/`: 200.
- Anonymous `/api/v1/me/`: 401, as expected.
- Candidate home/sign-in/sign-up and admin home/sign-in: 200.
- Candidate plans/profile/dashboard and admin workspace: 307 to authentication.

Authenticated sign-in, first-admin provisioning and private S3 upload are not
certified by these anonymous HTTP checks. The test database starts empty, so
previous candidate profiles and operational roles do not appear here.

## Reproduce the successful feature checks

From the repository root:

```sh
docker compose -p hammerthefounder build
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml up -d --no-build postgres redis
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml run --rm backend python manage.py migrate --noinput
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml up -d --no-build
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml exec -T backend python -m pytest -q
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml exec -T backend python manage.py check
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml exec -T backend python manage.py makemigrations --check --dry-run
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml exec -T backend python manage.py migrate --check

cd client-web
npm ci && npm run typecheck && npm test && npm run lint && npm run build
npx playwright install chromium
npm run test:e2e
cd ../admin-web
npm ci && npm run typecheck && npm test && npm run lint && npm run build
```

The overlay uses Compose's `!override` tag; use a version supporting that tag
(2.24.4+; verified here with 5.3.1). It reuses the explicitly named development
images built above. Rebuild those images after source changes before testing.
To stop the test environment while preserving its database:

```sh
docker compose -p htf-restore-test -f docker-compose.yml -f compose.verification.yml down
```

Do not add `--volumes` without explicit permission to delete the test data.

## Merge blockers

### 1. Existing local database is not upgrade-compatible

Against the default development database, this command failed:

```sh
docker compose exec -T backend python manage.py makemigrations --check --dry-run
```

Error:

```text
InconsistentMigrationHistory:
Migration applications.0001_initial is applied before its dependency
campaigns.0002_campaign_assigned_to on database 'default'.
```

The database reports only `applications.0001_initial` and
`campaigns.0001_initial` for those apps. The current application initial migration
requires campaign assignment first. Earlier development used a different schema
under the same migration names. A successful empty-database migration does not
prove that existing rows can be upgraded safely.

Before fixing this, back up the legacy database and compare its actual schema
with the branch's migration states. Choose a data-preserving forward migration
or an explicitly approved clean development database. Do not blindly `--fake`
dependencies, delete migration records, or delete volumes. The default stack was
rebuilt from the feature branch for testing, but its legacy DB remains incompatible;
use ports 13000/13001 for the clean testing environment.

An additional empty database `htf_restore_verification_20261003` was created on
the default PostgreSQL server for migration-only checks. It contains no customer
data; it was not substituted for the default database or deleted automatically.

### 2. A Git merge candidate is not equivalent to the tested feature

An isolated detached worktree from `main` was used for:

```sh
git merge --no-commit --no-ff feature/restore-inquiries-frontend
```

Git reports a modify/delete conflict in `client-web/src/app/auth-gate.tsx`.
The feature intentionally replaces that component with its new authenticated
route/customer-shell flow. The temporary candidate retained the feature deletion
for investigation; no resolution was committed to main.

Even after that conflict was resolved in the candidate, verification failed:

- Client `npm run typecheck`: duplicate `publishableKey` declarations, missing
  `clerkConfigured`, and missing exports consumed by auth routes and marketing.
  The auto-merged `client-web/src/app/auth-provider.tsx` is incompatible.
- Backend pytest using the branch's dependency-complete Docker image: test
  collection fails because `apps.companies.serializers` imports
  `normalize_company_name`, which the feature's current company model does not
  define. Main reintroduces legacy company/job/application modules and tests
  alongside the newer implementation. These need deliberate reconciliation,
  not a blanket acceptance of Git's automatically merged files.

The first host candidate test also reported missing Pydantic in an older local
virtualenv. That environment limitation was separated from the source error by
rerunning inside the current Docker image; the import incompatibility persists.

The temporary merge was aborted and its worktree removed. Feature source remains
unchanged. Main remains `aa35099`; no merge or remote push occurred.

## Next merge gate

1. Reconcile auth exports/provider and legacy backend files in an integration
   branch, preserving the latest UI and server-side access boundaries.
2. Decide and verify the legacy database transition without losing existing data.
3. Repeat backend, frontend, fresh migration, upgrade, and browser checks on the
   **merged source**, not just the feature source.
4. Merge into main only when the combined checks pass; remote publication is a
   separate Git operation and was not performed by this verification.
