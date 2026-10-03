---
name: frontend-architecture
description: Design UI architecture with React/Vue, state management, and component systems.
---

# Frontend / UI Architecture

Act as a senior frontend architect. Design the UI architecture for
[PRODUCT].
Framework: [React / Vue / Angular / Svelte — specify].
Deliver:
1. Project structure — folder organization (feature-based, not type-based).
2. State management strategy: local state, global state, server state (React Query / SWR / TanStack Query).
3. Component design system:
   - Atomic design hierarchy (atoms → molecules → organisms → templates → pages).
   - Props API conventions, composition patterns.
   - Shared component library structure.
4. Routing architecture — nested routes, protected routes, lazy loading.
5. Form handling — validation library, error display, multi-step forms.
6. Data fetching patterns — loading states, error states, empty states,
   optimistic updates.
7. Styling approach: CSS Modules / Tailwind / styled-components — justify.
8. Responsive design breakpoints and mobile-first strategy.
9. Dark mode / theming architecture.
10. Animation strategy — when to animate, performance budgets, library choice.
11. SEO: meta tags, Open Graph, structured data, SSR/SSG decisions.
12. Bundle optimization: tree-shaking, code splitting, dynamic imports.
No prop drilling beyond 2 levels. No "god components" over 200 lines.
Every component must have a single responsibility.
