
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from typing import Any
from typing import Dict

from logging import getLogger
from logging import Logger

from leaf_common.config.config_filter import ConfigFilter


class ServedManifestConfigFilter(ConfigFilter):
    """
    Implementation of the ConfigFilter interface that reads the contents
    of a single manifest file for agent networks/registries, removing any entries
    that are not supposed to be served.
    """

    def __init__(self, manifest_file: str):
        """
        Constructor

        :param manifest_file: The name of the manifest file we are processing for logging purposes
        """
        self.logger: Logger = getLogger(self.__class__.__name__)
        self.manifest_file: str = manifest_file

    def filter_config(self, basis_config: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Filters the given basis config.

        :param basis_config: The config dictionary to act as the basis
                for filtering
        :return: A config dictionary, potentially modified as per the
                policy encapsulated by the implementation
        """

        filtered: Dict[str, Dict[str, Any]] = {}

        for key, value in basis_config.items():

            if not value.get("serve", False):
                self.logger.warning("Manifest entry for %s in file %s will not be served, " +
                                    "per the 'serve' key in its config (default is False). Skipping.",
                                    key, self.manifest_file)
                continue

            filtered[key] = value

        return filtered
