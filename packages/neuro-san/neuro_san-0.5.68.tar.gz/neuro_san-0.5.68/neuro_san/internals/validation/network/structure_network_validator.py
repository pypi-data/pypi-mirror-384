
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
from neuro_san.internals.validation.network.cycles_network_validator import CyclesNetworkValidator
from neuro_san.internals.validation.network.missing_nodes_network_validator import MissingNodesNetworkValidator
from neuro_san.internals.validation.network.unreachable_nodes_network_validator import UnreachableNodesNetworkValidator


class StructureNetworkValidator(CompositeDictionaryValidator):
    """
    Implementation of CompositeDictionaryValidator interface that uses multiple specific validators
    to do some standard validation for topological issues.
    This gets used by agent network designer.
    """

    def __init__(self):
        """
        Constructor
        """
        validators: List[DictionaryValidator] = [
            CyclesNetworkValidator(),
            MissingNodesNetworkValidator(),
            UnreachableNodesNetworkValidator(),
        ]
        super().__init__(validators)
