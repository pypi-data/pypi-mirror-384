import abc
import logging
from threading import Lock

from cloud_storage_clients.client import Client
from cloud_storage_clients.connector import Connector


class ClientCache:
    @abc.abstractmethod
    def get(self, key: Connector) -> Client | None:
        pass

    @abc.abstractmethod
    def set(self, key: Connector, value: Client, timeout: int = None):
        pass

    @abc.abstractmethod
    def delete(self, key: Connector):
        pass

    @abc.abstractmethod
    def clear(self):
        pass


class DictCache(ClientCache):
    clients: dict[str, Client]

    def __init__(self) -> None:
        self.clients = {}
        self.lock = Lock()

    def get_cache_key(self, connector: Connector):
        return connector.key

    def get(self, connector: Connector) -> Client | None:
        with self.lock:
            cache_key = self.get_cache_key(connector)
            if cache_key in self.clients:
                return self.clients[cache_key]

            return None

    def set(self, connector: Connector, client: Client, timeout: int = None):
        with self.lock:
            cache_key = self.get_cache_key(connector)
            self.clients[cache_key] = client

    def delete(self, connector: Connector):
        with self.lock:
            cache_key = self.get_cache_key(connector)
            if cache_key in self.clients:
                try:
                    self.clients[cache_key].close()
                except Exception:
                    logging.exception(
                        f"Could not close client from connector {cache_key}"
                    )
                del self.clients[cache_key]

    def clear(self):
        with self.lock:
            for key, client in self.clients.items():
                try:
                    client.close()
                except Exception:
                    logging.exception(f"Could not close client from connector {key}")

            self.clients.clear()


class DisabledCache(ClientCache):
    def get(self, connector: Connector) -> Client | None:
        return None

    def set(self, connector: Connector, client: Client, timeout: int = None):
        pass

    def delete(self, connector: Connector):
        pass

    def clear(self):
        pass
