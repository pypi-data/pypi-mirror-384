
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


class KeywordNetworkValidator(AbstractNetworkValidator):
    """
    AgentNetworkValidator that looks for correct keywords in an agent network
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
        :return: List of errors indicating agents and missing keywords
        """
        errors: List[str] = []

        self.logger.info("Validating agent network keywords...")

        # Currently, only required "instructions" for non-function agents.
        for agent_name, agent in name_to_spec.items():
            if agent.get("instructions") == "":
                error_msg = f"{agent_name} 'instructions' cannot be empty."
                errors.append(error_msg)

        # Only warn if there is a problem
        if len(errors) > 0:
            self.logger.warning(str(errors))

        return errors
