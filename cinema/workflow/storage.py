from __future__ import annotations

"""Storage abstractions for WorkflowState.

This mirrors the StoryBuilder storage pattern:
- Strategy/repository interface
- File / SQLite / Postgres implementations
- Env-driven factory for selection

CLI defaults remain file-based; switching to sqlite/postgres is explicit.
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, TYPE_CHECKING

from cinema.db.migrator import run_migrations

if TYPE_CHECKING:  # Only for type checking, avoids runtime import cycles
    from cinema.workflow.interface import WorkflowState, WorkflowType


class WorkflowStateRepository(Protocol):
    """Abstract repository for WorkflowState persistence.

    Implementations are intentionally minimal and backend-agnostic. They
    operate on the Pydantic `WorkflowState` model but return plain dicts
    to avoid hard runtime coupling.
    """

    def save(self, state: "WorkflowState") -> None:  # pragma: no cover - protocol
        ...

    def load(self, workflow_id: str, workflow_type: "WorkflowType") -> Optional[Dict[str, Any]]:  # pragma: no cover - protocol
        ...


@dataclass
class FileWorkflowStateRepository:
    """File-based WorkflowState repository (default for CLI).

    This preserves the existing behavior of writing
    `output/<type>_{workflow_id}/workflow_state.json`.
    """

    base_dir: Path = Path("output")

    def _state_path(self, workflow_id: str, workflow_type: "WorkflowType") -> Path:
        return self.base_dir / f"{workflow_type.value}_{workflow_id}" / "workflow_state.json"

    def save(self, state: "WorkflowState") -> None:
        state_file = self._state_path(state.id, state.type)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file.open("w") as f:
            json.dump(state.model_dump(), f, indent=2)

    def load(self, workflow_id: str, workflow_type: "WorkflowType") -> Optional[Dict[str, Any]]:
        state_file = self._state_path(workflow_id, workflow_type)
        if not state_file.exists():
            return None
        with state_file.open("r") as f:
            return json.load(f)


@dataclass
class SQLiteWorkflowStateRepository:
    """SQLite-backed WorkflowState repository.

    Uses the `workflow_states` table defined in the migration system.
    """

    db_path: str = "./cinema_server.db"
    table_name: str = "workflow_states"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _ensure_schema(self) -> None:
        run_migrations(self.db_path)

    def save(self, state: "WorkflowState") -> None:
        self._ensure_schema()

        state_json = state.model_dump_json()
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            # Preserve created_at if row exists
            created_at = now
            try:
                cur = conn.execute(
                    f"SELECT created_at FROM {self.table_name} WHERE id = ?",
                    (state.id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    created_at = row[0]
            except Exception:
                created_at = now

            user_id: Optional[str] = None
            try:
                user_id = state.config.get("user_id")  # type: ignore[assignment]
            except Exception:
                user_id = None

            conn.execute(
                f"""
                INSERT OR REPLACE INTO {self.table_name} (
                    id, user_id, type, current_stage, state_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.id,
                    user_id,
                    state.type.value,
                    state.current_stage.value,
                    state_json,
                    created_at,
                    now,
                ),
            )

    def load(self, workflow_id: str, workflow_type: "WorkflowType") -> Optional[Dict[str, Any]]:
        self._ensure_schema()
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                f"SELECT state_json FROM {self.table_name} WHERE id = ?",
                (workflow_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            raw = row["state_json"]
            return json.loads(raw)


try:  # Optional Postgres backend
    import psycopg  # type: ignore[import]
except ImportError:  # pragma: no cover - optional
    psycopg = None


@dataclass
class PostgresWorkflowStateRepository:
    """Postgres-backed WorkflowState repository (e.g. Supabase).

    Stores state JSON in a `workflow_states` table with a JSONB column.
    """

    dsn: str
    table_name: str = "workflow_states"

    def _get_connection(self):  # pragma: no cover - thin wrapper
        if psycopg is None:
            raise ImportError(
                "psycopg is required for PostgresWorkflowStateRepository but is not installed"
            )
        return psycopg.connect(self.dsn, autocommit=True)  # type: ignore[call-arg]

    def save(self, state: "WorkflowState") -> None:
        payload = state.model_dump_json()
        now = datetime.now(timezone.utc)

        with self._get_connection() as conn:
            with conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (id, state_json, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(id) DO UPDATE SET
                        state_json = EXCLUDED.state_json,
                        updated_at = EXCLUDED.updated_at
                    """,
                    (state.id, payload, now, now),
                )

    def load(self, workflow_id: str, workflow_type: "WorkflowType") -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute(
                    f"SELECT state_json FROM {self.table_name} WHERE id = %s",
                    (workflow_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None

        raw = row[0]
        if isinstance(raw, str):
            return json.loads(raw)
        return raw


def get_workflow_state_repository() -> WorkflowStateRepository:
    """Factory for WorkflowStateRepository implementations.

    Backend is selected via environment variables:

    - WORKFLOW_STATE_STORAGE_BACKEND: "file" (default), "sqlite", or "postgres".
    - WORKFLOW_STATE_SQLITE_PATH: path to SQLite DB (default: "./cinema_server.db").
    - WORKFLOW_STATE_SQLITE_TABLE: table name (default: "workflow_states").
    - WORKFLOW_STATE_PG_DSN: Postgres DSN (required if backend=postgres).
    - WORKFLOW_STATE_PG_TABLE: table name (default: "workflow_states").
    """

    backend = os.getenv("WORKFLOW_STATE_STORAGE_BACKEND", "file").lower()

    if backend == "sqlite":
        db_path = os.getenv("WORKFLOW_STATE_SQLITE_PATH", "./cinema_server.db")
        table_name = os.getenv("WORKFLOW_STATE_SQLITE_TABLE", os.getenv("CINEMA_WORKFLOW_TABLE", "workflow_states"))
        return SQLiteWorkflowStateRepository(db_path=db_path, table_name=table_name)

    if backend == "postgres":
        dsn = os.environ.get("WORKFLOW_STATE_PG_DSN")
        if not dsn:
            raise ValueError(
                "WORKFLOW_STATE_PG_DSN must be set when WORKFLOW_STATE_STORAGE_BACKEND=postgres"
            )
        table_name = os.getenv("WORKFLOW_STATE_PG_TABLE", "workflow_states")
        return PostgresWorkflowStateRepository(dsn=dsn, table_name=table_name)

    # Default: local JSON files in output/<type>_{workflow_id}/workflow_state.json
    return FileWorkflowStateRepository()
