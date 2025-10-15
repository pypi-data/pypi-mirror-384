"""Client for sending requests to Diagon Control Plane."""

import re
from typing import Any, Dict, List, Optional

import google.auth
from google.auth.transport import requests as google_auth_requests
from google_cloud_mldiagnostics.src.google_cloud_mldiagnostics.utils import host_utils
import requests


class ControlPlaneClient:
  """Client for communicating with Google Cloud Hypercompute Cluster ML Run service."""

  def __init__(
      self,
      project_id: str = "supercomputer-testing",
      location: str = "us-central1",
      base_url: str = "https://autopush-hypercomputecluster.sandbox.googleapis.com/v1alpha",
  ):
    """Initializes a new ControlPlaneClient.

    Args:
        project_id: Google Cloud project ID
        location: Google Cloud location/region
        base_url: Base URL for the API endpoint
    """
    self.project_id = project_id
    self.location = location
    self.base_url = base_url
    self.ml_runs_url = f"{base_url}/projects/{project_id}/locations/{location}/machineLearningRuns"

    # Initialize Google Cloud credentials
    self.credentials, _ = google.auth.default()

  def _get_access_token(self) -> str:
    """Get Google Cloud access token for authentication."""
    if not self.credentials.valid:
      self.credentials.refresh(google_auth_requests.Request())

    return self.credentials.token

  def _get_headers(self) -> Dict[str, str]:
    """Get HTTP headers with authentication."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self._get_access_token()}",
    }

  def create_ml_run(
      self,
      name: str,
      display_name: str,
      run_phase: str,
      configs: Optional[Dict[str, Any]] = None,
      tools: Optional[List[Dict[str, Any]]] = None,
      metrics: Optional[Dict[str, str]] = None,
      artifacts: Optional[Dict[str, str]] = None,
      run_group: Optional[str] = None,
      labels: Optional[Dict[str, str]] = None,
  ) -> Dict[str, Any]:
    """Create a new ML run using the Google Cloud API.

    Args:
        name: Name of the run
        display_name: Display name for the run
        run_phase: Phase of the run (ACTIVE, COMPLETE, FAILED)
        configs: Configuration settings (userConfigs, softwareConfigs,
          hardwareConfigs)
        tools: List of tools to enable (e.g., XProf, NSys)
        metrics: Metrics for the run (e.g., avgStep, avgLatency)
        artifacts: Artifacts configuration (e.g., gcsPath)
        run_group: Run group grouping identifier
        labels: Custom labels for the run

    Returns:
        Response from the API as a dictionary

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails
    """
    payload = {"displayName": display_name, "name": name}

    if configs:
      payload["configs"] = configs

    if metrics:
      payload["metrics"] = metrics

    if artifacts:
      payload["artifacts"] = artifacts

    if run_group:
      payload["runSet"] = run_group

    if labels:
      payload["labels"] = labels

    if run_phase:
      payload["runPhase"] = run_phase

    if tools:
      payload["tools"] = tools

    # Sanitize the name for machineLearningRunId
    sanitized_name = host_utils.sanitize_identifier(name)

    params = {"machine_learning_run_id": sanitized_name}

    response = requests.post(
        self.ml_runs_url,
        headers=self._get_headers(),
        params=params,
        json=payload,
    )

    # Raise an exception for HTTP error status codes
    response.raise_for_status()

    return response.json()

  def update_ml_run(
      self
  ) -> None:
    """Update an existing ML run using the Google Cloud API."""
    del self
    pass
