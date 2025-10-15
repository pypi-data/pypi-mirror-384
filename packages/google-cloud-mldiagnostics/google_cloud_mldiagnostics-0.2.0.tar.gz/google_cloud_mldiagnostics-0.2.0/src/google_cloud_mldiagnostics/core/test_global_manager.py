"""Unit tests for the global run manager module."""

import threading
import unittest
from unittest import mock

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager


class TestGlobalRunManager(unittest.TestCase):
  """Test cases for GlobalRunManager singleton."""

  def setUp(self):
    """Set up test fixtures before each test method."""
    super().setUp()
    # Reset singleton state before each test
    global_manager.GlobalRunManager._instance = None  # pylint: disable=protected-access
    self.mock_logging_client = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.clients.logging_client.LoggingClient"
    ).start()
    self.mock_control_plane_client = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.clients.control_plane_client.ControlPlaneClient"
    ).start()
    self.mock_is_master_host = mock.patch(
        "google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils.host_utils.is_master_host"
    ).start()
    self.mock_is_master_host.return_value = True

  def tearDown(self):
    """Clean up after each test method."""
    super().tearDown()
    mock.patch.stopall()
    # Reset singleton state after each test
    global_manager.GlobalRunManager._instance = None  # pylint: disable=protected-access

  def _create_mock_mlrun(self, suffix=""):
    """Create a mock MLRun with all required attributes."""
    mock_mlrun = mock.Mock()
    mock_mlrun.run_group = f"test_run_group{suffix}"
    mock_mlrun.name = f"test_run_id{suffix}"
    mock_mlrun.location = f"us-central1{suffix}" if suffix else "us-central1"
    mock_mlrun.project = f"test_project{suffix}" if suffix else "test_project"
    mock_mlrun.project_id = (
        f"test_project{suffix}" if suffix else "test_project"
    )
    mock_mlrun.gcs_path = None
    mock_mlrun.configs = None
    mock_mlrun.run_phase = mock.Mock()
    mock_mlrun.run_phase.value = "ACTIVE"
    return mock_mlrun

  def test_singleton_pattern(self):
    """Test that only one instance is created."""
    manager1 = global_manager.GlobalRunManager()
    manager2 = global_manager.GlobalRunManager()

    self.assertIs(manager1, manager2)
    self.assertEqual(id(manager1), id(manager2))

  def test_get_instance_returns_singleton(self):
    """Test that get_instance returns the same singleton instance."""
    manager1 = global_manager.GlobalRunManager.get_instance()
    manager2 = global_manager.GlobalRunManager.get_instance()
    manager3 = global_manager.GlobalRunManager()

    self.assertIs(manager1, manager2)
    self.assertIs(manager1, manager3)

  def test_thread_safety(self):
    """Test that singleton creation is thread-safe."""
    instances = []

    def create_instance():
      """Create an instance and add it to the list."""
      instance = global_manager.GlobalRunManager()
      instances.append(instance)

    # Create multiple threads that try to create instances simultaneously
    threads = []
    for _ in range(10):
      thread = threading.Thread(target=create_instance)
      threads.append(thread)

    # Start all threads
    for thread in threads:
      thread.start()

    # Wait for all threads to complete
    for thread in threads:
      thread.join()

    # All instances should be the same
    first_instance = instances[0]
    for instance in instances:
      self.assertIs(instance, first_instance)

  def test_initial_state(self):
    """Test that initial state is properly set."""
    manager = global_manager.GlobalRunManager()

    self.assertIsNone(manager.run_id)
    self.assertIsNone(manager.run_group)
    self.assertIsNone(manager.location)
    self.assertIsNone(manager.project_id)
    self.assertIsNone(manager.logging_client)
    self.assertFalse(manager.is_initialized())

  def test_initialize_method_master(self):
    """Test the initialize method with master host."""
    manager = global_manager.GlobalRunManager()

    # Initially not initialized
    self.assertFalse(manager.is_initialized())

    # Create mock MLRun
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    # Initialize with mock MLRun
    mock_logging_client_instance = self.mock_logging_client.return_value
    mock_control_plane_client_instance = (
        self.mock_control_plane_client.return_value
    )

    manager.initialize(mock_mlrun)

    # Check state after initialization
    self.assertTrue(manager.is_initialized())
    self.assertEqual(manager.run_group, "test_run_group")
    self.assertEqual(manager.run_id, "test_run_id")
    self.assertEqual(manager.location, "us-central1")
    self.assertEqual(manager.project_id, "test_project")
    self.assertEqual(manager.logging_client, mock_logging_client_instance)

    # Verify clients were created correctly
    self.mock_control_plane_client.assert_called_once_with(
        project_id="test_project", location="us-central1"
    )
    mock_control_plane_client_instance.create_ml_run.assert_called_once()
    self.mock_logging_client.assert_called_once_with(project_id="test_project")

  def test_initialize_method_non_master(self):
    """Test the initialize method with non-master host."""
    self.mock_is_master_host.return_value = False
    manager = global_manager.GlobalRunManager()

    # Initially not initialized
    self.assertFalse(manager.is_initialized())

    # Create mock MLRun
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    # Initialize with mock MLRun
    mock_logging_client_instance = self.mock_logging_client.return_value
    mock_control_plane_client_instance = (
        self.mock_control_plane_client.return_value
    )

    manager.initialize(mock_mlrun)

    # Check state after initialization
    self.assertTrue(manager.is_initialized())
    self.assertEqual(manager.run_group, "test_run_group")
    self.assertEqual(manager.run_id, "test_run_id")
    self.assertEqual(manager.location, "us-central1")
    self.assertEqual(manager.project_id, "test_project")
    self.assertEqual(manager.logging_client, mock_logging_client_instance)

    # Verify clients were created correctly
    self.mock_control_plane_client.assert_not_called()
    mock_control_plane_client_instance.create_ml_run.assert_not_called()
    self.mock_logging_client.assert_called_once_with(project_id="test_project")

  def test_initialize_already_initialized(self):
    """Test that re-initialization logs a warning but updates values."""
    manager = global_manager.GlobalRunManager()

    # Create first mock MLRun
    mock_mlrun1 = self._create_mock_mlrun("_1")
    mock_mlrun1.location = "us-west1"
    mock_mlrun1.project = "project_1"
    mock_mlrun1.project_id = "project_1"

    # Create second mock MLRun
    mock_mlrun2 = self._create_mock_mlrun("_2")
    mock_mlrun2.location = "us-east1"
    mock_mlrun2.project = "project_2"
    mock_mlrun2.project_id = "project_2"

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/project/locations/location/machineLearningRuns/test-run"
        )
    }

    # First initialization
    manager.initialize(mock_mlrun1)

    # Second initialization should log warning
    with mock.patch.object(global_manager.logger, "info") as mock_log:
      manager.initialize(mock_mlrun2)

      # Check that the "already initialized" message was logged
      mock_log.assert_any_call(
          "GlobalRunManager already initialized. Updating with new run"
          " information."
      )

      # Verify that logger.info was called at least twice
      # (once for warning, once for successful creation)
      self.assertGreaterEqual(mock_log.call_count, 2)

    # Values should be updated to second MLRun
    self.assertEqual(manager.run_group, "test_run_group_2")
    self.assertEqual(manager.run_id, "test_run_id_2")
    self.assertEqual(manager.location, "us-east1")
    self.assertEqual(manager.project_id, "project_2")
    self.assertEqual(self.mock_logging_client.call_count, 2)
    self.assertEqual(self.mock_control_plane_client.call_count, 2)

  def test_clear_method(self):
    """Test the clear method resets state."""
    manager = global_manager.GlobalRunManager()

    # Create mock MLRun
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    # Initialize with test data
    manager.initialize(mock_mlrun)

    # Verify initialized
    self.assertTrue(manager.is_initialized())
    self.assertIsNotNone(manager.run_group)
    self.assertIsNotNone(manager.run_id)
    self.assertIsNotNone(manager.location)
    self.assertIsNotNone(manager.project_id)
    self.assertIsNotNone(manager.logging_client)

    # Clear state
    manager.clear()

    # Verify cleared
    self.assertFalse(manager.is_initialized())
    self.assertIsNone(manager.run_group)
    self.assertIsNone(manager.run_id)
    self.assertIsNone(manager.location)
    self.assertIsNone(manager.project_id)
    self.assertIsNone(manager.logging_client)

  def test_run_group_property(self):
    """Test the run_group property getter."""
    manager = global_manager.GlobalRunManager()

    # Initially None
    self.assertIsNone(manager.run_group)

    # Create mock MLRun and initialize
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    manager.initialize(mock_mlrun)

    self.assertEqual(manager.run_group, "test_run_group")

  def test_run_id_property(
      self,
  ):
    """Test the run_id property getter."""
    manager = global_manager.GlobalRunManager()

    # Initially None
    self.assertIsNone(manager.run_id)

    # Create mock MLRun and initialize
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    manager.initialize(mock_mlrun)

    self.assertEqual(manager.run_id, "test_run_id")

  def test_location_property(
      self,
  ):
    """Test the location property getter."""
    manager = global_manager.GlobalRunManager()

    # Initially None
    self.assertIsNone(manager.location)

    # Create mock MLRun and initialize
    mock_mlrun = self._create_mock_mlrun()
    mock_mlrun.location = "us-west2"

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-west2/machineLearningRuns/test-run"
        )
    }

    manager.initialize(mock_mlrun)

    self.assertEqual(manager.location, "us-west2")

  def test_project_id_property(
      self,
  ):
    """Test the project_id property getter."""
    manager = global_manager.GlobalRunManager()

    # Initially None
    self.assertIsNone(manager.project_id)

    # Create mock MLRun and initialize
    mock_mlrun = self._create_mock_mlrun()
    mock_mlrun.project = "my_test_project"
    mock_mlrun.project_id = "my_test_project"

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/my_test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    manager.initialize(mock_mlrun)

    self.assertEqual(manager.project_id, "my_test_project")

  def test_logging_client_property(self):
    """Test the logging_client property getter."""
    manager = global_manager.GlobalRunManager()

    # Initially None
    self.assertIsNone(manager.logging_client)

    # Create mock MLRun
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    # Initialize and test
    mock_logging_client_instance = self.mock_logging_client.return_value
    manager.initialize(mock_mlrun)

    self.assertEqual(manager.logging_client, mock_logging_client_instance)

  def test_property_thread_safety(self):
    """Test that property access is thread-safe."""
    manager = global_manager.GlobalRunManager()

    # Create mock MLRun
    mock_mlrun = self._create_mock_mlrun()

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/test_project/locations/us-central1/machineLearningRuns/test-run"
        )
    }

    # Initialize with test data
    manager.initialize(mock_mlrun)

    results = []

    def access_properties():
      """Access properties and store results."""
      result = {
          "run_group": manager.run_group,
          "run_id": manager.run_id,
          "location": manager.location,
          "project_id": manager.project_id,
          "is_initialized": manager.is_initialized(),
      }
      results.append(result)

    # Create multiple threads accessing properties
    threads = []
    for _ in range(5):
      thread = threading.Thread(target=access_properties)
      threads.append(thread)

    # Start all threads
    for thread in threads:
      thread.start()

    # Wait for all threads to complete
    for thread in threads:
      thread.join()

    # All results should be the same
    expected_result = {
        "run_group": "test_run_group",
        "run_id": "test_run_id",
        "location": "us-central1",
        "project_id": "test_project",
        "is_initialized": True,
    }

    for result in results:
      self.assertEqual(result, expected_result)

  def test_concurrent_initialization(self):
    """Test concurrent initialization doesn't break singleton."""
    barrier = threading.Barrier(5)
    instances = []

    def concurrent_init():
      """Initialize instance after barrier synchronization."""
      barrier.wait()  # Synchronize thread start
      instance = global_manager.GlobalRunManager()
      instances.append(instance)

    threads = []
    for _ in range(5):
      thread = threading.Thread(target=concurrent_init)
      threads.append(thread)

    for thread in threads:
      thread.start()

    for thread in threads:
      thread.join()

    # All instances should be identical
    first_instance = instances[0]
    for instance in instances:
      self.assertIs(instance, first_instance)

  def test_concurrent_initialize_calls(self):
    """Test that concurrent initialize calls are thread-safe."""
    manager = global_manager.GlobalRunManager()
    barrier = threading.Barrier(3)

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/project/locations/location/machineLearningRuns/test-run"
        )
    }

    def concurrent_initialize(run_suffix):
      """Initialize with different MLRun instances concurrently."""
      barrier.wait()  # Synchronize thread start

      # Create mock MLRun for this thread
      mock_mlrun = self._create_mock_mlrun(f"_{run_suffix}")
      mock_mlrun.location = f"us-central{run_suffix}"
      mock_mlrun.project = f"project_{run_suffix}"
      mock_mlrun.project_id = f"project_{run_suffix}"

      manager.initialize(mock_mlrun)

    threads = []
    for i in range(3):
      thread = threading.Thread(target=concurrent_initialize, args=(i,))
      threads.append(thread)

    for thread in threads:
      thread.start()

    for thread in threads:
      thread.join()

    # Manager should be initialized (with values from one of the threads)
    self.assertTrue(manager.is_initialized())
    self.assertIsNotNone(manager.run_group)
    self.assertIsNotNone(manager.run_id)
    self.assertIsNotNone(manager.location)
    self.assertIsNotNone(manager.project_id)
    self.assertIsNotNone(manager.logging_client)

    # Should have been called 3 times (once per thread)
    self.assertEqual(self.mock_logging_client.call_count, 3)
    self.assertEqual(self.mock_control_plane_client.call_count, 3)
    self.assertEqual(self.mock_is_master_host.call_count, 3)

  def test_read_waits_for_initialize_to_complete(self):
    """Tests that property access begun during initialization waits for it to complete."""
    manager = global_manager.GlobalRunManager()
    mock_mlrun = self._create_mock_mlrun()

    # Event to pause initialization
    init_pause_event = threading.Event()
    # Event to signal that initialization has reached the blocking point
    init_blocked_event = threading.Event()

    # We pause during the instantiation of the logging client.
    def wait_then_return(*args, **kwargs):
      init_blocked_event.set()  # Signal that we are now blocked
      init_pause_event.wait(5)
      return self.mock_logging_client.return_value

    self.mock_logging_client.side_effect = wait_then_return

    results = {}

    def reader_task():
      # Wait until initialize is blocked in LoggingClient creation.
      init_blocked_event.wait(10)
      # Now, when we access properties, initialize should be holding the lock.
      results["run_id"] = manager.run_id
      results["logging_client"] = manager.logging_client
      results["is_initialized"] = manager.is_initialized()
      results["has_active_run"] = manager.has_active_run()

    init_thread = threading.Thread(
        target=manager.initialize, args=(mock_mlrun,)
    )
    reader_thread = threading.Thread(target=reader_task)

    init_thread.start()
    reader_thread.start()

    # Allow initialize to complete after reader thread
    # has started and is waiting.
    init_pause_event.set()

    init_thread.join(5)
    reader_thread.join(5)

    # If reader_task ran and completed before init_pause_event was set,
    # it would mean manager.run_id didn't block, and result would be None.
    # If manager.run_id blocked as expected, it waited until init completed,
    # so the result should be the initialized value.
    self.assertEqual(results.get("run_id"), "test_run_id")
    self.assertEqual(
        results.get("logging_client"), self.mock_logging_client.return_value
    )
    self.assertTrue(results.get("is_initialized"))
    self.assertTrue(results.get("has_active_run"))

  def test_is_initialized_thread_safety(self):
    """Test that is_initialized is thread-safe."""
    manager = global_manager.GlobalRunManager()
    results = []

    def check_initialization():
      """Check if manager is initialized."""
      result = manager.is_initialized()
      results.append(result)

    # All threads should see the same initialization state
    threads = []
    for _ in range(10):
      thread = threading.Thread(target=check_initialization)
      threads.append(thread)

    for thread in threads:
      thread.start()

    for thread in threads:
      thread.join()

    # All results should be the same (False, since not initialized)
    for result in results:
      self.assertFalse(result)

  def test_get_global_run_manager_function(self):
    """Test the module-level get_global_run_manager function."""
    manager1 = global_manager.get_global_run_manager()
    manager2 = global_manager.get_global_run_manager()
    manager3 = global_manager.GlobalRunManager()

    # All should return the same singleton instance
    self.assertIs(manager1, manager2)
    self.assertIs(manager1, manager3)

  def test_properties_handle_none_mlrun(self):
    """Test that properties handle the case when ml_run is None."""
    manager = global_manager.GlobalRunManager()

    # Before initialization, all properties should return None gracefully
    self.assertIsNone(manager.run_group)
    self.assertIsNone(manager.run_id)
    self.assertIsNone(manager.location)
    self.assertIsNone(manager.project_id)
    self.assertIsNone(manager.logging_client)

  def test_initialize_with_different_mlrun_types(self):
    """Test initialization with different MLRun configurations."""
    manager = global_manager.GlobalRunManager()

    # Test with minimal MLRun
    minimal_mlrun = mock.Mock()
    minimal_mlrun.run_group = "minimal_set"
    minimal_mlrun.name = "minimal_run"
    minimal_mlrun.location = None  # Test with None values
    minimal_mlrun.project = "minimal_project"
    minimal_mlrun.project_id = "minimal_project"
    minimal_mlrun.gcs_path = None
    minimal_mlrun.configs = None
    minimal_mlrun.run_phase = mock.Mock()
    minimal_mlrun.run_phase.value = "ACTIVE"

    # Mock the create_ml_run response
    self.mock_control_plane_client.return_value.create_ml_run.return_value = {
        "name": (
            "projects/minimal_project/locations/None/machineLearningRuns/test-run"
        )
    }

    manager.initialize(minimal_mlrun)

    self.assertTrue(manager.is_initialized())
    self.assertEqual(manager.run_group, "minimal_set")
    self.assertEqual(manager.run_id, "minimal_run")
    self.assertIsNone(manager.location)  # Should handle None gracefully
    self.assertEqual(manager.project_id, "minimal_project")


if __name__ == "__main__":
  unittest.main()
