"""Custom exception classes."""


class MLDiagnosticError(Exception):
  """Base exception for ML Diagnostic SDK."""
  pass


class MLRunConfigurationError(ValueError):
  """Exception raised for ML run configuration errors."""
  pass


class RecordingError(ValueError):
  """Exception raised for recording metrics."""

  pass


class NoActiveRunError(Exception):
  """Raised when no active ML run is found."""

  pass


class ProfilingError(Exception):
  """Raised when profiling fails."""

  pass
