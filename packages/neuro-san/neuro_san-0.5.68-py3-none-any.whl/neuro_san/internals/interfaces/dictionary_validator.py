
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


class DictionaryValidator:
    """
    An interface for validating dictionaries of various meanings.
    """

    def validate(self, candidate: Dict[str, Any]) -> List[str]:
        """
        Validate the given dictionary

        :param candidate: The dictionary to validate
        :return: A list of error messages
        """
        raise NotImplementedError
