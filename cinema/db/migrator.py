from __future__ import annotations

"""Simple, production-ready migration runner for SQLite.

This is intentionally lightweight (no SQLAlchemy required) but provides:
- Versioned migrations (ordered by MIGRATION_ID)
- Idempotent application tracked in a `schema_migrations` table
- Python-based migrations with an `upgrade(conn)` function

Usage
-----
Call `run_migrations(db_path)` during startup for any SQLite DB
(called by server storage and StoryBuilder SQLite storage).
"""

import importlib
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List

import pkgutil


MIGRATIONS_PACKAGE = "cinema.db.migrations"


@dataclass
class Migration:
    id: str
    module_name: str
    upgrade: Callable[[sqlite3.Connection], None]


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )


def _get_applied_migration_ids(conn: sqlite3.Connection) -> set[str]:
    _ensure_schema_migrations_table(conn)
    cur = conn.execute("SELECT id FROM schema_migrations")
    return {row[0] for row in cur.fetchall()}


def _record_migration_applied(conn: sqlite3.Connection, migration_id: str) -> None:
    applied_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
        (migration_id, applied_at),
    )


def _discover_migrations() -> List[Migration]:
    """Discover migration modules under `cinema.db.migrations`.

    Each migration module must define:
      - MIGRATION_ID: str (lexicographically ordered)
      - upgrade(conn: sqlite3.Connection) -> None
    """

    migrations: List[Migration] = []

    pkg = importlib.import_module(MIGRATIONS_PACKAGE)
    pkg_path = Path(pkg.__file__).parent

    for module_info in pkgutil.iter_modules([str(pkg_path)]):
        if module_info.name.startswith("__"):
            continue

        module_qualname = f"{MIGRATIONS_PACKAGE}.{module_info.name}"
        mod = importlib.import_module(module_qualname)

        migration_id = getattr(mod, "MIGRATION_ID", None)
        upgrade_fn = getattr(mod, "upgrade", None)

        if not migration_id or not callable(upgrade_fn):
            # Skip modules that are not proper migrations
            continue

        migrations.append(Migration(id=migration_id, module_name=module_qualname, upgrade=upgrade_fn))

    # Order by MIGRATION_ID to guarantee deterministic application
    migrations.sort(key=lambda m: m.id)
    return migrations


def run_migrations(db_path: str) -> None:
    """Run all pending migrations against the given SQLite database.

    - Ensures `schema_migrations` exists in the target DB.
    - Discovers migration modules under `cinema.db.migrations`.
    - Applies any migration whose `MIGRATION_ID` is not yet recorded.
    """

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Use a dedicated connection here; callers can use their own for runtime ops.
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        _ensure_schema_migrations_table(conn)
        applied_ids = _get_applied_migration_ids(conn)

        migrations = _discover_migrations()
        for migration in migrations:
            if migration.id in applied_ids:
                continue

            # Apply migration in a transaction
            with conn:
                migration.upgrade(conn)
                _record_migration_applied(conn, migration.id)
    finally:
        conn.close()
