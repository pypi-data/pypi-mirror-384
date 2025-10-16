import abc
from abc import abstractmethod
from typing import Any

from cloud_storage_clients.connector import Connector
from cloud_storage_clients.responses import (
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


class Client(abc.ABC):
    def __init__(self, connector: Connector, credentials: dict | None):
        self.connector = connector
        self.bucket = connector.bucket
        self.is_authenticated = credentials is not None

    @abstractmethod
    def get(self, object_name: str) -> GetResponse:
        pass

    @abstractmethod
    def head(self, object_name: str) -> HeadResponse:
        pass

    @abstractmethod
    def put(self, object_name: str, data: Any) -> PutResponse:
        pass

    @abstractmethod
    def delete(self, object_name: str) -> DeleteResponse:
        pass

    @abstractmethod
    def copy(
        self, source_object_name: str, destination_object_name: str
    ) -> CopyResponse:
        pass

    @abstractmethod
    def list(self, prefix: str, delimiter: str) -> ListResponse:
        pass

    @abstractmethod
    def get_download_url(
        self, object_name: str, expiration: int
    ) -> GetDownloadUrlResponse:
        pass

    @abstractmethod
    def get_upload_url(
        self, object_name: str, file_type: str, expiration: int
    ) -> GetUploadUrlResponse:
        pass

    @abstractmethod
    def create_multipart_upload(
        self, object_name: str
    ) -> CreateMultipartUploadResponse:
        pass

    @abstractmethod
    def get_part_upload_url(
        self, object_name: str, upload_id: str, part_number: int, expiration: int
    ) -> GetPartUploadUrlResponse:
        pass

    @abstractmethod
    def complete_multipart_upload(
        self, object_name: str, upload_id: str, parts: Any
    ) -> CompleteMultipartUploadResponse:
        pass

    @abstractmethod
    def close(self):
        pass
