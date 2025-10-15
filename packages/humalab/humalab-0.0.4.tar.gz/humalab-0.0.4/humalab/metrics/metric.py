from enum import Enum
from typing import Any  
from humalab.constants import EpisodeStatus


class MetricType(Enum):
    DEFAULT = "default"
    STREAM = "stream"
    DISTRIBUTION = "distribution"
    SUMMARY = "summary"


class MetricGranularity(Enum):
    STEP = "step"
    EPISODE = "episode"
    RUN = "run"


class Metrics:
    def __init__(self, 
                 name: str, 
                 metric_type: MetricType,
                 episode_id: str,
                 run_id: str,
                 granularity: MetricGranularity = MetricGranularity.STEP) -> None:
        """
        Base class for different types of metrics.
        
        Args:
            name (str): The name of the metric.
            metric_type (MetricType): The type of the metric.
            episode_id (str): The ID of the episode.
            run_id (str): The ID of the run.
            granularity (MetricGranularity): The granularity of the metric.
        """
        self._name = name
        self._metric_type = metric_type
        self._granularity = granularity
        self._values = []
        self._x_values = []
        self._episode_id = episode_id
        self._run_id = run_id
        self._last_step = -1
    
    def reset(self, 
              episode_id: str | None = None) -> None:
        """Reset the metric for a new episode or run.

        Args:
            episode_id (str | None): Optional new episode ID. If None, keeps the current episode ID.
        """
        if self._granularity != MetricGranularity.RUN:
            self._submit()
            self._values = []
            self._x_values = []
        self._last_step = -1
        self._episode_id = episode_id
        
    @property
    def name(self) -> str:
        """The name of the metric.
        
        Returns:
            str: The name of the metric.
        """
        return self._name
    
    @property
    def metric_type(self) -> MetricType:
        """The type of the metric.

        Returns:
            MetricType: The type of the metric.
        """
        return self._metric_type
    
    @property
    def granularity(self) -> MetricGranularity:
        """The granularity of the metric.

        Returns:
            MetricGranularity: The granularity of the metric.
        """
        return self._granularity

    def log(self, data: Any, step: int | None = None, replace: bool = True) -> None:
        """Log a new data point for the metric. The behavior depends on the granularity.    

        Args:
            data (Any): The data point to log.
            step (int | None): The step number for STEP granularity. Must be provided if granularity is STEP.
            replace (bool): Whether to replace the last logged value if logging at the same step/episode/run.
        """
        if self._granularity == MetricGranularity.STEP:
            if step is None:
                raise ValueError("step Must be provided!")
            if step == self._last_step:
                if replace:
                    self._values[-1] = data
                else:
                    raise ValueError("Cannot log the data at the same step.")
            else:
                self._values.append(data)
                self._x_values.append(step)
        elif self._granularity == MetricGranularity.EPISODE:
            if len(self._x_values) > 0 and not replace:
                raise ValueError("Cannot log the data at the same episode.")
            self._values = [data]
            self._x_values = [self._episode_id]
        else: # MetricGranularity.RUN
            if len(self._values) > 0 and not replace:
                raise ValueError("Cannot log the data at the same run.")
            self._values = [data]
            self._x_values = [self._run_id]
    
    def _submit(self) -> None:
        if not self._values:
            # If there is no data to submit, then return.
            return
        # TODO: Implement commit logic

        # Clear data after the submission.
        self._values = []
        self._x_values = []
        
    def finish(self) -> None:
        """Finish the metric logging and submit the final data."""
        self.reset()
        self._submit()
