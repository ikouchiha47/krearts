"""
Workflow Metrics Tracking

Tracks workflow performance and success rates.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cinema.workflow.models import VeoWorkflowType

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMetric:
    """Single workflow execution metric"""

    workflow_type: VeoWorkflowType
    scene_id: str
    success: bool
    generation_time: float
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class WorkflowMetrics:
    """Tracks workflow performance metrics"""

    def __init__(self):
        self.metrics: List[WorkflowMetric] = []

    def record_success(
        self, workflow_type: VeoWorkflowType, scene_id: str, generation_time: float
    ):
        """Record successful generation"""
        metric = WorkflowMetric(
            workflow_type=workflow_type,
            scene_id=scene_id,
            success=True,
            generation_time=generation_time,
        )
        self.metrics.append(metric)
        logger.info(
            f"✅ Recorded success: {workflow_type.value} for {scene_id} ({generation_time:.1f}s)"
        )

    def record_failure(
        self, workflow_type: VeoWorkflowType, scene_id: str, error_message: str
    ):
        """Record failed generation"""
        metric = WorkflowMetric(
            workflow_type=workflow_type,
            scene_id=scene_id,
            success=False,
            generation_time=0.0,
            error_message=error_message,
        )
        self.metrics.append(metric)
        logger.warning(
            f"❌ Recorded failure: {workflow_type.value} for {scene_id}: {error_message}"
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.metrics:
            return {}

        summary = {}
        for workflow_type in VeoWorkflowType:
            workflow_metrics = [
                m for m in self.metrics if m.workflow_type == workflow_type
            ]

            if not workflow_metrics:
                continue

            successes = [m for m in workflow_metrics if m.success]
            failures = [m for m in workflow_metrics if not m.success]

            summary[workflow_type.value] = {
                "total": len(workflow_metrics),
                "successes": len(successes),
                "failures": len(failures),
                "success_rate": (
                    len(successes) / len(workflow_metrics) if workflow_metrics else 0
                ),
                "avg_generation_time": (
                    sum(m.generation_time for m in successes) / len(successes)
                    if successes
                    else 0
                ),
            }

        return summary

    def export_to_json(self, output_path: str):
        """Export metrics to JSON file"""
        data = {
            "metrics": [
                {
                    "workflow_type": m.workflow_type.value,
                    "scene_id": m.scene_id,
                    "success": m.success,
                    "generation_time": m.generation_time,
                    "error_message": m.error_message,
                    "timestamp": m.timestamp,
                }
                for m in self.metrics
            ],
            "summary": self.get_summary(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"📊 Metrics exported to: {output_path}")
