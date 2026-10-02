# ADR 0004: Delegate authentication to a managed provider

## Context

HTF needs secure sign-in and Google OAuth without owning password storage and
provider-specific identity flows. Authorization and application roles still
belong to HTF.

## Decision

Use managed authentication (Clerk with Google OAuth as the planned provider).
Django verifies the authenticated request and maps the external subject to its
local user record through an adapter.

## Alternatives

- Build and operate password authentication in Django.
- Couple business logic directly to a provider SDK.

## Consequences

Identity operations and social sign-in are delegated to a specialist while HTF
retains local authorization and object permissions. Provider integration must be
isolated and verified, and the service becomes an external dependency.
