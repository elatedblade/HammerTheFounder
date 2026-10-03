from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from rest_framework.exceptions import APIException


class StorageNotConfigured(APIException):
    status_code = 503
    default_detail = "Resume storage is not configured."
    default_code = "storage_not_configured"


class StorageUnavailable(APIException):
    status_code = 503
    default_detail = "Resume upload authorization is temporarily unavailable."
    default_code = "storage_unavailable"


@dataclass(frozen=True)
class UploadAuthorization:
    url: str
    headers: dict[str, str]
    expires_in: int


class ResumeStorage(Protocol):
    def authorize_upload(
        self, *, key: str, content_type: str, file_size: int, expires_in: int
    ) -> UploadAuthorization: ...

    def verify_upload(
        self, *, key: str, content_type: str, file_size: int
    ) -> None: ...

    def authorize_download(self, *, key: str, expires_in: int = 300) -> str: ...

    def read_document(self, *, key: str, max_bytes: int) -> bytes: ...


class S3ResumeStorage:
    def __init__(self, *, region, bucket, access_key_id, secret_access_key):
        # The factory rejects incomplete configuration before constructing a client.
        # Explicit credentials prevent implicit metadata-server credential discovery.
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4", connect_timeout=5, read_timeout=15, retries={"max_attempts": 2, "mode": "standard"}),
        )

    def authorize_upload(
        self, *, key: str, content_type: str, file_size: int, expires_in: int
    ) -> UploadAuthorization:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            url = self.client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                    "ContentType": content_type,
                    "ContentLength": file_size,
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable() from exc
        # No public ACL is sent. The bucket must have Block Public Access enabled;
        # omitting ACLs also supports S3's bucket-owner-enforced object ownership.
        # Content-Length is signed; browsers set it automatically from the file body.
        return UploadAuthorization(
            url=url, headers={"Content-Type": content_type}, expires_in=expires_in
        )

    def authorize_download(self, *, key: str, expires_in: int = 300):
        from botocore.exceptions import BotoCoreError, ClientError
        try:
            return self.client.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": key, "ResponseContentDisposition": "attachment"}, ExpiresIn=expires_in, HttpMethod="GET")
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable() from exc

    def read_document(self, *, key: str, max_bytes: int):
        from botocore.exceptions import BotoCoreError, ClientError
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            stream = response["Body"]
            try:
                if response.get("ContentLength", 0) > max_bytes:
                    raise StorageObjectMismatch()
                content = stream.read(max_bytes + 1)
                if len(content) > max_bytes:
                    raise StorageObjectMismatch()
                return content
            finally:
                stream.close()
        except (BotoCoreError, ClientError) as exc:
            raise StorageUnavailable() from exc

    def verify_upload(self, *, key: str, content_type: str, file_size: int) -> None:
        """Verify the private object uploaded by the browser matches its intent."""
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            metadata = self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise StorageObjectNotFound() from exc
            raise StorageUnavailable() from exc
        except BotoCoreError as exc:
            raise StorageUnavailable() from exc

        if (
            metadata.get("ContentLength") != file_size
            or metadata.get("ContentType") != content_type
        ):
            raise StorageObjectMismatch()


class StorageObjectNotFound(APIException):
    status_code = 409
    default_detail = "The resume upload could not be found."
    default_code = "resume_upload_not_found"


class StorageObjectMismatch(APIException):
    status_code = 409
    default_detail = "The uploaded resume does not match the requested file."
    default_code = "resume_upload_mismatch"


def get_resume_storage() -> ResumeStorage:
    config = {
        "region": settings.AWS_REGION,
        "bucket": settings.AWS_S3_BUCKET,
        "access_key_id": settings.AWS_ACCESS_KEY_ID,
        "secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }
    if any(not isinstance(value, str) or not value.strip() for value in config.values()):
        raise StorageNotConfigured()
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        return S3ResumeStorage(**config)
    except (BotoCoreError, ClientError) as exc:
        raise StorageUnavailable() from exc
