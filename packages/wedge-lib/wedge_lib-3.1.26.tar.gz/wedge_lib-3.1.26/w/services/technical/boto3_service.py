import logging
from io import BytesIO
from pathlib import Path
from typing import Union

import boto3
from boto3 import Session
from botocore.exceptions import ClientError
from django.conf import settings

from w.services.abstract_service import AbstractService

# disable boto3 logging
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("botocore").setLevel(logging.ERROR)


class Boto3Service(AbstractService):
    _s3_resource: Session.resource = None
    _s3_client: Session.client = None
    _bucket_name = None
    _prefix_path = None

    @classmethod
    def init(cls):
        for key in [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_STORAGE_BUCKET_NAME",
        ]:
            if not hasattr(settings, key) or not getattr(settings, key):
                raise RuntimeError(f"Please set {key} in your settings")

        credentials = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_S3_REGION_NAME,
        }
        if getattr(settings, "AWS_S3_ENDPOINT_URL", None):
            credentials["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
        cls._s3_resource = Boto3Service._get_ressource(credentials)
        cls._s3_client = Boto3Service._get_client(credentials)
        cls._prefix_path = settings.AWS_BUCKET_PREFIX
        cls._bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    @classmethod
    def _get_client(cls, credentials):  # pragma: no cover (todo one day)
        return boto3.client("s3", **credentials)

    @classmethod
    def _get_ressource(cls, credentials):  # pragma: no cover (todo one day)
        return boto3.resource("s3", **credentials)

    @classmethod
    def create_bucket_if_not_exist(cls):
        cls._check_is_init()
        if cls.is_bucket_exists():  # pragma: no cover (todo one day)
            return None
        cls._s3_client.create_bucket(Bucket=cls._bucket_name)

    @classmethod
    def _check_is_init(cls):
        """
        Check if service is initialized and raise RuntimeError if not
        """
        if cls._s3_resource is None or cls._s3_client is None:
            raise RuntimeError("Boto3Service not initialized")

    @classmethod
    def is_bucket_exists(cls):
        cls._check_is_init()
        try:
            cls._s3_resource.meta.client.head_bucket(Bucket=cls._bucket_name)
            return True
        except ClientError:
            return False

    @classmethod
    def clear(cls):
        cls._s3_resource = None
        cls._s3_client = None
        cls._prefix_path = ""

    @classmethod
    def delete_bucket(cls):
        cls._check_is_init()
        if cls.is_bucket_exists():
            cls._s3_resource.Bucket(cls._bucket_name).delete()

    @classmethod
    def reset_bucket(cls):
        cls._check_is_init()
        if cls.is_bucket_exists() is False:
            return None
        bucket = cls._s3_resource.Bucket(cls._bucket_name)
        bucket.objects.all().delete()

    @classmethod
    def upload(cls, file: BytesIO, destination_path: Union[str, Path]):
        cls._check_is_init()
        if isinstance(destination_path, Path):  # pragma: no cover (todo one day)
            destination_path = str(destination_path)
        s3_path = destination_path

        s3_path = cls.get_s3_path(s3_path)
        cls._s3_client.upload_fileobj(file, cls._bucket_name, s3_path)

    @classmethod
    def get_s3_path(cls, file_path: Union[str, Path]):
        if isinstance(file_path, Path):  # pragma: no cover (todo one day)
            file_path = str(file_path)
        return (
            f"{cls._prefix_path}/{file_path}"
            if cls._prefix_path and not file_path.startswith(cls._prefix_path)
            else file_path
        )

    @classmethod
    def is_bucket_empty(cls):
        cls._check_is_init()

        bucket = cls._s3_resource.Bucket(cls._bucket_name)
        objects = list(bucket.objects.all())
        return not objects

    @classmethod
    def is_file_exists(cls, file_path: str):
        cls._check_is_init()

        try:
            cls.get_object(file_path)
            return True
        except cls._s3_client.exceptions.NoSuchKey:
            return False

    @classmethod
    def get_object(cls, file_path: str) -> dict:
        s3_path = cls.get_s3_path(file_path)
        return cls._s3_client.get_object(Bucket=cls._bucket_name, Key=s3_path)

    @classmethod
    def generate_signed_url(cls, file_path):
        cls._check_is_init()

        s3_path = cls.get_s3_path(file_path)
        return cls._s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": cls._bucket_name, "Key": s3_path},
        )
