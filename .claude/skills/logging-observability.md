---
name: logging-observability
description: Set up structured logging, metrics, tracing, and alerting for production observability.
---

# Logging & Observability

Act as an observability engineer. Set up complete observability for
[PRODUCT] in production.
Deliver:
1. Structured logging format — JSON schema with: timestamp, level,
   service, request_id, user_id, action, duration_ms, metadata.
2. Log levels — define what goes at DEBUG, INFO, WARN, ERROR, FATAL
   with concrete examples from MY app.
3. Distributed tracing — setup with trace_id and span_id propagation
   across services.
4. Metrics to collect:
   - Business: signups, conversions, active users
   - Technical: latency p50/p95/p99, error rate, saturation, traffic
   - Infrastructure: CPU, memory, disk, network
5. Dashboard design — what charts, what alerts, for which audience
   (dev, ops, business).
6. Alerting rules — conditions, severity, escalation path, runbooks.
7. Health check endpoints — /health, /ready, /live with what each checks.
8. Log aggregation stack recommendation (ELK, Grafana+Loki, Datadog, etc.)
   with cost/benefit analysis.
9. PII redaction — which fields to mask in logs, how to implement.
10. Log retention policy — how long, where, compliance requirements.
Every request must be traceable end-to-end with a single request_id.
