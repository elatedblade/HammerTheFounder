---
name: code-review-quality
description: Define code quality standards with linting, formatting, and review checklists.
---

# Code Review & Quality Gates

Act as an engineering manager. Define code quality standards for [PRODUCT].
Deliver:
1. Linting config — ESLint/Pylint/Clippy rules with justification for
   each non-default rule.
2. Formatting — Prettier/Black/rustfmt config, enforced via pre-commit hooks.
3. Type checking — TypeScript strict mode / mypy strict / equivalent.
4. Code review checklist — what reviewers must check (security, performance,
   tests, naming, edge cases).
5. PR template with sections: what, why, how, testing, screenshots.
6. Branch protection rules — required reviews, status checks, no force push.
7. Complexity limits — max function length, max file length, cyclomatic
   complexity threshold.
8. Dead code detection and removal process.
9. Dependency update strategy — Renovate/Dependabot config, auto-merge rules.
10. Tech debt tracking — how to tag, prioritize, and schedule debt repayment.
No PR merges without: passing CI, at least 1 approval, and linked tests
for new logic.
