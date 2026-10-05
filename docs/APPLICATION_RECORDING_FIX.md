# Application recording fix — 2026-10-05

## Five-stage follow-up

### Consistent editor follow-up

The application stage editor always displays the same five choices. It uses a
dedicated permission-scoped, transactional `applications/{id}/stage/` endpoint,
not a varying list of legacy next transitions. Current stage is preselected.
Forward stage jumps are supported; backward changes and historical terminal
record rewrites are rejected with explanatory errors. An unsent record advancing
to Under review, Interviews or Offers requires an explicit unchecked-by-default
submission confirmation and active campaign/open-job validation. First submission
date is retained; same-stage requests do not duplicate audit events or counts.

Verification: 96 focused application/history/sync tests passed on PostgreSQL.
Final full backend suite: 332 passed using the isolated reused test database after
interrupted runs; Django checks passed and migration drift reported no changes.
Admin 27 tests, typecheck/lint/build passed. Local backend/admin services updated.
A concurrent outreach consumer expected `replied` while the API exposed `replies`;
an additive alias now returns the same aggregate under both keys without deleting
the existing key. No live application records were changed or messages sent.

Admin and customer application filters/display now use Saved, In progress,
Under review, Interviews and Offers. These are non-destructive projections:
Saved includes saved/discovered/shortlisted/ready; In progress includes queued/
in-progress; Under review includes submitted/in-review/recruiter-contacted;
Interviews includes interview/scheduled; Offers includes offer. Rejected,
withdrawn and failed records remain truthful historical outcomes accessible in
All history, not falsely reassigned to a successful stage.

Dashboard uses server `applications.stage_counts` for these five cards. Lifetime
submitted count is prominent and separate; admin candidate submitted counts use
the same existing submission-evidence predicate. Explicit Record submitted is
retained, then its application appears Under review. No preparation record is
silently submitted. Stage filters intersect existing permissions and pagination;
legacy status API compatibility and history are preserved without migrations.

Follow-up verification: 236 backend tests passed against PostgreSQL on updated
source; Django and migration-drift checks passed. Delegated frontend checks passed:
22 admin tests and 23 customer tests, both typechecks/lint/builds. New tests cover
legacy-stage mapping, authoritative counts, stage filtering and access isolation.
Updated local services restarted. Live authenticated browser walkthrough remains
a separate acceptance step.

Admin application rows now show candidate name/email from the actual linked
candidate, plus company, role, current stage and submitted date. Candidate identity
is read-only and filtered out of customer responses; existing permission scoping
is retained. Additional timestamps and references remain in record details.

Saved/Discovered/Ready are preparation stages, not evidence of submission.
The explicit **Record submitted** action confirms external work already happened,
records SUBMITTED and its timestamp, and refreshes saved records. It does not send
an application. Saved/Discovered/Shortlisted may now record confirmed submission
without replaying every preparation stage. Active-campaign/open-job guards remain.

The stable COLD_APPLY identifier now represents the currently marketed Better
Apply plan, whose public deliverables include applications. Removed the obsolete
outreach-only application restriction for that identifier. No plan IDs, prices,
payment state or live application statuses were changed.

The existing submitted-count predicate was correct: unsent preparation records
do not count; timestamp-backed later rejections/withdrawals retain lifetime count.
The current local records had no submission dates during read-only diagnosis.
No records were automatically marked submitted to change the totals.

Verification: 213 backend tests passed on updated source against PostgreSQL;
Django system and migration-drift checks passed. Admin 12 tests, typecheck, lint
and production build passed. New tests cover identity/spoof filtering, direct
confirmed submissions, all three current plans, timestamps, lifetime counts,
customer synchronization and active/open-job/access guards. Services updated
locally using existing dependency images; no dependencies changed. Authenticated
browser acceptance is still separate from these API/helper checks.
