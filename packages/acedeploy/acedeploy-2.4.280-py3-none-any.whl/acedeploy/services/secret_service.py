import abc
import os
from enum import Enum


class SecretService(abc.ABC):
    """
    Base class for all secret retrieval services
    """

    @abc.abstractmethod
    def get_secret(self, secret_name: str):
        pass


class SecretServiceType(Enum):
    """
    The type of secret service to use
    """

    ENVIRONMENT = "ENVIRONMENT"


class EnvironmentSecretService(SecretService):
    """
    Retrieves secrets from environment variables
    """

    key_map: dict = {}

    def __init__(self, key_map: dict = None):
        """
            Inits a new environment secret service
        Args:
            key_map: dict - optional dictionary that maps secret keys to environment variables
        """
        self.key_map = {} if key_map is None else key_map

    def get_secret(self, secret_name: str):
        """
            Retrieves the environment variable by name
            First tries to lookup key in key mapping
            secret_name is case-sensitive
        Args:
            secret_name: str - the name of the secret to retrieve
        """
        key = self.key_map[secret_name] if secret_name in self.key_map else secret_name
        secret_value = os.getenv(key)

        if secret_value is None:
            raise ValueError(f"Environment variable {secret_name} not found")

        return secret_value
