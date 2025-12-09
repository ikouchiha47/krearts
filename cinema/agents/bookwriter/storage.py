from __future__ import annotations

"""Local file-based storage helpers for the StoryBuilder flow.

This module centralizes how StoryBuilder flow state is persisted so that
later we can swap in alternative backends (e.g., Supabase) without touching
CLI or flow logic.

Current behavior matches the existing layout used by the CLI:
    output/flow_states/storybuilder_{flow_id}.json
"""

from pathlib import Path
from typing import Any, Dict, Optional, Protocol
import json
import os
import sqlite3
from datetime import datetime, timezone

from cinema.db import run_migrations

try:  # Optional dependency for Postgres-backed storage
    import psycopg  # type: ignore[import]
except ImportError:  # pragma: no cover - optional
    psycopg = None


class StoryBuilderStateRepository(Protocol):
    """Typed repository interface for StoryBuilder state persistence.

    This keeps the flow logic decoupled from any particular storage backend
    (local files, SQLite, Supabase, etc.). Implementations operate on
    JSON-serializable dictionaries that mirror the `StoryBuilderState` model.
    """

    def save(self, flow_id: str, state_data: Dict[str, Any]) -> Path:  # pragma: no cover - protocol
        ...

    def load(self, flow_id: str) -> Dict[str, Any]:  # pragma: no cover - protocol
        ...


class LocalStoryBuilderStorage:
    """Simple JSON file storage for StoryBuilder state.

    This mirrors the previous hardcoded path logic in StoryBuilder so
    existing commands like `krearts read --storyline` keep working.
    """

    def __init__(
        self,
        base_dir: str = "output/flow_states",
        prefix: Optional[str] = None,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.prefix = prefix

    def _state_path(self, flow_id: str) -> Path:
        _file = flow_id
        if self.prefix is not None:
            _file = f"{self.prefix}_{flow_id}.json"
 
        return self.base_dir / _file

    def save(self, flow_id: str, state_data: Dict[str, Any]) -> Path:
        """Save flow state to disk and return the path used."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        state_file = self._state_path(flow_id)

        with state_file.open("w") as f:
            json.dump(state_data, f, indent=2)

        return state_file

    def load(self, flow_id: str) -> Dict[str, Any]:
        """Load flow state from disk.

        Raises FileNotFoundError if the state file does not exist.
        """
        state_file = self._state_path(flow_id)
        if not state_file.exists():
            raise FileNotFoundError(f"Flow state not found: {state_file}")

        with state_file.open("r") as f:
            return json.load(f)


class SQLiteStoryBuilderStorage:
    """SQLite-based StoryBuilderStateRepository implementation.

    This is useful for environments where you want DB-backed flow state
    persistence but don't have Postgres/Supabase available. It stores the
    StoryBuilder state as JSON in a simple `storybuilder_states` table.
    """

    def __init__(
        self,
        db_path: str = "./cinema_storybuilder.db",
        table_name: str = "storybuilder_states",
    ) -> None:
        self.db_path = db_path
        self.table_name = table_name
        # Ensure schema is up-to-date before any access
        run_migrations(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def save(self, flow_id: str, state_data: Dict[str, Any]) -> Path:
        """Persist flow state in SQLite and return a synthetic path.

        The returned Path is used only for logging/debugging and does not
        correspond to an actual file on disk.
        """
        now = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(state_data)

        with self._get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (id, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    state_json = excluded.state_json,
                    updated_at = excluded.updated_at
                """,
                (flow_id, payload, now, now),
            )

        # Represent the logical location for logs
        return Path(f"sqlite://{self.db_path}#{self.table_name}/{flow_id}")

    def load(self, flow_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                f"SELECT state_json FROM {self.table_name} WHERE id = ?",
                (flow_id,),
            )
            row = cur.fetchone()

        if not row:
            raise FileNotFoundError(
                f"StoryBuilder state not found in SQLite for id={flow_id}"
            )

        raw = row["state_json"]
        return json.loads(raw)


class PostgresStoryBuilderStorage:
    """Postgres-backed StoryBuilderStateRepository implementation.

    This is intended for production/server environments (e.g. Supabase).
    It stores the state in a `storybuilder_states` table with a JSONB column.

    Note: Requires the `psycopg` package. If it is not installed, attempting
    to instantiate this class will raise an ImportError.
    """

    def __init__(
        self,
        dsn: str,
        table_name: str = "storybuilder_states",
    ) -> None:
        if psycopg is None:  # pragma: no cover - runtime guard
            raise ImportError(
                "psycopg is required for PostgresStoryBuilderStorage but is not installed"
            )

        self.dsn = dsn
        self.table_name = table_name
        self._init_db()

    def _get_connection(self):  # type: ignore[override]
        # Autocommit simplifies usage for these small operations
        return psycopg.connect(self.dsn, autocommit=True)  # type: ignore[call-arg]

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id TEXT PRIMARY KEY,
                        state_json JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )

    def save(self, flow_id: str, state_data: Dict[str, Any]) -> Path:
        now = datetime.now(timezone.utc)
        payload = json.dumps(state_data)

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
                    (flow_id, payload, now, now),
                )

        # Synthetic Path-like identifier for logging
        return Path(f"postgres://{self.table_name}/{flow_id}")

    def load(self, flow_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute(
                    f"SELECT state_json FROM {self.table_name} WHERE id = %s",
                    (flow_id,),
                )
                row = cur.fetchone()

        if row is None:
            raise FileNotFoundError(
                f"StoryBuilder state not found in Postgres for id={flow_id}"
            )

        raw = row[0]
        # row[0] may already be a dict (JSONB) or a string
        if isinstance(raw, str):
            return json.loads(raw)
        return raw


def get_storybuilder_storage() -> StoryBuilderStateRepository:
    """Factory for StoryBuilderStateRepository implementations.

    Backend is selected via environment variables:

    - STORYBUILDER_STORAGE_BACKEND: "file" (default), "sqlite", or "postgres".
    - STORYBUILDER_SQLITE_PATH: path to SQLite DB (default: "./cinema_storybuilder.db").
    - STORYBUILDER_SQLITE_TABLE: table name (default: "storybuilder_states").
    - STORYBUILDER_PG_DSN: Postgres DSN (required if backend=postgres).
    - STORYBUILDER_PG_TABLE: table name (default: "storybuilder_states").
    """

    backend = os.getenv("STORYBUILDER_STORAGE_BACKEND", "file").lower()

    if backend == "sqlite":
        db_path = os.getenv("STORYBUILDER_SQLITE_PATH", "./cinema_storybuilder.db")
        table_name = os.getenv("STORYBUILDER_SQLITE_TABLE", "storybuilder_states")
        return SQLiteStoryBuilderStorage(db_path=db_path, table_name=table_name)

    if backend == "postgres":
        dsn = os.environ.get("STORYBUILDER_PG_DSN")
        if not dsn:
            raise ValueError(
                "STORYBUILDER_PG_DSN must be set when STORYBUILDER_STORAGE_BACKEND=postgres"
            )
        table_name = os.getenv("STORYBUILDER_PG_TABLE", "storybuilder_states")
        return PostgresStoryBuilderStorage(dsn=dsn, table_name=table_name)

    # Default: local JSON files in output/flow_states
    return LocalStoryBuilderStorage(prefix="storybuilder")
