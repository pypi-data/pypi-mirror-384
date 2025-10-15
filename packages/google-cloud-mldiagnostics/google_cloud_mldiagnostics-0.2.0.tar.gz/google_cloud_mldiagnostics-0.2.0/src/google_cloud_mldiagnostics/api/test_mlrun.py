"""Unit tests for the machinelearning_run module."""

import json
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.api import mlrun as api_mlrun
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import exceptions


class TestMachineLearningRun(unittest.TestCase):
  """Test cases for the machinelearning_run function."""

  def setUp(self):
    """Set up test fixtures before each test method."""
    super().setUp()
    self.valid_run_group = "test_run_group"
    self.valid_name = "test_run_name"
    self.valid_configs = {"epochs": 100, "batch_size": 32}
    self.valid_gcs_path = "gs://test-bucket/path"
    self.mock_create_mlrun = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core.create_mlrun.initialize_mlrun"
    ).start()

  def tearDown(self):
    """Clean up after each test method."""
    mock.patch.stopall()
    super().tearDown()

  def test_machinelearning_run_with_all_parameters(self):
    """Test creating ML run with all parameters provided."""
    api_mlrun.machinelearning_run(
        run_group=self.valid_run_group,
        name=self.valid_name,
        configs=self.valid_configs,
        gcs_path=self.valid_gcs_path
    )

    self.mock_create_mlrun.assert_called_once_with(
        run_group=self.valid_run_group,
        name=self.valid_name,
        configs=self.valid_configs,
        gcs_path=self.valid_gcs_path,
        gcp_project=None,
        gcp_region=None,
        metrics_record_interval_sec=10.0,
    )

  def test_machinelearning_run_none_run_group_raises_error(self):
    """Test that None run_group raises MLRunConfigurationError."""
    with self.assertRaises(exceptions.MLRunConfigurationError) as context:
      api_mlrun.machinelearning_run(run_group=None)

    self.assertIn(
        "run_group is required and must be provided. The run_group parameter"
        " helps identify and organize your ML workloads. Please provide a"
        " meaningful run_group name (e.g., 'training_v1',"
        " 'experiment_batch_1').",
        str(context.exception),
    )
    self.assertIn("identify and organize", str(context.exception))

  def test_yaml_json_workflow_configs(self):
    """Test ML run creation with configs loaded from a JSON representation of YAML."""
    self.valid_run_group = "test_run_group"
    self.valid_name = "test_run_name"
    self.valid_configs = {"epochs": 100, "batch_size": 32}
    self.valid_gcs_path = "gs://test-bucket/path"

    # Simulate YAML data that was loaded and converted to JSON
    yaml_data = {
        "epochs": 200,
        "batch_size": 64,
        "learning_rate": 0.001,
        "model_type": "transformer"
    }
    json_data = json.dumps(yaml_data)

    api_mlrun.machinelearning_run(
        run_group=self.valid_run_group,
        name=self.valid_name,
        configs=json.loads(json_data),  # Parse JSON back to dict for this test
        gcs_path=self.valid_gcs_path
    )

    self.mock_create_mlrun.assert_called_once_with(
        run_group=self.valid_run_group,
        name=self.valid_name,
        configs=yaml_data,  # Verify that the YAML data was correctly converted
        gcs_path=self.valid_gcs_path,
        gcp_project=None,
        gcp_region=None,
        metrics_record_interval_sec=10.0,
    )

if __name__ == "__main__":
  unittest.main()
