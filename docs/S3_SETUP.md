# Enable resume uploads

The supplied bucket is `hammerthefounder` in `ap-southeast-2` (Sydney).
The running backend has the bucket/region, but AWS access-key ID and secret-key
settings are missing. The upload warning is therefore intentional: no upload can
be authorized yet. Do not hide the warning or make the bucket public.

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
