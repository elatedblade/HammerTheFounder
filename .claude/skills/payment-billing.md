---
name: payment-billing
description: Implement subscription and billing with Stripe including webhooks and compliance.
---

# Payment & Billing

Act as a payments engineer. Implement billing for [PRODUCT].
Model: [subscription / one-time / usage-based / freemium — specify].
Provider: [Stripe / Paddle / Lemonsqueezy — specify].
Deliver:
1. Pricing model implementation — plans, tiers, feature gating.
2. Checkout flow — hosted vs. embedded, UX considerations.
3. Subscription lifecycle: create, upgrade, downgrade, cancel,
   pause, resume, trial.
4. Webhook handling — every event type, idempotency, signature verification,
   retry handling.
5. Invoice and receipt generation.
6. Failed payment recovery — dunning flow, grace period, account lockout.
7. Proration and mid-cycle plan changes.
8. Tax handling — sales tax, VAT, GST compliance (or Stripe Tax integration).
9. Refund flow — full, partial, policy enforcement.
10. Revenue metrics: MRR, churn, LTV — how to calculate from webhook data.
11. PCI compliance — what you handle vs. what the provider handles.
12. Testing: test mode, test card numbers, webhook simulator.
Never store raw card numbers. Never build your own payment form without
PCI DSS compliance. Use the provider's hosted fields/elements.
