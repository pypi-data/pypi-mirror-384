from humalab.dists.distribution import Distribution
from typing import Any

import numpy as np

class LogUniform(Distribution):
    def __init__(self, 
                 generator: np.random.Generator,
                 low: float | Any,
                 high: float | Any,
                 size: int | tuple[int, ...]| None = None) -> None:
        """
        Initialize the log-uniform distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            low (float | Any): The lower bound (inclusive).
            high (float | Any): The upper bound (exclusive).
            size (int | tuple[int, ...]| None): The size of the output.
        """
        super().__init__(generator=generator)
        self._log_low = np.log(np.array(low))
        self._log_high = np.log(np.array(high))
        self._size = size

    def _sample(self) -> int | float | np.ndarray:
        return np.exp(self._generator.uniform(self._log_low, self._log_high, size=self._size))
    
    def __repr__(self) -> str:
        return f"LogUniform(low={np.exp(self._log_low)}, high={np.exp(self._log_high)}, size={self._size})"

    @staticmethod
    def create(generator: np.random.Generator, 
               low: float | Any, 
               high: float | Any, 
               size: int | tuple[int, ...]| None = None) -> 'LogUniform':
        """
        Create a log-uniform distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            low (float | Any): The lower bound (inclusive).
            high (float | Any): The upper bound (exclusive).
            size (int | tuple[int, ...]| None): The size of the output.

        Returns:
            LogUniform: The created log-uniform distribution.
        """
        return LogUniform(generator=generator, low=low, high=high, size=size)