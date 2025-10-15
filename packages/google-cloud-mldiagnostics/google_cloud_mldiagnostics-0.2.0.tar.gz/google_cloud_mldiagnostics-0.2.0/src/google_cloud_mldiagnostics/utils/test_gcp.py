"""Additional unit tests for GCP utility functions to improve code coverage."""

import unittest
from unittest import mock
import urllib.error

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import gcp


class TestGCPUtilsAdditional(unittest.TestCase):
  """Additional test cases for GCP utility functions to improve coverage."""

  def setUp(self):
    """Set up test fixtures."""
    super().setUp()
    self.timeout = 5

  # Tests for line 23 - get_project_id decode/strip coverage
  @mock.patch('urllib.request.urlopen')
  def test_get_project_id_with_whitespace(self, mock_urlopen):
    """Test project ID retrieval with whitespace that needs stripping."""
    # Mock response with leading/trailing whitespace
    mock_response = mock.Mock()
    mock_response.read.return_value = b'  my-test-project  \n'
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock(return_value=None)
    mock_urlopen.return_value = mock_response

    result = gcp.get_project_id(timeout=self.timeout)

    # Should strip whitespace and newlines
    self.assertEqual(result, 'my-test-project')

  @mock.patch('urllib.request.urlopen')
  def test_get_project_id_empty_response(self, mock_urlopen):
    """Test project ID retrieval with empty response."""
    mock_response = mock.Mock()
    mock_response.read.return_value = b'   '  # Only whitespace
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock(return_value=None)
    mock_urlopen.return_value = mock_response

    result = gcp.get_project_id(timeout=self.timeout)

    # Should return empty string after stripping
    self.assertEqual(result, '')

  @mock.patch('urllib.request.urlopen')
  @mock.patch('logging.warning')
  def test_get_project_id_http_error(self, mock_warning, mock_urlopen):
    """Test project ID retrieval with HTTP error."""
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url='test', code=404, msg='Not Found', hdrs=None, fp=None
    )

    result = gcp.get_project_id()

    self.assertIsNone(result)
    mock_warning.assert_called_once()

  @mock.patch('urllib.request.urlopen')
  def test_get_instance_zone_with_whitespace(self, mock_urlopen):
    """Test zone retrieval with whitespace that needs stripping."""
    mock_response = mock.Mock()
    mock_response.read.return_value = (
        b'  projects/123456789/zones/us-central1-a  \n'
    )
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock(return_value=None)
    mock_urlopen.return_value = mock_response

    result = gcp.get_instance_zone(timeout=self.timeout)

    # Should extract zone name and strip whitespace
    self.assertEqual(result, 'us-central1-a')

  @mock.patch('urllib.request.urlopen')
  def test_get_instance_zone_url_error(self, mock_urlopen):
    """Test zone retrieval with URL error."""
    mock_urlopen.side_effect = urllib.error.URLError('Connection failed')

    result = gcp.get_instance_zone()

    self.assertIsNone(result)

  @mock.patch('urllib.request.urlopen')
  def test_get_instance_zone_http_error(self, mock_urlopen):
    """Test zone retrieval with HTTP error."""
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url='test', code=500, msg='Server Error', hdrs=None, fp=None
    )

    result = gcp.get_instance_zone()

    self.assertIsNone(result)

  @mock.patch('urllib.request.urlopen')
  def test_get_instance_zone_value_error(self, mock_urlopen):
    """Test zone retrieval with value error."""
    mock_urlopen.side_effect = ValueError('Invalid response')

    result = gcp.get_instance_zone()

    self.assertIsNone(result)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_success(self, mock_get_zone):
    """Test successful region extraction from zone."""
    mock_get_zone.return_value = 'us-central1-a'

    result = gcp.get_instance_region(timeout=self.timeout)

    self.assertEqual(result, 'us-central1')
    mock_get_zone.assert_called_once_with(self.timeout)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_different_zones(self, mock_get_zone):
    """Test region extraction from different zone formats."""
    test_cases = [
        ('europe-west1-b', 'europe-west1'),
        ('asia-southeast1-c', 'asia-southeast1'),
        ('us-east1-d', 'us-east1'),
        ('australia-southeast1-a', 'australia-southeast1'),
    ]

    for zone, expected_region in test_cases:
      with self.subTest(zone=zone):
        mock_get_zone.return_value = zone
        result = gcp.get_instance_region()
        self.assertEqual(result, expected_region)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_zone_none(self, mock_get_zone):
    """Test region extraction when get_instance_zone returns None."""
    mock_get_zone.return_value = None

    result = gcp.get_instance_region()

    self.assertIsNone(result)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_malformed_zone_short(self, mock_get_zone):
    """Test region extraction with malformed zone (too few parts)."""
    mock_get_zone.return_value = 'us-central'

    result = gcp.get_instance_region()

    self.assertIsNone(result)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_malformed_zone_single_part(self, mock_get_zone):
    """Test region extraction with malformed zone (single part)."""
    mock_get_zone.return_value = 'invalid-zone'

    result = gcp.get_instance_region()

    self.assertIsNone(result)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_empty_zone(self, mock_get_zone):
    """Test region extraction with empty zone string."""
    mock_get_zone.return_value = ''

    result = gcp.get_instance_region()

    self.assertIsNone(result)

  @mock.patch(
      'google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.gcp.get_instance_zone'
  )
  def test_get_instance_region_zone_with_extra_parts(self, mock_get_zone):
    """Test region extraction with zone having extra parts."""
    mock_get_zone.return_value = 'us-central1-a-extra-part'

    result = gcp.get_instance_region()

    # Should still work, taking all but the last part
    self.assertEqual(result, 'us-central1-a-extra')

  # Edge cases for decode coverage
  @mock.patch('urllib.request.urlopen')
  def test_get_project_id_unicode_content(self, mock_urlopen):
    """Test project ID retrieval with unicode content."""
    mock_response = mock.Mock()
    # Response with unicode characters (encoded as UTF-8)
    mock_response.read.return_value = 'my-test-project-ñ'.encode('utf-8')
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock(return_value=None)
    mock_urlopen.return_value = mock_response

    result = gcp.get_project_id()

    self.assertEqual(result, 'my-test-project-ñ')

  @mock.patch('urllib.request.urlopen')
  def test_get_instance_zone_unicode_content(self, mock_urlopen):
    """Test zone retrieval with unicode content in path."""
    mock_response = mock.Mock()
    zone_path = 'projects/123456789/zones/us-central1-a-test'
    mock_response.read.return_value = zone_path.encode('utf-8')
    mock_response.__enter__ = mock.Mock(return_value=mock_response)
    mock_response.__exit__ = mock.Mock(return_value=None)
    mock_urlopen.return_value = mock_response

    result = gcp.get_instance_zone()

    self.assertEqual(result, 'us-central1-a-test')


if __name__ == '__main__':
  # Run the tests
  unittest.main(verbosity=2)
