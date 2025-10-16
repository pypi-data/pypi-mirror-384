import os
from typing import Any

import boto3
import botocore.session
from botocore.config import Config
from botocore.credentials import RefreshableCredentials

from cloud_storage_clients.client import Client
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.exceptions import ObjectNotFoundError
from cloud_storage_clients.responses import (
    BucketFile,
    BucketFolder,
    BucketObjects,
    CompleteMultipartUploadResponse,
    CopyResponse,
    CreateMultipartUploadResponse,
    DeleteResponse,
    GetDownloadUrlResponse,
    GetPartUploadUrlResponse,
    GetResponse,
    GetUploadUrlResponse,
    HeadResponse,
    ListResponse,
    PutResponse,
)


class S3Client(Client):
    def __init__(
        self,
        connector: Connector,
        credentials: dict | None,
        default_region_name: str | None,
    ):
        super().__init__(connector, credentials)

        if not credentials:
            raise NotImplementedError()

        if "region_name" in credentials:
            region_name = credentials["region_name"]
        else:
            region_name = default_region_name

        if (
            "access_key_id" not in credentials
            and "secret_access_key" not in credentials
        ):
            botocore_session = botocore.session.get_session()
            self._session = boto3.Session(botocore_session=botocore_session)
            self._client = self._session.client(
                "s3",
                region_name=region_name,
                config=Config(signature_version="s3v4"),
            )

            # Set credentials refresh timeouts, impossible to set otherwise.
            # In the normal flow, the botocore.credentials.InstanceMetadataProvider
            # creates the RefreshableCredentials instance with default timeouts.
            # The credentials typically last for 6 hours, we try to refresh them
            # 3 hours before expiration.
            credentials: RefreshableCredentials = botocore_session.get_credentials()
            if credentials is None:
                raise ValueError("invalid S3 client credentials")
            assert isinstance(credentials, RefreshableCredentials)
            credentials._advisory_refresh_timeout = 3 * 60 * 60  # 3 hours
            credentials._mandatory_refresh_timeout = 2 * 60 * 60  # 2 hours
        else:
            if "endpoint_url" in credentials:
                endpoint_url = credentials["endpoint_url"]
            else:
                endpoint_url = f"https://s3.{region_name}.amazonaws.com"

            self._client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                region_name=region_name,
                aws_access_key_id=credentials.get("access_key_id", None),
                aws_secret_access_key=credentials.get("secret_access_key"),
                config=Config(signature_version="s3v4"),
            )

    def get(self, object_name: str) -> GetResponse:
        return GetResponse(
            content=self._client.get_object(Bucket=self.bucket, Key=object_name)[
                "Body"
            ].read()
        )

    def head(self, object_name: str) -> HeadResponse:
        metadata = self._client.head_object(Bucket=self.bucket, Key=object_name)
        if not metadata:
            raise ObjectNotFoundError()
        return HeadResponse(
            file_size=metadata["ContentLength"], content_type=metadata["ContentType"]
        )

    def put(self, object_name: str, data: Any) -> PutResponse:
        return PutResponse(
            info=self._client.put_object(Bucket=self.bucket, Key=object_name, Body=data)
        )

    def delete(self, object_name: str) -> DeleteResponse:
        return DeleteResponse(
            info=self._client.delete_object(Bucket=self.bucket, Key=object_name)
        )

    def copy(
        self, source_object_name: str, destination_object_name: str
    ) -> CopyResponse:
        copy_source = os.path.join(self.bucket, source_object_name)
        return CopyResponse(
            info=self._client.copy_object(
                Bucket=self.bucket,
                CopySource=copy_source,
                Key=destination_object_name,
            )
        )

    def list(self, prefix: str, delimiter: str) -> ListResponse:
        paginator = self._client.get_paginator("list_objects_v2")
        folders = []
        files = []
        for page in paginator.paginate(
            Bucket=self.bucket, Prefix=prefix, Delimiter=delimiter
        ):
            if "CommonPrefixes" in page:
                folders.extend(
                    [
                        BucketFolder(name=folder["name"])
                        for folder in page["CommonPrefixes"]
                    ]
                )
            if "Contents" in page:
                files.extend(
                    [
                        BucketFile(
                            name=file["Key"],
                            last_modified=file["LastModified"],
                            size=file["Size"],
                        )
                        for file in page["Contents"]
                    ]
                )
        return ListResponse(bucket_objects=BucketObjects(folders=folders, files=files))

    def get_download_url(
        self, object_name: str, expiration: int
    ) -> GetDownloadUrlResponse:
        return GetDownloadUrlResponse(
            url=self._client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_name,
                },
                ExpiresIn=expiration,
            )
        )

    def get_upload_url(
        self, object_name: str, file_type: str, expiration: int
    ) -> GetUploadUrlResponse:
        presigned_post = self._client.generate_presigned_post(
            Bucket=self.bucket,
            Key=object_name,
            Fields={"Content-Type": file_type},
            Conditions=[{"Content-Type": file_type}],
            ExpiresIn=expiration,
        )
        return GetUploadUrlResponse(
            url=presigned_post["url"],
            fields=presigned_post["fields"],
        )

    def create_multipart_upload(
        self, object_name: str
    ) -> CreateMultipartUploadResponse:
        response = self._client.create_multipart_upload(
            Bucket=self.bucket, Key=object_name
        )
        return CreateMultipartUploadResponse(upload_id=response["UploadId"])

    def get_part_upload_url(
        self, object_name: str, upload_id: str, part_number: int, expiration: int
    ) -> GetPartUploadUrlResponse:
        return GetPartUploadUrlResponse(
            url=self._client.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_name,
                    "UploadId": upload_id,
                    "PartNumber": part_number,
                },
                ExpiresIn=expiration,
            )
        )

    def complete_multipart_upload(
        self, object_name: str, upload_id: str, parts: Any
    ) -> CompleteMultipartUploadResponse:
        return CompleteMultipartUploadResponse(
            info=self._client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=object_name,
                MultipartUpload={"Parts": parts},
                UploadId=upload_id,
            )
        )

    def close(self):
        self._client.close()
