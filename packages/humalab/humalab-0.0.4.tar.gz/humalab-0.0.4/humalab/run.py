import uuid
from humalab.metrics.dist_metric import DistributionMetric
from humalab.metrics.metric import MetricGranularity, MetricType, Metrics
from humalab.constants import EpisodeStatus

from humalab.metrics.summary import Summary
from humalab.scenario import Scenario

class Run:
    def __init__(self,
                 entity: str,
                 project: str,
                 scenario: Scenario,
                 name: str | None = None,
                 description: str | None = None,
                 id: str | None = None,
                 tags: list[str] | None = None,
                 ) -> None:
        """
        Initialize a new Run instance.
        
        Args:
            entity (str): The entity (user or team) under which the run is created.
            project (str): The project name under which the run is created.
            scenario (Scenario): The scenario instance for the run.
            name (str | None): The name of the run.
            description (str | None): A description of the run.
            id (str | None): The unique identifier for the run. If None, a UUID is generated.
            tags (list[str] | None): A list of tags associated with the run.
        """
        self._entity = entity
        self._project = project
        self._id = id or str(uuid.uuid4())
        self._name = name or ""
        self._description = description or ""
        self._tags = tags or []
        self._finished = False

        self._episode = str(uuid.uuid4())

        self._scenario = scenario

        self._metrics = {}
    
    @property
    def entity(self) -> str:
        """The entity (user or team) under which the run is created.
        
        Returns:
            str: The entity name.
        """
        return self._entity
    
    @property
    def project(self) -> str:
        """The project name under which the run is created.
        
        Returns:
            str: The project name.
        """
        return self._project
    
    @property
    def id(self) -> str:
        """The unique identifier for the run.
        
        Returns:
            str: The run ID.
        """
        return self._id
    
    @property
    def name(self) -> str:
        """The name of the run.

        Returns:
            str: The run name.
        """
        return self._name
    
    @property
    def description(self) -> str:
        """The description of the run.

        Returns:
            str: The run description.
        """
        return self._description
    
    @property
    def tags(self) -> list[str]:
        """The tags associated with the run.

        Returns:
            list[str]: The list of tags.
        """
        return self._tags
    
    @property
    def episode(self) -> str:
        """The episode ID for the run.

        Returns:
            str: The episode ID.
        """
        return self._episode
    
    @property
    def scenario(self) -> Scenario:
        """The scenario associated with the run.

        Returns:
            Scenario: The scenario instance.
        """
        return self._scenario

    def finish(self,
               status: EpisodeStatus = EpisodeStatus.PASS,
               quiet: bool | None = None) -> None:
        """Finish the run and submit final metrics.

        Args:
            status (EpisodeStatus): The final status of the episode.
            quiet (bool | None): Whether to suppress output.
        """
        self._finished = True
        self._scenario.finish()
        for metric in self._metrics.values():
            metric.finish(status=status)
    
    def log(self,
            data: dict,
            step: int | None = None,
            commit: bool = True,
            ) -> None:
        """Log metrics for the run.

        Args:
            data (dict): A dictionary of metric names and their values.
            step (int | None): The step number for the metrics.
            commit (bool): Whether to commit the metrics immediately.
        """
        for key, value in data.items():
            if key in self._metrics:
                metric = self._metrics[key]
                metric.log(value, step=step, commit=commit)
            else:
                self._metrics[key] = Metrics(key, 
                                             metric_type=MetricType.DEFAULT,
                                             run_id=self._id,
                                             granularity=MetricGranularity.EPISODE,
                                             episode_id=self._episode)
                self._metrics[key].log(value, step=step, commit=commit)

    def reset(self, status: EpisodeStatus = EpisodeStatus.PASS) -> None:
        """Reset the run for a new episode.

        Args:
            status (EpisodeStatus): The status of the current episode before reset.
        """
        self._submit_episode_status(status=status, episode=self._episode)
        self._episode = str(uuid.uuid4())
        self._finished = False
        self._scenario.reset(episode_id=self._episode)
        for metric in self._metrics.values():
            metric.reset(episode=self._episode)
    
    def _submit_episode_status(self, status: EpisodeStatus, episode: str) -> None:
        # TODO: Implement submission of episode status
        pass

    def define_metric(self, 
                      name: str, 
                      metric_type: MetricType = MetricType.DEFAULT,
                      granularity: MetricGranularity = MetricGranularity.RUN,
                      distribution_type: str | None = None,
                      summary: str | None = None,
                      replace: bool = False) -> None:
        """Define a new metric for the run.
        
        Args:
            name (str): The name of the metric.
            metric_type (MetricType): The type of the metric.
            granularity (MetricGranularity): The granularity of the metric.
            distribution_type (str | None): The type of distribution if metric_type is DISTRIBUTION.
            summary (str | None): Specify aggregate metrics added to summary.
                Supported aggregations include "min", "max", "mean", "last",
                "first", and "none". "none" prevents a summary
                from being generated.
            replace (bool): Whether to replace the metric if it already exists.
        """
        if name not in self._metrics or replace:
            if metric_type == MetricType.DISTRIBUTION:
                if distribution_type is None:
                    raise ValueError("distribution_type must be specified for distribution metrics.")
                self._metrics[name] = DistributionMetric(name=name, 
                                                         distribution_type=distribution_type, 
                                                         run_id=self._id,
                                                         episode_id=self._episode,
                                                         granularity=granularity)  
            elif summary is not None:
                self._metrics[name] = Summary(name=name, 
                                              summary=summary, 
                                              run_id=self._id,
                                              episode_id=self._episode,
                                              granularity=granularity)
            else:
                self._metrics[name] = Metrics(name=name, 
                                              metric_type=metric_type, 
                                              run_id=self._id,
                                              episode_id=self._episode,
                                              granularity=granularity)
        else:
            raise ValueError(f"Metric {name} already exists.")
