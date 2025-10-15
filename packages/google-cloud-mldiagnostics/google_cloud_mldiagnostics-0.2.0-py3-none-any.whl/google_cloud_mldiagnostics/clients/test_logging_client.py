"""Unit tests for LoggingClient."""

import datetime
from unittest.mock import Mock, patch
from google.auth import credentials
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.clients import logging_client
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import exceptions
import pytest


class TestLoggingClientInitialization:
  """Test LoggingClient initialization scenarios."""

  def setup_method(self):
    """Set up test fixtures."""
    self.mock_logging_client_cls = patch("google.cloud.logging.Client").start()
    self.mock_client_instance = Mock()
    self.mock_logger_instance = Mock()
    self.mock_client_instance.logger.return_value = self.mock_logger_instance
    self.mock_logging_client_cls.return_value = self.mock_client_instance

  def teardown_method(self):
    """Tear down test fixtures."""
    patch.stopall()

  def test_init_with_default_credentials(self):
    """Test initialization with default credentials."""
    client = logging_client.LoggingClient(
        project_id="test-project", log_name="test-log"
    )

    assert client.project_id == "test-project"
    assert client.log_name == "test-log"
    self.mock_logging_client_cls.assert_called_once_with(project="test-project")
    self.mock_client_instance.logger.assert_called_once_with("test-log")
    assert client.logger == self.mock_logger_instance

  def test_init_with_user_credentials(self):
    """Test initialization with explicit user credentials."""
    mock_credentials = Mock(spec=credentials.Credentials)

    logging_client.LoggingClient(
        project_id="test-project", user_credentials=mock_credentials
    )

    self.mock_logging_client_cls.assert_called_once_with(
        project="test-project", credentials=mock_credentials
    )

  def test_init_with_default_log_name(self):
    """Test initialization with default log name."""
    client = logging_client.LoggingClient(project_id="test-project")

    assert client.log_name == "ml_diagnostics_metric"
    self.mock_client_instance.logger.assert_called_once_with(
        "ml_diagnostics_metric"
    )

  def test_init_failure_raises_mldiagnostic_error(self):
    """Test that initialization failure raises MLDiagnosticError."""
    self.mock_logging_client_cls.side_effect = Exception("Connection failed")

    with pytest.raises(exceptions.MLDiagnosticError) as exc_info:
      logging_client.LoggingClient(project_id="test-project")

    assert "Failed to initialize logging client" in str(exc_info.value)
    assert "Connection failed" in str(exc_info.value)


class TestLoggingClientWriteMetric:
  """Test LoggingClient write_metric method."""

  def setup_method(self):
    """Set up test fixtures."""
    self.mock_logging_client_cls = patch("google.cloud.logging.Client").start()
    self.mock_cloud_client = Mock()
    self.mock_logger = Mock()
    self.mock_cloud_client.logger.return_value = self.mock_logger
    self.mock_logging_client_cls.return_value = self.mock_cloud_client

    self.client = logging_client.LoggingClient(
        project_id="test-project", log_name="test-log"
    )

    mock_datetime = patch("datetime.datetime").start()
    mock_datetime.now.return_value = datetime.datetime(
        2024, 7, 30, 10, 30, 45, tzinfo=datetime.timezone.utc
    )
    mock_datetime.timezone = datetime.timezone

  def teardown_method(self):
    """Tear down test fixtures."""
    patch.stopall()

  def test_write_metric_minimal_params(self):
    """Test write_metric with minimal required parameters."""
    self.client.write_metric(
        metric_name="test_metric",
        value=42.5,
        run_id="test_run_001",
        location="us-central1",
    )

    # Verify log_struct was called with correct parameters
    self.mock_logger.log_struct.assert_called_once()
    call_args = self.mock_logger.log_struct.call_args

    # payload is position argument
    payload = call_args.args[0]
    assert payload == {"values": [42.5]}

    # Other metadata are keyword arguments
    log_kwargs = call_args.kwargs

    # Assertions for keyword arguments
    assert log_kwargs["resource"].type == "generic_node"
    assert log_kwargs["resource"].labels["project_id"] == "test-project"
    assert log_kwargs["resource"].labels["location"] == "us-central1"
    assert log_kwargs["resource"].labels["namespace"] == "test_metric"
    assert log_kwargs["resource"].labels["node_id"] == "test_run_001"
    assert "labels" not in log_kwargs

  def test_write_metric_with_step(self):
    """Test write_metric with step parameter."""
    self.client.write_metric(
        metric_name="test_metric",
        value=42.5,
        run_id="test_run_001",
        location="us-central1",
        step=10,
    )

    # Verify log_struct was called with correct parameters
    self.mock_logger.log_struct.assert_called_once()
    call_args = self.mock_logger.log_struct.call_args

    # payload is position argument
    payload = call_args.args[0]
    assert payload == {"values": [42.5], "step_index": 10}

    # Other metadata are keyword arguments
    log_kwargs = call_args.kwargs

    # Assertions for keyword arguments
    assert log_kwargs["resource"].type == "generic_node"
    assert log_kwargs["resource"].labels["project_id"] == "test-project"
    assert log_kwargs["resource"].labels["location"] == "us-central1"
    assert log_kwargs["resource"].labels["namespace"] == "test_metric"
    assert log_kwargs["resource"].labels["node_id"] == "test_run_001"

  def test_write_metric_with_int_value(self):
    """Test write_metric with int value."""
    self.client.write_metric(
        metric_name="test_metric_int",
        value=100,
        run_id="test_run_001",
        location="us-central1",
    )

    # Verify log_struct was called with correct parameters
    self.mock_logger.log_struct.assert_called_once()
    call_args = self.mock_logger.log_struct.call_args

    # payload is position argument
    payload = call_args.args[0]
    assert payload == {"values": [100]}

  def test_write_metric_with_list_value(self):
    """Test write_metric with list value."""
    self.client.write_metric(
        metric_name="test_metric_list",
        value=[1.0, 2.0, 3.0],
        run_id="test_run_001",
        location="us-central1",
    )

    # Verify log_struct was called with correct parameters
    self.mock_logger.log_struct.assert_called_once()
    call_args = self.mock_logger.log_struct.call_args

    # payload is position argument
    payload = call_args.args[0]
    assert payload == {"values": [1.0, 2.0, 3.0]}

  def test_write_metric_with_labels(self):
    """Test write_metric with labels."""
    self.client.write_metric(
        metric_name="test_metric_labels",
        value=50.0,
        run_id="test_run_001",
        location="us-central1",
        labels={"custom_label": "custom_value"},
    )

    # Verify log_struct was called with correct parameters
    self.mock_logger.log_struct.assert_called_once()
    call_args = self.mock_logger.log_struct.call_args

    # payload is position argument
    payload = call_args.args[0]
    assert payload == {"values": [50.0], "custom_label": "custom_value"}

  def test_write_metric_logging_failure(self):
    """Test that logging failures raise MLDiagnosticError."""
    self.mock_logger.log_struct.side_effect = Exception("Logging failed")

    with pytest.raises(exceptions.MLDiagnosticError) as exc_info:
      self.client.write_metric(
          metric_name="test_metric",
          value=1.0,
          run_id="test_run",
          location="us-central1",
      )

    assert "Failed to write to Cloud Logging" in str(exc_info.value)
    assert "Logging failed" in str(exc_info.value)


if __name__ == "__main__":
  pytest.main([__file__])
