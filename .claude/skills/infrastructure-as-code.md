---
name: infrastructure-as-code
description: Define cloud infrastructure with Terraform/Pulumi including networking, compute, and security.
---

# Infrastructure as Code

Act as a cloud infrastructure engineer. Define IaC for [PRODUCT].
Cloud: [AWS / GCP / Azure].
Scale: [expected traffic, data volume, regions].
Deliver:
1. Full Terraform (or Pulumi/CDK) modules for:
   - Networking: VPC, subnets, security groups, load balancer.
   - Compute: containers (ECS/GKE/AKS) or serverless.
   - Database: managed DB with replicas, backups, encryption.
   - Cache: managed Redis/Memcached.
   - Storage: object storage with lifecycle policies.
   - CDN: distribution with custom domain and SSL.
   - DNS: domain configuration.
   - Monitoring: CloudWatch/Stackdriver/Azure Monitor.
2. Environment separation: dev/staging/prod via workspaces or modules.
3. State management: remote state, locking, access control.
4. Cost estimation per environment.
5. Security: least-privilege IAM roles, network isolation, encryption.
6. Auto-scaling policies with specific thresholds.
7. Disaster recovery: multi-AZ, cross-region backup.
No ClickOps. Everything reproducible from code. Destroying and
recreating an environment must take < 30 minutes.
