import math

from typing import Dict, List


def gcd(values: List[int]):
    """
    Computes the greatest common denominator for a list of integers.

    :param values: the integers to find the gcd for (at least 2)
    :type values: list
    :return: the gcd
    :rtype: int
    """
    if len(values) < 2:
        raise Exception("At least two numbers required for gcd!")
    values = values[:]
    result = values.pop(0)
    while len(values) > 0:
        b = values.pop(0)
        result = math.gcd(result, b)
    return result


class Splitter:
    """
    Class for dividing a token stream into sub-streams.
    """

    def __init__(self, split_ratios: List[int], split_names: List[str]):
        """
        Initializes the splitter.

        :param split_ratios: the list of (int) ratios to use (must sum up to 100)
        :type split_ratios: list
        :param split_names: the list of names to use for the splits
        :type split_names: list
        """
        self.split_ratios = split_ratios
        self.split_names = split_names
        self._schedule = None
        self._counter = 0
        self._stats = None

    def initialize(self):
        """
        Initializes the splitter, throws exceptions if undefined state or incorrect values.
        """
        if self.split_ratios is None:
            raise Exception("No split ratios defined!")
        if self.split_names is None:
            raise Exception("No split name defined!")
        if len(self.split_ratios) != len(self.split_names):
            raise Exception("Differing number of split ratios and names: %d != %d" % (len(self.split_ratios), len(self.split_names)))
        if sum(self.split_ratios) != 100:
            raise Exception("Split ratios must sum up to 100, but got: %d" % sum(self.split_ratios))

        # compute greatest common denominator and generate schedule
        _gcd = gcd(self.split_ratios)
        self._schedule = [0] * (len(self.split_ratios) + 1)
        for i, ratio in enumerate(self.split_ratios):
            self._schedule[i + 1] = self._schedule[i] + ratio / _gcd
        self._counter = 0
        self._stats = dict()

    def reset(self):
        """
        Resets the counter and stats.
        """
        self._counter = 0
        self._stats = dict()

    def next(self) -> str:
        """
        Returns the next split name.

        :return: the name of the split
        :rtype: str
        """
        split = None
        for i in range(len(self.split_names)):
            if (self._counter >= self._schedule[i]) and (self._counter < self._schedule[i + 1]):
                split = self.split_names[i]

        # update counter
        self._counter += 1
        if self._counter == self._schedule[-1]:
            self._counter = 0

        # update stats
        if split not in self._stats:
            self._stats[split] = 0
        self._stats[split] += 1

        return split

    def stats(self) -> Dict:
        """
        Returns the statistics.
        """
        return self._stats

    def counter(self) -> int:
        """
        Returns the counter.
        """
        return self._counter
