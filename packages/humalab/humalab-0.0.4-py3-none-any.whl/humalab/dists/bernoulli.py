from humalab.dists.distribution import Distribution

from typing import Any
import numpy as np

class Bernoulli(Distribution):
    def __init__(self,
                 generator: np.random.Generator,
                 p: float | Any,
                 size: int | tuple[int, ...] | None = None) -> None:
        """
        Initialize the Bernoulli distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            p (float | Any): The probability of success.
            size (int | tuple[int, ...] | None): The size of the output.
        """
        super().__init__(generator=generator)
        self._p = p
        self._size = size

    def _sample(self) -> int | float | np.ndarray:
        return self._generator.binomial(n=1, p=self._p, size=self._size)

    def __repr__(self) -> str:
        return f"Bernoulli(p={self._p}, size={self._size})"
    
    @staticmethod
    def create(generator: np.random.Generator, 
               p: float | Any, 
               size: int | tuple[int, ...] | None = None) -> 'Bernoulli':
        """
        Create a Bernoulli distribution.

        Args:
            generator (np.random.Generator): The random number generator.
            p (float | Any): The probability of success.
            size (int | tuple[int, ...] | None): The size of the output.

        Returns:
            Bernoulli: The created Bernoulli distribution.
        """
        return Bernoulli(generator=generator, p=p, size=size)
