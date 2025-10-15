
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

import json
import logging

from json.decoder import JSONDecodeError
from pyparsing.exceptions import ParseException
from pyparsing.exceptions import ParseSyntaxException

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.interface.restorer import Restorer


class RawManifestRestorer(Restorer):
    """
    Implementation of the Restorer interface that reads the contents
    of a single manifest file for agent networks/registries.
    """

    def __init__(self):
        """
        Constructor
        """
        self.logger = logging.getLogger(self.__class__.__name__)

    def restore(self, file_reference: str = None) -> Dict[str, Any]:
        """
        :param file_reference: The file reference to use when restoring.
                Default is None, implying the file reference is up to the
                implementation.
        :return: a built map of agent networks
        """

        one_manifest: Dict[str, Any] = {}

        if file_reference.endswith(".hocon"):
            hocon = EasyHoconPersistence()
            try:
                one_manifest = hocon.restore(file_reference=file_reference)
            except (ParseException, ParseSyntaxException) as exception:
                message: str = f"""
There was an error parsing the agent network manifest file "{file_reference}".
See the accompanying ParseException (above) for clues as to what might be
syntactically incorrect in that file.
"""
                raise ParseException(message) from exception
        else:
            try:
                with open(file_reference, "r", encoding="utf-8") as json_file:
                    one_manifest = json.load(json_file)
            except FileNotFoundError:
                # Use the common verbiage below
                one_manifest = None
            except JSONDecodeError as exception:
                message: str = f"""
There was an error parsing the agent network manifest file "{file_reference}".
See the accompanying JSONDecodeError exception (above) for clues as to what might be
syntactically incorrect in that file.
"""
                raise ParseException(message) from exception

        if one_manifest is None:
            message = f"Could not find manifest file at path: {file_reference}.\n" + """
Some common problems include:
* The file itself simply does not exist.
* Path is not an absolute path and you are invoking the server from a place
  where the path is not reachable.
* The path has a typo in it.

Double-check the value of the AGENT_MANIFEST_FILE env var and
your current working directory (pwd).
"""
            raise FileNotFoundError(message)

        return one_manifest
