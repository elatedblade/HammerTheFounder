# HTF delivery status — 2026-10-03

## Delivered in this build

This is a code-delivery record, not a claim that a production deployment or live
providers have been certified. The existing stack and manual-first product scope
are preserved; no customer data was used during verification.

| Area | Implemented |
| --- | --- |
| Candidate intake | Full structured fields, compensation bounds, optimistic versioning, review status and operator approval/changes-requested flow |
| Resumes | Existing verified private upload, authorized expiring download, PDF/DOCX queued parsing, bounded operator-only extracted-text view |
| Campaigns | Create/edit settings, trial metadata, admin assignment, scoped operators, approved-profile readiness, start/pause/resume/complete/cancel |
| Companies/jobs | Canonical records, source fields, normalized URL/identity deduplication, editing and filtering |
| Applications | Candidate/job uniqueness, explicit full lifecycle, submission/failure/progress timestamps, interview scheduling, notes and source tracking |
| Outreach | Contacts, templates, suppression, full lifecycle, manual-send records, replies, positive/negative responses, delivery/bounce/follow-up data |
| Human tasks | Creation, priority, assignment, claiming/completion and workflow-generated fit/contact/outreach/failure/interview review tasks |
| Events/audit | Transactional actor-attributed events and safe before/after identifiers; sanitized candidate timeline and operational audit API |
| Dashboards | Real aggregate queries and state counts; candidate progress/tables/interviews/activity; operator workspaces for all implemented domains |
| Billing | Pending ledger records, idempotency support, admin receipt verification/refunds, unique receipt references, campaign billing updates, UPI configuration |
| Communications | Customer-only Resend transactional drafts/send, templates, manual WhatsApp recording, bounded delivery retries and uncertain-delivery states |
| AI | Canonical-input PydanticAI proposals through OmniRoute; four capabilities; schemas, source/prompt versions, usage/latency, human-review-only results |
| Background support | Celery parsing/notification/AI tasks, explicit trial-expiry and interrupted-job reconciliation commands |
| Delivery foundations | Gunicorn, standalone non-root Next images, separate production Compose, TLS/security settings, Redis rate counters, private API caching policy |
| Observability | Opt-in scrubbed Django/Celery and browser-runtime Sentry, frontend error boundaries |
| Administration | Audited first-superadmin bootstrap and explicit role-management command |

### Manual-first boundary

Applications, cold outreach and WhatsApp messages are performed externally by
operators, then recorded. Payment verification records a human-confirmed receipt;
it does not move money. Only explicitly requested transactional email and AI
proposal tasks call providers. Nothing was sent during this build.

## Actual verification

| Check | Result |
| --- | --- |
| Backend pytest using disposable PostgreSQL 16 | **128 passed** |
| Apply all migrations to clean PostgreSQL | **Passed** |
| `manage.py makemigrations --check --dry-run` | **No changes detected** |
| Django system checks | **Passed** |
| Production `check --deploy --fail-level WARNING` with synthetic configuration | **Passed** |
| Admin typecheck / ESLint / production build | **Passed** |
| Client typecheck / ESLint / production build | **Passed** |
| Development and production Compose config validation | **Passed** (production used stand-in values, not credentials) |
| `git diff --check` | **Passed** |

The combined pass initially found an uppercase error-code assertion mismatch and
a browser Sentry option incompatible with the installed SDK. Those integration
issues were corrected. New no-store middleware also required two tests to accept
the stronger private cache directive. No unrelated legacy bug sweep was done.

Reproduce with backend dependencies installed from `backend/pyproject.toml` and
`DATABASE_URL` pointing to a **disposable test PostgreSQL database**:

```sh
cd backend
python -m pytest -q
python manage.py check
python manage.py makemigrations --check --dry-run
cd ../client-web
npm ci && npm run typecheck && npm run lint && npm run build
cd ../admin-web
npm ci && npm run typecheck && npm run lint && npm run build
```

## Remaining acceptance and limitations

These are intentionally visible, not claimed complete:

1. **Live integrations:** actual Google/Clerk sessions, private S3 upload/download
   and CORS, Resend delivery, and OmniRoute native JSON-schema support need staging
   verification with authorized credentials. Tests substitute providers.
2. **Browser acceptance:** authenticated candidate/operator journeys, accessibility
   and responsive interaction testing remain. No frontend E2E runner was added;
   successful builds are not proof of every browser interaction.
3. **Production operations:** real TLS/proxy/firewall, hosting, monitoring alerts,
   encrypted backups/restore drills, retention/deletion policy and any required
   malware scanning must be configured and reviewed. No deployment was performed.
4. **Parsing:** legacy DOC extraction and OCR are not implemented. Unsupported or
   image-only documents expose explicit failure states, never fabricated text.
5. **Scheduling:** expiry and recovery commands/tasks exist, but no recurring
   schedule was created. Run expiry explicitly until deployment scheduling is approved.
6. **Scale:** main operational tables paginate; lookup selections cap at 500.
   Supporting notification/payment/AI lists cap at 200. Related review-task panels
   show the first 100; the task workspace paginates. No load/concurrency certification.
7. **Monitoring:** source-map upload and Next server-runtime instrumentation are
   not configured. Browser runtime, Django and workers have opt-in error reporting.
8. **AI economics:** token/latency/source-version records exist; exact currency
   costs, budget accounting and offline model-quality evaluation remain.
9. **Automation non-goals:** autonomous applications, automated cold outreach,
   unofficial WhatsApp automation and payment reconciliation remain excluded.

## Where to continue

`docs/OPERATIONS_RUNBOOK.md` contains setup, first-admin provisioning, private
storage, production commands, backup guidance and a concrete launch acceptance
checklist. `docs/BUILD_CONTRACT.md` is the API integration map; model/serializer
definitions are authoritative for fields and transitions.

## Clerk development setup follow-up

Clerk CLI authentication/linking completed for the user-selected existing app.
Both frontend diagnostics confirmed development keys; no environment files were
read or printed by the agent. CLI-generated duplicate providers were removed,
Next 16 proxies and sign-in/sign-up routes were integrated, and server-only Clerk
keys were wired into container runtime. Development session email/phone claims
were configured for the Django identity adapter.

Both frontends passed typecheck, lint and production build after the auth changes.
The local database was backed up outside the repository before migrations; the
updated Docker stack built and started. HTTP checks confirmed health 200,
unauthenticated identity 401, frontend/sign-up/sign-in 200, and signed-out workspace
redirect 307. These checks do not prove an authenticated browser journey. Built-in
browser opening timed out; the user must complete the first signup directly.

Docker npm installs reported **five high-severity dependency advisories per
frontend**. They have not been triaged or fixed; do not treat this as production
security clearance. No forced dependency upgrades were applied during auth setup.
S3 bucket/region were supplied, but credentials, policies and uploads remain unverified.

### Subsequent S3 verification

After the user configured credentials, CORS and IAM object permissions, the live
synthetic PDF check passed: PUT preflight, signed upload, response CORS, HEAD
size/type verification, signed download with identical bytes, and anonymous
access denied. The earlier S3-unverified note above is superseded for these checks.
The actual authenticated candidate browser upload still requires acceptance.
One synthetic PDF remains because cleanup lacked DeleteObject permission; its
exact key is documented in `S3_SETUP.md`. No permission escalation was performed.
