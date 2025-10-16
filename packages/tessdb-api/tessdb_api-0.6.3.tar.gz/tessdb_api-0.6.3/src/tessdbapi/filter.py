import logging
import itertools
from typing import Optional, List, Tuple
from collections import deque

from tessdbdao import PhotometerModel
from .model import ReadingInfo, ReadingInfo4c


class Sampler:
    instances = dict()

    @classmethod
    def instance(cls, name: str, divisor: int):
        obj = cls.instances.get(name)
        if obj is None:
            obj = cls(name, divisor)
            cls.instances[name] = obj
        return obj

    def __init__(self, name, divisor: int) -> None:
        self._divisor = divisor
        self._next_divisor = divisor
        self._iter = itertools.cycle(range(divisor))
        self._name = name
        self.log = logging.getLogger(name)

    @property
    def divisor(self) -> int:
        return self._divisor

    @divisor.setter
    def divisor(self, value: int) -> None:
        self._next_divisor = value

    def set_log_level(self, level: int) -> None:
        self.log.setLevel(level)

    def push_pop(self, item: ReadingInfo) -> Optional[ReadingInfo]:
        result = None
        i = next(self._iter)
        if i == 0:
            result = item
            if self._divisor != self._next_divisor:
                self._divisor = self._next_divisor
                self._iter = itertools.cycle(range(self._divisor))
                next(self._iter)  # skip 0 on this new iterator
        if result:
            self.log.debug(
                "%s: allowing reading seq# = %d",
                self.__class__.__name__,
                result.sequence_number,
            )
        else:
            self.log.debug("%s: dropping %s", self.__class__.__name__, dict(item))
        return result


class LookAheadFilter:
    instances = dict()
    flushing_names = set()  # filters that are flushing

    @classmethod
    def reset(cls) -> None:
        """For testing purposes"""
        cls.instances = dict()
        cls.flushing_names = set()

    @classmethod
    def instance(cls, name: str, window_size: int, flushing: bool, buffered: bool):
        obj = cls.instances.get(name)
        if obj is None:
            obj = cls(name, window_size, flushing, buffered)
            cls.instances[name] = obj
        return obj

    def __init__(self, name: str, window_size: int, flushing: bool, buffered: bool) -> None:
        if (window_size % 2) != 1:
            raise ValueError(
                "%s: window_size should be an odd number, not %d",
                self.__class__.__name__,
                window_size,
            )
        self._buffered = buffered
        self._W = window_size
        self._middle = window_size // 2
        self._fifo = deque(maxlen=window_size)
        self._flushing = flushing
        self._name = name
        self.log = logging.getLogger(name)
        # some filters may start in flushing state
        if flushing:
            LookAheadFilter.flushing_names.add(name)

    def __len__(self) -> int:
        return len(self._fifo)

    @property
    def name(self) -> str:
        return self._name

    @property
    def buffered(self) -> bool:
        return self._buffered

    @buffered.setter
    def buffered(self, value: bool) -> None:
        self._buffered = value

    @property
    def window(self) -> int:
        return self._W

    @property
    def youngest(self) -> int:
        return self._fifo[0]

    @property
    def oldest(self) -> int:
        return self._fifo[-1]

    @property
    def flushing(self) -> bool:
        return self._flushing

    def flush(self):
        self._flushing = True

    def set_log_level(self, level: int) -> None:
        self.log.setLevel(level)

    def is_saturated(self) -> bool:
        model = (
            PhotometerModel.TESS4C
            if isinstance(self._fifo[0], ReadingInfo4c)
            else PhotometerModel.TESSW
        )
        if model == PhotometerModel.TESS4C:
            mag_list = [item.mag4 for item in self._fifo]
        else:
            mag_list = [item.mag1 for item in self._fifo]
        # saturated magnitudes have a value of zero
        return sum(mag_list) == 0

    def is_monotonic(self) -> bool:
        """Monotonic if all second differences in sequence nuumbers are 0"""
        seq = [item.sequence_number for item in self._fifo]
        n = len(seq)
        return all([(seq[i + 2] - 2 * seq[i + 1] + seq[i]) == 0 for i in range(n - 2)])

    def _log_result(self, sample: ReadingInfo) -> None:
        if sample:
            self.log.debug(
                "%s: chosen reading seq# = %d",
                self.__class__.__name__,
                sample.sequence_number,
            )
        elif self._saturated and self._monotonic:
            self.log.debug(
                "%s: dropping saturated reading (full FIFO) seq# = %d",
                self.__class__.__name__,
                self._fifo[self._middle].sequence_number,
            )
        elif self._saturated and self._monotonic is None:
            self.log.debug(
                "%s: dropping saturated reading seq# = %d",
                self.__class__.__name__,
                self._fifo[self._middle].sequence_number,
            )

    def _buffered_push_pop(
        self, sample: ReadingInfo
    ) -> Tuple[Optional[ReadingInfo], List[ReadingInfo]]:
        self._fifo.appendleft(sample)  # so that fifo[0] is the youngest sample.
        # Refilling half of the FIFO, but don't loose the first ones if not saturated
        N = len(self._fifo)
        if N <= self._middle:
            chosen_sample = None
            self._saturated = None
            self._monotonic = None
            self.log.debug("%s: refilling FIFO [%d/%d]", self.__class__.__name__, N, self._W)
        # refilling the FIFO but not full yet
        elif self._middle < N < self._W:
            self._saturated = self.is_saturated()
            self._monotonic = None
            chosen_sample = None if self._saturated else self._fifo[self._middle]
            self.log.debug("%s: almost full FIFO [%d/%d]", self.__class__.__name__, N, self._W)
        # Full FIFO
        # Throw away samples if they consecutive samples and are saturated.
        else:
            self._saturated = self.is_saturated()
            self._monotonic = self.is_monotonic()
            chosen_sample = (
                None if self._saturated and self._monotonic else self._fifo[self._middle]
            )
        self._log_result(chosen_sample)
        return chosen_sample, list()  # No extra samples

    def _unbuffered_push_pop(
        self, sample: ReadingInfo
    ) -> Tuple[Optional[ReadingInfo], List[ReadingInfo]]:
        extra_samples = list()
        N = len(self._fifo)
        if N > 0:
            M = min(N, self._middle)
            extra_samples = [self._fifo[i] for i in range(M)]  # saves what's needed to be saved
            self._fifo.clear()  # queue closed for ever
            LookAheadFilter.flushing_names.add(self._name)
            self.log.debug("%s Flushing %d extra readings", self.__class__.__name__, M)
        self.log.debug(
            "%s chosen reading #seq = %d", self.__class__.__name__, sample.sequence_number
        )
        return sample, extra_samples

    def push_pop(self, sample: ReadingInfo) -> Tuple[Optional[ReadingInfo], List[ReadingInfo]]:
        return (
            self._unbuffered_push_pop(sample)
            if (not self._buffered or self._flushing)
            else self._buffered_push_pop(sample)
        )
