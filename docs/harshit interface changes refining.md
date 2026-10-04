# Harshit interface changes refining

Date: 2026-10-03. Status: implementation progressed after owner approval; see
the delivery update below. Local `.env` now includes `SUPPORT_EMAIL`; no
address is invented and any existing configured value is preserved.

## Delivery update following approval

### Latest follow-up: restored navigation and verified admin/customer parity

Inquiries and Notifications are primary admin tabs again. The Campaigns duplicate
request panel is removed. Campaign scope and its explanatory toolbar render only
in Overview; other tabs receive an empty global campaign filter, so an Overview
selection cannot silently hide Applications, Payments or Notifications records.
Campaign selection within individual create forms remains available and required.

The customer overview has exactly five primary cards: Total applications, In
progress, Under review, Interviews, Offers. All other numeric metrics remain in
collapsed Additional metrics, and detailed tabs are retained. Total includes
recorded unsent applications; In progress means IN_PROGRESS; Under review means
IN_REVIEW plus RECRUITER_CONTACTED. These are server-derived counts, not editable
numbers. Admin updates them through Applications → Open → Update application
status. Legal transitions/readiness checks still apply. Customer Refresh overview
or a fresh page load reads the saved state; cross-session push updates are not
implemented or claimed.

Help's requested mailbox is configured through local `SUPPORT_EMAIL`, not embedded
in UI source. The live public contact endpoint was checked for the exact requested
value. Restored Notifications now supports deterministic paging beyond 200 records
on both admin/customer views, with drafts still hidden from customers.

New isolated `test_admin_customer_sync.py` tests execute admin HTTP view mutations
and customer reads: create company/job/application; progress through READY,
IN_PROGRESS, SUBMITTED, IN_REVIEW, INTERVIEW and OFFER; verify matching history,
metrics and submitted count; verify/refund payment; update inquiry; record manual
notification send. They assert outsider/client/unassigned-operator restrictions
and private-field filtering. A separate test checks 205 sent notifications remain
reachable without exposing a draft. No real candidates were changed and no external
messages were sent. These use DRF test authentication, not live Clerk browser auth.

Latest checks: **186 backend tests passed**, Django and migration-drift checks
passed; admin **6** helper/contract tests and customer **10** helper tests passed;
both frontend lint/typechecks/builds passed; **3 anonymous browser tests passed**.
Browser tests now wait for DOM content and visible controls rather than the full
resource load event, with a bounded cold-dev-compilation allowance. All six local
services are running; public frontends and contact endpoint returned HTTP 200.
Dependencies were reused locally because lockfiles/manifests were unchanged apart
from scripts; no fresh provider installs or business data mutations were required.

Remaining scope: full live authenticated browser walkthrough and security-advisory
triage remain open; passing isolation tests is not a guarantee of zero vulnerabilities.

## Outreach and refresh follow-up

Outreach is again a primary admin tab and uses existing manual resources. It is
connected to the customer dashboard's Outreach view with paged records, safe
customer serialization and the same campaign visibility boundary as applications.
The dashboard refresh button now starts a new reload generation for all customer
progress resources and cancels stale requests, so admin status updates can be read
without a full browser reload. Sync tests cover application and outreach status
changes, customer visibility and outsider denial.

- Dashboard now derives its next action from campaign lifecycle. ACTIVE wins over
  missing inquiries and profile prompts; READY/onboarding/draft/paused states do
  not show acquisition CTAs. Loading and failed campaign reads are not empty states.
  Removed the residual choose-plan empty inquiry text for existing campaigns too.
- Admin default tabs are Overview, Candidates, Campaigns, Applications, Payments.
  Removed embedded task queue chrome. Domain APIs/data remain; plan-request
  conversion is available in an explicitly expanded Campaigns panel.
- Overview uses explicit cards instead of raw nested JSON. Added ready-to-start,
  pending payment and future scheduled interview counts with real scope. Activity
  is collapsed and campaign-specific; no global raw-ID timeline by default.
- Candidate table has server-scoped submitted counts and server-side name/email
  search. Details include paged application/payment histories while retaining
  editing, review, private resume download and parsing. Read-only tables have no
  dead Open buttons. Operator aggregates cannot include other assignments.
- Applications have a separate creation flow with searchable paged job/company
  catalogs and dependent creation, preserving the draft and selecting the saved
  job. UUIDs stay strings; a regression test protects against numeric coercion.
- Payment API preserves array compatibility and adds deterministic limit/offset;
  both customer and admin histories can page beyond the old 200-record cap.
- Both workspaces use the landing's light ivory/ink/rust palette. Dark auto-theme
  overrides were removed. Low-contrast leftovers in admin labels/links/selection
  were corrected during integration.

Known limitations: authenticated browser acceptance remains outstanding. Campaign
selector still preloads a bounded list; not every original optional optimization
is complete. Communications is retained in source/API but hidden in default admin
navigation. Full accessibility certification and dependency-advisory remediation
are not claimed. No actual campaign was activated or payment changed by this work.

The remaining sections preserve the audit baseline and intended acceptance criteria;
their point-in-time observations are not a current database snapshot.

### Refinement verification

Final integration completed: **182 backend tests passed** on the updated running
image, Django check passed, migration-drift check reported no changes. All six
local Compose services are running. Landing, admin and public contact returned
HTTP 200; signed-out dashboard redirected to sign-in successfully.

The slow backend rebuild was stopped during unchanged dependency downloads. For
local verification, the existing dependency image was reused and current apps,
config, tests and manage.py were copied into a new non-root image layer. Dependency
manifest was unchanged; the regular repository Dockerfile remains usable for clean
builds. Frontend images were rebuilt normally. No volumes or business records were
reset. A new test fixture initially violated the interview-date constraint; it was
corrected to supply a date, without weakening that constraint, and the suite rerun.

Read-only final database snapshot still reports two READY campaigns, zero ACTIVE
and one pending payment. The UI fix handles actual ACTIVE records, but this release
does not turn payment verification or a READY record into a campaign start. The
owner should use the explicit Start action and check its result/readiness message.

- Admin: TypeScript, ESLint, production build and 3 tests passed (one behavioral
  UUID/lookup helper test, two source-contract checks; not browser coverage).
- Customer: TypeScript, ESLint, production build and 8 helper/lifecycle tests passed.
- Anonymous Playwright: 3 passed after clearing an orphan test dev server from a
  timed-out run and warming the lazily compiled target route. This does not verify
  authenticated admin/customer interaction.
- New backend history regression suite passed against a rebuilt image (181 total
  tests at that point). A further scoped-overview test and additive overview metrics
  were added during integration; the final rebuilt backend result is recorded below
  when available. Never treat an old running Docker image's tests as new-code proof.

## 1. Goal and governing scope

Make HTF a focused candidate/application operations product, with the landing
page's warm ivory/ink theme across customer and admin interfaces. Preserve the
working backend, customer plan selection, manual execution, role restrictions,
private resumes, payment verification and historical records.

References: `IMPLEMENTATION_PLAN.md` sections 12 (client dashboard), 13 (admin
dashboard), campaign lifecycle, tasks and manual billing; `new by harshit.md`
and its later dedicated Plans amendment. The original plan requires server-derived
counts, candidate/application visibility and payment oversight. Tasks/outreach/AI
are supported domains, not inherently useless features; their prominence is wrong
for the owner's current operating needs. This latest request supersedes their
default admin navigation placement, not their data or security requirements.

Do not auto-activate campaigns, fabricate jobs/applications, mark receipts paid,
delete operational domains, or change provider/account choices during refinement.
“Industry standard” means measurable checks below, not a guarantee of perfection.

## 2. Findings confirmed from code and local read-only checks

| Priority | Finding and evidence | Required correction |
| --- | --- | --- |
| P1 | Active count is consistent with stored data: two campaigns are READY; none ACTIVE. One has billing_status ACTIVE, one PENDING. Payments include one VERIFIED and one PENDING. `backend/apps/dashboard/selectors.py` correctly counts lifecycle ACTIVE only. | Separate “Campaign: Ready to start” from “Payment: Verified”; make explicit Start action/readiness blockers easy to find. Never count paid-but-not-started campaigns as active. |
| P1 | Application Job dropdown has no available records: authenticated read-only jobs and companies requests each return HTTP 200 and zero rows. Exact reported browser error is not reproduced. `workspace.tsx` requests jobs?limit=500 and `ui.tsx` renders an empty required select. | Distinguish empty, loading and error states; offer create company → create job → return to application. Capture exact browser/network error before declaring the reported bug fixed. |
| P1 | Candidate detail in `candidates-panel.tsx` contains profile/review/resumes only. Candidate table lacks application counts. | Add authoritative submitted count, paginated application history and payment history scoped to candidate's visible campaigns. |
| P1 | Overview loops over arbitrary metrics; nested by_status maps reach the generic display formatter in `dashboard.tsx`. This is the source of the raw JSON block. | Typed explicit summary cards; no raw object rendering. Remove outreach/task metrics from default overview. |
| P2 | `billing/views.py` silently limits payment history to 200 and has no paging. | Add backward-compatible pagination and matching customer/admin navigation; never call a truncated response “all payments.” |
| P2 | Application and payment customer views already exist in `candidate-progress.tsx`. | Reuse and validate these, do not create competing copies or separate stored counts. |
| P2 | Admin hardcodes dark/yellow styles; landing uses ivory/ink/rust CSS variables. Customer workspace is a third style. | Shared semantic design specification and reusable tokens, without coupling styles to API/state logic. |
| P2 | Generic Details renders every returned field; global event list displays internal-looking event labels and campaign IDs. | Curated fields and human labels; move contextual activity to candidate/campaign detail. Preserve audit events server-side. |
| P2 | Form lookups preload at most 500 rows; candidate search searches only the loaded page. | Searchable, paginated server lookups and explicitly scoped candidate search. |
| P2 | Application review tasks also render under Applications, not only the Tasks tab. | Remove queue-like chrome there too; retain actionable failure/interview guidance near the source record. |

The database observations are a point-in-time snapshot, not a judgement that the
owner did not perform work externally. If work is running externally, record
the campaign start through its authorized lifecycle action after readiness checks.
No production/local business records were modified for this audit.

## 3. Feature disposition and target navigation

**Default admin:** Overview, Candidates, Campaigns, Applications, Payments.

- **Hide now:** Inquiries, Outreach, Tasks and AI proposals from default admin
  navigation, overview cards and queue widgets. Preserve modules, endpoints,
  migrations, authorization, events and historical data. Centralize the UI
  visibility registry; UI flags are not authorization controls.
- **Keep:** candidate intake/review/resumes, campaign start/pause/resume, application
  recording/outcomes, payment history/verification and audit trails.
- **Companies/Jobs:** needed dependencies, not top-level distractions. Accessible
  within application creation and secondary catalog management.
- **Communications:** retain functionality; propose a secondary/advanced entry
  rather than deleting it. This is a recommendation, not an explicit removal request.
- **Inquiries hidden ≠ acquisition disabled:** provide a selected-plan/request
  summary in candidate/campaign detail and preserve a deliberate conversion action
  there, or retain direct admin access outside default navigation. Pre-profile
  inquiries must not be lost. Do not auto-create campaigns as a substitute.
- **Outreach customer data:** do not remove customer history or advertised Cold
  Apply deliverables merely because its admin navigation is hidden. Record the
  temporary operational limitation and keep a deliberate re-enable mechanism.

Customer navigation remains Home, Dashboard, Plans, Profile. Applications and
Payments stay readable inside the dashboard with the same authoritative records
as admin; they are not new disconnected customer pages.

## 4. Overview and campaign lifecycle UX

Use a small explicit card set: active campaigns, ready-to-start campaigns,
applications submitted, upcoming interviews and pending payments. Show selected
scope plainly; distinguish global totals from a selected campaign's totals.
Hide zero-heavy status matrices; put meaningful nonzero breakdowns behind details.

Payment verified is a financial event, not a campaign-start event. Show separate
badges “Campaign: Ready to start” and “Payment: Verified”; use readable labels even
if legacy API enums remain unchanged. After successful Start, invalidate both
campaign list and overview metrics. Verify ACTIVE count increments exactly once;
repeat/failed starts cannot double-count. Explain profile/resume/billing/assignment
blockers without changing readiness rules. Contextual activity includes dates and
human descriptions, not a global wall of machine labels or raw IDs.

## 5. Candidate-centered application and payment views

Candidate list adds submitted application count; detail contains Profile & resumes,
Applications, Payments and campaign summaries. Aggregate across the candidate's
campaigns by default with an explicit optional campaign filter.

Define “applications sent” as confirmed submitted at any time: use the existing
server submitted predicate (submitted timestamp or supported post-submission
legacy statuses), not just current status SUBMITTED. Draft/saved/queued/failed
before submission do not count; later replies/rejections do not erase sent count.
Use database aggregates, not page lengths or one request per candidate.

Applications show company, role, submitted date, current status, last update and
campaign label. All records are reachable through paging. New records created as
saved/draft are not presented as sent; operator explicitly records external submission.
Customer reads must strip internal notes, failure diagnostics and source references.

Payments show date, amount/currency, status and campaign. Admin can see receipt
reference/verifier under existing permissions; client must not receive internal
notes, verifier identity or currently protected receipt references. Pending is not
paid. Refund is not an extra payment. Do not sum mixed currencies into one total.

Candidate-scoped endpoints or filters must intersect candidate visibility AND
visible campaigns: an operator seeing a candidate via one assignment must not
gain access to that candidate's other operators' campaigns. Client candidate IDs
cannot expand scope. Add permission tests before exposing aggregates.

## 6. Application creation repair

1. Reproduce the reported dropdown error with the owner's session or a synthetic
   authenticated test; capture sanitized request status/validation field, not tokens.
2. Separate no jobs from lookup/network failure. Show “Create a job first” with
   inline/returnable company and job creation; disable application submission until
   a real job and authorized campaign are selected.
3. Refresh options after saving a job and select that returned job ID. Preserve
   campaign and form values across dependent creation; do not submit automatically.
4. Search/paginate jobs server-side, show company/title/location and closed state.
   Decide closed-job policy explicitly rather than quietly changing backend behavior.
5. Preserve backend job identity and candidate/job deduplication; show useful 409
   conflicts. No random IDs, fake jobs or client-only application records.

## 7. Theme and component isolation

Use landing palette as source: ivory #f7f4ed, paper #fffdf8, ink #1f2925,
muted #66706a, line #dfe3dc, rust #ae3917, blue #294f63. Validate contrast for
actual combinations; palette reuse alone does not prove WCAG compliance.

Create semantic tokens for surfaces, text, action, focus, success/warning/error,
spacing and typography. Reuse visual primitives for navigation, cards, tables,
forms, badges and empty/error/loading states. Preserve dense readable operational
tables rather than applying giant marketing headings everywhere. Scope CSS to
avoid global heading/form overrides. Keep status-to-label mapping explicit.

Feature modules own their loading, error and retry boundaries; shared auth/API
utilities live outside optional feature folders. A hidden or failed AI/inquiry/
outreach module must not load or block Candidates, Applications or Payments.
Request cancellation and stale-response guards must protect account/candidate
switches. Preserve field values on validation/network errors and version conflicts.

## 8. Sequenced implementation with rollback boundaries

1. **Baseline and contracts:** preserve current work, snapshot relevant API schemas,
   add failing regressions for reported behavior, specify submitted-count semantics.
   No schema change just to hide tabs. Back up privately before any later migration.
2. **Correctness:** job dependent-creation UX, lifecycle/payment labels and metric
   refresh. Add backend candidate aggregates/history filters and payment paging.
   Keep old endpoints compatible; no counters independently stored in the UI.
3. **Navigation simplification:** hide requested modules via one registry; remove
   their overview/embedded queue chrome. Keep conversion and essential manual
   operational routes usable without reinstating whole tabs.
4. **Candidate hub and customer parity:** candidate counts, application/payment
   panels, paging and scoped refresh. Reuse authoritative serializers/selectors.
5. **Theme:** visual-only tokens/primitives and responsive layouts. Keep behavioral
   commits separate from style changes so either can be rolled back independently.
6. **Combined acceptance:** API permissions/lifecycle tests, browser workflows,
   builds, responsive/keyboard review and owner walkthrough. Report actual gaps.

No destructive migrations, forced dependency upgrades, provider changes, cloud
provisioning, payment execution or external application sending in this refinement.
Do not erase uncommitted work. A navigation rollback restores feature visibility,
not database snapshots or historical state.

## 9. Required acceptance tests for implementation

- READY + verified payment => active zero; successful explicit Start => active one;
  pause => zero; resume => one. Verify global and selected-campaign scopes.
- Overview never renders nested JSON/status maps. API failure is unavailable,
  not zero. Every prominent action leads to its named task.
- Hide Inquiries/Outreach/Tasks/AI nav without deleting APIs/data or breaking plan
  inquiries, application failure handling, interview records or campaign conversion.
- Empty job catalog guides company/job creation; a real saved job becomes selectable.
  Lookup failure/retry, duplicates, stale selection and forbidden campaign fail safely.
- Two candidates and multiple campaigns: application counts match database truth;
  complete paged application and payment histories agree with each client's dashboard.
  Test >200 payments and >500 lookup records with isolated synthetic fixtures.
- Application transitions retain sent totals after interview/rejection/withdrawal
  where submission evidence exists. Unsent records do not inflate totals.
- ADMIN, assigned OPERATOR, unrelated OPERATOR, CLIENT and inactive identities:
  no cross-candidate/cross-assignment reads or writes, including aggregate counts.
- Support email blank/invalid => honest unavailable state; valid config => safe
  email link. No config values embedded in code, logs or screenshots.
- Mobile tables/navigation, keyboard-only actions, focus visibility, color contrast,
  errors, loading and empty states; same visual system on admin/customer/landing.
- Simulated inquiry/AI/contact failures do not block candidate applications/payments.
  Account switching and delayed requests cannot reveal previous-account records.

## 10. Checks actually run during this audit

| Check | Result |
| --- | --- |
| `docker compose exec -T backend python -m pytest -q` | 177 passed |
| Backend `python manage.py check` | No issues |
| Backend `python manage.py makemigrations --check --dry-run` | No changes detected |
| Admin `npm run typecheck && npm run lint && npm run build` | Passed |
| Client `npm run typecheck && npm run lint && npm test` | Passed; 4 helper tests |
| Client `npm run test:e2e` | 3 anonymous browser tests passed |
| Read-only DRF jobs/companies requests using current admin identity | HTTP 200; zero records each |
| Read-only admin dashboard request | HTTP 200; total 2, active 0, matches stored lifecycle states |

DRF request-factory checks validate view behavior but bypass Clerk/browser transport;
they do not reproduce the precise dropdown interaction. Existing anonymous browser
tests do not cover authenticated admin flows or candidate/payment parity. Passing
the current suite does not establish the proposed refinement is implemented.

## 11. Remaining risks and decisions

- Support mailbox still needed; `.env` option exists, not a fabricated address.
- Exact dropdown error and reported external campaign activity need owner/browser
  confirmation. The data explains empty options and zero active count, not every
  possible browser failure.
- Earlier five high-severity frontend dependency advisories need separate targeted
  triage and regression checks; not resolved by a theme change. Clerk's route
  matcher deprecation is still reported. No security certification claimed.
- Hiding outreach/tasks/AI reduces clutter, but those domains implement original
  plan requirements. Keep essential review guidance and a deliberate route to
  supported manual workflows; do not silently strand paid service delivery.
- Full project readiness still depends on authenticated acceptance, live provider
  checks and deployment/privacy/backups documented in `DELIVERY_STATUS.md`.

Audit deliverables are this plan and the `.env` support-email option. No admin
navigation, theme, campaign state, payment or application data changed in this pass.
