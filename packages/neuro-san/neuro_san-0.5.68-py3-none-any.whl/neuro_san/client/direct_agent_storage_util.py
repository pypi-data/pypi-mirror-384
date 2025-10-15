
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
from typing import Dict

from neuro_san.internals.graph.registry.agent_network import AgentNetwork
from neuro_san.internals.graph.persistence.registry_manifest_restorer import RegistryManifestRestorer
from neuro_san.internals.network_providers.agent_network_storage import AgentNetworkStorage


class DirectAgentStorageUtil:
    """
    Sets up AgentNetworkStorage for direct usage.
    """

    @staticmethod
    def create_network_storage(manifest_networks: Dict[str, Dict[str, AgentNetwork]] = None,
                               storage_type: str = "public") -> AgentNetworkStorage:
        """
        Creates an AgentNetworkStorage instance for a given type.

        :param manifest_networks: Optional structure that is handed back from a RegistryManifestRestorer.restore()
                        call.  This has major keys being different network storage options like
                        "public" and "protected". The values are agent name -> AgentNetwork mappings.
                        By default the value is None, indicating we need to get this information
                        by calling the RegistryManifestRestorer.
        :param storage_type: The type of storage ("public" or "protected")
                        Default value is "public".
        :return: An AgentNetworkStorage populated from the Registry Manifest
        """
        network_storage = AgentNetworkStorage()

        if manifest_networks is None:
            manifest_restorer = RegistryManifestRestorer()
            manifest_networks = manifest_restorer.restore()

        storage_networks: Dict[str, AgentNetwork] = manifest_networks.get(storage_type)
        if storage_networks is None:
            return None

        for agent_name, agent_network in storage_networks.items():
            network_storage.add_agent_network(agent_name, agent_network)

        return network_storage
