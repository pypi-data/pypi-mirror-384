from abc import ABC, abstractmethod

import numpy as np

class Distribution(ABC):
    def __init__(self,
                 generator: np.random.Generator) -> None:
        """
        Initialize the distribution.

        Args:
            generator (np.random.Generator): The random number generator.
        """
        super().__init__()
        self._generator = generator
        self._last_sample = None

    def sample(self) -> int | float | np.ndarray:
        """
        Sample from the distribution.

        Returns:
            int | float | np.ndarray: The sampled value(s).
        """
        self._last_sample = self._sample()
        return self._last_sample

    @abstractmethod
    def _sample(self) -> int | float | np.ndarray:
        pass

    @property
    def last_sample(self) -> int | float | np.ndarray | None:
        """Get the last sampled value.
        Returns:
            int | float | np.ndarray | None: The last sampled value, or None if no sample has been taken yet.
        """
        return self._last_sample