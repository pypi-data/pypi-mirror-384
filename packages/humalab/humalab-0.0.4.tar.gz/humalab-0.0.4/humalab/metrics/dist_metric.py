
from humalab.metrics.metric import MetricGranularity, Metrics, MetricType

class DistributionMetric(Metrics):
    def __init__(self, 
                 name: str, 
                 distribution_type: str,
                 episode_id: str,
                 run_id: str,
                 granularity: MetricGranularity = MetricGranularity.EPISODE) -> None:
        """
        Initialize the distribution metric.

        Args:
            name (str): The name of the metric.
            distribution_type (str): The type of distribution (e.g., "normal", "uniform").
            episode_id (str): The ID of the episode.
            run_id (str): The ID of the run.
            granularity (MetricGranularity): The granularity of the metric.
        """
        super().__init__(name, MetricType.DISTRIBUTION, episode_id=episode_id, run_id=run_id, granularity=granularity)
        self.distribution_type = distribution_type
