"""Unit tests for host utility functions."""

import json
import os
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import host_utils


class TestHostUtils(unittest.TestCase):
  """Test cases for host utility functions."""

  def setUp(self):
    super().setUp()
    self.env_patcher = mock.patch.dict(os.environ, {}, clear=True)
    self.env_patcher.start()

  def tearDown(self):
    super().tearDown()
    self.env_patcher.stop()

  @mock.patch("jax.process_index")
  def test_get_host_index(self, mock_jax_process_index):
    """Test get_host_index returns the correct host index."""
    mock_jax_process_index.return_value = 3
    self.assertEqual(host_utils.get_host_index(), 3)

  @mock.patch("jax.process_index")
  def test_is_master_host_when_master(self, mock_process_index):
    """Test is_master_host returns True when process_index is 0."""
    mock_process_index.return_value = 0
    self.assertTrue(host_utils.is_master_host())

  @mock.patch("jax.process_index")
  def test_is_master_host_when_not_master(self, mock_process_index):
    """Test is_master_host returns False when process_index is not 0."""
    mock_process_index.return_value = 1
    self.assertFalse(host_utils.is_master_host())

  def test_get_workload_details_all_set(self):
    """Test get_workload_details when all env vars are set."""
    ident_data = {
        "metadata.name": "test-id",
        "metadata.kind": "JobSet",
        "clustername": "test-cluster",
        "namespace": "default",
    }
    metadata_data = {
        "associated-labels": {"foo": "bar"},
        "parent-workload": "RunSet",
        "timestamp": "2024-05-20T11:08:40Z",
    }
    os.environ["GKE_DIAGON_IDENTIFIER"] = json.dumps(ident_data)
    os.environ["GKE_DIAGON_METADATA"] = json.dumps(metadata_data)

    expected = {
        "id": "test-id",
        "kind": "JobSet",
        "cluster": "test-cluster",
        "namespace": "default",
        "parent_workload": "RunSet",
        "labels": {"foo": "bar"},
        "timestamp": "2024-05-20T11:08:40Z",
    }
    self.assertEqual(host_utils.get_workload_details(), expected)

  def test_get_workload_details_partially_set(self):
    """Test get_workload_details when env vars are partially set."""
    ident_data = {
        "metadata.name": "test-id",
    }
    metadata_data = {
        "associated-labels": {"foo": "bar"},
    }
    os.environ["GKE_DIAGON_IDENTIFIER"] = json.dumps(ident_data)
    os.environ["GKE_DIAGON_METADATA"] = json.dumps(metadata_data)
    self.assertEqual(
        host_utils.get_workload_details(),
        {
            "id": "test-id",
            "kind": "",
            "cluster": "",
            "namespace": "",
            "parent_workload": None,
            "labels": {"foo": "bar"},
            "timestamp": "",
        },
    )

  def test_get_identifier_success(self):
    """Tests get_identifier with valid workload details."""
    workload_details = {
        "id": "test-id",
        "kind": "test-kind",
        "cluster": "/projects/p/locations/l/clusters/test-cluster",
        "namespace": "test-namespace",
        "timestamp": "2024-01-01T01:00:00Z",
    }
    identifier = host_utils.get_identifier(workload_details)
    expected = "test-cluster-test-namespace-test-kind-test-id-20240101-010000"
    self.assertEqual(
        identifier, expected
    )

  def test_get_identifier_success_another_timestamp(self):
    """Tests get_identifier with valid workload details and different timestamp."""
    workload_details = {
        "id": "test-id",
        "kind": "test-kind",
        "cluster": "/projects/p/locations/l/clusters/test-cluster",
        "namespace": "test-namespace",
        "timestamp": "2024-01-01T14:15:16Z",
    }
    identifier = host_utils.get_identifier(workload_details)
    expected = "test-cluster-test-namespace-test-kind-test-id-20240101-141516"
    self.assertEqual(
        identifier, expected
    )

  def test_get_identifier_none_workload_details(self):
    """Tests get_identifier with None workload details."""
    with self.assertRaisesRegex(
        ValueError,
        "Could not generate GKE workload identifier due to missing workload"
        " details. This might be because environment variables"
        " 'GKE_DIAGON_IDENTIFIER' or 'GKE_DIAGON_METADATA' are not set or are"
        " incomplete. Please ensure you are running SDK in a GKE environment"
        " with the GKE diagon operator webhook enabled.",
    ):
      host_utils.get_identifier(None)

  def test_get_identifier_missing_all(self):
    """Tests get_identifier with missing id."""
    workload_details = {
        "id": "",
        "kind": "",
        "cluster": "",
        "namespace": "",
        "timestamp": "",
    }
    with self.assertRaisesRegex(
        ValueError,
        "Could not generate GKE workload identifier due to missing"
        " properties: namespace, cluster, kind, id, timestamp.",
    ):
      host_utils.get_identifier(workload_details)

  def test_sanitize_identifier(self):
    """Tests sanitize_identifier with various inputs."""
    self.assertEqual(
        host_utils.sanitize_identifier("TestIdentifier"), "testidentifier"
    )
    self.assertEqual(
        host_utils.sanitize_identifier("test_identifier"), "test-identifier"
    )
    self.assertEqual(
        host_utils.sanitize_identifier("!test@identifier#"), "test-identifier"
    )
    self.assertEqual(
        host_utils.sanitize_identifier("TeSt--IdenTifier"), "test-identifier"
    )
    self.assertEqual(host_utils.sanitize_identifier("123_TestID"), "123-testid")
    self.assertEqual(
        host_utils.sanitize_identifier("-LEADING-trailing-"), "leading-trailing"
    )
    self.assertEqual(
        host_utils.sanitize_identifier(" leading%!@*trailing "),
        "leading-trailing",
    )


if __name__ == "__main__":
  unittest.main()
