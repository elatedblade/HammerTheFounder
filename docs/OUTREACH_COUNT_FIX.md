# Outreach current-stage counts — 2026-10-05

Candidate detail follow-up: Admin → Candidates → Open now includes paginated
Outreach history alongside Applications and Payments, with current Sent/Responded
labels, channel, contact/company and recorded dates. The server candidate filter
intersects candidate and campaign permissions, so other candidates/operators'
records cannot leak into this view. Independent loading/error/retry states added.
Verification: 360 PostgreSQL backend tests passed; admin 33 tests, typecheck and
lint passed. Local backend and candidate UI updated; no business data changed.

Cause: the Sent dashboard card used historical `sent_at` evidence, while Responded
used reply evidence. One replied row appeared in both counters even though a status
transition updated the original row. Read-only local audit found zero duplicate
outreach identity groups and zero duplicate candidate/job application groups.

Both dashboards now use authoritative mutually exclusive `outreach.stage_counts`:
SENT includes Sent/Delivered; RESPONDED includes Replied/Positive reply/Negative
reply. Responding moves one record from Sent to Responded. Bounced, Closed and
Suppressed are historical outcomes outside these two current stages. All history,
IDs and dates are preserved. No live records were deleted or rewritten.

Grouped Outreach filters use `stage=SENT|RESPONDED`, so filtered records agree
with dashboard cards; exact legacy `status=` remains compatible. Backend historical
evidence is explicitly named `*_lifetime`; these counters and redundant aliases
are hidden from the UI. Delivery/positive/negative details are outcome subsets,
not extra records to sum with the primary cards.

Application five-stage counts were checked for disjoint membership. Upcoming
interviews are intentionally a dated subset of interview records, not additional
applications. Tests check stage totals, transitions retaining one PK, historical
outcomes, status/filter consistency and user/operator/campaign isolation.

Verification: 351 backend tests passed against PostgreSQL on updated source;
Django and migration-drift checks passed. Admin 32 tests and customer 28 tests,
both typechecks/lint/production builds passed. All local services updated. Live
authenticated browser acceptance remains separate; no external messages sent.
