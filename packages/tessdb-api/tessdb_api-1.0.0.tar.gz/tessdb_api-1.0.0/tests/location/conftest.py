import pytest

from typing import List

from tessdbapi.model import LocationInfo


@pytest.fixture()
def melorse(request) -> LocationInfo:
    return LocationInfo(
        longitude=-3.6124434,
        latitude=40.4208393,
        height=900,
        place="Melrose Place",
    )
