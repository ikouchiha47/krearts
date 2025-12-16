"""
Character storage - stores parsed character data from storyline
Uses existing database connection patterns with WAL mode
Schema managed by migrations/0005_add_characters_table.py
"""
import json
import sqlite3
from typing import List, Optional, Dict, Any
from cinema.models.storyline import CharacterDetail


def generate_character_id(workflow_id: str, character_number: int) -> str:
    """
    Generate character ID: {workflow_id}_{character_number}
    Example: "c778f39d_1", "c778f39d_2"
    This format matches character_images.character_id for linking.
    """
    return f"{workflow_id}_{character_number}"


class CharacterStore:
    """Store and retrieve character details"""
    
    def __init__(self, db_path: str = "cinema_server.db"):
        self.db_path = db_path
        # Note: Table creation is handled by migrations (0005_add_characters_table.py)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with WAL mode"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn
    
    def save_character(self, workflow_id: str, character: CharacterDetail, character_number: int):
        """Save a character to the database"""
        character_id = generate_character_id(workflow_id, character_number)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO characters (
                    id, workflow_id, character_number, character_name, character_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                character_id,
                workflow_id,
                character_number,
                character.name,
                json.dumps(character.to_dict()),
            ))
            
            conn.commit()
    
    def save_characters(self, workflow_id: str, characters: List[CharacterDetail]):
        """Save multiple characters with auto-incrementing number"""
        for number, character in enumerate(characters, start=1):
            self.save_character(workflow_id, character, number)
    
    def get_character(self, workflow_id: str, character_name: str) -> Optional[CharacterDetail]:
        """Get a specific character by name"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT character_data
                FROM characters
                WHERE workflow_id = ? AND character_name = ?
            """, (workflow_id, character_name))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            data = json.loads(row[0])
            return CharacterDetail(**data)
    
    def get_character_by_id(self, character_id: str) -> Optional[CharacterDetail]:
        """Get a specific character by character_id (e.g., 'c778f39d_1')"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT character_data
                FROM characters
                WHERE id = ?
            """, (character_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            data = json.loads(row[0])
            return CharacterDetail(**data)
    
    def get_all_characters(self, workflow_id: str) -> List[CharacterDetail]:
        """Get all characters for a workflow, ordered by character_number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT character_data
                FROM characters
                WHERE workflow_id = ?
                ORDER BY character_number
            """, (workflow_id,))
            
            characters = []
            for row in cursor.fetchall():
                data = json.loads(row[0])
                characters.append(CharacterDetail(**data))
            
            return characters
    
    def get_character_names(self, workflow_id: str) -> List[str]:
        """Get list of character names for a workflow"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT character_name
                FROM characters
                WHERE workflow_id = ?
                ORDER BY character_number
            """, (workflow_id,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_character_ids(self, workflow_id: str) -> List[str]:
        """Get list of character IDs for a workflow"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id
                FROM characters
                WHERE workflow_id = ?
                ORDER BY character_number
            """, (workflow_id,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def get_character_mapping(self, workflow_id: str) -> Dict[str, str]:
        """Get mapping of character_id -> character_name"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, character_name
                FROM characters
                WHERE workflow_id = ?
                ORDER BY character_number
            """, (workflow_id,))
            
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def delete_characters(self, workflow_id: str):
        """Delete all characters for a workflow"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM characters WHERE workflow_id = ?
            """, (workflow_id,))
            conn.commit()
    
    def get_characters_for_image_gen(self, workflow_id: str) -> Dict[str, str]:
        """
        Get character details formatted for image generation
        Returns dict of {character_id: formatted_prompt}
        """
        characters = self.get_all_characters(workflow_id)
        char_ids = self.get_character_ids(workflow_id)
        
        return {
            char_id: char.to_image_gen_prompt()
            for char_id, char in zip(char_ids, characters)
        }
    
    def get_character_full_texts(self, workflow_id: str) -> List[str]:
        """
        Get full character text blocks for passing to BookWriterSchema
        """
        characters = self.get_all_characters(workflow_id)
        return [char.full_text for char in characters if char.full_text]
    
    def get_characters_with_images(self, workflow_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get characters with their associated images from character_images table.
        Links by character_id (id field in characters, character_id in character_images).
        
        Returns:
            Dict mapping character_id to {
                "name": str,
                "character": CharacterDetail,
                "images": {view_type: image_path}
            }
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all characters with their images via JOIN
            cursor.execute("""
                SELECT 
                    c.id,
                    c.character_name,
                    c.character_data,
                    ci.view_type,
                    ci.image_path
                FROM characters c
                LEFT JOIN character_images ci 
                    ON c.id = ci.character_id
                WHERE c.workflow_id = ?
                ORDER BY c.character_number, ci.view_type
            """, (workflow_id,))
            
            result = {}
            for row in cursor.fetchall():
                char_id = row[0]
                char_name = row[1]
                char_data_json = row[2]
                view_type = row[3]
                image_path = row[4]
                
                # Initialize character entry if not exists
                if char_id not in result:
                    char_data = json.loads(char_data_json)
                    result[char_id] = {
                        "name": char_name,
                        "character": CharacterDetail(**char_data),
                        "images": {}
                    }
                
                # Add image if exists
                if view_type and image_path:
                    result[char_id]["images"][view_type] = image_path
            
            return result
