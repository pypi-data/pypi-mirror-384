import unittest
import numpy as np
from humalab.scenario import Scenario


class ScenarioTest(unittest.TestCase):
    """Unit tests for Scenario class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scenario = Scenario()
        self.run_id = "test_run_id"
        self.episode_id = "test_episode_id"

    def tearDown(self):
        """Clean up after each test method."""
        self.scenario._clear_resolvers()

    def test_init_should_initialize_with_empty_scenario(self):
        """Test that init() initializes with empty scenario when none provided."""
        # Pre-condition
        self.assertIsNone(self.scenario._scenario_id)

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=None,
            seed=42
        )

        # Post-condition
        self.assertEqual(self.scenario._run_id, self.run_id)
        self.assertEqual(self.scenario._episode_id, self.episode_id)
        self.assertIsNotNone(self.scenario._scenario_id)
        self.assertEqual(len(self.scenario._cur_scenario), 0)

    def test_init_should_initialize_with_dict_scenario(self):
        """Test that init() correctly processes dict-based scenario."""
        # Pre-condition
        scenario_dict = {
            "test_key": "test_value",
            "nested": {"inner_key": "inner_value"}
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_dict,
            seed=42
        )

        # Post-condition
        self.assertEqual(self.scenario.test_key, "test_value")
        self.assertEqual(self.scenario.nested.inner_key, "inner_value")

    def test_init_should_use_provided_scenario_id(self):
        """Test that init() uses provided scenario_id."""
        # Pre-condition
        custom_id = "custom_scenario_id"

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={},
            scenario_id=custom_id
        )

        # Post-condition
        self.assertEqual(self.scenario._scenario_id, custom_id)

    def test_init_should_set_seed_for_reproducibility(self):
        """Test that init() with same seed produces reproducible results."""
        # Pre-condition
        scenario_config = {"value": "${uniform: 0.0, 1.0}"}
        seed = 42

        # In-test
        scenario1 = Scenario()
        scenario1.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=seed
        )
        value1 = scenario1.value

        scenario2 = Scenario()
        scenario2.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=seed
        )
        value2 = scenario2.value

        # Post-condition
        self.assertEqual(value1, value2)

        # Cleanup
        scenario1._clear_resolvers()
        scenario2._clear_resolvers()

    def test_uniform_distribution_should_resolve_correctly(self):
        """Test that uniform distribution resolver works correctly."""
        # Pre-condition
        scenario_config = {
            "uniform_value": "${uniform: 0.0, 1.0}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        value = self.scenario.uniform_value
        self.assertIsInstance(value, (int, float))
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)

    def test_uniform_distribution_should_handle_size_parameter(self):
        """Test that uniform distribution with size parameter returns list."""
        # Pre-condition
        scenario_config = {
            "uniform_array": "${uniform: 0.0, 1.0, 5}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        value = self.scenario.uniform_array
        # Convert to list if it's a ListConfig
        value_list = list(value) if hasattr(value, '__iter__') else [value]
        self.assertEqual(len(value_list), 5)
        for v in value_list:
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_gaussian_distribution_should_resolve_correctly(self):
        """Test that gaussian distribution resolver works correctly."""
        # Pre-condition
        scenario_config = {
            "gaussian_value": "${gaussian: 0.0, 1.0}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        value = self.scenario.gaussian_value
        self.assertIsInstance(value, (int, float))

    def test_gaussian_distribution_should_handle_size_parameter(self):
        """Test that gaussian distribution with size parameter returns list."""
        # Pre-condition
        scenario_config = {
            "gaussian_array": "${gaussian: 0.0, 1.0, 3}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        value = self.scenario.gaussian_array
        # Convert to list if it's a ListConfig
        value_list = list(value) if hasattr(value, '__iter__') else [value]
        self.assertEqual(len(value_list), 3)

    def test_bernoulli_distribution_should_resolve_correctly(self):
        """Test that bernoulli distribution resolver works correctly."""
        # Pre-condition
        scenario_config = {
            "bernoulli_value": "${bernoulli: 0.5}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        value = self.scenario.bernoulli_value
        self.assertIn(value, [0, 1, True, False])

    def test_reset_should_regenerate_distribution_values(self):
        """Test that reset() regenerates new values from distributions."""
        # Pre-condition
        scenario_config = {
            "random_value": "${uniform: 0.0, 100.0}"
        }
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=None  # No seed for randomness
        )
        _ = self.scenario.random_value  # Access once to populate cache

        # In-test
        self.scenario.reset(episode_id="new_episode")

        # Post-condition
        second_value = self.scenario.random_value
        # Values should be different (statistically very unlikely to be same)
        # Note: There's a tiny chance they could be equal, but extremely unlikely
        self.assertIsInstance(second_value, (int, float))

    def test_getattr_should_access_scenario_values(self):
        """Test that __getattr__ allows attribute-style access."""
        # Pre-condition
        scenario_config = {
            "test_attribute": "test_value"
        }
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        value = self.scenario.test_attribute

        # Post-condition
        self.assertEqual(value, "test_value")

    def test_getattr_should_raise_error_for_missing_attribute(self):
        """Test that __getattr__ raises AttributeError for missing attributes."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test & Post-condition
        with self.assertRaises(AttributeError) as context:
            _ = self.scenario.nonexistent_attribute
        self.assertIn("nonexistent_attribute", str(context.exception))

    def test_getitem_should_access_scenario_values(self):
        """Test that __getitem__ allows dict-style access."""
        # Pre-condition
        scenario_config = {
            "test_key": "test_value"
        }
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        value = self.scenario["test_key"]

        # Post-condition
        self.assertEqual(value, "test_value")

    def test_getitem_should_raise_error_for_missing_key(self):
        """Test that __getitem__ raises KeyError for missing keys."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test & Post-condition
        with self.assertRaises(KeyError) as context:
            _ = self.scenario["nonexistent_key"]
        self.assertIn("nonexistent_key", str(context.exception))

    def test_get_final_size_should_handle_none_size_with_num_env(self):
        """Test _get_final_size with None size and num_env set."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={},
            num_env=4
        )

        # In-test
        result = self.scenario._get_final_size(None)

        # Post-condition
        self.assertEqual(result, 4)

    def test_get_final_size_should_handle_int_size_with_num_env(self):
        """Test _get_final_size with int size and num_env set."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={},
            num_env=4
        )

        # In-test
        result = self.scenario._get_final_size(3)

        # Post-condition
        self.assertEqual(result, (4, 3))

    def test_get_final_size_should_handle_tuple_size_with_num_env(self):
        """Test _get_final_size with tuple size and num_env set."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={},
            num_env=4
        )

        # In-test
        result = self.scenario._get_final_size((2, 3))

        # Post-condition
        self.assertEqual(result, (4, 2, 3))

    def test_get_final_size_should_handle_size_without_num_env(self):
        """Test _get_final_size with size but no num_env."""
        # Pre-condition
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={},
            num_env=None
        )

        # In-test
        result = self.scenario._get_final_size(5)

        # Post-condition
        self.assertEqual(result, 5)

    def test_convert_to_python_should_handle_numpy_scalar(self):
        """Test _convert_to_python with numpy scalar."""
        # Pre-condition
        np_scalar = np.float64(3.14)

        # In-test
        result = Scenario._convert_to_python(np_scalar)

        # Post-condition
        self.assertIsInstance(result, float)
        self.assertEqual(result, 3.14)

    def test_convert_to_python_should_handle_numpy_array(self):
        """Test _convert_to_python with numpy array."""
        # Pre-condition
        np_array = np.array([1, 2, 3])

        # In-test
        result = Scenario._convert_to_python(np_array)

        # Post-condition
        self.assertIsInstance(result, list)
        self.assertEqual(result, [1, 2, 3])

    def test_convert_to_python_should_handle_zero_dim_array(self):
        """Test _convert_to_python with 0-dimensional numpy array."""
        # Pre-condition
        np_zero_dim = np.array(42)

        # In-test
        result = Scenario._convert_to_python(np_zero_dim)

        # Post-condition
        self.assertIsInstance(result, int)
        self.assertEqual(result, 42)

    def test_convert_to_python_should_handle_regular_python_types(self):
        """Test _convert_to_python with regular Python types."""
        # Pre-condition
        regular_values = [42, 3.14, "string", [1, 2, 3], {"key": "value"}]

        # In-test & Post-condition
        for value in regular_values:
            result = Scenario._convert_to_python(value)
            self.assertEqual(result, value)

    def test_get_node_path_should_find_simple_key(self):
        """Test _get_node_path with simple dictionary key."""
        # Pre-condition
        root = {"key1": "target_node", "key2": "other"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test
        path = self.scenario._get_node_path(root, "target_node")

        # Post-condition
        self.assertEqual(path, "key1")

    def test_get_node_path_should_find_nested_key(self):
        """Test _get_node_path with nested dictionary."""
        # Pre-condition
        root = {"level1": {"level2": "target_node"}}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test
        path = self.scenario._get_node_path(root, "target_node")

        # Post-condition
        self.assertEqual(path, "level1.level2")

    def test_get_node_path_should_find_in_list(self):
        """Test _get_node_path with list containing target."""
        # Pre-condition
        root = {"key": ["item1", "target_node", "item3"]}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test
        path = self.scenario._get_node_path(root, "target_node")

        # Post-condition
        self.assertEqual(path, "key[1]")

    def test_get_node_path_should_return_empty_for_missing_node(self):
        """Test _get_node_path returns empty string when node not found."""
        # Pre-condition
        root = {"key": "value"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario={}
        )

        # In-test
        path = self.scenario._get_node_path(root, "nonexistent")

        # Post-condition
        self.assertEqual(path, "")

    def test_template_property_should_return_scenario_template(self):
        """Test that template property returns the scenario template."""
        # Pre-condition
        scenario_config = {"key": "value"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        template = self.scenario.template

        # Post-condition
        self.assertIsNotNone(template)
        self.assertEqual(template.key, "value")

    def test_cur_scenario_property_should_return_current_scenario(self):
        """Test that cur_scenario property returns the current scenario."""
        # Pre-condition
        scenario_config = {"key": "value"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        cur_scenario = self.scenario.cur_scenario

        # Post-condition
        self.assertIsNotNone(cur_scenario)
        self.assertEqual(cur_scenario.key, "value")

    def test_yaml_property_should_return_yaml_representation(self):
        """Test that yaml property returns YAML string."""
        # Pre-condition
        scenario_config = {"key": "value"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        yaml_str = self.scenario.yaml

        # Post-condition
        self.assertIsInstance(yaml_str, str)
        self.assertIn("key:", yaml_str)
        self.assertIn("value", yaml_str)

    def test_finish_should_call_finish_on_metrics(self):
        """Test that finish() calls finish on all metrics."""
        # Pre-condition
        scenario_config = {
            "dist_value": "${uniform: 0.0, 1.0}"
        }
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )
        # Access the value to create the metric
        _ = self.scenario.dist_value

        # In-test
        self.scenario.finish()

        # Post-condition
        # Verify metrics exist and finish was called
        self.assertGreater(len(self.scenario._metrics), 0)

    def test_nested_scenario_access_should_work(self):
        """Test accessing deeply nested scenario values."""
        # Pre-condition
        scenario_config = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config
        )

        # In-test
        value = self.scenario.level1.level2.level3

        # Post-condition
        self.assertEqual(value, "deep_value")

    def test_multiple_distributions_should_work_together(self):
        """Test scenario with multiple different distributions."""
        # Pre-condition
        scenario_config = {
            "uniform_val": "${uniform: 0.0, 1.0}",
            "gaussian_val": "${gaussian: 0.0, 1.0}",
            "bernoulli_val": "${bernoulli: 0.5}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )

        # Post-condition
        self.assertIsInstance(self.scenario.uniform_val, (int, float))
        self.assertIsInstance(self.scenario.gaussian_val, (int, float))
        self.assertIn(self.scenario.bernoulli_val, [0, 1, True, False])

    def test_num_env_should_affect_distribution_size(self):
        """Test that num_env parameter affects distribution output size."""
        # Pre-condition
        scenario_config = {
            "value": "${uniform: 0.0, 1.0}"
        }

        # In-test
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            num_env=3,
            seed=42
        )

        # Post-condition
        value = self.scenario.value
        # Convert to list if it's a ListConfig
        value_list = list(value) if hasattr(value, '__iter__') else [value]
        self.assertEqual(len(value_list), 3)

    def test_clear_resolvers_should_clear_dist_cache(self):
        """Test that _clear_resolvers clears the distribution cache."""
        # Pre-condition
        scenario_config = {"value": "${uniform: 0.0, 1.0}"}
        self.scenario.init(
            run_id=self.run_id,
            episode_id=self.episode_id,
            scenario=scenario_config,
            seed=42
        )
        _ = self.scenario.value  # Trigger cache population

        # In-test
        self.scenario._clear_resolvers()

        # Post-condition
        self.assertEqual(len(Scenario.dist_cache), 0)

    def test_main_script_scenario_should_initialize_with_nested_structure(self):
        """Test scenario initialization matching the __main__ script example."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "scenario_id": "scenario_1",
                "cup_x": "${uniform: 0.7, 1.5}",
                "cup_y": "${uniform: 0.3, 0.7}",
            }
        }

        # In-test
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        # Post-condition
        # Verify scenario structure exists
        self.assertIsNotNone(self.scenario.scenario)
        self.assertEqual(self.scenario.scenario.scenario_id, "scenario_1")

        # Verify cup_x and cup_y are resolved and are lists (due to num_env=2)
        cup_x = self.scenario.scenario.cup_x
        cup_y = self.scenario.scenario.cup_y

        cup_x_list = list(cup_x) if hasattr(cup_x, '__iter__') else [cup_x]
        cup_y_list = list(cup_y) if hasattr(cup_y, '__iter__') else [cup_y]

        self.assertEqual(len(cup_x_list), 2)
        self.assertEqual(len(cup_y_list), 2)

        # Verify values are in expected ranges
        for val in cup_x_list:
            self.assertGreaterEqual(val, 0.7)
            self.assertLessEqual(val, 1.5)

        for val in cup_y_list:
            self.assertGreaterEqual(val, 0.3)
            self.assertLessEqual(val, 0.7)

    def test_main_script_scenario_should_allow_both_access_methods(self):
        """Test that both attribute and dict access work as shown in __main__ script."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "scenario_id": "scenario_1",
                "cup_x": "${uniform: 0.7, 1.5}",
            }
        }

        # In-test
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        # Post-condition
        # Both access methods should return the same value
        cup_x_attr = self.scenario.scenario.cup_x
        cup_x_dict = self.scenario["scenario"].cup_x

        # Convert to lists for comparison
        cup_x_attr_list = list(cup_x_attr) if hasattr(cup_x_attr, '__iter__') else [cup_x_attr]
        cup_x_dict_list = list(cup_x_dict) if hasattr(cup_x_dict, '__iter__') else [cup_x_dict]

        self.assertEqual(cup_x_attr_list, cup_x_dict_list)

    def test_main_script_scenario_should_regenerate_on_reset(self):
        """Test that reset regenerates values as shown in __main__ script."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "cup_x": "${uniform: 0.7, 1.5}",
            }
        }
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=None,  # No seed for random values
            num_env=2
        )

        first_cup_x = self.scenario.scenario.cup_x
        first_list = list(first_cup_x) if hasattr(first_cup_x, '__iter__') else [first_cup_x]

        # In-test
        self.scenario.reset()

        # Post-condition
        second_cup_x = self.scenario.scenario.cup_x
        second_list = list(second_cup_x) if hasattr(second_cup_x, '__iter__') else [second_cup_x]

        # Both should be valid lists
        self.assertEqual(len(first_list), 2)
        self.assertEqual(len(second_list), 2)

        # Values should be in valid range
        for val in second_list:
            self.assertGreaterEqual(val, 0.7)
            self.assertLessEqual(val, 1.5)

    def test_main_script_scenario_should_convert_to_numpy_array(self):
        """Test that scenario values can be converted to numpy arrays."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "cup_x": "${uniform: 0.7, 1.5}",
            }
        }
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        # In-test
        cup_x = self.scenario.scenario.cup_x
        np_array = np.array(cup_x)

        # Post-condition
        self.assertIsInstance(np_array, np.ndarray)
        self.assertEqual(len(np_array), 2)

        # Verify values are in expected range
        for val in np_array:
            self.assertGreaterEqual(val, 0.7)
            self.assertLessEqual(val, 1.5)

    def test_main_script_scenario_should_produce_valid_yaml(self):
        """Test that scenario.yaml returns valid YAML string."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "scenario_id": "scenario_1",
                "cup_x": "${uniform: 0.7, 1.5}",
                "cup_y": "${uniform: 0.3, 0.7}",
            }
        }
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        # In-test
        yaml_str = self.scenario.yaml

        # Post-condition
        self.assertIsInstance(yaml_str, str)
        self.assertIn("scenario:", yaml_str)
        self.assertIn("scenario_id:", yaml_str)
        self.assertIn("scenario_1", yaml_str)
        self.assertIn("cup_x:", yaml_str)
        self.assertIn("cup_y:", yaml_str)

    def test_main_script_scenario_should_handle_multiple_resets(self):
        """Test multiple reset calls as shown in __main__ script."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "cup_x": "${uniform: 0.7, 1.5}",
            }
        }
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        first_values = list(self.scenario.scenario.cup_x)

        # In-test - First reset
        self.scenario.reset()
        second_values = list(self.scenario.scenario.cup_x)

        # In-test - Second reset
        self.scenario.reset()
        third_values = list(self.scenario.scenario.cup_x)

        # Post-condition
        # All should be valid lists of size 2
        self.assertEqual(len(first_values), 2)
        self.assertEqual(len(second_values), 2)
        self.assertEqual(len(third_values), 2)

        # All values should be in range
        for vals in [first_values, second_values, third_values]:
            for val in vals:
                self.assertGreaterEqual(val, 0.7)
                self.assertLessEqual(val, 1.5)

    def test_main_script_scenario_should_reinitialize_with_none(self):
        """Test reinitializing scenario with None as shown in __main__ script."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "cup_x": "${uniform: 0.7, 1.5}",
            }
        }
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )

        # Verify initial scenario has content
        first_yaml = self.scenario.yaml
        self.assertIn("cup_x:", first_yaml)

        # In-test - Reinitialize with None
        self.scenario.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=None,
            seed=42
        )

        # Post-condition
        # Should have an empty scenario
        second_yaml = self.scenario.yaml
        self.assertEqual(second_yaml.strip(), "{}")

    def test_main_script_scenario_should_handle_seed_consistency(self):
        """Test that same seed produces consistent results across resets."""
        # Pre-condition
        scenario_config = {
            "scenario": {
                "cup_x": "${uniform: 0.7, 1.5}",
                "cup_y": "${uniform: 0.3, 0.7}",
            }
        }

        # Create first scenario with seed
        scenario1 = Scenario()
        scenario1.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )
        values1_x = list(scenario1.scenario.cup_x)
        values1_y = list(scenario1.scenario.cup_y)

        # Create second scenario with same seed
        scenario2 = Scenario()
        scenario2.init(
            run_id="run_id",
            episode_id="episode_id",
            scenario=scenario_config,
            seed=42,
            num_env=2
        )
        values2_x = list(scenario2.scenario.cup_x)
        values2_y = list(scenario2.scenario.cup_y)

        # Post-condition
        self.assertEqual(values1_x, values2_x)
        self.assertEqual(values1_y, values2_y)

        # Cleanup
        scenario1._clear_resolvers()
        scenario2._clear_resolvers()


if __name__ == "__main__":
    unittest.main()
