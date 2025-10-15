"""Tests for config_utils."""

import os
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import config_utils
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.jax_utils import jax_config


class ConfigUtilsTest(unittest.TestCase):
  """Tests for config_utils."""

  def setUp(self):
    """Sets up the test environment."""
    super().setUp()
    config_utils._config_instance = None  # pylint: disable=protected-access

  # pylint: disable=protected-access
  @mock.patch.object(jax_config, "JaxConfig")
  @mock.patch.dict(os.environ, {"TPU_ML_PLATFORM": "JAX"}, clear=True)
  def test_get_framework_config_instance_jax(self, mock_jax_config):
    """Tests _get_framework_config_instance for JAX."""
    mock_instance = mock_jax_config.return_value
    config = config_utils._get_framework_config_instance()
    self.assertEqual(config, mock_instance)
    mock_jax_config.assert_called_once()
    # test singleton
    config2 = config_utils._get_framework_config_instance()
    self.assertIs(config, config2)
    mock_jax_config.assert_called_once()  # still called once

  @mock.patch("logging.warning")
  @mock.patch.dict(os.environ, {"TPU_ML_PLATFORM": "PyTorch/XLA"}, clear=True)
  def test_get_framework_config_instance_unsupported(self, mock_warning):
    """Tests _get_framework_config_instance for unsupported framework."""
    config_instance = config_utils._get_framework_config_instance()
    self.assertIsNone(config_instance)
    mock_warning.assert_called_once_with(
        "Hardware configuration for framework '%s' is not supported.",
        "PyTorch/XLA",
    )

  @mock.patch.object(jax_config, "JaxConfig")
  @mock.patch.dict(
      os.environ,
      {
          "TPU_ML_PLATFORM": "JAX",
          "TPU_ML_PLATFORM_VERSION": "1.0",
          "XLA_FLAGS": "--xla_flags",
      },
      clear=True,
  )
  def test_get_configs_jax(self, mock_jax_config):
    """Tests get_software_config and get_hardware_config for JAX."""
    mock_jax_config_instance = mock_jax_config.return_value
    mock_jax_config_instance.get_config.return_value = {
        "device_type": "tpu",
        "num_slices": 1,
        "devices_per_slice": 1,
    }
    hardware_config = config_utils.get_hardware_config()
    self.assertEqual(
        hardware_config,
        {
            "device_type": "tpu",
            "num_slices": 1,
            "devices_per_slice": 1,
        },
    )
    software_config = config_utils.get_software_config()
    self.assertEqual(
        software_config,
        {
            "framework": "JAX",
            "framework_version": "1.0",
            "xla_flags": "--xla_flags",
        },
    )
    mock_jax_config_instance.get_config.assert_called_once()

  @mock.patch.object(jax_config, "JaxConfig")
  @mock.patch.dict(
      os.environ,
      {
          "TPU_ML_PLATFORM": "JAX",
          "TPU_ML_PLATFORM_VERSION": "1.0",
          "XLA_FLAGS": "--xla_flags",
      },
      clear=True,
  )
  def test_get_configs_jax_missing_keys(self, mock_jax_config):
    """Tests get_configs for JAX when keys are missing."""
    mock_jax_config_instance = mock_jax_config.return_value
    mock_jax_config_instance.get_config.return_value = {}
    hardware_config = config_utils.get_hardware_config()
    self.assertEqual(
        hardware_config,
        {
            "device_type": "unknown",
            "num_slices": "unknown",
            "devices_per_slice": "unknown",
        },
    )
    software_config = config_utils.get_software_config()
    self.assertEqual(
        software_config,
        {
            "framework": "JAX",
            "framework_version": "1.0",
            "xla_flags": "--xla_flags",
        },
    )
    mock_jax_config_instance.get_config.assert_called_once()

  @mock.patch.object(jax_config, "JaxConfig")
  @mock.patch.dict(os.environ, {"TPU_ML_PLATFORM": "JAX"}, clear=True)
  def test_get_configs_jax_unknown_env(self, mock_jax_config):
    """Tests get_configs for JAX when env vars are missing."""
    mock_jax_config_instance = mock_jax_config.return_value
    mock_jax_config_instance.get_config.return_value = {
        "device_type": "tpu",
        "num_slices": 1,
        "devices_per_slice": 1,
    }
    hardware_config = config_utils.get_hardware_config()
    self.assertEqual(
        hardware_config,
        {
            "device_type": "tpu",
            "num_slices": 1,
            "devices_per_slice": 1,
        },
    )
    software_config = config_utils.get_software_config()
    self.assertEqual(
        software_config,
        {
            "framework": "JAX",
            "framework_version": "unknown",
            "xla_flags": "default",
        },
    )
    mock_jax_config_instance.get_config.assert_called_once()

  @mock.patch.dict(os.environ, {"TPU_ML_PLATFORM": "PyTorch/XLA"}, clear=True)
  def test_get_configs_unsupported(self):
    """Tests get_configs for unsupported framework."""
    hardware_config = config_utils.get_hardware_config()
    self.assertEqual(
        hardware_config,
        {
            "device_type": "unknown",
            "num_slices": "unknown",
            "devices_per_slice": "unknown",
        },
    )
    software_config = config_utils.get_software_config()
    self.assertEqual(
        software_config,
        {
            "framework": "PyTorch/XLA",
            "framework_version": "unknown",
            "xla_flags": "default",
        },
    )


if __name__ == "__main__":
  unittest.main()
