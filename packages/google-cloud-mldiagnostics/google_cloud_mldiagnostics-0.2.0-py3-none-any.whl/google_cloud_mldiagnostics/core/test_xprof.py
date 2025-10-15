"""Unit tests for xprof.py - JAX profiling SDK wrapper."""

import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import xprof


class TestXprof(unittest.TestCase):
  """Test cases for the Xprof class."""

  def setUp(self):
    """Set up test fixtures before each test method."""
    super().setUp()

    # Mock host utils
    mock.patch(
        'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.'
        'host_utils.get_host_index',
        return_value=1,
    ).start()

    # Mock MLRun
    mock_mlrun = mock.Mock()
    mock_mlrun.run_group = 'test-run-set'
    mock_mlrun.name = 'test-run-id'
    mock_mlrun.gcs_path = 'test-gcs-path'
    mock_mlrun.project = 'test-project'
    mock_mlrun.location = 'us-central1'
    mock_mlrun.workload_details = {
        'id': 'test-workload-id',
        'kind': 'test-kind',
        'cluster': 'test-cluster',
        'namespace': 'test-namespace',
        'parent_workload': 'test-parent-workload',
        'labels': {'test-label-key': 'test-label-value'},
        'timestamp': '2024-01-01T11:00:00Z',
    }

    # Mock global_manager to return the mock MLRun
    mock.patch.object(
        global_manager, 'get_current_run', return_value=mock_mlrun
    ).start()

    # Mock JAX profiler
    self.mock_jax_start_trace = mock.patch('jax.profiler.start_trace').start()
    self.mock_jax_stop_trace = mock.patch('jax.profiler.stop_trace').start()

    # Mock JAX profiler trace for context manager usage
    self.mock_jax_trace = mock.patch('jax.profiler.trace').start()

    # Set up the trace context manager mock
    self.mock_trace_context_manager = mock.MagicMock()
    self.mock_jax_trace.return_value = self.mock_trace_context_manager

    # Mock logger
    self.mock_logger = mock.patch(
        'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core.xprof.logger'
    ).start()

  def tearDown(self):
    """Clean up after each test method."""
    super().tearDown()
    mock.patch.stopall()

  # pylint: disable=protected-access
  def test_ensure_initialized_success(self):
    """Test successful initialization of profiling."""
    prof = xprof.Xprof()
    prof._ensure_initialized()
    self.assertEqual(prof._resolved_run, global_manager.get_current_run())
    self.assertEqual(
        prof._gcs_profile_dir,
        'test-gcs-path/diagon/xprof/test-run-id',
    )

  def test_start_stop_success(self):
    """Test successful start and stop of profiling."""
    prof = xprof.Xprof()
    with mock.patch('builtins.print') as mock_print_start:
      prof.start()

    self.assertTrue(prof._is_profiling)  # pylint: disable=protected-access
    self.mock_jax_start_trace.assert_called_once_with(
        prof._gcs_profile_dir  # pylint: disable=protected-access
    )
    self.mock_logger.info.assert_called_once_with('profiling_status: started')
    mock_print_start.assert_called_with(
        f'Starting JAX profiling to: {prof._gcs_profile_dir}'  # pylint: disable=protected-access
    )
    self.mock_logger.info.reset_mock()

    with mock.patch('builtins.print') as mock_print_stop:
      prof.stop()

    self.assertFalse(prof._is_profiling)  # pylint: disable=protected-access
    self.mock_jax_stop_trace.assert_called_once()
    self.mock_logger.info.assert_has_calls([
        mock.call('profiling_status: stopped'),
        mock.call(
            'profiling traces should be available at: %s',
            prof._gcs_profile_dir,  # pylint: disable=protected-access
        ),
    ])
    mock_print_stop.assert_called_with(
        f'Stopping JAX profiling for: {prof._gcs_profile_dir}'  # pylint: disable=protected-access
    )

  def test_context_manager_success(self):
    """Test context manager usage."""
    prof = xprof.Xprof()

    with mock.patch('builtins.print') as mock_print:
      with prof as p:
        self.assertEqual(p, prof)
        self.assertTrue(prof._is_profiling)  # pylint: disable=protected-access

        self.mock_jax_trace.assert_called_once_with(
            prof._gcs_profile_dir  # pylint: disable=protected-access
        )

        self.mock_trace_context_manager.__enter__.assert_called_once()

        mock_print.assert_called_with(
            f'Entering xprof context for: {prof._gcs_profile_dir}'  # pylint: disable=protected-access
        )

    self.mock_trace_context_manager.__exit__.assert_called_once()
    self.assertFalse(prof._is_profiling)  # pylint: disable=protected-access

  def test_decorator_success(self):
    """Test decorator usage."""
    prof = xprof.Xprof()

    @prof
    def test_function(x, y):
      return x + y

    with mock.patch('builtins.print'):
      with mock.patch.object(prof, 'start') as mock_start:
        with mock.patch.object(prof, 'stop') as mock_stop:
          result = test_function(1, 2)

    self.assertEqual(result, 3)
    mock_start.assert_called_once()
    mock_stop.assert_called_once()


if __name__ == '__main__':
  unittest.main(verbosity=2)
