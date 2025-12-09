from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from cinema.db.migrator import run_migrations


class ComicMetadataRepository(Protocol):  # pragma: no cover - protocol
    """Repository abstraction for comic chapter/page metadata.

    Implementations may store data in files, SQLite, Postgres, etc.
    """

    def save_chapter(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:
        """Persist a single chapter's comic metadata.

        The payload should match the JSON we currently write to
        ``chapter_{n:02d}.json`` (ComicBookOutput-like structure).
        """

    def list_chapters(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Return all stored chapter JSON documents for a workflow."""

    def list_pages(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Return flattened page metadata for a workflow.

        Each entry contains at least:
            - workflow_id
            - chapter_number
            - scene_number
            - page_number
            - page_data (original page dict)
            - chapter_data (full chapter JSON document)
            - global_index (1-based page index across workflow)
        """


class ChapterJsonWriter(Protocol):  # pragma: no cover - protocol
    """Strategy for optional chapter JSON side-effects."""

    def write_chapter_json(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:
        ...


def _extract_chapter_number(chapter_json: Dict[str, Any]) -> int:
    """Extract chapter_number from stored JSON structure."""

    chapters = chapter_json.get("chapters")
    if isinstance(chapters, list) and chapters:
        num = chapters[0].get("chapter_number")
        if isinstance(num, int):
            return num
    num = chapter_json.get("chapter_number")
    if isinstance(num, int):
        return num
    raise ValueError("chapter_json missing chapter_number")


@dataclass
class FileChapterJsonWriter(ChapterJsonWriter):
    """Real JSON writer used by file / sqlite backends when enabled."""

    base_dir: Path = Path("output")

    def write_chapter_json(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:
        chapter_number = _extract_chapter_number(chapter_json)
        output_dir = self.base_dir / f"book_{workflow_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        state_file = output_dir / f"chapter_{chapter_number:02d}.json"
        with state_file.open("w") as f:
            json.dump(chapter_json, f, indent=2)


@dataclass
class NullChapterJsonWriter(ChapterJsonWriter):
    """No-op writer used when JSON side-effects are disabled."""

    def write_chapter_json(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:  # noqa: D401
        return


@dataclass
class FileComicMetadataRepository(ComicMetadataRepository):
    """File-based comic metadata repository (current default behavior).

    Reads/writes JSON chapter files under ``output/book_{id}`` (and
    ``output/detective_{id}`` for backwards compatibility).
    """

    base_dir: Path = Path("output")

    def _workflow_dirs(self, workflow_id: str) -> List[Path]:
        return [
            self.base_dir / f"book_{workflow_id}",
            self.base_dir / f"detective_{workflow_id}",
        ]

    def save_chapter(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:
        writer = FileChapterJsonWriter(base_dir=self.base_dir)
        writer.write_chapter_json(workflow_id, chapter_json)

    def list_chapters(self, workflow_id: str) -> List[Dict[str, Any]]:
        chapters: List[Dict[str, Any]] = []
        for base in self._workflow_dirs(workflow_id):
            if not base.exists():
                continue
            for path in sorted(base.glob("chapter_*.json")):
                try:
                    with path.open("r") as f:
                        data = json.load(f)
                    chapters.append(data)
                except Exception:
                    continue
        return chapters

    def list_pages(self, workflow_id: str) -> List[Dict[str, Any]]:
        chapters = self.list_chapters(workflow_id)
        all_pages: List[Dict[str, Any]] = []
        for chapter_doc in chapters:
            for chapter in chapter_doc.get("chapters", []):
                chapter_num = chapter.get("chapter_number")
                for scene in chapter.get("scenes", []):
                    scene_num = scene.get("scene_number")
                    for page in scene.get("pages", []):
                        page_num = page.get("page_number")
                        all_pages.append(
                            {
                                "workflow_id": workflow_id,
                                "chapter_number": chapter_num,
                                "scene_number": scene_num,
                                "page_number": page_num,
                                "page_data": page,
                                "chapter_data": chapter_doc,
                                "global_index": len(all_pages) + 1,
                            }
                        )
        return all_pages


@dataclass
class SQLiteComicMetadataRepository(ComicMetadataRepository):
    """SQLite-backed comic metadata repository.

    Stores full chapter JSON documents plus a flattened pages table for
    indexing/analytics. Reads derive pages from chapters to keep logic
    consistent with the file backend.
    """

    db_path: str = "./cinema_server.db"
    chapter_table: str = "chapters"
    page_table: str = "pages"
    json_writer: ChapterJsonWriter | None = None

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _ensure_schema(self) -> None:
        run_migrations(self.db_path)

    def save_chapter(self, workflow_id: str, chapter_json: Dict[str, Any]) -> None:
        self._ensure_schema()

        chapter_number = _extract_chapter_number(chapter_json)
        payload = json.dumps(chapter_json)
        now = datetime.now(timezone.utc).isoformat()
        chapter_id = f"{workflow_id}:{chapter_number:04d}"

        with self._get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.chapter_table} (
                    id, workflow_id, chapter_number, chapter_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    chapter_json = excluded.chapter_json,
                    updated_at = excluded.updated_at
                """,
                (chapter_id, workflow_id, chapter_number, payload, now, now),
            )

            # Rebuild pages for this chapter
            conn.execute(
                f"DELETE FROM {self.page_table} WHERE workflow_id = ? AND chapter_number = ?",
                (workflow_id, chapter_number),
            )

            page_rows: List[tuple[str, str, int, int, int, str, str, str]] = []
            for chapter in chapter_json.get("chapters", []):
                ch_num = chapter.get("chapter_number")
                for scene in chapter.get("scenes", []):
                    scene_num = scene.get("scene_number")
                    for page in scene.get("pages", []):
                        page_num = page.get("page_number")
                        page_id = f"{workflow_id}:{ch_num:04d}:{scene_num:03d}:{page_num:04d}"
                        page_payload = json.dumps(page)
                        page_rows.append(
                            (
                                page_id,
                                workflow_id,
                                ch_num,
                                scene_num,
                                page_num,
                                page_payload,
                                now,
                                now,
                            )
                        )

            if page_rows:
                conn.executemany(
                    f"""
                    INSERT INTO {self.page_table} (
                        id, workflow_id, chapter_number, scene_number,
                        page_number, page_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        page_json = excluded.page_json,
                        updated_at = excluded.updated_at
                    """,
                    page_rows,
                )

        if self.json_writer is not None:
            try:
                self.json_writer.write_chapter_json(workflow_id, chapter_json)
            except Exception:
                # JSON side-effects are best-effort only
                pass

    def list_chapters(self, workflow_id: str) -> List[Dict[str, Any]]:
        self._ensure_schema()
        chapters: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                f"SELECT chapter_json FROM {self.chapter_table} WHERE workflow_id = ? ORDER BY chapter_number ASC",
                (workflow_id,),
            )
            for row in cur.fetchall():
                try:
                    chapters.append(json.loads(row["chapter_json"]))
                except Exception:
                    continue
        return chapters

    def list_pages(self, workflow_id: str) -> List[Dict[str, Any]]:
        chapters = self.list_chapters(workflow_id)
        all_pages: List[Dict[str, Any]] = []
        for chapter_doc in chapters:
            for chapter in chapter_doc.get("chapters", []):
                chapter_num = chapter.get("chapter_number")
                for scene in chapter.get("scenes", []):
                    scene_num = scene.get("scene_number")
                    for page in scene.get("pages", []):
                        page_num = page.get("page_number")
                        all_pages.append(
                            {
                                "workflow_id": workflow_id,
                                "chapter_number": chapter_num,
                                "scene_number": scene_num,
                                "page_number": page_num,
                                "page_data": page,
                                "chapter_data": chapter_doc,
                                "global_index": len(all_pages) + 1,
                            }
                        )
        return all_pages


def get_comic_metadata_repository() -> ComicMetadataRepository:
    """Factory for ComicMetadataRepository based on environment.

    Environment variables:
        COMIC_METADATA_STORAGE_BACKEND: "file" | "sqlite" (default: "file")
        COMIC_METADATA_SQLITE_PATH: path to SQLite DB (default: ./cinema_server.db)
        COMIC_METADATA_SQLITE_CHAPTER_TABLE: chapters table name (default: chapters)
        COMIC_METADATA_SQLITE_PAGE_TABLE: pages table name (default: pages)
        COMIC_METADATA_JSON_WRITE_MODE: "file" | "none" (default: "file")
    """

    backend = os.getenv("COMIC_METADATA_STORAGE_BACKEND", "file").lower()

    if backend == "sqlite":
        db_path = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
        chapter_table = os.getenv("COMIC_METADATA_SQLITE_CHAPTER_TABLE", "chapters")
        page_table = os.getenv("COMIC_METADATA_SQLITE_PAGE_TABLE", "pages")

        json_mode = os.getenv("COMIC_METADATA_JSON_WRITE_MODE", "file").lower()
        if json_mode == "none":
            writer: ChapterJsonWriter | None = NullChapterJsonWriter()
        else:
            writer = FileChapterJsonWriter()

        return SQLiteComicMetadataRepository(
            db_path=db_path,
            chapter_table=chapter_table,
            page_table=page_table,
            json_writer=writer,
        )

    # Default: pure file-based behavior
    return FileComicMetadataRepository()
