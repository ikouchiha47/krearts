"""
Workflow Validator

Validates workflow parameters before API calls.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cinema.workflow.models import VeoWorkflowType

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """Validates workflow parameters before API calls"""

    def validate(
        self,
        workflow_type: VeoWorkflowType,
        parameters: Dict[str, Any],
        assets: Dict[str, str],
    ) -> Tuple[bool, List[str]]:
        """
        Validate workflow parameters.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
            errors.extend(self._validate_interpolation(parameters, assets))

        elif workflow_type == VeoWorkflowType.INGREDIENTS_TO_VIDEO:
            errors.extend(self._validate_ingredients(parameters, assets))

        elif workflow_type == VeoWorkflowType.TIMESTAMP_PROMPTING:
            errors.extend(self._validate_timestamp(parameters))

        # Common validations
        errors.extend(self._validate_duration(parameters))
        errors.extend(self._validate_incompatible_params(parameters))

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Validation failed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")

        return (is_valid, errors)

    def _validate_interpolation(
        self, params: Dict[str, Any], assets: Dict[str, str]
    ) -> List[str]:
        """Validate first and last frame interpolation parameters"""
        errors = []

        # Check required parameters
        if "image" not in params:
            errors.append("Missing 'image' parameter for interpolation")
        if "last_image" not in params:
            errors.append("Missing 'last_image' parameter for interpolation")

        # Check files exist
        if "image" in params and not self._file_exists(params["image"]):
            errors.append(f"First frame image not found: {params['image']}")
        if "last_image" in params and not self._file_exists(params["last_image"]):
            errors.append(f"Last frame image not found: {params['last_image']}")

        # Check incompatibility with reference_images
        if "reference_images" in params:
            errors.append(
                "Cannot use 'reference_images' with 'last_image' in interpolation workflow"
            )

        return errors

    def _validate_ingredients(
        self, params: Dict[str, Any], assets: Dict[str, str]
    ) -> List[str]:
        """Validate ingredients to video parameters"""
        errors = []

        # Check reference_images parameter
        if "reference_images" not in params:
            errors.append("Missing 'reference_images' parameter for ingredients workflow")
        else:
            ref_images = params["reference_images"]

            # Check count (max 3)
            if len(ref_images) > 3:
                errors.append(
                    f"Too many reference images: {len(ref_images)}. Maximum is 3."
                )

            # Check files exist
            for ref_img in ref_images:
                if not self._file_exists(ref_img):
                    errors.append(f"Reference image not found: {ref_img}")

        # Check incompatibility with last_image
        if "last_image" in params:
            errors.append(
                "Cannot use 'last_image' with 'reference_images' in ingredients workflow"
            )

        return errors

    def _validate_timestamp(self, params: Dict[str, Any]) -> List[str]:
        """Validate timestamp prompting parameters"""
        errors = []

        # Check duration constraint (max 8 seconds)
        duration = params.get("duration", 0)
        if duration > 8:
            errors.append(
                f"Timestamp prompting duration {duration}s exceeds maximum of 8s"
            )

        # Validate timestamp format in prompt
        prompt = params.get("prompt", "")
        if not self._has_valid_timestamps(prompt):
            errors.append(
                "Prompt does not contain valid timestamp notation [HH:MM:SS-HH:MM:SS]"
            )

        return errors

    def _validate_duration(self, params: Dict[str, Any]) -> List[str]:
        """Validate duration constraints"""
        errors = []
        duration = params.get("duration", 0)

        if duration < 4:
            errors.append(f"Duration {duration}s is below minimum of 4s")
        if duration > 8:
            errors.append(f"Duration {duration}s exceeds maximum of 8s")

        return errors

    def _validate_incompatible_params(self, params: Dict[str, Any]) -> List[str]:
        """Check for incompatible parameter combinations"""
        errors = []

        # last_image and reference_images are mutually exclusive
        if "last_image" in params and "reference_images" in params:
            errors.append(
                "Parameters 'last_image' and 'reference_images' are mutually exclusive"
            )

        return errors

    @staticmethod
    def _file_exists(path: str) -> bool:
        """Check if file exists"""
        return Path(path).exists()

    @staticmethod
    def _has_valid_timestamps(prompt: str) -> bool:
        """Check if prompt contains valid timestamp notation"""
        pattern = r"\[\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}\]"
        return bool(re.search(pattern, prompt))
