from typing import Any
import numpy as np
from omegaconf import OmegaConf, ListConfig, AnyNode, DictConfig
import yaml
from humalab.dists.bernoulli import Bernoulli
from humalab.dists.categorical import Categorical
from humalab.dists.uniform import Uniform
from humalab.dists.discrete import Discrete
from humalab.dists.log_uniform import LogUniform
from humalab.dists.gaussian import Gaussian
from humalab.dists.truncated_gaussian import TruncatedGaussian
from functools import partial
from humalab.constants import EpisodeStatus
from humalab.metrics.dist_metric import DistributionMetric
from humalab.metrics.metric import MetricGranularity
import copy
import uuid

DISTRIBUTION_MAP = {
    "uniform": Uniform,
    "bernoulli": Bernoulli,
    "categorical": Categorical,
    "discrete": Discrete,
    "log_uniform": LogUniform,
    "gaussian": Gaussian,
    "truncated_gaussian": TruncatedGaussian,
}

DISTRIBUTION_PARAM_NUM_MAP = {
    "uniform": 3,
    "bernoulli": 2,
    "categorical": 3,
    "discrete": 4,
    "log_uniform": 3,
    "gaussian": 3,
    "truncated_gaussian": 5,
}

class Scenario:
    dist_cache = {}
    def __init__(self) -> None:
        self._generator = np.random.default_rng()
        self._scenario_template = OmegaConf.create()
        self._cur_scenario = OmegaConf.create()
        self._scenario_id = None

    def init(self,
             run_id: str,
             episode_id: str,
             scenario: str | list | dict | None = None, 
             seed: int | None=None, 
             scenario_id: str | None=None,
             num_env: int | None = None) -> None:
        """
        Initialize the scenario with the given parameters.
        
        Args:
            run_id: The ID of the current run.
            episode_id: The ID of the current episode.
            scenario: The scenario configuration (YAML string, list, or dict).
            seed: Optional seed for random number generation.
            scenario_id: Optional scenario ID. If None, a new UUID is generated.
            num_env: Optional number of parallel environments.
        """
        self._run_id = run_id
        self._episode_id = episode_id
        self._metrics = {}

        self._num_env = num_env
        self._scenario_id = scenario_id or str(uuid.uuid4())
        self._generator = np.random.default_rng(seed)
        self._configure()
        scenario = scenario or {}
        self._scenario_template = OmegaConf.create(scenario)
        self.reset(episode_id=episode_id)

    def _get_final_size(self, size: int | tuple[int, ...] | None) -> int | tuple[int, ...] | None:
        n = self._num_env
        if size is None:
            return n
        if n is None:
            return size
        if isinstance(size, int):
            return (n, size)
        return (n, *size)
    
    def _get_node_path(self, root: dict | list, node: str) -> str:
        if isinstance(root, list):
            root = {str(i): v for i, v in enumerate(root)}
        
        for key, value in root.items():
            if value == node:
                return str(key)
            if isinstance(value, dict):
                sub_path = self._get_node_path(value, node)
                if sub_path:
                    return f"{key}.{sub_path}"
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if item == node:
                        return f"{key}[{idx}]"
                    if isinstance(item, (dict, list)):
                        sub_path = self._get_node_path(item, node)
                        if sub_path:
                            return f"{key}[{idx}].{sub_path}"
        return ""

    @staticmethod
    def _convert_to_python(obj) -> Any:
        if not isinstance(obj, (np.ndarray, np.generic)):
            return obj

        # NumPy scalar (np.generic) or 0-D ndarray
        if isinstance(obj, np.generic) or (isinstance(obj, np.ndarray) and obj.ndim == 0):
            return obj.item()

        # Regular ndarray (1-D or higher)
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        return obj

    def _configure(self) -> None:
        self._clear_resolvers()
        def distribution_resolver(dist_name: str, *args, _node_, _root_, _parent_, **kwargs):
            if len(args) > DISTRIBUTION_PARAM_NUM_MAP[dist_name]:
                args = args[:DISTRIBUTION_PARAM_NUM_MAP[dist_name]]
                print(f"Warning: Too many parameters for {dist_name}, expected {DISTRIBUTION_PARAM_NUM_MAP[dist_name]}, got {len(args)}. Extra parameters will be ignored.")
            
            # print("_node_: ", _node_, type(_node_))
            # print("_root_: ", _root_, type(_root_))
            # print("_parent_: ", _parent_, type(_parent_))
            # print("Args: ", args, len(args))
            # print("Kwargs: ", kwargs)

            root_yaml = yaml.safe_load(OmegaConf.to_yaml(_root_))
            key_path = self._get_node_path(root_yaml, str(_node_))
            # print("Key path: ", key_path)
            
            if key_path not in self._metrics:
                self._metrics[key_path] = DistributionMetric(name=key_path,
                                                            distribution_type=dist_name,
                                                            run_id=self._run_id,
                                                            episode_id=self._episode_id,
                                                            granularity=MetricGranularity.EPISODE)

            shape = None 
            
            if len(args) == DISTRIBUTION_PARAM_NUM_MAP[dist_name]:
                shape = args[DISTRIBUTION_PARAM_NUM_MAP[dist_name] - 1]
                args = args[:-1]
            shape = self._get_final_size(shape)

            key = str(_node_)
            if key not in Scenario.dist_cache:
                Scenario.dist_cache[key] = DISTRIBUTION_MAP[dist_name].create(self._generator, *args, size=shape, **kwargs)
            ret_val = Scenario.dist_cache[key].sample()
            ret_val = Scenario._convert_to_python(ret_val)

            if isinstance(ret_val, list):
                ret_val = ListConfig(ret_val)
            self._metrics[key_path].log(ret_val)
            return ret_val

        for dist_name in DISTRIBUTION_MAP.keys():
            OmegaConf.register_new_resolver(dist_name, partial(distribution_resolver, dist_name))

    def _clear_resolvers(self) -> None:
        self.dist_cache.clear()
        OmegaConf.clear_resolvers()
    
    def __getattr__(self, name: Any) -> Any:
        if name in self._cur_scenario:
            return self._cur_scenario[name]
        raise AttributeError(f"'Scenario' object has no attribute '{name}'")

    def __getitem__(self, key: Any) -> Any:
        if key in self._cur_scenario:
            return self._cur_scenario[key]
        raise KeyError(f"'Scenario' object has no key '{key}'")

    def reset(self,
              episode_id: str | None = None) -> None:
        """Reset the scenario for a new episode.
        
        Args:
            episode_id: Optional new episode ID. If None, keeps the current episode ID.
        """
        for metric in self._metrics.values():
            metric.reset(episode_id=episode_id)
        self._cur_scenario = copy.deepcopy(self._scenario_template)
        OmegaConf.resolve(self._cur_scenario)
    
    def finish(self) -> None:
        """Finish the scenario and submit final metrics.
        """
        for metric in self._metrics.values():
            metric.finish()

    @property
    def template(self) -> Any:
        """The template scenario configuration.
        
        Returns:
            Any: The template scenario as an OmegaConf object.
        """
        return self._scenario_template
    
    @property
    def cur_scenario(self) -> Any:
        """The current scenario configuration.

        Returns:
            Any: The current scenario as an OmegaConf object.
        """
        return self._cur_scenario
    
    @property
    def yaml(self) -> str:
        """The current scenario configuration as a YAML string.

        Returns:
            str: The current scenario as a YAML string.
        """
        return OmegaConf.to_yaml(self._cur_scenario)
