# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import importlib.resources
import random
import string
from enum import auto, Enum
from typing import Dict, Final


class MockDataType(str, Enum):
    """
    The types of test data that can be mocked. Matches the file names in the
    mock_data directory.
    """

    def _generate_next_value_(name, start, count, last_values):
        return name.upper()

    GLASSES_DATA = auto()
    GLASSES_FILES = auto()
    GROUP_DATA = auto()
    PAST_MPS_DATA = auto()
    RECORDINGS_ON_COMPUTER = auto()
    SINGLE_MPS_RESPONSE = auto()


__MOCK_DATA: Final[Dict[MockDataType, str]] = {
    e: str(
        importlib.resources.files(__name__).joinpath(f"mock_data/{e.name.lower()}.json")
    )
    for e in MockDataType
}


def generate_random_string(length: int = 8) -> str:
    """
    Function to generate a random string of a given length
    """

    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def get_mock_data_path(test_data_type: MockDataType) -> str:
    """
    Function to get the mock data path for a given test data type
    """
    return __MOCK_DATA[test_data_type]
