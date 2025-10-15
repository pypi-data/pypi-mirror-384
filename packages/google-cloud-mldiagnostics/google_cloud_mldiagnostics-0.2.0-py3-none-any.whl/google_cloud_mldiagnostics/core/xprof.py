"""JAX profiling SDK wrapper for Google Cloud ML Diagnostics."""

import logging

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import exceptions
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import mlrun_types
import jax


logger = logging.getLogger(__name__)


class Xprof:
  """Wrapper for JAX profiling with Google Cloud ML Diagnostics.

  Supports:
  - Object-oriented API (prof.start(), prof.stop())
  - Context manager (with Xprof() as prof:)
  - Decorator (@Xprof())
  """

  def __init__(
      self,
      run: mlrun_types.MLRun | None = None,
  ):
    """Initializes the xprof profiler.

    Args:
        run: An instance of machinelearning_run to associate the profile with.
          If None, retrieve from global manager when needed.
    """
    # Store input run but don't resolve until needed (lazy initialization)
    self._input_run = run
    self._resolved_run = None
    self._is_profiling = False
    self._gcs_profile_dir = None
    self._initialized = False

  def _ensure_initialized(self):
    """Lazy initialization - resolve run and setup directories when needed."""
    if self._initialized:
      return

    # Resolve the run now (at usage time, not construction time)
    self._resolved_run = (
        self._input_run
        if self._input_run is not None
        else global_manager.get_current_run()
    )

    if self._resolved_run is None:
      raise exceptions.ProfilingError(
          "No MLRun found for profiling. Please provide a valid MLRun with"
          " a GCS path, or initialize the global manager with a valid MLRun."
      )

    if self._resolved_run.gcs_path is None:
      raise exceptions.ProfilingError(
          "No GCS path found for profiling. Please provide a valid MLRun with"
          " a GCS path."
      )

    # Set up the GCS directory path
    identifier = self._resolved_run.name
    self._gcs_profile_dir = (
        f"{self._resolved_run.gcs_path}/diagon/xprof/{identifier}"
    )
    print(
        "xprof initialized. Profiling output path set to:"
        f" {self._gcs_profile_dir}"
    )

    self._initialized = True

  def start(self):
    """Starts the JAX profiler."""
    # Ensure initialization happens before starting
    self._ensure_initialized()

    if self._is_profiling:
      print("Warning: Profiling is already active. Call stop() first.")
      return

    print(f"Starting JAX profiling to: {self._gcs_profile_dir}")
    try:
      jax.profiler.start_trace(self._gcs_profile_dir)
      self._is_profiling = True
      logger.info("profiling_status: started")
    except exceptions.ProfilingError as e:
      print(f"Error starting JAX profiler: {e}")
      self._is_profiling = False

  def stop(self):
    """Stops the JAX profiler."""
    if not self._is_profiling:
      print("Warning: No active profiling session to stop.")
      return

    print(f"Stopping JAX profiling for: {self._gcs_profile_dir}")
    try:
      jax.profiler.stop_trace()
      self._is_profiling = False
      logger.info("profiling_status: stopped")
      logger.info(
          "profiling traces should be available at: %s", self._gcs_profile_dir
      )
    except exceptions.ProfilingError as e:
      print(f"Error stopping JAX profiler: {e}")

  def __enter__(self):
    """Context manager entry point."""
    # Ensure initialization happens before entering context
    self._ensure_initialized()

    self._trace_context_manager = jax.profiler.trace(self._gcs_profile_dir)
    print(f"Entering xprof context for: {self._gcs_profile_dir}")
    self._trace_context_manager.__enter__()
    self._is_profiling = True
    logger.info("profiling_status: context_started")
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit point."""
    print(f"Exiting xprof context for: {self._gcs_profile_dir}")
    self._trace_context_manager.__exit__(exc_type, exc_val, exc_tb)
    self._is_profiling = False
    logger.info("profiling_status: context_stopped")
    logger.info(
        "profiling traces should be available at: %s",
        self._gcs_profile_dir,
    )

  def __call__(self, func):
    """Decorator for profiling a function."""

    def wrapper(*args, **kwargs):
      # Ensure initialization happens when the decorated function is called,
      # not when the decorator is applied
      self._ensure_initialized()

      print(f"Profiling function '{func.__name__}' with xprof decorator.")
      self.start()
      try:
        result = func(*args, **kwargs)
      finally:
        self.stop()
      return result

    return wrapper
