from humalab.dists.distribution import Distribution
from typing import Any
import numpy as np


class TruncatedGaussian(Distribution):
    def __init__(self,
                 generator: np.random.Generator,
                 loc: float | Any,
                 scale: float | Any,
                 low: float | Any,
                 high: float | Any,
                 size: int | tuple[int, ...] | None = None) -> None:
        """
        Initialize the truncated Gaussian (normal) distribution.
        
        Args:
            generator (np.random.Generator): The random number generator.
            loc (float | Any): The mean of the distribution.
            scale (float | Any): The standard deviation of the distribution.
            low (float | Any): The lower truncation bound.
            high (float | Any): The upper truncation bound.
            size (int | tuple[int, ...] | None): The size of the output.
        """
        super().__init__(generator=generator)
        self._loc = loc
        self._scale = scale
        self._low = low
        self._high = high
        self._size = size

    def _sample(self) -> int | float | np.ndarray:
        samples = self._generator.normal(loc=self._loc, scale=self._scale, size=self._size)
        mask = (samples < self._low) | (samples > self._high)
        while np.any(mask):
            samples[mask] = self._generator.normal(loc=self._loc, scale=self._scale, size=np.sum(mask))
            mask = (samples < self._low) | (samples > self._high)
        return samples

    def __repr__(self) -> str:
        return f"TruncatedGaussian(loc={self._loc}, scale={self._scale}, low={self._low}, high={self._high}, size={self._size})"
    
    @staticmethod
    def create(generator: np.random.Generator, 
               loc: float | Any, 
               scale: float | Any, 
               low: float | Any, 
               high: float | Any, 
               size: int | tuple[int, ...] | None = None) -> 'TruncatedGaussian':
        """
        Create a truncated Gaussian (normal) distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            loc (float | Any): The mean of the distribution.
            scale (float | Any): The standard deviation of the distribution.
            low (float | Any): The lower truncation bound.
            high (float | Any): The upper truncation bound.
            size (int | tuple[int, ...] | None): The size of the output.

        Returns:
            TruncatedGaussian: The created truncated Gaussian distribution.
        """
        return TruncatedGaussian(generator=generator, loc=loc, scale=scale, low=low, high=high, size=size)