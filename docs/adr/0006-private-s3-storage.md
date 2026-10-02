# ADR 0006: Keep uploaded files in private S3

## Context

Resumes and other candidate documents are sensitive. They need durable object
storage without exposing public URLs or routing large files through Django.

## Decision

Store uploads in a private AWS S3 bucket. Store object keys in PostgreSQL and
use short-lived presigned upload/download URLs after authorization.

## Alternatives

- Make the bucket or objects public.
- Store files directly in PostgreSQL or on the application filesystem.

## Consequences

Candidate files receive a smaller exposure surface and storage scales
independently from application containers. Bucket policies, credentials, URL
expiry, and lifecycle/backup operations must be managed carefully.
