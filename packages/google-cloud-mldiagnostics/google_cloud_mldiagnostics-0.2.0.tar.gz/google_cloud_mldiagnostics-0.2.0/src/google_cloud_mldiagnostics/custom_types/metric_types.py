"""Metric type definitions."""

import enum


class MetricType(enum.Enum):
  """Predefined metric types for ML training."""

  # Model quality metrics
  LEARNING_RATE = "learning_rate"
  LOSS = "loss"
  GRADIENT_NORM = "gradient_norm"
  TOTAL_WEIGHTS = "total_weights"

  # Model performance metrics
  STEP_TIME = "step_time"
  THROUGHPUT = "throughput"
  LATENCY = "latency"
  MFU = "mfu"  # Model FLOPs Utilization
  TFLOPS = "tflops"

  # System utilization metrics
  TPU_DUTY_CYCLE = "tpu_duty_cycle"
  TPU_TENSORCORE_UTILIZATION = "tpu_tensorcore_utilization"
  HBM_UTILIZATION = "hbm_utilization"
  HOST_CPU_UTILIZATION = "host_cpu_utilization"
  HOST_MEMORY_UTILIZATION = "host_memory_utilization"

  # Step metrics, system will recocord step metric automatically when invoking
  # other metrics with step information. However, if there is a need to record
  # step separate, use this metric type.
  STEP = "step"
