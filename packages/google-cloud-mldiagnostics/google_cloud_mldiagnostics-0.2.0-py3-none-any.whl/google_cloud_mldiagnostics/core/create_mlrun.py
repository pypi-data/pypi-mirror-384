"""Module for registering and managing ML runs."""

import datetime
import logging
import threading
from typing import Any

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import global_manager
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import metrics
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import metric_types
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import mlrun_types
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import config_utils
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import gcp
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import host_utils
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import metric_utils


_METRICS_RECORDER_THREAD_LOCK = threading.Lock()
_METRICS_RECORDER_THREAD_STARTED = False


def initialize_mlrun(
    run_group: str,
    name: str | None = None,
    configs: dict[str, Any] | None = None,
    gcs_path: str | None = None,
    gcp_project: str | None = None,
    gcp_region: str | None = None,
    metrics_record_interval_sec: float = 10.0,
) -> mlrun_types.MLRun:
  """Initializes a new ML run.

  Args:
      run_group: The run set this run belongs to.
      name: The name of the run.
      configs: Dictionary of configuration parameters.
      gcs_path: GCS path for storing run artifacts.
      gcp_project: The GCP project ID.
      gcp_region: The GCP region.
      metrics_record_interval_sec: The metrics record interval in seconds.

  Returns:
      The initialized ML run object.
  """
  # Combine default configs with user configs.
  software_configs = config_utils.get_software_config()
  hardware_configs = config_utils.get_hardware_config()
  configs = mlrun_types.ConfigDict({
      "softwareConfigs": software_configs,
      "hardwareConfigs": hardware_configs,
      "userConfigs": configs if configs else {},
  })

  if gcp_region is None:
    gcp_region = gcp.get_instance_region()
  if gcp_project is None:
    gcp_project = gcp.get_project_id()

  # TODO(b/428025390): Add support for checking the repetitive registered ML
  # name in Spanner after control plane client ready.
  # Otherwise, generate new UUID.

  created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
  run_phase = mlrun_types.RunPhase.PHASE_ACTIVE
  workload_details = host_utils.get_workload_details()

  # Generate unique identifier for the run if not provided.
  # TODO: b/444305756 - Add support for non-GKE workloads.
  if name is None:
    name = host_utils.get_identifier(workload_details)

  ml_run = mlrun_types.MLRun(
      run_group=run_group,
      name=name,
      configs=configs,
      gcs_path=gcs_path,
      location=gcp_region,
      project=gcp_project,
      run_phase=run_phase,
      created_at=created_at,
      workload_details=workload_details,
  )

  # register the run to global manager.
  manager = global_manager.get_global_run_manager()
  manager.initialize(ml_run)

  diagon_url = create_diagnostics_url(gcp_region, gcp_project, name)
  xprof_url = create_xprof_url(diagon_url)
  logging.info(
      "Diagon SDK is in experimental mode, to visualize the run, please go to\n"
      "%s\n",
      diagon_url,
  )
  logging.info(
      "Xprof profiling url:\n%s\n",
      xprof_url,
  )

  global _METRICS_RECORDER_THREAD_STARTED
  if not _METRICS_RECORDER_THREAD_STARTED:
    with _METRICS_RECORDER_THREAD_LOCK:
      if not _METRICS_RECORDER_THREAD_STARTED:
        # Avoid starting the metrics recorder thread repeatedly if the run is
        # already initialized.
        default_metrics_recorder = metrics.MetricsRecorderThread(
            metric_collectors=[
                (
                    metric_types.MetricType.TPU_DUTY_CYCLE.value,
                    metric_utils.get_tpu_duty_cycle,
                ),
                (
                    metric_types.MetricType.TPU_TENSORCORE_UTILIZATION.value,
                    metric_utils.get_tpu_tensorcore_utilization,
                ),
                (
                    metric_types.MetricType.HBM_UTILIZATION.value,
                    metric_utils.get_hbm_utilization,
                ),
                (
                    metric_types.MetricType.HOST_CPU_UTILIZATION.value,
                    metric_utils.get_host_cpu_utilization,
                ),
                (
                    metric_types.MetricType.HOST_MEMORY_UTILIZATION.value,
                    metric_utils.get_host_memory_utilization,
                ),
            ],
            labels={"hostname": "host" + str(host_utils.get_host_index())},
            interval_seconds=metrics_record_interval_sec,
        )
        default_metrics_recorder.start()
        _METRICS_RECORDER_THREAD_STARTED = True

  return ml_run


def create_diagnostics_url(gcp_region: str, gcp_project: str, name: str) -> str:
  return f"https://console.cloud.google.com/cluster-director/diagnostics/details/{gcp_region}/{name}?project={gcp_project}"


def create_xprof_url(diagon_url: str) -> str:
  return diagon_url + "&pageState=(%22nav%22:(%22section%22:%22profiles%22))"
