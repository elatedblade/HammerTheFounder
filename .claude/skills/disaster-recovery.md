---
name: disaster-recovery
description: Design disaster recovery with backups, failover, and incident response playbooks.
---

# Disaster Recovery & Backups

Act as an SRE building DR for a production product.
Deliver:
1. RTO (Recovery Time Objective) and RPO (Recovery Point Objective) targets
   per service/data store — with justification.
2. Backup strategy:
   - Database: automated daily + point-in-time recovery, cross-region.
   - File storage: versioning, cross-region replication.
   - Configuration: IaC in version control = instant rebuild.
3. Backup verification — automated restore tests (weekly).
4. Disaster scenarios and playbooks:
   - Database corruption / accidental deletion.
   - Full region outage.
   - Security breach / ransomware.
   - Upstream provider outage (auth, payment, email).
5. Failover architecture — active-passive or active-active, with DNS failover.
6. Communication plan — status page, incident channels, customer notification.
7. Post-incident review template — timeline, root cause, action items.
8. Chaos engineering — what to test (kill a pod, drop a DB connection,
   inject latency) and how.
Backups you haven't tested are not backups. They're hopes.
