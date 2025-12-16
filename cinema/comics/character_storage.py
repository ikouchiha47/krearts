from __future__ import annotations

"""Character image repository for storing and retrieving character reference images.

Supports both file-based (manifest.json) and SQLite backends based on
COMIC_METADATA_STORAGE_BACKEND environment variable.
"""

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Protocol


class CharacterImageRepository(Protocol):  # pragma: no cover - protocol
    """Repository abstraction for character image metadata.
    
    Implementations may store data in manifest.json files or SQLite.
    """

    def save_character_image(
        self, 
        workflow_id: str, 
        character_id: str, 
        character_name: str, 
        view_type: str, 
        image_path: str
    ) -> None:
        """Save character image metadata."""

    def list_character_images(self, workflow_id: str) -> Dict[str, Dict[str, any]]:
        """Return character images for a workflow.
        
        Returns:
            Dict mapping character_id -> {"name": str, "images": {view_type: image_path}}
            Example: {"CHAR_1": {"name": "Kira_Byte", "images": {"front": "path/to/front.png"}}}
        """

    def delete_character_images(self, workflow_id: str) -> None:
        """Delete all character images for a workflow."""


@dataclass
class FileCharacterImageRepository(CharacterImageRepository):
    """File-based character image repository using character_manifest.json."""
    
    base_dir: Path = Path("output")
    
    def _get_manifest_path(self, workflow_id: str) -> Path:
        """Get path to character manifest file."""
        return self.base_dir / workflow_id / "characters" / "character_manifest.json"
    
    def save_character_image(
        self, 
        workflow_id: str, 
        character_id: str, 
        character_name: str, 
        view_type: str, 
        image_path: str
    ) -> None:
        """Save character image to manifest file."""
        manifest_path = self._get_manifest_path(workflow_id)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing manifest
        manifest = {}
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        # Update manifest with character name and images
        if character_id not in manifest:
            manifest[character_id] = {
                "name": character_name,
                "images": {}
            }
        
        # Ensure name is set (in case of partial updates)
        if "name" not in manifest[character_id]:
            manifest[character_id]["name"] = character_name
        
        # Ensure images dict exists
        if "images" not in manifest[character_id]:
            manifest[character_id]["images"] = {}
        
        manifest[character_id]["images"][view_type] = image_path
        
        # Save manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def list_character_images(self, workflow_id: str) -> Dict[str, Dict[str, any]]:
        """Load character images from manifest file."""
        manifest_path = self._get_manifest_path(workflow_id)
        
        if not manifest_path.exists():
            return {}
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Handle both old format {char_id: {view: path}} and new format {char_id: {name: str, images: {}}}
        result = {}
        for char_id, data in manifest.items():
            if isinstance(data, dict) and "images" in data:
                # New format with name and images
                result[char_id] = data
            else:
                # Old format - just view: path mapping
                # Migrate to new format on the fly
                result[char_id] = {
                    "name": char_id.replace("CHAR_", "Character_"),
                    "images": data
                }
        
        return result
    
    def delete_character_images(self, workflow_id: str) -> None:
        """Delete manifest file for a workflow."""
        manifest_path = self._get_manifest_path(workflow_id)
        if manifest_path.exists():
            manifest_path.unlink()


@dataclass
class SQLiteCharacterImageRepository(CharacterImageRepository):
    """SQLite-based character image repository."""
    
    db_path: str = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
    table_name: str = os.getenv("COMIC_METADATA_SQLITE_CHARACTER_TABLE", "character_images")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn
    
    def save_character_image(
        self, 
        workflow_id: str, 
        character_id: str, 
        character_name: str, 
        view_type: str, 
        image_path: str
    ) -> None:
        """Save character image to database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {self.table_name}
                (workflow_id, character_id, character_name, view_type, image_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workflow_id, character_id, character_name, view_type, image_path)
            )
            conn.commit()
    
    def list_character_images(self, workflow_id: str) -> Dict[str, Dict[str, any]]:
        """Load character images from database."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT character_id, character_name, view_type, image_path FROM {self.table_name} WHERE workflow_id = ?",
                (workflow_id,)
            )
            rows = cursor.fetchall()
            
            if not rows:
                return {}
            
            # Group by character_id
            result = {}
            for row in rows:
                char_id = f"CHAR_{row['character_id']}"
                if char_id not in result:
                    result[char_id] = {
                        "name": row['character_name'],
                        "images": {}
                    }
                result[char_id]["images"][row['view_type']] = row['image_path']
            
            return result
    
    def delete_character_images(self, workflow_id: str) -> None:
        """Delete all character images from database for a workflow."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE workflow_id = ?",
                (workflow_id,)
            )
            conn.commit()


def get_character_image_repository() -> CharacterImageRepository:
    """Factory for CharacterImageRepository based on environment.
    
    Returns SQLite or file-based repository depending on
    COMIC_METADATA_STORAGE_BACKEND environment variable.
    """
    backend = os.getenv("COMIC_METADATA_STORAGE_BACKEND", "sqlite").lower()
    
    if backend == "sqlite":
        return SQLiteCharacterImageRepository()
    elif backend == "file":
        return FileCharacterImageRepository()
    else:
        raise ValueError(f"Unknown COMIC_METADATA_STORAGE_BACKEND: {backend}")
