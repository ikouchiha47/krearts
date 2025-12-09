"""Schema migrations for Cinema.

Each migration module should define:

    MIGRATION_ID: str  # unique, lexicographically sortable
    DESCRIPTION: str
    def upgrade(conn: sqlite3.Connection) -> None: ...

Migrations are applied in order of `MIGRATION_ID` and tracked in the
`schema_migrations` table by `cinema.db.migrator.run_migrations`.
"""
