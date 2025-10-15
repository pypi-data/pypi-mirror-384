
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

from neuro_san.internals.interfaces.dictionary_validator import DictionaryValidator


class CompositeDictionaryValidator(DictionaryValidator):
    """
    Implementation of the DictionaryValidator interface that uses multiple validators
    """

    def __init__(self, validators: List[DictionaryValidator]):
        """
        Constructor

        :param validators: A list of validators to use
        """
        self.validators: List[DictionaryValidator] = validators

    def validate(self, candidate: Dict[str, Any]) -> List[str]:
        """
        Validate the agent network.

        :param candidate: The dictionary to validate
        :return: A list of error messages
        """
        errors: List[str] = []

        if not candidate:
            errors.append("Nothing to validate.")
            return errors

        if self.validators is None or len(self.validators) == 0:
            errors.append("No validation policy.")
            return errors

        for validator in self.validators:
            errors.extend(validator.validate(candidate))

        return errors
