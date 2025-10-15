from humalab.dists.distribution import Distribution
from typing import Any

import numpy as np

class Discrete(Distribution):
    def __init__(self, 
                 generator: np.random.Generator,
                 low: int | Any, 
                 high: int | Any,
                 endpoint: bool | None = None,
                 size: int | tuple[int, ...] | None = None,
                 ) -> None:
        """
        Initialize the discrete distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            low (int | Any): The lower bound (inclusive).
            high (int | Any): The upper bound (exclusive).
            endpoint (bool | None): Whether to include the endpoint.
            size (int | tuple[int, ...] | None): The size of the output.
        """
        super().__init__(generator=generator)
        self._low = np.array(low)
        self._high = np.array(high)
        self._size = size
        self._endpoint = endpoint if endpoint is not None else True

    def _sample(self) -> int | float | np.ndarray:
        return self._generator.integers(self._low, self._high, size=self._size, endpoint=self._endpoint)

    def __repr__(self) -> str:
        return f"Discrete(low={self._low}, high={self._high}, size={self._size}, endpoint={self._endpoint})"
    
    @staticmethod
    def create(generator: np.random.Generator, 
               low: int | Any, 
               high: int | Any, 
               endpoint: bool = True,
               size: int | tuple[int, ...] | None = None, 
               ) -> 'Discrete':
        """
        Create a discrete distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            low (int | Any): The lower bound (inclusive).
            high (int | Any): The upper bound (exclusive).
            endpoint (bool): Whether to include the endpoint.
            size (int | tuple[int, ...] | None): The size of the output.

        Returns:
            Discrete: The created discrete distribution.
        """
        return Discrete(generator=generator, low=low, high=high, size=size, endpoint=endpoint)