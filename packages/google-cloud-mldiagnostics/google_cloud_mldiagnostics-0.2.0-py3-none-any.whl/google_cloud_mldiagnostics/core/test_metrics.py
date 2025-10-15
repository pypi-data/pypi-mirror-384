"""Unit tests for the metrics module."""

import threading
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import metrics
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import exceptions


# pylint: disable=protected-access
class TestMetricsRecorder(unittest.TestCase):
  """Test cases for _MetricsRecorder class."""

  def setUp(self):
    """Set up test fixtures before each test method."""
    super().setUp()
    self.recorder = metrics.metrics_recorder

    self.mock_control_plane_client_class = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.clients.control_plane_client.ControlPlaneClient"
    ).start()
    self.mock_logging_client_class = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.clients.logging_client.LoggingClient"
    ).start()
    self.mock_is_master_host = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.host_utils.is_master_host"
    ).start()
    self.mock_is_master_host.return_value = True

    self.mock_control_plane_client = (
        self.mock_control_plane_client_class.return_value
    )
    self.mock_logging_client = self.mock_logging_client_class.return_value

    self.mock_mlrun = mock.Mock()
    self.mock_mlrun.project = "test-project"
    self.mock_mlrun.name = "test-run-id"
    self.mock_mlrun.location = "us-central1"
    self.mock_mlrun.run_group = "test-run-set"
    global_manager.initialize_with_mlrun(self.mock_mlrun)

  def tearDown(self):
    """Clean up after each test method."""
    global_manager.get_global_run_manager().clear()
    self.recorder._metric_tracker.clear()
    mock.patch.stopall()
    super().tearDown()

  def test_get_active_run_and_client_success(self):
    """Test successful retrieval of active run and client."""
    ml_run, client = self.recorder._get_active_run_and_client()

    # Assertions
    self.assertEqual(ml_run, self.mock_mlrun)
    self.assertEqual(client, self.mock_logging_client)
    self.mock_logging_client_class.assert_called_with(
        project_id=self.mock_mlrun.project
    )

  def test_record_success_all_params(self):
    """Test successful recording with all parameters."""
    custom_labels = {"experiment": "test", "model": "v1"}
    self.recorder.record(
        metric_name="test_metric",
        value=100,
        step=5,
        labels=custom_labels,
    )

    self.mock_logging_client.write_metric.assert_called_once()
    self.mock_logging_client.write_metric.assert_called_with(
        metric_name="test_metric",
        value=100,
        run_id="test-run-id",
        location="us-central1",
        step=5,
        labels=custom_labels,
    )

  def test_record_non_master_host(self):
    """Test recording on non-master host should not write metrics."""
    self.mock_is_master_host.return_value = False
    # Call record method with all parameters
    custom_labels = {"experiment": "test", "model": "v1"}
    with mock.patch.object(metrics.logger, "info"):
      self.recorder.record(
          metric_name="test_metric",
          value=100,
          step=5,
          labels=custom_labels,
      )

    # Verify that no metrics were written
    self.mock_logging_client.write_metric.assert_not_called()

  def test_record_non_master_host_record_on_all_hosts(self):
    """Test recording on non-master host with record_on_all_hosts=True."""
    self.mock_is_master_host.return_value = False

    # Create a mock metric type
    mock_metric_name = "test_metric"

    # Call record method with all parameters
    custom_labels = {"experiment": "test", "model": "v1"}
    self.recorder.record(
        metric_name=mock_metric_name,
        value=100,
        step=5,
        labels=custom_labels,
        record_on_all_hosts=True,
    )
    custom_labels.update({
        "run_group": "test-run-set",
        "run_name": "test-run-id",
        "step": "5",
    })

    # Verify write_metric was called correctly because record_on_all_hosts=True
    self.mock_logging_client.write_metric.assert_has_calls(
        [
            mock.call(
                metric_name="test_metric",
                value=100.0,
                run_id="test-run-id",
                location="us-central1",
                step=5,
                labels=custom_labels,
            ),
        ],
        any_order=True,
    )

  def test_record_exception_handling(self):
    """Test exception handling for errors."""
    self.mock_logging_client.write_metric.side_effect = Exception(
        "Failed to write metric"
    )
    with self.assertRaises(exceptions.RecordingError) as context:
      self.recorder.record(metric_name="test_metric", value=100, step=5)
    self.assertIn("Failed to write metric", str(context.exception))
    self.assertIn("Error recording metric", str(context.exception))

  def test_record_none_value(self):
    """Test recording with None value."""
    self.recorder.record(
        metric_name="test_metric",
        value=None,
    )
    self.mock_logging_client.write_metric.assert_not_called()

  def test_metric_tracker(self):
    """Test metric tracker."""
    self.recorder.record(metric_name="step_time", value=10)
    self.assertEqual(
        self.recorder._metric_tracker["step_time"],
        {"num_records": 1, "avg": 10.0},
    )
    self.recorder.record(metric_name="step_time", value=20)
    self.assertEqual(
        self.recorder._metric_tracker["step_time"],
        {"num_records": 2, "avg": 15.0},
    )
    self.recorder.record(metric_name="mfu", value=100)
    self.assertEqual(
        self.recorder._metric_tracker["mfu"],
        {"num_records": 1, "avg": 100.0},
    )
    self.recorder.record(metric_name="mfu", value=200)
    self.assertEqual(
        self.recorder._metric_tracker["mfu"],
        {"num_records": 2, "avg": 150.0},
    )
    self.recorder.record(metric_name="throughput", value=50)
    self.assertEqual(
        self.recorder._metric_tracker["throughput"],
        {"num_records": 1, "avg": 50.0},
    )
    self.recorder.record(metric_name="throughput", value=250)
    self.assertEqual(
        self.recorder._metric_tracker["mfu"],
        {"num_records": 2, "avg": 150.0},
    )
    self.recorder.record(metric_name="latency", value=20.0)
    self.assertEqual(
        self.recorder._metric_tracker["latency"],
        {"num_records": 1, "avg": 20.0},
    )
    self.recorder.record(metric_name="latency", value=20.0)
    self.assertEqual(
        self.recorder._metric_tracker["latency"],
        {"num_records": 2, "avg": 20.0},
    )
    # test_metric is not in _track_list and should not be tracked.
    self.recorder.record(metric_name="test_metric", value=[100, 200])
    self.assertNotIn("test_metric", self.recorder._metric_tracker)


# pylint: disable=protected-access
class TestMetricsRecorderThread(unittest.TestCase):
  """Test cases for MetricsRecorderThread class."""

  def setUp(self):
    super().setUp()
    self.mock_collector1 = mock.Mock(return_value=1.0)
    self.mock_collector2 = mock.Mock(return_value=2.0)
    self.metric_collectors = [
        ("metric1", self.mock_collector1),
        ("metric2", self.mock_collector2),
    ]
    self.mock_record = mock.patch.object(
        metrics.metrics_recorder, "record"
    ).start()
    self.mock_logger = mock.patch.object(metrics, "logger").start()

  def tearDown(self):
    mock.patch.stopall()
    super().tearDown()

  def test_collect_and_record_success(self):
    """Test successful collection and recording of metrics."""
    recorder = metrics.MetricsRecorderThread(
        metric_collectors=self.metric_collectors,
        interval_seconds=10.0,
        labels={"experiment": "test"}
    )
    recorder._collect_and_record()
    self.mock_collector1.assert_called_once()
    self.mock_collector2.assert_called_once()
    self.mock_record.assert_has_calls([
        mock.call(
            metric_name="metric1",
            value=1.0,
            labels={"experiment": "test"},
            record_on_all_hosts=True,
        ),
        mock.call(
            metric_name="metric2",
            value=2.0,
            labels={"experiment": "test"},
            record_on_all_hosts=True,
        ),
    ])

  def test_collect_and_record_collector_exception(self):
    """Test exception handling in metric collector."""
    self.mock_collector1.side_effect = Exception("Collector failed")
    recorder = metrics.MetricsRecorderThread(
        metric_collectors=self.metric_collectors,
        interval_seconds=10.0,
        labels={"experiment": "test"}
    )
    recorder._collect_and_record()
    self.mock_collector1.assert_called_once()
    self.mock_collector2.assert_called_once()
    self.mock_record.assert_called_once_with(
        metric_name="metric2",
        value=2.0,
        labels={"experiment": "test"},
        record_on_all_hosts=True,
    )
    self.mock_logger.error.assert_called_once_with(
        "Failed to collect or record metric '%s': %s",
        "metric1",
        mock.ANY,
    )
    call_args, _ = self.mock_logger.error.call_args
    self.assertEqual(call_args[1], "metric1")
    self.assertIsInstance(call_args[2], Exception)
    self.assertIn("Collector failed", str(call_args[2]))

  def test_collect_and_record_record_exception(self):
    """Test exception handling in metrics recorder."""
    self.mock_record.side_effect = [None, Exception("Record failed")]
    recorder = metrics.MetricsRecorderThread(
        metric_collectors=self.metric_collectors,
        interval_seconds=10.0,
        labels={"experiment": "test"}
    )
    recorder._collect_and_record()  # pylint: disable=protected-access
    self.mock_collector1.assert_called_once()
    self.mock_collector2.assert_called_once()
    self.mock_record.assert_has_calls([
        mock.call(
            metric_name="metric1",
            value=1.0,
            labels={"experiment": "test"},
            record_on_all_hosts=True,
        ),
        mock.call(
            metric_name="metric2",
            value=2.0,
            labels={"experiment": "test"},
            record_on_all_hosts=True,
        ),
    ])
    self.mock_logger.error.assert_called_once_with(
        "Failed to collect or record metric '%s': %s",
        "metric2",
        mock.ANY,
    )
    call_args, _ = self.mock_logger.error.call_args
    self.assertEqual(call_args[1], "metric2")
    self.assertIsInstance(call_args[2], Exception)
    self.assertIn("Record failed", str(call_args[2]))

  def test_start_stop(self):
    """Tests that start begins collection and stop ends it."""
    collected = threading.Event()

    def record_side_effect(
        metric_name, value, **kwargs
    ):
      if metric_name == "metric2":
        collected.set()

    self.mock_record.side_effect = record_side_effect

    recorder = metrics.MetricsRecorderThread(
        metric_collectors=self.metric_collectors,
        interval_seconds=1.0,
        labels={"experiment": "test"},
    )
    with mock.patch.object(
        recorder, "_update_avg_metrics"
    ) as mock_update_avg_metrics:
      recorder.start()
      self.assertIsNotNone(recorder._thread)
      self.assertTrue(recorder._thread.is_alive())

      self.assertTrue(
          collected.wait(timeout=5), "Metric collection did not run"
      )

      recorder.stop()
      self.assertIsNone(recorder._thread)

      self.mock_collector1.assert_called()
      self.mock_collector2.assert_called()
      self.mock_record.assert_called_with(
          metric_name="metric2",
          value=2.0,
          labels={"experiment": "test"},
          record_on_all_hosts=True,
      )
      mock_update_avg_metrics.assert_called()
      metric_names = [item[0] for item in self.metric_collectors]
      self.mock_logger.info.assert_has_calls([
          mock.call(
              "Started collecting metrics (%s) with interval %d seconds.",
              ", ".join(metric_names),
              1.0,
          ),
          mock.call(
              "Stopped metrics (%s) collection.",
              ", ".join(metric_names),
          ),
      ])

  def test_start_already_running(self):
    """Tests that calling start() when already running does nothing."""
    recorder = metrics.MetricsRecorderThread(
        self.metric_collectors,
        interval_seconds=1.0,
    )
    recorder.start()
    thread1 = recorder._thread
    recorder.start()  # second call
    self.assertIs(recorder._thread, thread1)
    self.mock_logger.warning.assert_called_with(
        "Metrics collection thread is already running."
    )
    recorder.stop()

  def test_stop_not_running(self):
    """Tests that calling stop() when not running does nothing."""
    recorder = metrics.MetricsRecorderThread(
        self.metric_collectors,
        interval_seconds=1,)
    recorder.stop()  # stop without start
    self.assertIsNone(recorder._thread)


if __name__ == "__main__":
  unittest.main()
