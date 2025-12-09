from __future__ import annotations

"""Add chapters/pages tables for comic metadata.

This migration adds logical storage for comic chapter/page metadata used
by the BookWorkflow / ParallelComicGenerator. Chapters are stored as
full JSON documents (ComicBookOutput-like), and pages are flattened for
indexing/analytics.

Table names are configurable via environment variables so deployments
can share a DB or customize naming.
"""

import os
import sqlite3


MIGRATION_ID = "0003_add_comic_metadata"
DESCRIPTION = "Add chapters/pages tables for comic metadata"


def _chapter_table_name() -> str:
    # Prefer dedicated env, fall back to a generic name.
    return os.getenv("COMIC_METADATA_SQLITE_CHAPTER_TABLE", "chapters")


def _page_table_name() -> str:
    return os.getenv("COMIC_METADATA_SQLITE_PAGE_TABLE", "pages")


def upgrade(conn: sqlite3.Connection) -> None:
    chapter_table = _chapter_table_name()
    page_table = _page_table_name()

    # Chapters table - stores full JSON documents for each chapter.
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {chapter_table} (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            chapter_number INTEGER NOT NULL,
            chapter_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{chapter_table}_workflow_chapter
        ON {chapter_table}(workflow_id, chapter_number)
        """
    )

    # Pages table - optional flattened page-level metadata.
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {page_table} (
            id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            chapter_number INTEGER NOT NULL,
            scene_number INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            page_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{page_table}_workflow_page
        ON {page_table}(workflow_id, page_number)
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_{page_table}_workflow_chapter_page
        ON {page_table}(workflow_id, chapter_number, page_number)
        """
    )
