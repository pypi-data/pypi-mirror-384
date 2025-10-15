
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
from typing import List

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator
from neuro_san.internals.validation.common.composite_dictionary_validator import CompositeDictionaryValidator
from neuro_san.internals.validation.network.keyword_network_validator import KeywordNetworkValidator
from neuro_san.internals.validation.network.missing_nodes_network_validator import MissingNodesNetworkValidator
from neuro_san.internals.validation.network.tool_name_network_validator import ToolNameNetworkValidator
from neuro_san.internals.validation.network.unreachable_nodes_network_validator import UnreachableNodesNetworkValidator
from neuro_san.internals.validation.network.url_network_validator import UrlNetworkValidator


class ManifestNetworkValidator(CompositeDictionaryValidator):
    """
    Implementation of CompositeDictionaryValidator interface that uses multiple specific validators
    to do some standard validation upon reading in an agent network description.
    """

    def __init__(self, external_network_names: List[str] = None, mcp_servers: List[str] = None):
        """
        Constructor

        :param external_network_names: A list of external network names
        :param mcp_servers: A list of MCP servers, as read in from a mcp_info.hocon file
        """
        validators: List[DictionaryValidator] = [
            # Note we do use the CyclesNetworkValidator here because cycles are actually OK.
            KeywordNetworkValidator(),
            MissingNodesNetworkValidator(),
            UnreachableNodesNetworkValidator(),
            # No ToolBoxNetworkValidator yet.
            ToolNameNetworkValidator(),
            UrlNetworkValidator(external_network_names, mcp_servers),
        ]
        super().__init__(validators)
