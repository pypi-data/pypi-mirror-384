"""Tests for libtpu_metric."""

import importlib
import sys
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils import libtpu_metric


class LibtpuMetricTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_monitoring = mock.Mock()
    libtpu_metric._monitoring_module = self.mock_monitoring

  def test_get_monitoring_module_unavailable(self):
    with mock.patch.dict(sys.modules, {"libtpu": None}):
      importlib.reload(libtpu_metric)
      self.assertIsNone(libtpu_metric._get_monitoring_module())
    importlib.reload(libtpu_metric)

  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils.libtpu_metric._LIBTPU_METRICS_AVAILABLE",
      True,
  )
  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils.libtpu_metric.libtpu_sdk"
  )
  def test_get_monitoring_module_tpumonitoring(self, mock_libtpu_sdk):
    mock_libtpu_sdk.tpumonitoring = "tpumonitoring"
    self.assertEqual(
        libtpu_metric._get_monitoring_module(), "tpumonitoring"
    )

  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils.libtpu_metric._LIBTPU_METRICS_AVAILABLE",
      True,
  )
  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils.libtpu_metric.libtpu_sdk"
  )
  def test_get_monitoring_module_monitoring(self, mock_libtpu_sdk):
    del mock_libtpu_sdk.tpumonitoring
    mock_libtpu_sdk.monitoring = "monitoring"
    self.assertEqual(libtpu_metric._get_monitoring_module(), "monitoring")

  def test_get_tpu_duty_cycle(self):
    mock_metric = mock.Mock()
    mock_metric.data.return_value = ["70.0", "80.0"]
    self.mock_monitoring.get_metric.return_value = mock_metric
    duty_cycle = libtpu_metric.get_tpu_duty_cycle()
    self.assertEqual(duty_cycle, [70.0, 80.0])
    self.mock_monitoring.get_metric.assert_called_once_with("duty_cycle_pct")

  def test_get_tpu_tensorcore_utilization(self):
    mock_metric = mock.Mock()
    mock_metric.data.return_value = ["60.0", "70.0"]
    self.mock_monitoring.get_metric.return_value = mock_metric
    tensorcore_util = libtpu_metric.get_tpu_tensorcore_utilization()
    self.assertEqual(tensorcore_util, [60.0, 70.0])
    self.mock_monitoring.get_metric.assert_called_once_with("tensorcore_util")

  def test_get_hbm_utilization(self):
    def get_metric_side_effect(metric_name):
      if metric_name == "hbm_capacity_usage":
        mock_metric = mock.Mock()
        mock_metric.data.return_value = ["10", "20"]
        return mock_metric
      elif metric_name == "hbm_capacity_total":
        mock_metric = mock.Mock()
        mock_metric.data.return_value = ["100", "100"]
        return mock_metric
      else:
        return mock.DEFAULT

    self.mock_monitoring.get_metric.side_effect = get_metric_side_effect
    hbm_util = libtpu_metric.get_hbm_utilization()
    self.assertEqual(hbm_util, [10.0, 20.0])
    self.mock_monitoring.get_metric.assert_any_call("hbm_capacity_usage")
    self.mock_monitoring.get_metric.assert_any_call("hbm_capacity_total")

  def test_get_hbm_utilization_zero_total(self):
    def get_metric_side_effect(metric_name):
      if metric_name == "hbm_capacity_usage":
        mock_metric = mock.Mock()
        mock_metric.data.return_value = ["10", "20"]
        return mock_metric
      elif metric_name == "hbm_capacity_total":
        mock_metric = mock.Mock()
        mock_metric.data.return_value = ["100", "0"]
        return mock_metric
      else:
        return mock.DEFAULT

    self.mock_monitoring.get_metric.side_effect = get_metric_side_effect
    hbm_util = libtpu_metric.get_hbm_utilization()
    self.assertEqual(hbm_util, [10.0, 0.0])
    self.mock_monitoring.get_metric.assert_any_call("hbm_capacity_usage")
    self.mock_monitoring.get_metric.assert_any_call("hbm_capacity_total")

  def test_get_tpu_duty_cycle_exception(self):
    self.mock_monitoring.get_metric.side_effect = Exception("test exception")
    self.assertIsNone(libtpu_metric.get_tpu_duty_cycle())
    self.mock_monitoring.get_metric.assert_called_once_with("duty_cycle_pct")

  def test_get_tpu_tensorcore_utilization_exception(self):
    self.mock_monitoring.get_metric.side_effect = Exception("test exception")
    self.assertIsNone(libtpu_metric.get_tpu_tensorcore_utilization())
    self.mock_monitoring.get_metric.assert_called_once_with("tensorcore_util")

  def test_get_hbm_utilization_exception(self):
    self.mock_monitoring.get_metric.side_effect = Exception("test exception")
    self.assertIsNone(libtpu_metric.get_hbm_utilization())
    self.mock_monitoring.get_metric.assert_called_once_with(
        "hbm_capacity_usage"
    )

  @mock.patch(
      "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.libtpu_utils.libtpu_metric._monitoring_module",
      None,
  )
  def test_metrics_unavailable(self):
    self.assertIsNone(libtpu_metric.get_tpu_duty_cycle())
    self.assertIsNone(libtpu_metric.get_tpu_tensorcore_utilization())
    self.assertIsNone(libtpu_metric.get_hbm_utilization())


if __name__ == "__main__":
  unittest.main()
