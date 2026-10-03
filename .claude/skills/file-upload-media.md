---
name: file-upload-media
description: Build file upload systems with validation, processing, and CDN delivery.
---

# File Upload & Media

Act as a media infrastructure engineer. Build file upload for [PRODUCT].
Use cases: [profile photos, documents, videos, etc.].
Deliver:
1. Upload flow: direct-to-cloud (presigned URL) vs. through backend — justify.
2. File validation: allowed types (MIME + magic bytes), size limits,
   malware scanning approach.
3. Storage: S3/GCS/Azure Blob — bucket structure, lifecycle policies,
   access control.
4. Image processing pipeline: resize, crop, thumbnail generation,
   format conversion (WebP/AVIF).
5. Video processing: transcoding, HLS/DASH streaming, thumbnail extraction.
6. CDN delivery with signed URLs for private content.
7. Progress tracking — upload progress bar, resumable uploads (tus protocol).
8. Metadata storage — DB schema for file records (URL, size, type,
   dimensions, owner).
9. Cleanup: orphaned file detection, user deletion → file deletion.
10. Cost management: storage tiers, intelligent tiering, compression.
Never trust client-provided MIME types. Always validate server-side.
Never store uploads in your application server's filesystem.
