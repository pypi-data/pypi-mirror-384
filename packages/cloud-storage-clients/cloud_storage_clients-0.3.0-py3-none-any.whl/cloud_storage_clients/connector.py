from dataclasses import dataclass


@dataclass
class Connector:
    client_type: str
    bucket: str
    id: str | None = None

    @property
    def key(self):
        if self.id:
            return self.id
        else:
            return f"{self.client_type}/{self.bucket}"
