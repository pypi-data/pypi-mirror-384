"""
This module contains the basic functionality for downloading from sftp
"""

import logging
import os
import typing as tp
from abc import ABC, abstractmethod

from paramiko import AutoAddPolicy, SSHClient

LOGGER = logging.getLogger(__name__)


class ConfigurationError(Exception):
    pass


class VersionHandlerMissing(Exception):
    pass


class Client(ABC):
    """
    Abstract base class to be used as a template for downloading clients
    E.g. FTP, HTTP
    """

    def __init__(
        self,
        config: tp.Dict,
        logger: logging.Logger = LOGGER,
    ):
        self.config = config
        self.logger = logger

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def download_all_files(self, target_version: str, local_directory: str) -> None:
        """
        Download all files defined in the configuration.

        :param target_version: the version related to all the files we want to download
        :param local_directory: the local storage path
        """

    @abstractmethod
    def download_one_file(self, target_file: str, local_directory: str) -> None:
        """
        Download one file that corresponds to the given filename.

        :param target_file: the file name for the file we want to download
        :param local_directory: the local storage path
        """


class SFTPClient(Client):
    """The class for an SFTP client using paramiko"""

    def __init__(
        self,
        config: tp.Dict,
        logger: logging.Logger = LOGGER,
    ):
        super().__init__(config, logger)
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())

        if "username" not in config or "password" not in config:
            raise ConfigurationError(
                "Username or password not specified in configuration."
            )

        self.client.connect(
            config["url"], username=config["username"], password=config["password"]
        )
        self.sftp = self.client.open_sftp()
        self.sftp.chdir(config.get("remote_directory", "."))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sftp.close()
        self.client.close()

    def get_all_file_names(self) -> tp.List[str]:
        """List all files in the current directory on the SFTP server"""
        return self.sftp.listdir()

    def download_one_file(self, target_file: str, local_directory: str = ".") -> None:
        """
        Download one file from the SFTP server.
        """
        self.logger.info(f"Downloading {target_file}...")
        local_filepath = os.path.join(local_directory, target_file)
        self.sftp.get(target_file, str(local_filepath))

    def download_all_files(self, target_version: str, local_directory: str) -> None:
        """
        Download all files that match the target version from the SFTP server.
        """
        all_files = self.get_all_file_names()
        for file_name in all_files:
            if target_version in file_name:
                self.download_one_file(file_name, local_directory)
