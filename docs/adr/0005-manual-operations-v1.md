# ADR 0005: Keep external operations manual in v1

## Context

The initial product must prove the managed operating workflow before adding
fragile browser or messaging automation. Operators need an auditable system of
record for actions performed outside HTF.

## Decision

Operators manually submit applications, send outreach, verify payments, and
update statuses in v1. The application records those actions and keeps
integration boundaries replaceable.

## Alternatives

- Automate browser submissions and outreach immediately.
- Defer operational tooling until integrations are automated.

## Consequences

Launch risk and external automation coupling are reduced, while operators get
an explicit workflow to improve. Throughput depends on operators initially, and
future automation must preserve the same controlled service boundaries.
