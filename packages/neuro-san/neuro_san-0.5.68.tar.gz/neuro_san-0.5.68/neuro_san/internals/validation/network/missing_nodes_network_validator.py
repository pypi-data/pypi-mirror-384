
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
from typing import List

from logging import getLogger
from logging import Logger

from neuro_san.internals.validation.network.abstract_network_validator import AbstractNetworkValidator


class MissingNodesNetworkValidator(AbstractNetworkValidator):
    """
    AbstractNetworkValidator that looks for missing nodes that are referred to
    in an agent network.
    """

    def __init__(self):
        """
        Constructor
        """
        self.logger: Logger = getLogger(self.__class__.__name__)

    def validate_name_to_spec_dict(self, name_to_spec: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network, specifically in the form of a name -> agent spec dictionary.

        :param name_to_spec: The name -> agent spec dictionary to validate
        :return: A list of error messages
        """
        errors: List[str] = []

        # Validate that agent tools have corresponding nodes
        missing_nodes: Dict[str, List[str]] = self.find_missing_agent_nodes(name_to_spec)
        if missing_nodes:
            for agent, missing_tools in missing_nodes.items():
                # Format the comma-separated list of missing tools
                tools_str: str = ", ".join(f"'{tool}'" for tool in missing_tools)
                errors.append(
                    f"Agent '{agent}' references non-existent agent(s) in tools: {tools_str}"
                )

        if len(errors) > 0:
            # Only warn if there is a problem
            self.logger.warning(str(errors))

        return errors

    def find_missing_agent_nodes(self, name_to_spec: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Find agents referenced in "tools" lists that don't have corresponding nodes in the network.

        :param name_to_spec: The agent network to validate
        :return: Dictionary mapping agent names to list of tools that reference non-existent agents
                Format: {agent_name: [missing_tool1, missing_tool2, ...]}
        """
        missing_nodes: Dict[str, List[str]] = {}

        # Iterate through all agents in the network
        for agent_name, agent_data in name_to_spec.items():

            tools: List[str] = agent_data.get("tools", [])
            safe_tools: List[str] = self.remove_dictionary_tools(tools)

            # Check each tool in the agent's tools list
            for tool in safe_tools:
                # Skip URL/path tools - they're not agents and don't need nodes
                if self.is_url_or_path(tool):
                    continue

                # If tool is an agent reference but has no node in network, it's invalid
                if tool not in name_to_spec:
                    if agent_name not in missing_nodes:
                        missing_nodes[agent_name] = []
                    missing_nodes[agent_name].append(tool)

        return missing_nodes
