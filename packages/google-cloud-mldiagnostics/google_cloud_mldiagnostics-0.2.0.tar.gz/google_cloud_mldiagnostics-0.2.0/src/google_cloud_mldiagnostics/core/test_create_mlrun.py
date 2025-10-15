"""Unit tests for create_mlrun."""

import datetime
import threading
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import create_mlrun
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import metrics
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import mlrun_types
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import config_utils
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import gcp
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import host_utils
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import metric_utils


class CreateMLRunTest(unittest.TestCase):
  """Test cases for MLRun creation."""

  def setUp(self):
    """Set up test fixtures before each test method."""
    super().setUp()
    self.mock_logging = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core.create_mlrun.logging"
    ).start()
    self.mock_get_software_config = mock.patch.object(
        config_utils, "get_software_config"
    ).start()
    self.mock_get_hardware_config = mock.patch.object(
        config_utils, "get_hardware_config"
    ).start()
    self.mock_get_instance_region = mock.patch.object(
        gcp, "get_instance_region", autospec=True
    ).start()
    self.mock_get_project_id = mock.patch.object(
        gcp, "get_project_id", autospec=True
    ).start()
    self.mock_datetime = mock.patch(
        "datetime.datetime", wraps=datetime.datetime
    ).start()
    self.mock_get_workload_details = mock.patch.object(
        host_utils, "get_workload_details", autospec=True
    ).start()
    self.mock_get_identifier = mock.patch.object(
        host_utils, "get_identifier", autospec=True
    ).start()
    self.mock_get_host_index = mock.patch.object(
        host_utils, "get_host_index", autospec=True
    ).start()
    self.mock_get_global_run_manager = mock.patch.object(
        global_manager, "get_global_run_manager", autospec=True
    ).start()
    self.mock_manager = self.mock_get_global_run_manager.return_value
    self.mock_default_metrics_recorder_cls = mock.patch.object(
        metrics, "MetricsRecorderThread", autospec=True
    ).start()
    self.mock_default_metrics_recorder = (
        self.mock_default_metrics_recorder_cls.return_value
    )

    # Default mock return values
    self.mock_get_software_config.return_value = {"sw_key": "sw_value"}
    self.mock_get_hardware_config.return_value = {"hw_key": "hw_value"}
    self.mock_get_instance_region.return_value = "us-central1"
    self.mock_get_project_id.return_value = "test-project"
    self.mock_datetime.now.return_value = datetime.datetime(
        2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
    )
    self.mock_get_workload_details.return_value = {
        "test_workload_key": "test_workload_value",
        "test_workload_key2": "test_workload_value2",
    }
    self.mock_get_identifier.return_value = "mock-identifier"
    self.mock_get_host_index.return_value = 0
    create_mlrun._METRICS_RECORDER_THREAD_STARTED = False  # pylint: disable=protected-access

  def tearDown(self):
    """Clean up mocks after each test method."""
    super().tearDown()
    mock.patch.stopall()

  def test_initialize_mlrun_minimal(self):
    """Test initialize_mlrun with minimal arguments."""
    ml_run = create_mlrun.initialize_mlrun(run_group="test_run_group")

    self.assertEqual(ml_run.run_group, "test_run_group")
    self.assertEqual(
        ml_run.name, "mock-identifier"
    )
    self.assertEqual(
        ml_run.configs,
        {
            "softwareConfigs": {"sw_key": "sw_value"},
            "hardwareConfigs": {"hw_key": "hw_value"},
            "userConfigs": {},
        },
    )
    self.assertIsNone(ml_run.gcs_path)
    self.assertEqual(ml_run.location, "us-central1")
    self.assertEqual(ml_run.project, "test-project")
    self.assertEqual(ml_run.run_phase, mlrun_types.RunPhase.PHASE_ACTIVE)
    self.assertEqual(ml_run.created_at, "2025-01-01T00:00:00+00:00")
    self.assertEqual(
        ml_run.workload_details,
        {
            "test_workload_key": "test_workload_value",
            "test_workload_key2": "test_workload_value2",
        },
    )

    self.mock_get_software_config.assert_called_once()
    self.mock_get_hardware_config.assert_called_once()
    self.mock_get_instance_region.assert_called_once()
    self.mock_get_project_id.assert_called_once()
    self.mock_get_identifier.assert_called_once_with(
        self.mock_get_workload_details.return_value
    )
    self.mock_get_workload_details.assert_called_once()
    self.mock_manager.initialize.assert_called_once_with(ml_run)

    self.mock_default_metrics_recorder_cls.assert_called_once_with(
        metric_collectors=[
            ("tpu_duty_cycle", metric_utils.get_tpu_duty_cycle),
            (
                "tpu_tensorcore_utilization",
                metric_utils.get_tpu_tensorcore_utilization,
            ),
            ("hbm_utilization", metric_utils.get_hbm_utilization),
            ("host_cpu_utilization", metric_utils.get_host_cpu_utilization),
            (
                "host_memory_utilization",
                metric_utils.get_host_memory_utilization,
            ),
        ],
        interval_seconds=10.0,
        labels={"hostname": "host0"},
    )
    self.mock_default_metrics_recorder.start.assert_called_once()

    expected_diagon_url = "https://console.cloud.google.com/cluster-director/diagnostics/details/us-central1/mock-identifier?project=test-project"
    expected_xprof_url = (
        expected_diagon_url 
        + "&pageState=(%22nav%22:(%22section%22:%22profiles%22))"
    )
    self.mock_logging.info.assert_any_call(
        "Diagon SDK is in experimental mode, "
        "to visualize the run, please go to\n"
        "%s\n",
        expected_diagon_url,
    )
    self.mock_logging.info.assert_any_call(
        "Xprof profiling url:\n%s\n",
        expected_xprof_url,
    )

  def test_initialize_mlrun_all_args(self):
    """Test initialize_mlrun with all arguments provided."""
    user_configs = {"user_key": "user_value", "default_key": "user_override"}
    ml_run = create_mlrun.initialize_mlrun(
        run_group="test_run_group",
        name="test_run_name",
        configs=user_configs,
        gcs_path="gs://test-bucket/path",
        gcp_project="provided-project",
        gcp_region="us-west1",
        metrics_record_interval_sec=5.0,
    )

    self.assertEqual(ml_run.run_group, "test_run_group")
    self.assertEqual(ml_run.name, "test_run_name")
    self.assertEqual(
        ml_run.configs,
        {
            "softwareConfigs": {"sw_key": "sw_value"},
            "hardwareConfigs": {"hw_key": "hw_value"},
            "userConfigs": {
                "user_key": "user_value",
                "default_key": "user_override",
            },
        },
    )
    self.assertEqual(ml_run.gcs_path, "gs://test-bucket/path")
    self.assertEqual(ml_run.location, "us-west1")
    self.assertEqual(ml_run.project, "provided-project")
    self.assertEqual(ml_run.run_phase, mlrun_types.RunPhase.PHASE_ACTIVE)
    self.assertEqual(ml_run.created_at, "2025-01-01T00:00:00+00:00")
    self.assertEqual(
        ml_run.workload_details,
        {
            "test_workload_key": "test_workload_value",
            "test_workload_key2": "test_workload_value2",
        },
    )

    self.mock_get_software_config.assert_called_once()
    self.mock_get_hardware_config.assert_called_once()
    self.mock_get_instance_region.assert_not_called()
    self.mock_get_project_id.assert_not_called()
    self.mock_get_identifier.assert_not_called()
    self.mock_get_workload_details.assert_called_once()
    self.mock_manager.initialize.assert_called_once_with(ml_run)

    self.mock_default_metrics_recorder_cls.assert_called_once_with(
        metric_collectors=[
            ("tpu_duty_cycle", metric_utils.get_tpu_duty_cycle),
            (
                "tpu_tensorcore_utilization",
                metric_utils.get_tpu_tensorcore_utilization,
            ),
            ("hbm_utilization", metric_utils.get_hbm_utilization),
            ("host_cpu_utilization", metric_utils.get_host_cpu_utilization),
            (
                "host_memory_utilization",
                metric_utils.get_host_memory_utilization,
            ),
        ],
        labels={"hostname": "host0"},
        interval_seconds=5.0,
    )
    self.mock_default_metrics_recorder.start.assert_called_once()

    expected_diagon_url = "https://console.cloud.google.com/cluster-director/diagnostics/details/us-west1/test_run_name?project=provided-project"
    expected_xprof_url = (
        expected_diagon_url
        + "&pageState=(%22nav%22:(%22section%22:%22profiles%22))"
    )
    self.mock_logging.info.assert_any_call(
        "Diagon SDK is in experimental mode, "
        "to visualize the run, please go to\n"
        "%s\n",
        expected_diagon_url,
    )
    self.mock_logging.info.assert_any_call(
        "Xprof profiling url:\n%s\n",
        expected_xprof_url,
    )

  def test_create_diagnostics_url(self):
    """Test create_diagnostics_url generates the correct URL."""
    url = create_mlrun.create_diagnostics_url(
        "us-central1", "test-project", "test-run"
    )
    expected_url = "https://console.cloud.google.com/cluster-director/diagnostics/details/us-central1/test-run?project=test-project"
    self.assertEqual(url, expected_url)

  def test_create_xprof_url(self):
    """Test create_xprof_url generates the correct URL."""
    diagon_url = "diagon_url"
    url = create_mlrun.create_xprof_url(diagon_url)
    expected_url = "diagon_url&pageState=(%22nav%22:(%22section%22:%22profiles%22))"
    self.assertEqual(url, expected_url)

  def test_initialize_mlrun_starts_metrics_recorder_only_once_thread_safe(self):
    """Test initialize_mlrun starts metrics recorder only once against thread racing."""
    thread_count = 5
    threads = []

    def target():
      create_mlrun.initialize_mlrun(run_group="test-group", name="test-run")

    for _ in range(thread_count):
      thread = threading.Thread(target=target)
      threads.append(thread)
      thread.start()

    for thread in threads:
      thread.join()

    # Verify MetricsRecorderThread was started only once
    self.mock_default_metrics_recorder_cls.assert_called_once()
    self.mock_default_metrics_recorder_cls.return_value.start.assert_called_once()
    self.assertEqual(self.mock_manager.initialize.call_count, thread_count)


if __name__ == "__main__":
  unittest.main()
