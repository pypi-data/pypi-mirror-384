from dataclasses import dataclass
from datetime import datetime


@dataclass
class GetResponse:
    content: bytes


@dataclass
class HeadResponse:
    file_size: int
    content_type: str | None


@dataclass
class PutResponse:
    info: dict | None


@dataclass
class DeleteResponse:
    info: dict | None


@dataclass
class CopyResponse:
    info: dict | None


@dataclass
class BucketFolder:
    name: str


@dataclass
class BucketFile:
    name: str
    last_modified: datetime
    size: int


@dataclass
class BucketObjects:
    folders: list[BucketFolder]
    files: list[BucketFile]


@dataclass
class ListResponse:
    bucket_objects: BucketObjects


@dataclass
class GetDownloadUrlResponse:
    url: str


@dataclass
class GetUploadUrlResponse:
    url: str
    fields: dict


@dataclass
class CreateMultipartUploadResponse:
    upload_id: str


@dataclass
class GetPartUploadUrlResponse:
    url: str


@dataclass
class CompleteMultipartUploadResponse:
    info: dict | None
