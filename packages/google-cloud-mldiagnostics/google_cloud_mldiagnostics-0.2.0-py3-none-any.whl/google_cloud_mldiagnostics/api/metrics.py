"""Module for recording metrics."""

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import metrics
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import metric_types


_metrics_recorder = metrics.metrics_recorder


def record(
    metric_name: metric_types.MetricType or str,
    value: int | float,
    step: int | None = None,
    labels: dict[str, str] | None = None,
    record_on_all_hosts: bool = False,
) -> None:
  """Record a single metric value using the active run.

  Args:
      metric_name: Name of metric to record.
      value: Metric value.
      step: Optional step number (auto-incremented if not provided).
      labels: Optional additional labels.
      record_on_all_hosts: Whether to record metrics on all hosts.

  Raises:
      RecordingError: If no active run or recording fails.

  Example:
      metrics.record(MetricType.TF_FLOPS, per_device_tf_flops)
      metrics.record(MetricType.LEARNING_RATE, learning_rate)
      metrics.record(MetricType.LEARNING_RATE, learning_rate, step=1)
  """
  is_enum = isinstance(metric_name, metric_types.MetricType)
  metric_name = metric_name.value if is_enum else metric_name
  _metrics_recorder.record(
      metric_name, value, step, labels, record_on_all_hosts
  )
