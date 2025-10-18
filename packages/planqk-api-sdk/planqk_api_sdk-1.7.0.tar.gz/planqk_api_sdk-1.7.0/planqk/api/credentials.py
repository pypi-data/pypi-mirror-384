import json
import os
import platform
from abc import ABC, abstractmethod
from json import JSONDecodeError

_PERSONAL_ACCESS_TOKEN = "KQH_PERSONAL_ACCESS_TOKEN"
_CONFIG_FILE_PATH = "KQH_CONFIG_FILE_PATH"


class CredentialUnavailableError(Exception):
    """
    Exception raised when credentials are unavailable for authentication.
    """

    def __init__(self, message=None):
        if message is None:
            message = "Credentials not found. Please set your personal access token as parameter, in the environment, or use 'planqk login' to authenticate."
        super().__init__(message)


class CredentialProvider(ABC):

    @abstractmethod
    def get_access_token(self) -> str:
        pass


class EnvironmentCredential(CredentialProvider):

    def get_access_token(self) -> str:
        access_token = os.environ.get(_PERSONAL_ACCESS_TOKEN)

        if not access_token:
            raise CredentialUnavailableError(f"Environment variable {_PERSONAL_ACCESS_TOKEN} is not set")

        return access_token


def get_config_file_path():
    config_file_path = os.environ.get(_CONFIG_FILE_PATH, None)
    if not config_file_path:
        if platform.system() == "Windows":
            config_dir = os.path.join(os.getenv("LOCALAPPDATA"), "planqk")
        else:
            config_dir = os.path.join(os.path.expanduser("~"), ".config", "planqk")
        config_file_path = os.path.join(config_dir, "config.json")
    return config_file_path


class ConfigFileCredential(CredentialProvider):
    def __init__(self):
        self.config_file = get_config_file_path()

    def get_access_token(self) -> str:
        if not self.config_file:
            raise CredentialUnavailableError("Config file location not set")
        if not os.path.isfile(self.config_file):
            raise CredentialUnavailableError(f"Config file at {self.config_file} does not exist")
        try:
            access_token = ConfigFileCredential.parse_file(self.config_file)
        except JSONDecodeError:
            raise CredentialUnavailableError("Failed to parse config file: Invalid JSON")
        except KeyError as e:
            raise CredentialUnavailableError(f"Failed to parse config file: Missing expected value - {str(e)}")
        except Exception as e:
            raise CredentialUnavailableError(f"Failed to parse config file: {str(e)}")
        return access_token

    @staticmethod
    def parse_file(path) -> str:
        with open(path, "r") as file:
            data = json.load(file)
            return data["auth"]["value"]


class StaticCredential(CredentialProvider):
    def __init__(self, access_token=None):
        self.access_token = access_token

    def get_access_token(self) -> str:
        if not self.access_token:
            raise CredentialUnavailableError("Access token not set")
        return self.access_token


class DefaultCredentialsProvider(CredentialProvider):
    def __init__(self, access_token=None):
        self.credentials = [
            StaticCredential(access_token),
            EnvironmentCredential(),
            ConfigFileCredential(),
        ]

    def get_access_token(self) -> str:
        for credential in self.credentials:
            try:
                return credential.get_access_token()
            except CredentialUnavailableError:
                # ignore and try the next credential provider
                pass

        raise CredentialUnavailableError()
