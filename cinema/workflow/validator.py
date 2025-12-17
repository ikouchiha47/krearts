"""Workflow state validation for enforcing prerequisites."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from cinema.workflow.interface import WorkflowState, WorkflowStage


class ValidationResult(BaseModel):
    """Result of state validation."""
    valid: bool
    current_state: Dict[str, Any]
    missing_prerequisites: List[str] = []
    message: Optional[str] = None
    available_actions: List[Dict[str, str]] = []
    blocked_actions: List[str] = []


class WorkflowStateValidator:
    """Validates workflow state transitions and prerequisites."""
    
    # Define prerequisites for each operation
    PREREQUISITES = {
        "generate_content": {
            "requires": ["storyline_done"],
            "message": "Complete storyline generation first (POST /workflows/book/init)"
        },
        "generate_cover": {
            "requires": ["content_done"],
            "message": "Generate novel content first (POST /workflows/{workflow_id}/content)"
        },
        "generate_characters": {
            "requires": ["content_done"],
            "message": "Generate novel content first (POST /workflows/{workflow_id}/content)"
        },
        "generate_chapters": {
            "requires": ["content_done", "characters_generated"],
            "message": "Generate characters first - needed for consistent character appearance in pages"
        },
        "generate_chapter_cover": {
            "requires": ["chapters_generated"],
            "message": "Generate chapters first"
        },
        "generate_pages": {
            "requires": ["chapters_generated", "characters_generated"],
            "message": "Generate chapters and characters first"
        }
    }
    
    # Define available actions for each state
    AVAILABLE_ACTIONS = {
        "storyline_done": [
            {
                "action": "generate_content",
                "endpoint": "POST /workflows/{workflow_id}/content",
                "description": "Generate novel (prose chapters from storyline)"
            }
        ],
        "content_done": [
            {
                "action": "generate_cover",
                "endpoint": "POST /workflows/{workflow_id}/cover",
                "description": "Generate book cover image (optional)"
            },
            {
                "action": "generate_characters",
                "endpoint": "POST /workflows/{workflow_id}/characters/generate",
                "description": "Generate character reference images (required for chapters)"
            }
        ],
        "characters_generated": [
            {
                "action": "generate_chapters",
                "endpoint": "POST /workflows/{workflow_id}/chapters",
                "description": "Generate comic chapters (visual storyboards)"
            }
        ],
        "chapters_generated": [
            {
                "action": "generate_pages",
                "endpoint": "POST /workflows/{workflow_id}/pages",
                "description": "Generate page images"
            },
            {
                "action": "generate_chapter_cover",
                "endpoint": "POST /workflows/{workflow_id}/chapters/{chapter_number}/cover",
                "description": "Generate cover for specific chapter (optional)"
            }
        ]
    }
    
    def validate_operation(
        self, 
        workflow_state: WorkflowState, 
        operation: str
    ) -> ValidationResult:
        """
        Validate if operation can be performed given current state.
        
        Args:
            workflow_state: Current workflow state
            operation: Operation to validate (e.g., "generate_chapters")
        
        Returns:
            ValidationResult with validation status and guidance
        """
        prereqs = self.PREREQUISITES.get(operation)
        if not prereqs:
            # Unknown operation - allow it
            return ValidationResult(
                valid=True,
                current_state=self._get_state_dict(workflow_state)
            )
        
        # Check all prerequisites
        missing = []
        for req in prereqs["requires"]:
            if req == "chapters_generated":
                # Special case: check if any chapters generated
                if not workflow_state.chapters_generated:
                    missing.append(req)
            else:
                # Boolean flags
                if not getattr(workflow_state, req, False):
                    missing.append(req)
        
        if missing:
            return ValidationResult(
                valid=False,
                current_state=self._get_state_dict(workflow_state),
                missing_prerequisites=missing,
                message=prereqs["message"],
                available_actions=self._get_available_actions(workflow_state)
            )
        
        return ValidationResult(
            valid=True,
            current_state=self._get_state_dict(workflow_state)
        )
    
    def _get_state_dict(self, state: WorkflowState) -> Dict[str, Any]:
        """Get current state as dict."""
        return {
            "stage": state.current_stage.value,
            "storyline_done": state.storyline_done,
            "content_done": state.content_done,
            "cover_generated": state.cover_generated,
            "characters_generated": state.characters_generated,
            "chapters_generated": state.chapters_generated,
            "pages_generated": state.pages_generated,
        }
    
    def _get_available_actions(self, state: WorkflowState) -> List[Dict[str, str]]:
        """Get list of available actions based on current state."""
        actions = []
        
        if state.storyline_done and not state.content_done:
            actions.extend(self.AVAILABLE_ACTIONS["storyline_done"])
        
        if state.content_done and not state.characters_generated:
            actions.extend(self.AVAILABLE_ACTIONS["content_done"])
        
        if state.characters_generated and not state.chapters_generated:
            actions.extend(self.AVAILABLE_ACTIONS["characters_generated"])
        
        if state.chapters_generated:
            actions.extend(self.AVAILABLE_ACTIONS["chapters_generated"])
        
        return actions
    
    def _get_blocked_actions(self, state: WorkflowState) -> List[str]:
        """Get list of blocked actions based on current state.
        
        Checks prerequisites directly without calling validate_operation
        to avoid infinite recursion.
        """
        blocked = []
        
        for operation, prereqs in self.PREREQUISITES.items():
            # Check prerequisites directly
            missing = []
            for req in prereqs["requires"]:
                if req == "chapters_generated":
                    if not state.chapters_generated:
                        missing.append(req)
                else:
                    # Boolean flags
                    if not getattr(state, req, False):
                        missing.append(req)
            
            # If any prerequisites are missing, operation is blocked
            if missing:
                blocked.append(operation)
        
        return blocked
