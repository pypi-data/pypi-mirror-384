class StorageProviders(Exception):
    pass


class RepositoryError(StorageProviders):
    pass


class ConfigurationError(StorageProviders):
    pass


class ObjectNotFoundError(StorageProviders):
    pass


class FactoryNotFoundError(StorageProviders):
    pass
