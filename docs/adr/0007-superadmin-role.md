# ADR 0007: Retain an intentional SUPERADMIN role

## Context

HTF needs a narrowly controlled break-glass role for platform-wide governance
and recovery that is distinct from routine operational administration. The role
must not be introduced accidentally through ordinary user provisioning.

## Decision

Keep `SUPERADMIN` as an explicit application role for exceptional, audited,
platform-wide actions. It is separate from Django's `is_staff` and
`is_superuser` flags, is not the default role, and is granted only through an
explicit administrative process.

## Alternatives

- Treat every `ADMIN` as globally privileged.
- Rely only on Django's built-in staff/superuser flags.
- Omit a break-glass role entirely.

## Consequences

Routine admins can follow least-privilege policies while exceptional actions
remain possible and attributable. Authorization checks, granting/revoking,
monitoring, and audit policy must make the role intentionally rare.
