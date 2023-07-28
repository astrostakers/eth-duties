"""Module for main filter function which filters for inactive and duplicate validator identifiers
"""

from logging import getLogger
from typing import Dict, List

from constants import logging
from fetcher.data_types import ValidatorIdentifier
from fetcher.identifier import core

__LOGGER = getLogger()


def log_inactive_and_duplicated_validators(
    provided_validators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> None:
    """Log inactive and duplicated validators to the console

    Args:
        provided_validators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator
        identifiers filtered for inactive ones and duplicates
    """
    active_validators = [
        core.get_validator_index_or_pubkey(provided_validators, identifier)
        for identifier in complete_validator_identifiers.values()
    ]
    potentital_inactive_validators = list(
        set(provided_validators).difference(set(active_validators))
    )
    duplicates = __get_duplicates_with_different_identifiers(
        provided_validators, complete_validator_identifiers
    )
    inactive_validators = [
        validator
        for validator in potentital_inactive_validators
        if validator not in duplicates
    ]
    if inactive_validators:
        __LOGGER.warning(logging.INACTIVE_VALIDATORS_MESSAGE, inactive_validators)


def __get_duplicates_with_different_identifiers(
    provided_valdiators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> List[str]:
    """Filter for duplicated validators which were provided with different identifiers

    Args:
        provided_valdiators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator
        identifiers filtered for inactive ones and duplicates

    Returns:
        List[str]: Duplicated validator indices and pubkeys
    """
    duplicates = {
        index: identifier
        for (index, identifier) in complete_validator_identifiers.items()
        if identifier.index in provided_valdiators
        and identifier.validator.pubkey in provided_valdiators
    }
    if duplicates:
        __LOGGER.warning(logging.DUPLICATE_VALIDATORS_MESSAGE, list(duplicates.keys()))
    return list(duplicates.keys()) + [
        duplicate.validator.pubkey for duplicate in duplicates.values()
    ]
