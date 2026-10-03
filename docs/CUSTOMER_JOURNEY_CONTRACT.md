# Three-page customer journey integration contract

Scope: `new by harshit.md`. No invented WhatsApp number/prices. Retain permissions
and manual campaign activation.

## File ownership

- Landing agent: `client-web/src/app/page.tsx`, `src/components/marketing/**`,
  `src/lib/marketing.ts`, their CSS modules. Public server-rendered page.
- Workspace agent: other client-web files, shared API, profile/dashboard routes,
  auth, /workspace redirect, tests and globals.
- Backend/admin agent: `backend/apps/inquiries/**`, conversion integration if
  necessary, tests, admin-web inquiry screens. Main wires settings/URLs/env.
- EC2 agent: NEW deployment files/docs only; not existing Compose/Dockerfiles,
  apps, private environment files or actual cloud resources.

## Shared plans

Landing agent creates `src/lib/marketing.ts`, exports `SERVICE_PLANS` array:
`{id:'NORMAL_APPLY'|'COLD_APPLY'|'FULL_THROTTLE',name,summary,features:string[]}`.
No prices. Workspace imports this stable export. Landing CTA links to
`/dashboard?plan=PLAN_ID`, not an invented wa.me destination.

## API (backend/admin agent)

- `GET /api/v1/public/contact/`: public `{whatsapp_configured:boolean}`. Backend
  setting `WHATSAPP_BUSINESS_NUMBER` holds country-code-inclusive digits (no `+`).
- `GET /api/v1/candidate/inquiries/`: active CLIENT only, owned records newest first.
- `POST /api/v1/candidate/inquiries/`: CLIENT `{plan}`. Lock user and reuse same-plan
  open inquiry on retry/double-click. Link to User; saved profile not required.
  Missing contact config returns stable 503 before writes. Never create campaign,
  profile, payment or send anything automatically.
- Inquiry DTO: `{id,reference,plan,status,created_at,updated_at,campaign_id,whatsapp_url}`.
  Status OPEN/CONTACTED/CONVERTED/CLOSED. Customer whatsapp_url only for open
  follow-up states and valid config: trusted `https://wa.me/NUMBER?text=...` containing
  plan + reference, not email/resume/compensation or private profile data.
- `GET /api/v1/admin/inquiries/`: admin all; operator visibility matches assigned/
  intake candidate policy. Optional status/limit/offset. Adds
  `user_id,candidate_id|null,customer_name,customer_email,notes` to DTO.
- `PATCH /api/v1/admin/inquiries/{id}/`: explicit OPEN→CONTACTED/CLOSED,
  CONTACTED→CLOSED; optional internal notes. No arbitrary IDs or ownership mutation.
- `POST /api/v1/admin/inquiries/{id}/convert/`: admin-only; requires existing active
  CLIENT profile, uses campaign service to create selected plan, links and marks
  CONVERTED with audit. Repeats return same campaign; never starts/charges.
  Response `{inquiry:...,campaign_id:uuid}`. Missing profile 409 actionable error.
- Error envelope unchanged. Validate fields, scope reads/writes, audit transitions,
  use transactions/uniqueness for retries and bounded throttle for inquiry creation.

## Client workspace

- `/dashboard?plan=...` validates enum and shows explicit confirmation button
  'Continue to WhatsApp'. POST only on click, then validate returned wa.me URL and
  navigate. No effect-based mutations or fictional message-sent status. Errors
  preserve intent. Missing config offers truthful notice, never false success.
- Preserve plan query through Clerk sign-in/up redirects. Profile/resumes live on
  /profile. Dashboard shows inquiry/status, compact real progress and next action.
- Protect /profile and /dashboard in src/proxy.ts. /workspace redirects /dashboard.
- Operational roles get clear admin link using NEXT_PUBLIC_ADMIN_URL (localhost:3001
  default), not candidate permissions. Auth supporting routes remain intact.
- Never read/print existing environment files. Defer broad checks to main integration.
