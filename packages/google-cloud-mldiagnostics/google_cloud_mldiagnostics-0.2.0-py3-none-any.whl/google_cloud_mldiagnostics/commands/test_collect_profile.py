"""Unit tests for the API metrics module."""

import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands import collect_profile


class TestCollectProfile(unittest.TestCase):
  """Test cases for collect_profile."""

  def test_collect_profile_for_single_host(self):
    """Test collect_profile function for single host."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      collect_profile.main(
          ["--hosts=a", "--port=11", "--duration_in_ms=90", "--log_dir=f"]
      )

      xprof_mock.trace.assert_called_once_with(
          "a:11",
          "f",
          "",
          True,
          90,
          3,
          {
              "host_tracer_level": 2,
              "device_tracer_level": 1,
              "python_tracer_level": 1,
          },
      )

  def test_collect_profile_for_multi_host(self):
    """Test collect_profile for multiple hosts."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      collect_profile.main([
          "--hosts=h1,h2,192.169",
          "--port=11",
          "--duration_in_ms=90",
          "--log_dir=f",
      ])

      xprof_mock.trace.assert_called_once_with(
          "h1:11,h2:11,192.169:11",
          "f",
          "",
          True,
          90,
          3,
          {
              "host_tracer_level": 2,
              "device_tracer_level": 1,
              "python_tracer_level": 1,
          },
      )

  def test_hosts_is_required_arg(self):
    """Test collect_profile fails if hosts parameter missed."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      exception = None
      try:
        collect_profile.main([
            "--port=11",
            "--duration_in_ms=90",
            "--log_dir=f",
        ])

        self.fail("Should fail parsing")
      except SystemExit as e:
        exception = e

      self.assertIn(
          "the following arguments are required: --hosts",
          str(exception.__context__),
      )
      xprof_mock.assert_not_called()

  def test_port_is_required_arg(self):
    """Test collect_profile if port parameter missed."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      exception = None
      try:
        collect_profile.main([
            "--hosts=11",
            "--duration_in_ms=90",
            "--log_dir=f",
        ])

        self.fail("Should fail parsing")
      except SystemExit as e:
        exception = e

      self.assertIn(
          "the following arguments are required: --port",
          str(exception.__context__),
      )
      xprof_mock.assert_not_called()

  def test_duration_in_ms_is_required_arg(self):
    """Test collect_profile if duration parameter is missed."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      exception = None
      try:
        collect_profile.main([
            "--hosts=11",
            "--port=11",
            "--log_dir=f",
        ])

        self.fail("Should fail parsing")
      except SystemExit as e:
        exception = e

      self.assertIn(
          "the following arguments are required: --duration_in_ms",
          str(exception.__context__),
      )
      xprof_mock.assert_not_called()

  def test_log_dir_is_required_arg(self):
    """Test collect_profile if log_dir parameter is missed."""
    with mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.commands.collect_profile._import_xprof"
    ) as xprof_import_mock:
      xprof_mock = mock.MagicMock()
      xprof_import_mock.return_value = xprof_mock

      exception = None
      try:
        collect_profile.main([
            "--hosts=11",
            "--duration_in_ms=11",
            "--port=11",
        ])

        self.fail("Should fail parsing")
      except SystemExit as e:
        exception = e

      self.assertIn(
          "the following arguments are required: --log_dir",
          str(exception.__context__),
      )
      xprof_mock.assert_not_called()


if __name__ == "__main__":
  unittest.main()
