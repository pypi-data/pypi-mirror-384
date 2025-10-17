import logging
import os
from typing import NamedTuple

import boto3

from labels.model.core import SourceType

LOGGER = logging.getLogger(__name__)


class ExecutionMetrics(NamedTuple):
    """Metrics collected during execution.

    Attributes:
       group: Group identifier for the metrics
       technique_time: Execution time in seconds

    """

    group: str
    technique_time: float


def is_fluid_batch_env() -> bool:
    return "FLUIDATTACKS_EXECUTION" in os.environ


def process_sbom_metrics(
    execution_id: str | None,
    technique_time: float,
    source_type: SourceType,
) -> None:
    try:
        if (
            source_type == SourceType.DIRECTORY
            and execution_id is not None
            and is_fluid_batch_env()
            and (execution_id_parts := execution_id.split("_"))
            and len(execution_id_parts) >= 3
        ):
            metrics = ExecutionMetrics(
                group=execution_id_parts[0],
                technique_time=round(technique_time, 2),
            )
            send_metrics_to_cloudwatch(metrics)
    except Exception as exc:
        LOGGER.exception(
            "Unable to send metrics to cloudwatch",
            extra={
                "extra": {
                    "exception": str(exc),
                },
            },
        )


def send_metrics_to_cloudwatch(execution_metrics: ExecutionMetrics) -> None:
    try:
        dimensions = [
            {"Name": "Group", "Value": execution_metrics.group},
        ]

        metric_data = [
            {
                "MetricName": "ExecutionTime",
                "Dimensions": dimensions,
                "Value": execution_metrics.technique_time,
                "Unit": "Seconds",
            },
        ]

        cloudwatch_client = boto3.client("cloudwatch", "us-east-1")  # type: ignore[misc]
        cloudwatch_client.put_metric_data(  # type: ignore[misc]
            Namespace="LabelsMetrics",
            MetricData=metric_data,
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Unable to send metrics to cloudwatch: %s", exc)
