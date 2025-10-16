import pytest
import logging
from datetime import datetime, timezone
from typing import Iterator, List
from tessdbapi.filter import Sampler
from tessdbapi.model import ReadingInfo1c

log = logging.getLogger(__name__.split(".")[-1])


@pytest.fixture()
def iterator1(stars1) -> Iterator[List[ReadingInfo1c]]:
    return iter(stars1)


def test_subsampler(iterator1, stars1):
    s1 = Sampler(name="stars1", divisor=3)
    value = s1.push_pop(next(iterator1))
    assert value is stars1[0]
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is stars1[3]
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is stars1[6]
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is None


def test_subsampler_change(iterator1, stars1):
    s1 = Sampler(name="stars1", divisor=3)
    value = s1.push_pop(next(iterator1))
    assert value is stars1[0]
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is stars1[3]
    value = s1.push_pop(next(iterator1))
    assert value is None
    # We change the divisor in the middle of a cycle
    # Finish the current downsampling cycle completerly
    # and then restarts the next one
    s1.divisor = 2
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is stars1[6]
    value = s1.push_pop(next(iterator1))
    assert value is None
    value = s1.push_pop(next(iterator1))
    assert value is stars1[8]
