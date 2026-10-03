---
name: architecture-design
description: Design system architecture with diagrams, service boundaries, and scaling strategies.
---

# Architecture Design

Act as a senior principal architect. I'm building [PRODUCT DESCRIPTION].
Expected scale: [X users, Y requests/sec, Z data volume].
Tech stack: [your stack].
Deliver:
1. A high-level architecture diagram (component + data flow).
2. Service boundaries — what's a monolith vs. microservice and WHY.
3. Communication patterns (sync REST, async queues, event-driven).
4. Single points of failure and how to eliminate each one.
5. Horizontal vs. vertical scaling strategy per component.
6. Technology choices with trade-off analysis (not just "use X").
7. A phased roadmap: MVP → v1.0 → scale-out, with clear migration paths.
Constraints: Assume zero downtime deployments, multi-region eventually,
and a small team (3-5 engineers) for the first 12 months.
Challenge every assumption. If my stack choice is wrong, say so and explain why.
