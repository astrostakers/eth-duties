"""
Entrypoint for the simple cli tool to check for upcoming duties for one or many validators
"""

# pylint: disable=import-error

from argparse import Namespace
from time import sleep
from typing import List, Callable
from logging import getLogger
from fetcher.fetcher import ValidatorDutyFetcher
from fetcher.data_types import ValidatorDuty, DutyType
from fetcher.printer import print_time_to_next_duties
from helper.killer import GracefulKiller
from cli.cli import get_arguments
from protocol.protocol import get_current_slot

__sort_duties: Callable[[ValidatorDuty], int] = lambda duty: duty.slot


def __fetch_validator_duties(
    arguments: Namespace,
    duty_fetcher: ValidatorDutyFetcher,
    duties: List[ValidatorDuty],
) -> List[ValidatorDuty]:
    """Fetches upcoming validator duties

    Args:
        arguments (Namespace): CLI arguments
        duty_fetcher (ValidatorDutyFetcher): Holds all logic for fetching validator duties
        duties (List[ValidatorDuty]): List of validator duties for last logging interval

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    if not __is_current_data_outdated(duty_fetcher, duties):
        return duties
    next_attestation_duties: dict[int, ValidatorDuty] = {}
    if not arguments.omit_attestation_duties:
        next_attestation_duties = duty_fetcher.get_next_attestation_duties()
    next_proposing_duties = duty_fetcher.get_next_proposing_duties()
    next_sync_committee_duties = duty_fetcher.get_next_sync_committee_duties()
    duties = [
        duty
        for duties in [
            next_attestation_duties,
            next_proposing_duties,
            next_sync_committee_duties,
        ]
        for duty in duties.values()
    ]
    duties.sort(key=__sort_duties)
    return duties


def __is_current_data_outdated(
    duty_fetcher: ValidatorDutyFetcher, current_duties: List[ValidatorDuty]
) -> bool:
    current_slot = get_current_slot(duty_fetcher.genesis_time)
    first_non_sync_committee_duty = next(
        filter(lambda duty: duty.type is not DutyType.SYNC_COMMITTEE, current_duties),
        None,
    )
    if (
        current_duties
        and first_non_sync_committee_duty
        and first_non_sync_committee_duty.slot > current_slot
    ):
        return False
    return True


def __create_validator_duty_fetcher_instance(
    arguments: Namespace, graceful_killer: GracefulKiller
) -> ValidatorDutyFetcher:
    """Creates an instance of the class which holds logic for fetching validator duties

    Args:
        arguments (Namespace): CLI arguments
        graceful_killer (GracefulKiller): Instance of helper class to shutdown program gracefully

    Returns:
        ValidatorDutyFetcher: Instance of ValidatorDutyFetcher which
        holds logic for fetching validator duties
    """
    if arguments.validators:
        user_passed_validators = arguments.validators
    else:
        user_passed_validators = [
            validator.strip() for validator in arguments.validator_file
        ]
    return ValidatorDutyFetcher(
        arguments.beacon_node, user_passed_validators, graceful_killer
    )


if __name__ == "__main__":
    killer = GracefulKiller()
    args = get_arguments()
    validator_duty_fetcher = __create_validator_duty_fetcher_instance(args, killer)
    upcoming_duties: List[ValidatorDuty] = []
    while not killer.kill_now:
        upcoming_duties = __fetch_validator_duties(
            args, validator_duty_fetcher, upcoming_duties
        )
        print_time_to_next_duties(upcoming_duties, validator_duty_fetcher.genesis_time)
        sleep(args.interval)
    logger = getLogger(__name__)
    logger.info("Happy staking. See you for next maintenance \U0001F642 !")
