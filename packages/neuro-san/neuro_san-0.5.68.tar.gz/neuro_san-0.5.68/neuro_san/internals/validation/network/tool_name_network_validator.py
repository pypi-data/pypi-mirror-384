
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

import re

from neuro_san.internals.validation.network.abstract_network_validator import AbstractNetworkValidator


class ToolNameNetworkValidator(AbstractNetworkValidator):
    """
    AbstractNetworkValidator that looks for correct tool names in an agent network
    """

    # This comes from the langchain error message that happens when a tool name is not valid
    TOOL_NAME_PATTERN: str = r"^[a-zA-Z0-9_-]+$"

    def __init__(self):
        """
        Constructor
        """
        self.logger: Logger = getLogger(self.__class__.__name__)

    def validate_name_to_spec_dict(self, name_to_spec: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network, specifically in the form of a name -> agent spec dictionary.

        :param name_to_spec: The name -> agent spec dictionary to validate
        :return: List of errors indicating agents than have invalid names
        """
        errors: List[str] = []

        # Be sure all agent names are valid per the regex above.
        for agent_name, agent in name_to_spec.items():
            spec_name: str = agent.get("name")
            if not re.match(self.TOOL_NAME_PATTERN, agent_name) or \
                    not re.match(self.TOOL_NAME_PATTERN, spec_name):
                error_msg = f"{agent_name} must match the regex '{self.TOOL_NAME_PATTERN}'"
                errors.append(error_msg)

        # Only warn if there is a problem
        if len(errors) > 0:
            self.logger.warning(str(errors))

        return errors
