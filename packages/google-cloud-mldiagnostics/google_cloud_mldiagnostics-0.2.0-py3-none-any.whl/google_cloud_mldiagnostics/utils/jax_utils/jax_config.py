"""Utility functions for configurations in JAX framework."""

from typing import Any
import jax


class JaxConfig:
  """A class to hold and query JAX device configuration."""

  def __init__(self):
    self._devices = jax.devices()
    if not self._devices:
      raise ValueError('No JAX devices found.')
    self._is_multi_slice_tpu = hasattr(self._devices[0], 'slice_index')

  @property
  def _device_type(self) -> str:
    """Returns the device type used for ML workload."""
    return self._devices[0].device_kind

  @property
  def _num_slices(self) -> int:
    """Returns the number of TPU slices for ML workload."""
    if self._is_multi_slice_tpu:
      slice_indices = set()
      for device in self._devices:
        slice_indices.add(device.slice_index)
      return len(slice_indices)
    else:
      return 1

  @property
  def _devices_per_slice(self) -> int:
    """Returns the number of devices per TPU slice for ML workload."""
    return jax.device_count() // self._num_slices

  def get_config(self) -> dict[str, Any]:
    """Returns the default configuration for JAX framework."""
    return {
        'device_type': self._device_type,
        'num_slices': str(self._num_slices),
        'devices_per_slice': str(self._devices_per_slice),
    }
