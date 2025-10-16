from datetime import datetime, timedelta
from typing import Any

from azure.identity import ClientSecretCredential
from azure.storage.blob import (
    BlobClient,
    BlobPrefix,
    BlobSasPermissions,
    BlobServiceClient,
    UserDelegationKey,
    generate_blob_sas,
)

from cloud_storage_clients.client import Client
from cloud_storage_clients.connector import Connector
from cloud_storage_clients.exceptions import ConfigurationError
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


class AzureClient(Client):
    def __init__(
        self,
        connector: Connector,
        credentials: dict | None,
        delegation_key_expiration_time: int,
    ):
        super().__init__(connector, credentials)
        self.delegation_key_expiration_time = delegation_key_expiration_time

        if not credentials:
            raise NotImplementedError()

        if credentials:
            try:
                account_url = credentials["account_url"]
                azure_tenant_id = credentials["azure_tenant_id"]
                azure_client_id = credentials["azure_client_id"]
                azure_client_secret = credentials["azure_client_secret"]
            except KeyError as e:
                raise ConfigurationError() from e

            self._client = BlobServiceClient(
                account_url=account_url,
                credential=ClientSecretCredential(
                    tenant_id=azure_tenant_id,
                    client_id=azure_client_id,
                    client_secret=azure_client_secret,
                ),
            )

    def generate_user_delegation_key(self) -> UserDelegationKey:
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(
            seconds=self.delegation_key_expiration_time
        )
        return self._client.get_user_delegation_key(
            key_start_time=start_time, key_expiry_time=expiry_time
        )

    def _get_blob_client(self, object_name: str) -> BlobClient:
        return self._client.get_blob_client(container=self.bucket, blob=object_name)

    def get(self, object_name: str) -> GetResponse:
        blob_client = self._get_blob_client(object_name)
        return GetResponse(content=blob_client.download_blob().read())

    def head(self, object_name: str) -> HeadResponse:
        blob_client = self._get_blob_client(object_name)
        blob = blob_client.get_blob_properties()
        return HeadResponse(
            file_size=blob.size, content_type=blob.content_settings.content_type
        )

    def put(self, object_name: str, data: Any) -> PutResponse:
        blob_client = self._get_blob_client(object_name)
        return PutResponse(
            info=blob_client.upload_blob(data, blob_type="BlockBlob", overwrite=True)
        )

    def delete(self, object_name: str) -> DeleteResponse:
        return DeleteResponse(
            info=self._get_blob_client(object_name).delete_blob(
                delete_snapshots="include"
            )
        )

    def copy(self, source_object_name: str, destination_object_name: str):
        destination_blob = self._client.get_blob_client(
            container=self.bucket, blob=destination_object_name
        )
        source_url = self.get_download_url(
            object_name=source_object_name, expiration=3600
        ).url
        return CopyResponse(info=destination_blob.start_copy_from_url(source_url))

    def list(self, prefix: str, delimiter: str) -> ListResponse:
        folders = []
        files = []
        for blob in self._client.get_container_client(self.bucket).walk_blobs(
            name_starts_with=prefix, delimiter=delimiter
        ):
            if isinstance(blob, BlobPrefix):
                folders.append(BucketFolder(name=blob.name))
            else:
                files.append(
                    BucketFile(
                        name=blob.name, last_modified=blob.creation_time, size=blob.size
                    )
                )

        return ListResponse(bucket_objects=BucketObjects(folders=folders, files=files))

    def _generate_sas_url(self, object_name, expiration, permission) -> str:
        user_delegation_key = self.generate_user_delegation_key()
        blob_client = self._client.get_blob_client(
            container=self.bucket, blob=object_name
        )
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(seconds=expiration)
        sas_token = generate_blob_sas(
            account_name=blob_client.account_name,
            container_name=self.bucket,
            blob_name=object_name,
            user_delegation_key=user_delegation_key,
            permission=permission,
            expiry=expiry_time,
            start=start_time,
        )
        return f"{blob_client.url}?{sas_token}"

    def get_download_url(
        self, object_name: str, expiration: int
    ) -> GetDownloadUrlResponse:
        return GetDownloadUrlResponse(
            url=self._generate_sas_url(
                object_name, expiration, BlobSasPermissions(read=True)
            )
        )

    def get_upload_url(
        self, object_name: str, file_type: str, expiration: int
    ) -> GetUploadUrlResponse:
        url = self._generate_sas_url(
            object_name,
            expiration,
            BlobSasPermissions(write=True, read=True, add=True, create=True),
        )
        return GetUploadUrlResponse(url=url, fields={"Content-Type": file_type})

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
