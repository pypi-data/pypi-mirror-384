import boto3

"""Simple wrapper around boto3 S3 client."""

from botocore.client import BaseClient
from botocore.exceptions import ClientError, NoCredentialsError

from ..core.exception import RequestException

__all__ = ("Bucket",)


class Bucket:
    """High level interface for reading/writing files to S3 compatible
    storage."""

    def __init__(
        self,
        name: str | None = None,
        s3_mode: str | None = None,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str | None = None,
    ) -> None:
        self.__name = name
        self.__s3_mode = bool(s3_mode)
        self.__endpoint_url = endpoint_url
        self.__access_key = access_key
        self.__secret_key = secret_key
        self.__region_name = region_name
        self.__s3_client: BaseClient = boto3.client(
            service_name="s3",
            aws_access_key_id=self.__access_key,
            aws_secret_access_key=self.__secret_key,
            endpoint_url=self.__endpoint_url if not self.__s3_mode else None,
            region_name=self.__region_name if self.__s3_mode else None,
        )

    def url_generator(self, key: str) -> str:
        """Return the public URL for ``key`` in this bucket."""

        if self.__s3_mode:
            return f"{self.__endpoint_url}/{key}"
        else:
            return f"{self.__endpoint_url}/{self.__name}/{key}"

    def get_s3(self) -> BaseClient:
        """Return the underlying boto3 client."""

        return self.__s3_client

    def get_bucket_name(self) -> str | None:
        """Return the configured bucket name."""

        return self.__name

    def check_file_exists(self, key: str):
        """Check if ``key`` exists in the bucket."""
        controller = f"{__name__}.Bucket.check_file_exists"
        try:
            self.__s3_client.head_object(Bucket=self.__name, Key=key)
            return True
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        except:
            return False

    def upload(
        self, file: bytes, key: str, content_type: str, cache_control: str = "no-cache"
    ):
        """Upload bytes content to ``key``."""
        controller = f"{__name__}.Bucket.upload"
        try:
            self.__s3_client.put_object(
                Body=file,
                Bucket=self.__name,
                Key=key,
                ContentType=content_type,
                CacheControl=cache_control,
            )
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        return self.url_generator(key=key)

    def download(self, key: str, filepath: str) -> bool:
        """Download ``key`` to ``filepath``."""
        controller = f"{__name__}.Bucket.download"
        try:
            self.__s3_client.download_file(
                Bucket=self.__name,
                Key=key,
                Filename=filepath,
            )
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        return True

    def download_fileobj(self, key: str, file) -> bool:
        """Download ``key`` into an open file object."""
        controller = f"{__name__}.Bucket.download_fileobj"
        try:
            self.__s3_client.download_fileobj(
                Bucket=self.__name,
                Key=key,
                Fileobj=file,
            )
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        return True

    def upload_by_path(
        self,
        file_path: str,
        key: str,
        content_type: str | None = None,
        cache_control: str = "no-cache",
    ):
        """Upload the contents of ``file_path`` to ``key``."""
        controller = f"{__name__}.Bucket.upload_by_path"
        try:
            with open(file_path, "rb") as file:
                file_content = file.read()
                content_type = content_type or "application/octet-stream"
                return self.upload(
                    file=file_content,
                    key=key,
                    content_type=content_type,
                    cache_control=cache_control,
                )
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )

    def duplicate(
        self, source_key: str, destination_key: str, cache_control: str = "no-cache"
    ) -> str:
        """Duplicate an object within the bucket."""
        controller = f"{__name__}.Bucket.duplicate"
        try:
            self.__s3_client.copy(
                CopySource={"Bucket": self.__name, "Key": source_key},
                Bucket=self.__name,
                Key=destination_key,
                ExtraArgs={"CacheControl": cache_control},
            )
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        return self.url_generator(key=destination_key)

    def safe_duplicate(self, source_key: str, cache_control: str = "no-cache"):
        """Duplicate ``source_key`` avoiding name collisions."""
        controller = f"{__name__}.Bucket.safe_duplicate"
        try:
            default_key = source_key
            key = default_key
            i = 2
            while self.check_file_exists(key):
                name, ext = default_key.rsplit(".", 1)
                key = f"{name}-{i}.{ext}"
                i += 1
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )

        return self.duplicate(
            source_key=source_key, destination_key=key, cache_control=cache_control
        )

    def delete(self, key: str) -> bool:
        """Delete ``key`` from the bucket if it exists."""
        controller = f"{__name__}.Bucket.delete"
        try:
            self.__s3_client.delete_object(Bucket=self.__name, Key=key)
            return True
        except NoCredentialsError:
            raise RequestException(
                controller=controller,
                message="S3 credentials error",
                status_code=500,
            )
        except ClientError:
            return True
