"""Server-side storage backends for the Cinema web API.

This package defines the abstract `StorageBackend` plus concrete implementations
such as `SQLiteStorage`. Higher-level server code (FastAPI routes, Celery tasks,
etc.) should depend only on the abstract interface, not on specific backends.
"""

from .interface import Job, StorageBackend
from .sqlite import SQLiteStorage

__all__ = ["Job", "StorageBackend", "SQLiteStorage"]
