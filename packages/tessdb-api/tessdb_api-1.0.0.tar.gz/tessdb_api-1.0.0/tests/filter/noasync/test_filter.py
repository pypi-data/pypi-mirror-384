import pytest
import logging
from typing import List, Iterator

from collections import defaultdict

from tessdbapi.filter import LookAheadFilter
from tessdbapi.model import ReadingInfo

log = logging.getLogger(__name__.split(".")[-1])


class DataStore:
    def __init__(self):
        self._store = defaultdict(list)

    def append(self, item: ReadingInfo | list[ReadingInfo]) -> None:
        if item is None:
            return
        if isinstance(item, list):
            for x in item:
                self._store[x.sequence_number].append(x)
        else:
            self._store[item.sequence_number].append(item)

    @property
    def duplicates(self) -> list[ReadingInfo]:
        return [readings for _, readings in self._store.items() if len(readings) > 1]

    def __len__(self) -> int:
        return sum(len(lst) for lst in self._store.values())

    def log(self, detailed=False):
        log.info("DataStore seq_nums = %s", sorted(self._store.keys()))
        log.info(
            "DataStore has %d readings (%d distinct readings)",
            len(self),
            len(self._store),
        )
        for seq, readings in self._store.items():
            if len(readings) > 1:
                if detailed:
                    log.info("seq = %d -> %s", seq, readings)
                else:
                    log.info("seq = %d -> %d readings", seq, len(readings))


def refill(
    filt: LookAheadFilter, store: DataStore, samples: List[ReadingInfo], N: int
) -> Iterator[List[ReadingInfo]]:
    log.info("filling with %d samples", N)
    iterator = iter(samples)
    for i in range(N):
        reading, extra = filt.push_pop(next(iterator))
        store.append(reading)
        store.append(extra)
    return iterator


def test_unique():
    filt = LookAheadFilter.instance("stars1", 7, False, True)
    assert LookAheadFilter.instances == {"stars1": filt}
    filt = LookAheadFilter.instance("stars1", 7, False, True)
    assert LookAheadFilter.instances == {"stars1": filt}


def test_several():
    filt1 = LookAheadFilter.instance("stars1", 7, False, True)
    assert LookAheadFilter.instances == {"stars1": filt1}
    filt2 = LookAheadFilter.instance("stars2", 7, False, True)
    assert LookAheadFilter.instances == {"stars1": filt1, "stars2": filt2}


@pytest.fixture()
def store() -> DataStore:
    return DataStore()


# Different window sizes
window_sizes = [7]


@pytest.fixture(params=window_sizes)
def ord_filter_empty(request) -> LookAheadFilter:
    LookAheadFilter.reset()
    filt = LookAheadFilter.instance("stars1", window_size=request.param, flushing=False, buffered=True)
    return filt


@pytest.fixture(params=window_sizes)
def flsh_filter_empty(request) -> LookAheadFilter:
    LookAheadFilter.reset()
    filt = LookAheadFilter.instance("stars1", window_size=request.param, flushing=True, buffered=True)
    return filt


def test_duplicates(store, stars1_dup):
    for reading in stars1_dup:
        store.append(reading)
    assert len(store.duplicates) > 0
    store.log()


@pytest.mark.parametrize(
    "fixture_name", ["stars1_night1", "stars1_small_sunrise", "stars1_day", "stars1_day_sparse"]
)
def test_half_fill_1(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = min(ord_filter_empty.window // 2, len(readings))
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    assert len(store) == 0
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_night1"])
def test_half_fill_2(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = ord_filter_empty.window // 2
    iter_reading = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    reading, extra = ord_filter_empty.push_pop(next(iter_reading))
    assert reading is readings[0]
    assert reading is ord_filter_empty.oldest
    assert extra == list()
    reading, extra = ord_filter_empty.push_pop(next(iter_reading))
    assert reading is readings[1]
    assert reading is not ord_filter_empty.oldest
    assert extra == list()
    if N == 3:
        reading, extra = ord_filter_empty.push_pop(next(iter_reading))
        assert reading is readings[2]
        assert reading is not ord_filter_empty.oldest
        assert extra == list()


@pytest.mark.parametrize("fixture_name", ["stars1_day", "stars1_day_sparse"])
def test_almost_full_day(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = min(ord_filter_empty.window - 1, len(readings))
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    assert len(store) == 0
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_small_sunset"])
def test_almost_full_night(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = min(ord_filter_empty.window - 1, len(readings))
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    assert len(store) == 1
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_day"])
def test_full_day(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = min(ord_filter_empty.window, len(readings))
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    assert len(store) == 0
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_night1"])
def test_full_night_1(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = min(ord_filter_empty.window - 1, len(readings))
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == N
    assert len(store) == ord_filter_empty.window // 2
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_sunset"])
def test_full_night_2(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = len(readings)
    _ = refill(ord_filter_empty, store, readings, N)
    assert len(ord_filter_empty) == ord_filter_empty.window
    assert len(store) == 7
    assert store.duplicates == list()
    store.log()


@pytest.mark.parametrize("fixture_name", ["stars1_day"])
def test_flushing_1(flsh_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = flsh_filter_empty.window // 2
    _ = refill(flsh_filter_empty, store, readings, N)
    store.log()
    assert len(store) == N


@pytest.mark.parametrize("fixture_name", ["stars1_day"])
def test_flushing_2(ord_filter_empty, store, request, fixture_name):
    readings = request.getfixturevalue(fixture_name)
    N = ord_filter_empty.window // 2
    iter_reading = refill(ord_filter_empty, store, readings, N)
    store.log()
    assert len(store) == 0
    ord_filter_empty.flush()
    sample = next(iter_reading)
    reading, extra = ord_filter_empty.push_pop(sample)
    assert reading is sample
    assert len(extra) == N
    store.append(reading)
    store.append(extra)
    store.log()
    sample = next(iter_reading)
    reading, extra = ord_filter_empty.push_pop(sample)
    assert reading is sample
    assert len(extra) == 0
    store.append(reading)
    store.append(extra)
    store.log()
