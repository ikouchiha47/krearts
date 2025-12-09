from __future__ import annotations

"""Server-side storage abstractions for web/API workflows.

This module defines a generic, async-friendly storage interface that can be
implemented by different backends (SQLite, Supabase, etc.).

The goal is to support the Web API conversion plan in docs/WEB_API_CONVERSION.md
without coupling HTTP or queueing concerns to the persistence layer.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from cinema.workflow.interface import WorkflowState, WorkflowType


class Job(BaseModel):
    """Logical job record for web/API workflows.

    This is intentionally minimal and backend-agnostic. It is **not** the same
    as the low-level pipeline `Job` used inside `cinema.pipeline.state`.

    Typical usages:
    - Track long-running workflow operations (init/content/chapters/pages)
    - Associate application-level jobs with Celery task IDs
    - Persist status, metadata, and output locations
    """

    id: str
    workflow_id: str

    # Free-form type identifier (e.g. "workflow_init", "chapter_batch")
    type: str

    # e.g. "pending", "running", "completed", "failed", "cancelled"
    status: str

    # Retry / idempotency controls
    retry_count: int = 0
    max_retries: int = 0
    idempotency_key: Optional[str] = None

    # Arbitrary JSON-serializable metadata (task IDs, parameters, etc.)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Optional fields for output/error tracking
    output_path: Optional[str] = None
    error: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StorageBackend(ABC):
    """Abstract storage interface for web/API workflow persistence.

    Backends must be safe to call from async FastAPI endpoints. Implementations
    may wrap sync drivers (e.g. sqlite3) using `asyncio.to_thread`, or use
    native async clients (e.g. Supabase/HTTP) as appropriate.
    """

    @abstractmethod
    async def save_job(self, job: Job) -> None:
        """Insert or update a job record."""

    @abstractmethod
    async def load_job(self, job_id: str) -> Optional[Job]:
        """Load a job by its ID, or return ``None`` if it does not exist."""

    @abstractmethod
    async def save_state(self, state: WorkflowState) -> None:
        """Persist a workflow state.

        Implementations are free to project/denormalize fields as needed.
        The canonical in-memory representation remains `WorkflowState` from
        `cinema.workflow.interface`.
        """

    @abstractmethod
    async def load_state(self, workflow_id: str, workflow_type: WorkflowType) -> Optional[WorkflowState]:
        """Load a workflow state or return ``None`` if not found."""

    @abstractmethod
    async def list_workflows(self, user_id: str) -> List[WorkflowState]:
        """List workflows owned by the given user.

        Convention: the user ID should be stored in `WorkflowState.config["user_id"]`
        (or an equivalent backend-specific column) when available.
        """
