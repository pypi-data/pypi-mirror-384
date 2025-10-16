import pytest
import logging
from typing import List
from datetime import datetime, timezone


from tessdbapi.model import ReadingInfo1c

log = logging.getLogger(__name__.split(".")[-1])


@pytest.fixture()
def stars1() -> List[ReadingInfo1c]:
    return [
        # NIGHT
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 00, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=0,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 1, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=1,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 2, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=2,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 3, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=3,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 4, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=4,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 5, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=5,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 6, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=6,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 7, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=7,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        # DAY FROM 8
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 8, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=8,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 9, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=9,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 10, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=10,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 11, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=11,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 12, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=12,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 13, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=13,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 14, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=14,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 15, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=15,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 16, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=16,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 17, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=17,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 18, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=18,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 19, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=19,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 20, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=20,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 21, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=21,
            freq1=10,
            mag1=0,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        # NIGHT FROM 22
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 22, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=22,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 23, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=23,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 24, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=24,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 25, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=25,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 26, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=26,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 27, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=27,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 28, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=28,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 29, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=29,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 30, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=30,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 31, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=31,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
        ReadingInfo1c(
            tstamp=datetime(2025, 9, 4, 00, 31, 00, tzinfo=timezone.utc),
            name="stars1",
            sequence_number=31,
            freq1=10,
            mag1=23.4,
            box_temperature=12,
            sky_temperature=-12,
            signal_strength=-78,
        ),
    ]


@pytest.fixture()
def stars1_decimated(stars1) -> List[ReadingInfo1c]:
    return stars1[::2]


@pytest.fixture()
def stars1_dup(stars1) -> List[ReadingInfo1c]:
    return stars1[:5] * 2


@pytest.fixture()
def stars1_night1(stars1) -> List[ReadingInfo1c]:
    return stars1[:8]


@pytest.fixture()
def stars1_night2(stars1) -> List[ReadingInfo1c]:
    return stars1[22:]


@pytest.fixture()
def stars1_day(stars1) -> List[ReadingInfo1c]:
    return stars1[8:22]


@pytest.fixture()
def stars1_day_sparse(stars1) -> List[ReadingInfo1c]:
    new_list = stars1[8:10] + stars1[11:14] + stars1[15:16] + stars1[18:22]
    return new_list

@pytest.fixture()
def stars1_small_sunrise(stars1) -> List[ReadingInfo1c]:
    log.info("Sunrise transition point between index 7-8")
    return stars1[6:9]


@pytest.fixture()
def stars1_sunrise(stars1) -> List[ReadingInfo1c]:
    log.info("Sunrise transition point between index 7-8")
    return stars1[4:12]


@pytest.fixture()
def stars1_sunset(stars1) -> List[ReadingInfo1c]:
    log.info("Sunset transition point between index 21-22")
    return stars1[14:29]


@pytest.fixture()
def stars1_small_sunset(stars1) -> List[ReadingInfo1c]:
    log.info("Sunset transition point between index 21-22")
    return stars1[20:24]
