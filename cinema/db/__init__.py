"""Database utilities and migration runner for Cinema.

This package centralizes DB schema management so both server storage
and StoryBuilder flow storage can share a consistent migration story.
"""

from .migrator import run_migrations  # noqa: F401
