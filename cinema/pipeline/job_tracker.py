"""
SQLite-backed job tracking for resumable pipeline execution.
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState


class JobTracker:
    """
    Manages job persistence in SQLite.
    Allows resuming pipeline execution from any point.
    """

    def __init__(self, db_path: str = "./cinema_jobs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        """Get a database connection with proper timeout and isolation level"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        return conn
        conn.close()

    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    movie_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    scene_id TEXT,
                    character_id INTEGER,
                    metadata TEXT,
                    error TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    output_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_movie_id ON jobs(movie_id)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_type ON jobs(type)
            """
            )

            # Table for storing pipeline state
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_states (
                    movie_id TEXT PRIMARY KEY,
                    screenplay_complete INTEGER DEFAULT 0,
                    characters_complete INTEGER DEFAULT 0,
                    images_complete INTEGER DEFAULT 0,
                    videos_complete INTEGER DEFAULT 0,
                    post_production_complete INTEGER DEFAULT 0,
                    screenplay_data TEXT,
                    screenplay_hash TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

    def save_job(self, job: Job, movie_id: str) -> None:
        """Save or update a job"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs 
                (id, movie_id, type, status, scene_id, character_id, metadata, 
                 error, output_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job.id,
                    movie_id,
                    job.type.value,
                    job.status.value,
                    job.scene_id,
                    job.character_id,
                    json.dumps(job.metadata),
                    job.error,
                    job.output_path,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_job(row)

    def get_jobs_by_movie(self, movie_id: str) -> List[Job]:
        """Get all jobs for a movie"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE movie_id = ? ORDER BY created_at",
                (movie_id,),
            )
            return [self._row_to_job(row) for row in cursor.fetchall()]

    def get_jobs_by_status(
        self, movie_id: str, status: JobStatus
    ) -> List[Job]:
        """Get jobs by status for a movie"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE movie_id = ? AND status = ?",
                (movie_id, status.value),
            )
            return [self._row_to_job(row) for row in cursor.fetchall()]

    def update_job_status(
        self, job_id: str, status: JobStatus, error: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> None:
        """Update job status"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute(
                """
                UPDATE jobs 
                SET status = ?, error = ?, output_path = ?, updated_at = ?
                WHERE id = ?
            """,
                (status.value, error, output_path, datetime.now().isoformat(), job_id),
            )

    def save_state(self, state: PipelineState) -> None:
        """Save pipeline state"""
        screenplay_json = None
        if state.screenplay_dict:
            screenplay_json = json.dumps(state.screenplay_dict)

        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_states
                (movie_id, screenplay_complete, characters_complete, 
                 images_complete, videos_complete, post_production_complete,
                 screenplay_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    state.movie_id,
                    int(state.screenplay_complete),
                    int(state.characters_complete),
                    int(state.images_complete),
                    int(state.videos_complete),
                    int(state.post_production_complete),
                    screenplay_json,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

            # Save all jobs in the same transaction
            for job in state.jobs:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs 
                    (id, movie_id, type, status, scene_id, character_id, metadata, 
                     error, output_path, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        job.id,
                        state.movie_id,
                        job.type.value,
                        job.status.value,
                        job.scene_id,
                        job.character_id,
                        json.dumps(job.metadata),
                        job.error,
                        job.output_path,
                        job.created_at.isoformat(),
                        job.updated_at.isoformat(),
                    ),
                )

    def load_state(self, movie_id: str, base_dir: str = "./output") -> Optional[PipelineState]:
        """Load pipeline state from database"""
        with sqlite3.connect(self.db_path, timeout=10.0) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM pipeline_states WHERE movie_id = ?", (movie_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Create state
            state = PipelineState.create(movie_id, base_dir)

            # Load completion flags
            state.screenplay_complete = bool(row["screenplay_complete"])
            state.characters_complete = bool(row["characters_complete"])
            state.images_complete = bool(row["images_complete"])
            state.videos_complete = bool(row["videos_complete"])
            state.post_production_complete = bool(row["post_production_complete"])

            # Load screenplay data
            if row["screenplay_data"]:
                state.screenplay_dict = json.loads(row["screenplay_data"])

            # Load jobs
            state.jobs = self.get_jobs_by_movie(movie_id)

            return state

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        """Convert database row to Job object"""
        return Job(
            id=row["id"],
            type=JobType(row["type"]),
            status=JobStatus(row["status"]),
            scene_id=row["scene_id"],
            character_id=row["character_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            error=row["error"],
            output_path=row["output_path"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def get_next_pending_job(self, movie_id: str) -> Optional[Job]:
        """Get the next pending job for a movie"""
        pending_jobs = self.get_jobs_by_status(movie_id, JobStatus.PENDING)
        return pending_jobs[0] if pending_jobs else None

    def get_progress(self, movie_id: str) -> dict:
        """Get progress statistics for a movie"""
        jobs = self.get_jobs_by_movie(movie_id)
        total = len(jobs)

        if total == 0:
            return {"total": 0, "completed": 0, "failed": 0, "pending": 0, "progress": 0}

        completed = len([j for j in jobs if j.status == JobStatus.COMPLETED])
        failed = len([j for j in jobs if j.status == JobStatus.FAILED])
        pending = len([j for j in jobs if j.status == JobStatus.PENDING])

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress": (completed / total) * 100 if total > 0 else 0,
        }
