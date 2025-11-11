"""
Workflow Selection Data Models and Enums

Defines data structures for workflow classification, configuration,
and execution tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class VeoWorkflowType(Enum):
    """Enumeration of supported Veo workflow types"""
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_INTERPOLATION = "first_last_frame_interpolation"
    INGREDIENTS_TO_VIDEO = "ingredients_to_video"
    TIMESTAMP_PROMPTING = "timestamp_prompting"


class WorkflowSelectionMode(Enum):
    """How to select workflow when multiple options are valid"""
    CONFIG_DEFAULT = "config_default"  # Use configured default
    LLM_INTELLIGENT = "llm_intelligent"  # Use LLM to decide
    ALWAYS_INTERPOLATION = "always_interpolation"  # Force interpolation
    ALWAYS_INGREDIENTS = "always_ingredients"  # Force ingredients
    AB_TEST = "ab_test"  # Generate with both workflows


@dataclass
class WorkflowClassification:
    """Result of workflow classification"""
    workflow_type: VeoWorkflowType
    reason: str
    required_assets: List[str]
    confidence: float  # 0.0 to 1.0
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return (
            f"WorkflowClassification("
            f"type={self.workflow_type.value}, "
            f"confidence={self.confidence:.2f}, "
            f"reason='{self.reason}'"
            f")"
        )


@dataclass
class WorkflowConfig:
    """Configuration for workflow selection"""
    
    # Workflow selection mode
    selection_mode: WorkflowSelectionMode = WorkflowSelectionMode.LLM_INTELLIGENT
    
    # Default workflow when both interpolation and ingredients are valid
    default_workflow: VeoWorkflowType = VeoWorkflowType.INGREDIENTS_TO_VIDEO
    
    # Enable/disable specific workflows
    enable_interpolation: bool = True
    enable_ingredients: bool = True
    enable_timestamp: bool = True
    
    # LLM-based decision settings
    use_llm_for_workflow_decision: bool = True
    llm_model: str = "gemini-2.0-flash-exp"
    
    # A/B testing settings
    ab_test_enabled: bool = False
    ab_test_output_dir: str = "output/ab_test"
    
    # Interpolation quality thresholds
    interpolation_quality_threshold: float = 0.6  # 0.0 to 1.0
    
    # Validation settings
    strict_validation: bool = True
    allow_missing_assets: bool = False
    
    # Performance settings
    enable_classification_cache: bool = True
    max_reference_images: int = 3
    
    # Logging
    log_workflow_decisions: bool = True
    export_metrics: bool = True
    metrics_output_path: str = "output/workflow_metrics.json"
