---
name: internationalization
description: Set up i18n with translation management, RTL support, and locale-specific formatting.
---

# Internationalization (i18n)

Act as an i18n engineer. Set up internationalization for [PRODUCT].
Target languages: [list — e.g., English, Spanish, French, Arabic, Japanese].
Deliver:
1. i18n library setup (react-intl, next-intl, i18next — justify choice).
2. Translation key naming convention and file structure.
3. String extraction workflow — how devs mark strings, how translators
   get them.
4. Pluralization and gender handling per language.
5. Date, time, number, and currency formatting (Intl API).
6. RTL (right-to-left) layout support for Arabic/Hebrew.
7. Dynamic content translation — user-generated content strategy.
8. URL strategy: subpath (/en/), subdomain (en.), or query param.
9. Language detection: browser preference → user setting → default.
10. Translation management system (TMS) recommendation.
11. CI check: fail build if translation keys are missing for any locale.
12. Testing strategy — visual regression for each locale.
Never concatenate translated strings. Never hardcode date/number formats.
