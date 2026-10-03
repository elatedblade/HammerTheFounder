---
name: frontend-development
description: Build and maintain the project's frontend without changing backend contracts.
---

# Frontend Development

## Scope

This skill is for frontend work only.

Prefer:
- Reusable React components
- Existing project patterns
- Existing API contracts
- Responsive layouts
- Accessible UI
- Loading, empty and error states
- Frontend validation
- Component reuse

## Backend Boundary

Never modify:
- Database models
- Migrations
- Backend business logic
- Backend workflows
- Existing API contracts

If the frontend needs an API that doesn't exist yet:
- Do not implement the backend.
- Clearly identify the missing contract.
- Isolate the frontend integration point.
- Use mock data only when necessary.

## Parallel Agent Safety

Another agent may be modifying backend/core functionality simultaneously.

Before implementing a feature:
1. Inspect the current repository state.
2. Check the relevant API contracts.
3. Avoid unrelated refactors.
4. Adapt to current backend contracts.
5. Never overwrite backend work.

## UI Quality

Every significant page should consider:
- Loading state
- Empty state
- Error state
- Disabled state
- Success feedback
- Responsive layout
- Accessibility
- Destructive-action confirmation

## Workflow

Before coding:
- Inspect existing architecture.
- Identify reusable components.
- Identify existing API services/types.
- Identify dependencies on unfinished backend work.

After coding:
- Run tests.
- Run lint/type checks.
- Report changed files.
- Report assumptions.
- Report missing backend dependencies.
