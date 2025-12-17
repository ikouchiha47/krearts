from __future__ import annotations

from fastapi import Depends

from cinema.context import DirectorsContext
from cinema.jobs.storage import get_job_repository
from cinema.registry import OpenAiHerd
from cinema.server.services import BookWorkflowService
from cinema.server.storage.interface import StorageBackend


def get_storage() -> StorageBackend:
    """Get the storage backend instance."""
    from cinema.server.storage.sqlite import SQLiteStorage
    return SQLiteStorage()


def get_directors_context() -> DirectorsContext:
    """Construct the DirectorsContext used by workflows.

    In a real deployment this could be extended to include per-request user
    identity, request IDs, or other metadata from the HTTP layer.
    """

    return DirectorsContext(llmstore=OpenAiHerd, debug=True)


def get_book_service(
    ctx: DirectorsContext = Depends(get_directors_context),
    storage = Depends(get_storage),
) -> BookWorkflowService:
    """Dependency that provides a BookWorkflowService instance."""

    return BookWorkflowService(ctx=ctx, job_repo=get_job_repository(), storage=storage)
