"""Module for creating and managing ML runs."""
from typing import Any

from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.core import create_mlrun
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import exceptions
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.custom_types import mlrun_types


# Main SDK function - this is the primary interface users will import
def machinelearning_run(
    run_group: str,
    name: str | None = None,
    configs: dict[str, Any] | None = None,
    gcs_path: str | None = None,
    gcp_project: str | None = None,
    gcp_region: str | None = None,
    metrics_record_interval_sec: float = 10.0,
) -> mlrun_types.MLRun:
  """Create a new machine learning run.

  This is the main entry point for the SDK that users will call to create ML
  runs.

  Args:
      run_group: The run set this run belongs to
      name: The name of the run (optional), system will generate a unique ID if
        not provided by users.
      configs: dict of configuration parameters
      gcs_path: GCS path for storing run artifacts
      gcp_project: The GCP project ID
      gcp_region: The GCP region
      metrics_record_interval_sec: The interval in seconds
        for recording system metrics backend (tpu duty cycle,
        tpu tensorcore utilization, hbm utilization,
        host cpu utilization, host memory utilization).

  Returns:
      MLRun: A new ML run instance

  Example:
      from google_cloud_mldiagnostics import machinelearning_run

      my_run = machinelearning_run(
            run_group="training_set_v1",
            name="experiment_1",
            configs={"epochs": 100, "batch_size": 32},
            gcs_path="gs://my-bucket/experiments"
        )

      # Update configs using dict methods
      my_run.configs.update({"epochs": 300, "optimizer": "adam"})

      # Update configs using attribute notation
      my_run.configs.batch_size = 64
  """
  if not run_group:
    raise exceptions.MLRunConfigurationError(
        "run_group is required and must be provided. The run_group parameter"
        " helps identify and organize your ML workloads. Please provide a"
        " meaningful run_group name (e.g., 'training_v1',"
        " 'experiment_batch_1')."
    )
  return create_mlrun.initialize_mlrun(
      run_group=run_group,
      name=name,
      configs=configs,
      gcs_path=gcs_path,
      gcp_project=gcp_project,
      gcp_region=gcp_region,
      metrics_record_interval_sec=metrics_record_interval_sec,
  )
