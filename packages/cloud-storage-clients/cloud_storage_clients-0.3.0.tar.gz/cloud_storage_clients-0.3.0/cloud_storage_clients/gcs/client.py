from datetime import datetime, timedelta
from typing import Any

from google.cloud import storage
from google.cloud.storage import Blob
from google.oauth2 import service_account

from cloud_storage_clients.client import Client
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.exceptions import ConfigurationError, ObjectNotFoundError
from cloud_storage_clients.gcs.signer import GoogleSigner
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


class GcsClient(Client):
    def __init__(self, connector: Connector, credentials: dict | None):
        super().__init__(connector, credentials)

        if not credentials:
            raise NotImplementedError()

        try:
            private_key = credentials["private_key"]
            self._client_email = credentials["client_email"]
        except KeyError as e:
            raise ConfigurationError() from e

        account_info = {
            "type": "service_account",
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": self._client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        self._google_credentials = (
            service_account.Credentials.from_service_account_info(account_info)
        )
        self._client = storage.Client(project="", credentials=self._google_credentials)
        self.google_bucket = self._client.get_bucket(self.bucket)

    def _get_blob(self, object_name) -> Blob:
        return self.google_bucket.get_blob(object_name)

    def get(self, object_name: str) -> GetResponse:
        blob = self._get_blob(object_name)
        if not blob:
            raise ObjectNotFoundError(f"Object {object_name} not found")
        return GetResponse(content=blob.download_as_bytes())

    def head(self, object_name: str) -> HeadResponse:
        blob = self._get_blob(object_name)
        if not blob:
            raise ObjectNotFoundError(f"Object {object_name} not found")
        return HeadResponse(file_size=blob.size, content_type=blob.content_type)

    def put(self, object_name: str, data: Any) -> PutResponse:
        blob = self.google_bucket.blob(object_name)
        blob.upload_from_file(data)
        return PutResponse(info={"name": blob.name, "size": blob.size})

    def delete(self, object_name: str) -> DeleteResponse:
        blob = self._get_blob(object_name)
        if not blob:
            raise ObjectNotFoundError(f"Object {object_name} not found")
        return DeleteResponse(info=blob.delete())

    def copy(
        self, source_object_name: str, destination_object_name: str
    ) -> CopyResponse:
        source_blob = self._get_blob(source_object_name)
        if not source_blob:
            raise ObjectNotFoundError(f"Object {source_object_name} not found")
        return self.google_bucket.copy_blob(
            source_blob, self.google_bucket, new_name=destination_object_name
        )

    def list(self, prefix: str, delimiter: str) -> ListResponse:
        blobs = self.google_bucket.list_blobs(prefix=prefix, delimiter=delimiter)
        files = [
            BucketFile(name=blob.name, last_modified=blob.updated, size=blob.size)
            for blob in blobs
            if not blob.name.endswith("/")
        ]
        folders = [BucketFolder(name=prefix) for prefix in blobs.prefixes]
        return ListResponse(bucket_objects=BucketObjects(folders=folders, files=files))

    def get_download_url(
        self, object_name: str, expiration: int
    ) -> GetDownloadUrlResponse:
        signed_url = GoogleSigner.generate_signed_url(
            self._google_credentials, self.bucket, object_name, expiration=expiration
        )
        return GetDownloadUrlResponse(url=signed_url)

    def get_upload_url(
        self, object_name: str, file_type: str, expiration: int
    ) -> GetUploadUrlResponse:
        expiration_date = datetime.utcnow() + timedelta(seconds=expiration)
        presigned_post = self._client.generate_signed_post_policy_v4(
            bucket_name=self.bucket,
            blob_name=object_name,
            fields={"Content-Type": file_type},
            conditions=[{"Content-Type": file_type}],
            expiration=expiration_date,
        )
        return GetUploadUrlResponse(
            url=presigned_post["url"],
            fields=presigned_post["fields"],
        )

    def create_multipart_upload(
        self, object_name: str
    ) -> CreateMultipartUploadResponse:
        raise NotImplementedError()

    def get_part_upload_url(
        self, object_name: str, upload_id: str, part_number: int, expiration: int
    ) -> GetPartUploadUrlResponse:
        raise NotImplementedError()

    def complete_multipart_upload(
        self, object_name: str, upload_id: str, parts: Any
    ) -> CompleteMultipartUploadResponse:
        raise NotImplementedError()

    def close(self):
        self._client.close()
