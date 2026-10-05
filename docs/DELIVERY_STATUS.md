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

## Three-page customer journey revision (2026-10-03)

### Approved interface refinement implementation

Latest follow-up supersedes earlier hidden-tab notes: Inquiries and Notifications
are restored as primary admin tabs. Scope controls affect Overview only. Customer
overview presents five primary application metrics with extras collapsed, not
deleted. Help's requested mailbox is configured in local `SUPPORT_EMAIL` and
verified through the running contact endpoint. Notification history now paginates
beyond 200 records. No real messages were sent or candidate records changed.

Current verification: **186 backend tests**, **6 admin helper/contract tests**,
**10 customer helper tests**, **3 anonymous browser tests** passed; both frontend
lint/typechecks/builds and Django/migration checks passed. Added admin mutation →
customer read parity tests for application metrics/history, payments, inquiries,
notifications and access boundaries using isolated DRF test authentication.
Live Clerk authenticated browser acceptance remains separate and outstanding.

### Outreach and dashboard refresh follow-up

Outreach is restored as a primary admin tab with its existing manual resources:
outreach records, contacts, suppression and templates. It remains manual-only;
the UI does not send messages. Customer Dashboard → Outreach now reads the same
server records as Applications with paged loading, safe customer fields only,
empty/error/retry states and campaign choices limited to the customer's own
campaigns.

The dashboard refresh action now increments a reload generation for all progress
resources, including Applications, Outreach, Notifications and Payments, while
each request cancels stale work. A new DRF sync test verifies admin status changes
through the application and outreach pipelines are visible to the customer and
not to an outsider; private body/notes/contact/thread fields remain filtered.

Final follow-up checks: **187 backend tests passed**, Django check and migration
drift passed; client **13 helper tests**, typecheck/lint and browser **3/3 tests**
passed. Admin previously passed **8 tests**, typecheck/lint/build after Outreach
restoration. The live authenticated Clerk walkthrough is still not claimed.

Final verification: **182 backend tests passed**, Django checks and migration-drift
checks passed. Both frontend builds/lint/typechecks passed; customer helper tests
8 passed, admin checks 3 passed, anonymous browser tests 3 passed after dev-server
warmup/cleanup. All six local services are running and HTTP smoke checks passed.
Authenticated end-to-end acceptance and prior security/deployment gaps remain open.
Final local campaign snapshot is still READY=2, ACTIVE=0; no state was silently
changed. See the refinement plan for local dependency-image reuse during the slow
Docker rebuild and exact limitations of these checks.

See `docs/harshit interface changes refining.md` for scope and remaining acceptance.
The customer dashboard now uses actual campaign lifecycle before acquisition or
inquiry state. ACTIVE/READY/paused/onboarding campaigns no longer get the new-plan
prompt; null/loading/error campaign responses are not treated as empty. A manual
campaign-status refresh is available after work performed from another session.

Admin navigation is reduced to Overview, Candidates, Campaigns, Applications and
Payments. Optional domains remain implemented; inquiry conversion is a secondary
Campaigns panel. Overview has explicit real metrics instead of nested JSON, with
ready versus active and pending payments separate. Candidate detail now has scoped
submitted counts, application/payment history and preserved profile/resume review.
Payment lists page beyond 200 rows. Applications use searchable catalogs plus
company/job creation without losing the application draft or coercing UUIDs.
Both workspaces adopt the landing light palette; existing records are preserved.

New tests cover cross-operator candidate aggregates, visibility filters, >200
payment records, candidate search, overview scope, UUID payload serialization and
customer lifecycle choices. Admin tests include two source-level contract checks;
these must not be described as authenticated browser tests. Live authenticated UI
acceptance, campaign selector scaling, advisory triage and full accessibility
validation remain outstanding. Current combined-run results are recorded in the
refinement plan after the rebuild completes.

### Subsequent dedicated Plans page request

The latest request adds a fourth primary page, `/plans`, superseding the earlier
three-page restriction. Dashboard and landing plan links now lead there. Profile
links remain for profile-specific tasks only. The page includes plan selection,
actual ACTIVE campaigns, inquiry confirmation and an always-present Help section.

Plans has a lazy-loaded screen and route error boundary. Its API requests have
independent error/retry states; dashboard progress no longer depends on inquiry
or contact endpoints succeeding. Shared request handling lives outside the plans
feature. Abort/account guards, duplicate-click protection, backend ownership and
transactional deduplication remain in place. Selection cannot alter an active
campaign. These measures reduce failure coupling, not a guarantee of no failures.

Help reads validated `SUPPORT_EMAIL` configuration via the no-store public contact
endpoint, with additional mailto validation in the browser. No support email has
been supplied yet. The confirmed business WhatsApp destination is configured in
private local configuration; the running endpoint reports WhatsApp ready and
support email unavailable. No message was sent.

Verified after integration: backend `python -m pytest -q` **177 passed**, Django
check and migration-drift checks passed; client `npm run typecheck`, `npm run lint`,
`npm test` (**4 helper tests**), `npm run build`, and `npm run test:e2e` (**3 anonymous
browser tests**) passed. Docker services rebuilt; signed-out `/plans` redirects to
sign-in. Real authenticated Plans interaction and end-to-end external handoff
still need acceptance; anonymous tests are not evidence of that flow.

Review findings addressed: misleading dashboard CTA, coupling inquiry failure to
campaign progress, distinguishing ACTIVE from other states, hardcoded admin-link
fallback usage in the new screen, cancellation before handoff, and email/redirect
injection validation. Outstanding: support email missing, five reported high-severity
frontend dependency advisories still require triage, and Clerk route-matcher
deprecation is reported by tests. Existing backend permissions remain authoritative;
this is not a security certification or a promise of zero vulnerabilities.

Revised plan: `docs/new by harshit.md`. The original implementation plan is
unchanged. The customer app now has a public marketing landing `/`, editable
profile/resumes `/profile`, and progress-focused `/dashboard`. `/workspace`
redirects to the dashboard. Clerk sign-in/up remain supporting routes.

Marketing presentation and editable copy live in
`client-web/src/components/marketing/` and `client-web/src/lib/marketing.ts`;
profile, dashboard and API logic are separate. The page describes Normal Apply,
Cold Apply and Full-Throttle Sprint without fabricated prices or social proof.

Plan intent is preserved through sign-in. Explicit confirmation saves an owned
inquiry and opens a validated business WhatsApp URL. Existing open/contacted
inquiries are reused; internal notes are not customer-visible. Admin has an
Inquiries view, manual contacted/closed actions and idempotent conversion to a
draft campaign. Conversion does not activate or charge a campaign. Missing
WhatsApp configuration returns an honest unavailable state before database writes.

### Checks actually completed

- 147 backend tests passed against disposable PostgreSQL, including inquiry
  ownership, role/assignment boundaries, retry deduplication, private audit,
  invalid destinations, conversion and no automatic activation/payment.
- All migrations applied on disposable PostgreSQL; migration-drift and Django
  system checks passed.
- Both frontends passed TypeScript, ESLint and production builds.
- Two Node helper tests passed for safe auth redirects and WhatsApp URL guards.
- Three Playwright anonymous tests passed: public plan links, mobile menu/FAQ/
  overflow, and separate routes/legacy redirect. These deliberately run without
  Clerk credentials; they do NOT establish live authenticated end-to-end acceptance.
- EC2 Compose interpolation and evaluation settings passed synthetic checks;
  backup/restore scripts passed shell syntax checks. No EC2 instance was launched.
- Local Docker stack rebuilt and all six services are running. A private database
  backup was saved outside the repository before applying the three inquiry
  migrations. HTTP checks returned 200 for landing/admin/public contact, protected
  customer routes redirected to sign-in, and unauthenticated inquiries returned 401.

### Remaining inputs and launch gates

- Owner must supply `WHATSAPP_BUSINESS_NUMBER` (country code plus digits).
- Complete a real CLIENT sign-in → inquiry → WhatsApp → profile/resume → ADMIN
  conversion/start → customer progress journey. No real message was sent by tests.
- EC2 account/instance/access and cost eligibility remain unverified. Follow
  `docs/EC2_DEPLOYMENT.md` for SSH-tunneled private evaluation without a domain.
  Public production requires HTTPS, appropriate Clerk configuration and the
  previously documented backup/privacy/provider/security launch checks.
- Existing dependency advisories, live Resend/OmniRoute verification and earlier
  documented limitations are not superseded by the new UI or passing tests.
