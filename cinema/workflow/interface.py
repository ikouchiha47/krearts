"""
Workflow Interface - Core abstraction for incremental content generation.

This provides a unified interface for:
- Book generation (storyline -> novel -> chapters -> pages)
- Screenplay generation (storyline -> screenplay -> scenes)

Each stage can be run incrementally with --continue support.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class WorkflowStage(str, Enum):
    """Workflow stages"""
    INIT = "init"  # Generate storyline (up to critique)
    CONTENT = "content"  # Generate book/screenplay
    CHAPTERS = "chapters"  # Generate comic chapters
    PAGES = "pages"  # Generate page images


class WorkflowType(str, Enum):
    """Content type"""
    BOOK = "book"
    SCREENPLAY = "screenplay"


class WorkflowState(BaseModel):
    """Workflow state tracking"""
    id: str
    type: WorkflowType
    current_stage: WorkflowStage
    storyline_done: bool = False
    content_done: bool = False
    chapters_generated: List[int] = []
    pages_generated: List[int] = []
    output_dir: str
    
    # Configuration (includes skipper settings)
    config: Dict[str, Any] = {}
    
    def save(self):
        """Save state to disk"""
        import json
        state_file = Path(self.output_dir) / "workflow_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
    
    @classmethod
    def load(cls, workflow_id: str, workflow_type: WorkflowType) -> Optional["WorkflowState"]:
        """Load state from disk"""
        import json
        output_dir = f"output/{workflow_type.value}_{workflow_id}"
        state_file = Path(output_dir) / "workflow_state.json"
        
        if not state_file.exists():
            return None
        
        with open(state_file, 'r') as f:
            data = json.load(f)
        
        return cls(**data)


class WorkflowInterface(ABC):
    """
    Abstract interface for workflow operations.
    
    Implementations:
    - BookWorkflow: Storyline -> Novel -> Chapters -> Pages
    - ScreenplayWorkflow: Storyline -> Screenplay -> Scenes
    """
    
    def __init__(self, workflow_id: str, workflow_type: WorkflowType):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.output_dir = f"output/{workflow_type.value}_{workflow_id}"
        
        # Load or create state
        self.state = WorkflowState.load(workflow_id, workflow_type)
        if not self.state:
            self.state = WorkflowState(
                id=workflow_id,
                type=workflow_type,
                current_stage=WorkflowStage.INIT,
                output_dir=self.output_dir
            )
    
    @abstractmethod
    async def init(self, **kwargs) -> Dict[str, Any]:
        """
        Stage 1: Generate storyline (up to critique).
        
        Returns:
            {"storyline": str, "critique": str}
        """
        pass
    
    @abstractmethod
    async def generate_content(self, continue_from: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Stage 2: Generate book/screenplay from storyline.
        
        Args:
            continue_from: Continue from saved state
        
        Returns:
            {"content": str, "type": "book" | "screenplay"}
        """
        pass
    
    @abstractmethod
    async def generate_chapters(
        self, 
        chapters: Optional[List[int]] = None,
        continue_from: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Stage 3: Generate comic chapters.
        
        Args:
            chapters: Specific chapters to generate (e.g., [1, 5])
            continue_from: Continue from last generated chapter
        
        Returns:
            {"chapters": List[int], "output_dir": str}
        """
        pass
    
    @abstractmethod
    async def generate_pages(
        self,
        pages: Optional[List[int]] = None,
        continue_from: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Stage 4: Generate page images.
        
        Args:
            pages: Specific pages to generate (e.g., [1, 20])
            continue_from: Continue from last generated page
        
        Returns:
            {"pages": List[int], "output_dir": str}
        """
        pass
    
    def get_state(self) -> WorkflowState:
        """Get current workflow state"""
        return self.state
    
    def save_state(self):
        """Save workflow state"""
        self.state.save()
