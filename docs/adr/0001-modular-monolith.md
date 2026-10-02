# ADR 0001: Use a modular monolith

## Context

HTF's initial complexity is the managed job-search workflow, not independent
service scale. The system needs transactional coordination across domains and
fast iteration while requirements are still changing.

## Decision

Build v1 as a Django modular monolith. Keep domain modules, ownership, and
integration boundaries explicit so a component can be extracted later if
measured demand justifies it.

## Alternatives

- Start with networked microservices.
- Use an unstructured monolith with no module boundaries.

## Consequences

Local development and deployment are simpler, with fewer network failure modes
and straightforward transactions. Teams must preserve module boundaries and
avoid turning the monolith into shared, unowned code.
