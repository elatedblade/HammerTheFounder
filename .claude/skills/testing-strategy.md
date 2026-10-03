---
name: testing-strategy
description: Build a comprehensive testing strategy with unit, integration, and e2e tests.
---

# Testing Strategy

Act as a QA architect building a testing strategy for a production product.
Stack: [your stack].
Current test coverage: [none / basic / describe].
Deliver:
1. Testing pyramid — exact ratio of unit : integration : e2e tests for MY app.
2. Unit test plan: which functions/modules to test, edge cases, mocking strategy.
   Write 5 example tests as templates.
3. Integration test plan: which service boundaries to test, test DB setup/teardown,
   fixture strategy.
4. E2E test plan: critical user journeys to automate, tool choice
   (Playwright/Cypress/Selenium — justify), page object model structure.
5. API contract testing approach (Pact, schema validation).
6. Performance/load testing: tool, scenarios, acceptable thresholds.
7. Security testing: SAST, DAST tools and CI integration.
8. Test data management: factories, fixtures, seeding, cleanup.
9. CI pipeline integration: when each test type runs, parallelization,
   fail-fast rules.
10. Coverage targets — realistic numbers, NOT "100%," with justification
    for what to cover and what to skip.
11. Flaky test detection and quarantine process.
Every test must be deterministic, isolated, and fast. No tests that depend
on external services without mocks.
