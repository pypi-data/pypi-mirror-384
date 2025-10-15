"""Unit tests for the API metrics module."""

import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.api import metrics


class TestMetricsAPI(unittest.TestCase):
  """Test cases for the metrics API module."""

  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.api."
      "metrics._metrics_recorder"
  )
  def test_record_function_minimal_parameters(self, mock_recorder):
    """Test record function with minimal parameters."""
    # Setup
    mock_metric_type = mock.Mock()
    mock_metric_type.value = "test_metric"

    # Call the API function
    metrics.record(metric_name=mock_metric_type, value=42.5)

    # Verify delegation to the underlying recorder
    mock_recorder.record.assert_called_once_with(
        mock_metric_type, 42.5, None, None, False
    )


if __name__ == "__main__":
  unittest.main()
