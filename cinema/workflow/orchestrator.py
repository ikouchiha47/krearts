"""
Veo Workflow Orchestrator

Coordinates workflow selection, validation, and execution.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

from cinema.providers.gemini import GeminiMediaGen
from cinema.workflow.classifier import WorkflowClassifier
from cinema.workflow.metrics import WorkflowMetrics
from cinema.workflow.models import WorkflowClassification, WorkflowConfig
from cinema.workflow.parameter_builder import WorkflowParameterBuilder
from cinema.workflow.validator import WorkflowValidator

logger = logging.getLogger(__name__)


class VeoWorkflowOrchestrator:
    """Orchestrates the complete workflow selection and execution process"""

    def __init__(
        self,
        gemini_client: GeminiMediaGen,
        config: Optional[WorkflowConfig] = None,
    ):
        self.gemini = gemini_client
        self.config = config or WorkflowConfig()
        self.classifier = WorkflowClassifier(self.config)
        self.param_builder = WorkflowParameterBuilder()
        self.validator = WorkflowValidator()
        self.metrics = WorkflowMetrics()

    async def generate_video_with_workflow(
        self, scene: Dict[str, Any], assets: Dict[str, str]
    ) -> Tuple[str, WorkflowClassification]:
        """
        Complete workflow: classify, validate, and generate video.

        Args:
            scene: Scene metadata
            assets: Available asset paths

        Returns:
            (video_path, workflow_classification)
        """
        scene_id = scene.get("scene_id", "unknown")

        # Step 1: Classify workflow
        logger.info(f"🎯 Step 1: Classifying workflow for {scene_id}")
        classification = self.classifier.classify_scene(scene, assets)
        logger.info(f"   Selected: {classification.workflow_type.value}")
        logger.info(f"   Reason: {classification.reason}")

        if classification.warnings:
            for warning in classification.warnings:
                logger.warning(f"   ⚠️  {warning}")

        # Step 2: Build parameters
        logger.info("📋 Step 2: Building parameters")
        try:
            params = self.param_builder.build_parameters(
                classification.workflow_type, scene, assets
            )
            logger.debug(f"   Parameters: {list(params.keys())}")
        except Exception as e:
            logger.error(f"❌ Parameter building failed: {e}")
            self.metrics.record_failure(
                classification.workflow_type, scene_id, f"Parameter building: {e}"
            )
            raise

        # Step 3: Validate
        logger.info("✓ Step 3: Validating parameters")
        is_valid, errors = self.validator.validate(
            classification.workflow_type, params, assets
        )

        if not is_valid:
            error_msg = "\n".join(errors)
            logger.error(f"❌ Validation failed:\n{error_msg}")
            self.metrics.record_failure(
                classification.workflow_type, scene_id, f"Validation: {error_msg}"
            )
            raise ValueError(f"Workflow validation failed: {error_msg}")

        logger.info("   ✅ Validation passed")

        # Step 4: Execute generation
        logger.info(
            f"🎬 Step 4: Generating video with {classification.workflow_type.value}"
        )
        start_time = time.time()

        try:
            response = await self.gemini.generate_video(**params)

            output_path = f"output/{scene_id}.mp4"
            video_path = await self.gemini.render_video(output_path, response)

            generation_time = time.time() - start_time

            # Track metrics
            self.metrics.record_success(
                classification.workflow_type, scene_id, generation_time
            )

            logger.info(f"✅ Video generated in {generation_time:.1f}s: {video_path}")
            return video_path, classification

        except Exception as e:
            generation_time = time.time() - start_time

            # Track failure
            self.metrics.record_failure(classification.workflow_type, scene_id, str(e))

            logger.error(f"❌ Generation failed after {generation_time:.1f}s: {e}")
            raise

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get workflow metrics summary"""
        return self.metrics.get_summary()

    def export_metrics(self, output_path: str):
        """Export metrics to JSON file"""
        self.metrics.export_to_json(output_path)
