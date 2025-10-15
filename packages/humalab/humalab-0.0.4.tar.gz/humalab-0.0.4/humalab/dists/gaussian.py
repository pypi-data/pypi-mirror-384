from humalab.dists.distribution import Distribution
from typing import Any
import numpy as np


class Gaussian(Distribution):
    def __init__(self,
                 generator: np.random.Generator,
                 loc: float | Any,
                 scale: float | Any,
                 size: int | tuple[int, ...] | None = None) -> None:
        """
        Initialize the Gaussian (normal) distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            loc (float | Any): The mean of the distribution.
            scale (float | Any): The standard deviation of the distribution.
            size (int | tuple[int, ...] | None): The size of the output.
        """
        super().__init__(generator=generator)
        self._loc = loc
        self._scale = scale
        self._size = size

    def _sample(self) -> int | float | np.ndarray:
        return self._generator.normal(loc=self._loc, scale=self._scale, size=self._size)

    def __repr__(self) -> str:
        return f"Gaussian(loc={self._loc}, scale={self._scale}, size={self._size})"
    
    @staticmethod
    def create(generator: np.random.Generator, 
               loc: float | Any, 
               scale: float | Any, 
               size: int | tuple[int, ...] | None = None) -> 'Gaussian':
        """
        Create a Gaussian (normal) distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            loc (float | Any): The mean of the distribution.
            scale (float | Any): The standard deviation of the distribution.
            size (int | tuple[int, ...] | None): The size of the output.

        Returns:
            Gaussian: The created Gaussian distribution.
        """
        return Gaussian(generator=generator, loc=loc, scale=scale, size=size)