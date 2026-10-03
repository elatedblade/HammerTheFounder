# Enable resume uploads

The supplied bucket is `hammerthefounder` in `ap-southeast-2` (Sydney).
The initial upload warning was caused by missing credentials, followed by CORS
and IAM configuration gaps. Those storage checks now pass (see verification below).
Do not hide configuration errors or make the bucket public.

## Credentials (private configuration only)

In the repository's private root `.env`, set `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` for a restricted application identity. Never put the values
in chat, screenshots, source files or commits. The current storage adapter requires
these two explicit credentials; temporary session-token/role credentials need an
adapter update and are not supported by these instructions.

Grant only the required object actions for the candidate prefix, using this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject"],
    "Resource": "arn:aws:s3:::hammerthefounder/candidates/*"
  }]
}
```

S3 HEAD verification uses GetObject permission. A customer-managed KMS encryption
key also requires appropriate KMS permissions. Keep Block Public Access enabled.

## Bucket CORS

In S3 → bucket → Permissions → CORS, allow the candidate development origin:

```json
[{
  "AllowedOrigins": ["http://localhost:3000"],
  "AllowedMethods": ["PUT"],
  "AllowedHeaders": ["content-type"],
  "MaxAgeSeconds": 300
}]
```

Use an exact HTTPS frontend origin for production rather than a wildcard.
CORS permits browser transport; it does not grant object authorization.

## Apply and verify

```sh
docker compose up -d --force-recreate backend worker
```

Then use an active CLIENT test account with a saved profile to upload a small test
PDF. Confirm the record changes to UPLOADED and its authorized download succeeds.
A record left in PENDING_UPLOAD is not proof of success. Credential presence alone
does not prove the IAM policy, bucket policy, encryption or CORS are correct.

## Verified after configuration

On 2026-10-03, a synthetic, non-personal PDF passed the real S3 storage path:
browser-origin PUT preflight, signed upload (HTTP 200), upload-response CORS,
server-side size/type verification, and byte-matching signed download. Anonymous
access returned HTTP 403. This verifies storage transport, not a completed
authenticated candidate browser upload.

Cleanup was denied because the application identity has no DeleteObject permission.
No broader permission is needed for resume uploads. Remove the synthetic object
manually from the S3 console if desired:
`candidates/_setup-checks/b935979d-7a1e-45d9-b0e9-249bb0e5a3f0/original.pdf`.
