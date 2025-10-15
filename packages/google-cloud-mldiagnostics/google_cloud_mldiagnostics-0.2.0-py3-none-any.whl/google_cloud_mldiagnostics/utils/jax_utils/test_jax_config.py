"""Tests for jax_config."""

import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.jax_utils import jax_config


class JaxConfigTest(unittest.TestCase):
  """Tests for the jax_config.JaxConfig class."""

  @mock.patch('jax.device_count')
  @mock.patch('jax.devices')
  def test_multi_slice_tpu_config(
      self, mock_jax_devices, mock_jax_device_count
  ):
    """Tests JaxConfig initialization with a multi-slice TPU setup."""
    # Mock devices for a 2-slice TPU setup
    mock_devices = [
        mock.Mock(device_kind='TPU v4', slice_index=0),
        mock.Mock(device_kind='TPU v4', slice_index=0),
        mock.Mock(device_kind='TPU v4', slice_index=1),
        mock.Mock(device_kind='TPU v4', slice_index=1),
    ]
    mock_jax_devices.return_value = mock_devices
    mock_jax_device_count.return_value = 4

    config = jax_config.JaxConfig()
    self.assertEqual(config._is_multi_slice_tpu, True)  # pylint: disable=protected-access
    expected_config = {
        'device_type': 'TPU v4',
        'num_slices': '2',
        'devices_per_slice': '2',
    }
    self.assertDictEqual(config.get_config(), expected_config)

  @mock.patch('jax.device_count')
  @mock.patch('jax.devices')
  def test_single_slice_tpu_config(
      self, mock_jax_devices, mock_jax_device_count
  ):
    """Tests JaxConfig initialization with a single-slice TPU setup."""
    # Mock devices for a single-slice setup (no 'slice_index' attribute)
    mock_devices = [
        mock.Mock(spec=['device_kind'], device_kind='TPU v3'),
        mock.Mock(spec=['device_kind'], device_kind='TPU v3'),
        mock.Mock(spec=['device_kind'], device_kind='TPU v3'),
    ]

    mock_jax_devices.return_value = mock_devices
    mock_jax_device_count.return_value = 3

    config = jax_config.JaxConfig()
    # pylint: disable=protected-access
    self.assertEqual(config._is_multi_slice_tpu, False)
    expected_config = {
        'device_type': 'TPU v3',
        'num_slices': '1',
        'devices_per_slice': '3',
    }
    self.assertDictEqual(config.get_config(), expected_config)

  @mock.patch('jax.devices')
  def test_no_devices_found_raises_error(self, mock_jax_devices):
    mock_jax_devices.return_value = []

    with self.assertRaises(ValueError):
      jax_config.JaxConfig()


if __name__ == '__main__':
  unittest.main()
