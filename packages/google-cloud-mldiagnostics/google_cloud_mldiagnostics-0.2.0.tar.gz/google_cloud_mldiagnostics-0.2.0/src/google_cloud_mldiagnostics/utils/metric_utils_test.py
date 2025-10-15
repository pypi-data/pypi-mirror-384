"""Tests for metric_utils."""

import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import metric_utils


class MetricUtilsTest(unittest.TestCase):

  @mock.patch.object(metric_utils, "psutil", autospec=True)
  def test_get_host_cpu_utilization(self, mock_psutil):
    mock_psutil.cpu_percent.return_value = 50.0
    self.assertEqual(metric_utils.get_host_cpu_utilization(), 50.0)
    mock_psutil.cpu_percent.assert_called_once()

  @mock.patch.object(metric_utils, "psutil", autospec=True)
  def test_get_host_memory_utilization(self, mock_psutil):
    mock_vm_result = mock.Mock()
    mock_vm_result.percent = 75.0
    mock_psutil.virtual_memory.return_value = mock_vm_result
    self.assertEqual(metric_utils.get_host_memory_utilization(), 75.0)
    mock_psutil.virtual_memory.assert_called_once()

  @mock.patch.object(metric_utils, "libtpu_metric", autospec=True)
  def test_get_tpu_duty_cycle(self, mock_libtpu_metric):
    mock_libtpu_metric.get_tpu_duty_cycle.return_value = [80.0]
    self.assertEqual(metric_utils.get_tpu_duty_cycle(), [80.0])
    mock_libtpu_metric.get_tpu_duty_cycle.assert_called_once()

  @mock.patch.object(metric_utils, "libtpu_metric", autospec=True)
  def test_get_tpu_tensorcore_utilization(self, mock_libtpu_metric):
    mock_libtpu_metric.get_tpu_tensorcore_utilization.return_value = [
        70.0,
        85.0,
    ]
    self.assertEqual(
        metric_utils.get_tpu_tensorcore_utilization(), [70.0, 85.0]
    )
    mock_libtpu_metric.get_tpu_tensorcore_utilization.assert_called_once()

  @mock.patch.object(metric_utils, "libtpu_metric", autospec=True)
  def test_get_hbm_utilization(self, mock_libtpu_metric):
    mock_libtpu_metric.get_hbm_utilization.return_value = [60.0, 70.0]
    self.assertEqual(metric_utils.get_hbm_utilization(), [60.0, 70.0])
    mock_libtpu_metric.get_hbm_utilization.assert_called_once()

  @mock.patch.object(metric_utils, "psutil", autospec=True)
  def test_host_functions_return_none_on_exception(self, mock_psutil):
    mock_psutil.cpu_percent.side_effect = Exception("CPU exception")
    mock_psutil.virtual_memory.side_effect = Exception("Memory exception")
    self.assertIsNone(metric_utils.get_host_cpu_utilization())
    self.assertIsNone(metric_utils.get_host_memory_utilization())
    mock_psutil.cpu_percent.assert_called_once()
    mock_psutil.virtual_memory.assert_called_once()

  @mock.patch.object(metric_utils, "libtpu_metric", autospec=True)
  def test_tpu_functions_return_none(self, mock_libtpu_metric):
    mock_libtpu_metric.get_tpu_duty_cycle.return_value = None
    mock_libtpu_metric.get_tpu_tensorcore_utilization.return_value = None
    mock_libtpu_metric.get_hbm_utilization.return_value = None
    self.assertIsNone(metric_utils.get_tpu_duty_cycle())
    self.assertIsNone(metric_utils.get_tpu_tensorcore_utilization())
    self.assertIsNone(metric_utils.get_hbm_utilization())
    mock_libtpu_metric.get_tpu_duty_cycle.assert_called_once()
    mock_libtpu_metric.get_tpu_tensorcore_utilization.assert_called_once()
    mock_libtpu_metric.get_hbm_utilization.assert_called_once()


if __name__ == "__main__":
  unittest.main()
