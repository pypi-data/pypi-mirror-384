import unittest
from unittest.mock import patch, MagicMock, Mock
import uuid

from humalab import humalab
from humalab.run import Run
from humalab.scenario import Scenario
from humalab.humalab_config import HumalabConfig
from humalab.humalab_api_client import HumaLabApiClient
from humalab.constants import EpisodeStatus


class HumalabTest(unittest.TestCase):
    """Unit tests for humalab module functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset the global _cur_run before each test
        humalab._cur_run = None

    def tearDown(self):
        """Clean up after each test method."""
        # Reset the global _cur_run after each test
        humalab._cur_run = None

    # Tests for _pull_scenario

    def test_pull_scenario_should_return_scenario_when_no_scenario_id(self):
        """Test that _pull_scenario returns scenario when scenario_id is None."""
        # Pre-condition
        client = Mock()
        scenario = {"key": "value"}

        # In-test
        result = humalab._pull_scenario(client=client, scenario=scenario, scenario_id=None)

        # Post-condition
        self.assertEqual(result, scenario)
        client.get_scenario.assert_not_called()

    def test_pull_scenario_should_fetch_scenario_from_client_when_scenario_id_provided(self):
        """Test that _pull_scenario fetches from API when scenario_id is provided."""
        # Pre-condition
        client = Mock()
        scenario_id = "test-scenario-id"
        yaml_content = "scenario: test"
        client.get_scenario.return_value = {"yaml_content": yaml_content}

        # In-test
        result = humalab._pull_scenario(client=client, scenario=None, scenario_id=scenario_id)

        # Post-condition
        self.assertEqual(result, yaml_content)
        client.get_scenario.assert_called_once_with(uuid=scenario_id)

    def test_pull_scenario_should_prefer_scenario_id_over_scenario(self):
        """Test that _pull_scenario uses scenario_id even when scenario is provided."""
        # Pre-condition
        client = Mock()
        scenario = {"key": "value"}
        scenario_id = "test-scenario-id"
        yaml_content = "scenario: from_api"
        client.get_scenario.return_value = {"yaml_content": yaml_content}

        # In-test
        result = humalab._pull_scenario(client=client, scenario=scenario, scenario_id=scenario_id)

        # Post-condition
        self.assertEqual(result, yaml_content)
        client.get_scenario.assert_called_once_with(uuid=scenario_id)

    # Tests for init context manager

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_create_run_with_provided_parameters(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() creates a Run with provided parameters."""
        # Pre-condition
        entity = "test_entity"
        project = "test_project"
        name = "test_name"
        description = "test_description"
        run_id = "test_id"
        tags = ["tag1", "tag2"]
        scenario_data = {"key": "value"}

        mock_config = Mock()
        mock_config.entity = "default_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init(
            entity=entity,
            project=project,
            name=name,
            description=description,
            id=run_id,
            tags=tags,
            scenario=scenario_data
        ) as run:
            # Post-condition
            self.assertEqual(run, mock_run_inst)
            mock_run_class.assert_called_once()
            call_kwargs = mock_run_class.call_args.kwargs
            self.assertEqual(call_kwargs['entity'], entity)
            self.assertEqual(call_kwargs['project'], project)
            self.assertEqual(call_kwargs['name'], name)
            self.assertEqual(call_kwargs['description'], description)
            self.assertEqual(call_kwargs['id'], run_id)
            self.assertEqual(call_kwargs['tags'], tags)
            self.assertEqual(call_kwargs['scenario'], mock_scenario_inst)

        # Verify finish was called
        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_use_config_defaults_when_parameters_not_provided(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() uses config defaults when parameters are not provided."""
        # Pre-condition
        mock_config = Mock()
        mock_config.entity = "config_entity"
        mock_config.base_url = "http://config:8000"
        mock_config.api_key = "config_key"
        mock_config.timeout = 60.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init() as run:
            # Post-condition
            call_kwargs = mock_run_class.call_args.kwargs
            self.assertEqual(call_kwargs['entity'], "config_entity")
            self.assertEqual(call_kwargs['project'], "default")
            self.assertEqual(call_kwargs['name'], "")
            self.assertEqual(call_kwargs['description'], "")
            self.assertIsNotNone(call_kwargs['id'])  # UUID generated
            self.assertIsNone(call_kwargs['tags'])

        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_generate_uuid_when_id_not_provided(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() generates a UUID when id is not provided."""
        # Pre-condition
        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init() as run:
            # Post-condition
            call_kwargs = mock_run_class.call_args.kwargs
            run_id = call_kwargs['id']
            # Verify it's a valid UUID
            uuid.UUID(run_id)  # Will raise ValueError if not valid

        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_initialize_scenario_with_seed(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() initializes scenario with provided seed."""
        # Pre-condition
        seed = 42
        scenario_data = {"key": "value"}

        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init(scenario=scenario_data, seed=seed) as run:
            # Post-condition
            mock_scenario_inst.init.assert_called_once()
            call_kwargs = mock_scenario_inst.init.call_args.kwargs
            self.assertEqual(call_kwargs['seed'], seed)
            self.assertEqual(call_kwargs['scenario'], scenario_data)

        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_pull_scenario_from_api_when_scenario_id_provided(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() pulls scenario from API when scenario_id is provided."""
        # Pre-condition
        scenario_id = "test-scenario-id"
        yaml_content = "scenario: from_api"

        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client.get_scenario.return_value = {"yaml_content": yaml_content}
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init(scenario_id=scenario_id) as run:
            # Post-condition
            mock_api_client.get_scenario.assert_called_once_with(uuid=scenario_id)
            mock_scenario_inst.init.assert_called_once()
            call_kwargs = mock_scenario_inst.init.call_args.kwargs
            self.assertEqual(call_kwargs['scenario'], yaml_content)

        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_set_global_cur_run(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() sets the global _cur_run variable."""
        # Pre-condition
        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        self.assertIsNone(humalab._cur_run)
        with humalab.init() as run:
            # Post-condition
            self.assertEqual(humalab._cur_run, mock_run_inst)

        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_call_finish_on_exception(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() calls finish even when exception occurs in context."""
        # Pre-condition
        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "test_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test & Post-condition
        with self.assertRaises(RuntimeError):
            with humalab.init() as run:
                raise RuntimeError("Test exception")

        # Verify finish was still called
        mock_run_inst.finish.assert_called_once()

    @patch('humalab.humalab.HumaLabApiClient')
    @patch('humalab.humalab.HumalabConfig')
    @patch('humalab.humalab.Scenario')
    @patch('humalab.humalab.Run')
    def test_init_should_create_api_client_with_custom_parameters(self, mock_run_class, mock_scenario_class, mock_config_class, mock_api_client_class):
        """Test that init() creates API client with custom base_url, api_key, and timeout."""
        # Pre-condition
        base_url = "http://custom:9000"
        api_key = "custom_key"
        timeout = 120.0

        mock_config = Mock()
        mock_config.entity = "test_entity"
        mock_config.base_url = "http://localhost:8000"
        mock_config.api_key = "default_key"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        mock_api_client = Mock()
        mock_api_client_class.return_value = mock_api_client

        mock_scenario_inst = Mock()
        mock_scenario_class.return_value = mock_scenario_inst

        mock_run_inst = Mock()
        mock_run_class.return_value = mock_run_inst

        # In-test
        with humalab.init(base_url=base_url, api_key=api_key, timeout=timeout) as run:
            # Post-condition
            mock_api_client_class.assert_called_once_with(
                base_url=base_url,
                api_key=api_key,
                timeout=timeout
            )

        mock_run_inst.finish.assert_called_once()

    # Tests for finish function

    def test_finish_should_call_finish_on_current_run_with_default_status(self):
        """Test that finish() calls finish on the current run with default status."""
        # Pre-condition
        mock_run = Mock()
        humalab._cur_run = mock_run

        # In-test
        humalab.finish()

        # Post-condition
        mock_run.finish.assert_called_once_with(status=EpisodeStatus.PASS, quiet=None)

    def test_finish_should_call_finish_on_current_run_with_custom_status(self):
        """Test that finish() calls finish on the current run with custom status."""
        # Pre-condition
        mock_run = Mock()
        humalab._cur_run = mock_run
        status = EpisodeStatus.FAILED

        # In-test
        humalab.finish(status=status)

        # Post-condition
        mock_run.finish.assert_called_once_with(status=status, quiet=None)

    def test_finish_should_call_finish_on_current_run_with_quiet_parameter(self):
        """Test that finish() calls finish on the current run with quiet parameter."""
        # Pre-condition
        mock_run = Mock()
        humalab._cur_run = mock_run
        quiet = True

        # In-test
        humalab.finish(quiet=quiet)

        # Post-condition
        mock_run.finish.assert_called_once_with(status=EpisodeStatus.PASS, quiet=quiet)

    def test_finish_should_do_nothing_when_no_current_run(self):
        """Test that finish() does nothing when _cur_run is None."""
        # Pre-condition
        humalab._cur_run = None

        # In-test
        humalab.finish()  # Should not raise any exception

        # Post-condition
        # No exception means success
        self.assertIsNone(humalab._cur_run)

    # Tests for login function

    @patch('humalab.humalab.HumalabConfig')
    def test_login_should_set_api_key_when_provided(self, mock_config_class):
        """Test that login() sets the api_key when provided."""
        # Pre-condition
        mock_config = Mock()
        mock_config.api_key = "old_key"
        mock_config.base_url = "http://localhost:8000"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        new_key = "new_api_key"

        # In-test
        result = humalab.login(api_key=new_key)

        # Post-condition
        self.assertTrue(result)
        self.assertEqual(mock_config.api_key, new_key)

    @patch('humalab.humalab.HumalabConfig')
    def test_login_should_keep_existing_key_when_not_provided(self, mock_config_class):
        """Test that login() keeps existing api_key when key is not provided."""
        # Pre-condition
        existing_key = "existing_key"
        existing_url = "http://localhost:8000"
        existing_timeout = 30.0
        mock_config = Mock()
        mock_config.api_key = existing_key
        mock_config.base_url = existing_url
        mock_config.timeout = existing_timeout
        mock_config_class.return_value = mock_config

        # In-test
        result = humalab.login()

        # Post-condition
        self.assertTrue(result)
        self.assertEqual(mock_config.api_key, existing_key)
        self.assertEqual(mock_config.base_url, existing_url)
        self.assertEqual(mock_config.timeout, existing_timeout)

    @patch('humalab.humalab.HumalabConfig')
    def test_login_should_return_true(self, mock_config_class):
        """Test that login() always returns True."""
        # Pre-condition
        mock_config = Mock()
        mock_config.api_key = "test_key"
        mock_config.base_url = "http://localhost:8000"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        # In-test
        result = humalab.login()

        # Post-condition
        self.assertTrue(result)

    @patch('humalab.humalab.HumalabConfig')
    def test_login_should_accept_optional_parameters(self, mock_config_class):
        """Test that login() accepts optional parameters without errors."""
        # Pre-condition
        mock_config = Mock()
        mock_config.api_key = "old_key"
        mock_config.base_url = "http://old:8000"
        mock_config.timeout = 30.0
        mock_config_class.return_value = mock_config

        # In-test
        result = humalab.login(
            api_key="test_key",
            relogin=True,
            host="http://localhost:8000",
            force=True,
            timeout=60.0
        )

        # Post-condition
        self.assertTrue(result)
        self.assertEqual(mock_config.api_key, "test_key")
        self.assertEqual(mock_config.base_url, "http://localhost:8000")
        self.assertEqual(mock_config.timeout, 60.0)


if __name__ == "__main__":
    unittest.main()
