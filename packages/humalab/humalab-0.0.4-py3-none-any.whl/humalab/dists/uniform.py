from humalab.dists.distribution import Distribution

from typing import Any
import numpy as np

class Uniform(Distribution):
    def __init__(self, 
                 generator: np.random.Generator,
                 low: float | Any, 
                 high: float | Any, 
                 size: int | tuple[int, ...] | None = None, ) -> None:
        """
        Initialize the uniform distribution.
        
        Args:
            generator (np.random.Generator): The random number generator.
            low (float | Any): The lower bound (inclusive).
            high (float | Any): The upper bound (exclusive).
            size (int | tuple[int, ...] | None): The size of the output.
        """
        super().__init__(generator=generator)
        self._low = np.array(low)
        self._high = np.array(high)
        self._size = size

    def _sample(self) -> int | float | np.ndarray:
        return self._generator.uniform(self._low, self._high, size=self._size)

    def __repr__(self) -> str:
        return f"Uniform(low={self._low}, high={self._high}, size={self._size})"
    
    @staticmethod
    def create(generator: np.random.Generator, 
               low: float | Any, 
               high: float | Any, 
               size: int | tuple[int, ...] | None = None) -> 'Uniform':
        """
        Create a uniform distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            low (float | Any): The lower bound (inclusive).
            high (float | Any): The upper bound (exclusive).
            size (int | tuple[int, ...] | None): The size of the output.

        Returns:
            Uniform: The created uniform distribution.
        """
        return Uniform(generator=generator, low=low, high=high, size=size)