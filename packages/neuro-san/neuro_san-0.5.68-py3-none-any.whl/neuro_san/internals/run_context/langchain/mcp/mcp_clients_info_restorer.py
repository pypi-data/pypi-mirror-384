
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

import os
from typing import Any, Dict

import json
from pyparsing.exceptions import ParseException
from pyparsing.exceptions import ParseSyntaxException

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.interface.restorer import Restorer


class McpClientsInfoRestorer(Restorer):
    """
    Implementation of the Restorer interface that reads the MCP clients info file.
    NOTE: This class is highly experimental and implementation of MCP clients
    is very likely to change in future releases.
    """

    def restore(self, file_reference: str = None) -> Dict[str, Any]:
        """
        :param file_reference: The file reference to use when restoring.
                Default is None, implying the file reference is up to the
                implementation.
        :return: a dictionary with MCP clients information
        """
        file_path: str = file_reference
        if not file_path:
            file_path = os.environ.get("MCP_CLIENTS_INFO_FILE")
            if not file_path:
                # No clients info file specified.
                return None

        clients_info: Dict[str, Any] = None
        if file_path.endswith(".hocon"):
            hocon = EasyHoconPersistence()
            try:
                clients_info = hocon.restore(file_reference=file_path)
            except (ParseException, ParseSyntaxException) as exception:
                message: str = f"""
        There was an error parsing MCP clients info file "{file_path}".
        See the accompanying ParseException (above) for clues as to what might be
        syntactically incorrect in that file.
        """
                raise ParseException(message) from exception
        else:
            try:
                with open(file_path, "r", encoding="utf-8") as json_file:
                    clients_info = json.load(json_file)
            except FileNotFoundError:
                # Use the common verbiage below
                clients_info = None
            except json.decoder.JSONDecodeError as exception:
                message: str = f"""
        There was an error parsing MCP clients info file "{file_path}".
        See the accompanying JSONDecodeError exception (above) for clues as to what might be
        syntactically incorrect in that file.
        """
                raise ParseException(message) from exception
        if clients_info is None:
            message = f"Could not find MCP clients info file at path: {file_path}.\n" + """
            Some common problems include:
            * The file itself simply does not exist.
            * Path is not an absolute path and you are invoking the server from a place
              where the path is not reachable.
            * The path has a typo in it.

            Double-check the value of the MCP_CLIENTS_INFO_FILE env var and
            your current working directory (pwd).
            """
            raise FileNotFoundError(message)
        # Now, MCP endpoints urls could put in quotes, so strip them out.
        result_dict: Dict[str, Any] = {}
        for key, value in clients_info.items():
            use_key: str = key.replace(r'"', "")
            use_key = use_key.strip()
            result_dict[use_key] = value
        return result_dict
