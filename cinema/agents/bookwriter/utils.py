"""Utility functions for bookwriter agents"""
import logging
import re
import yaml
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def clean_agent_thinking_from_output(raw_output: str) -> str:
    """
    Remove agent thinking logs from raw crew output.
    
    When crews use tools, the raw output may contain agent thinking patterns
    like "Thought", "Action", "Observation" followed by the actual content.
    This function tries to extract just the clean content.
    
    Strategy:
    1. Look for known delimiter phrases that mark the end of agent thinking
    2. If found, return everything after the delimiter
    3. If output starts with "Thought" and has no delimiter, it's contaminated - return empty
    4. If not found, return the original output (it's likely already clean)
    
    Args:
        raw_output: The raw output from crew execution
        
    Returns:
        Cleaned output with agent thinking removed
    """
    if not raw_output:
        return raw_output
    
    # Known delimiter patterns that mark the transition from thinking to output
    delimiter_patterns = [
        r'I now know the final answer',
        r'Final Answer:',
    ]
    
    for pattern in delimiter_patterns:
        match = re.search(pattern, raw_output, re.IGNORECASE)
        if match:
            # Return everything after the delimiter
            cleaned = raw_output[match.end():].strip()
            logger.info(f"Cleaned agent thinking using delimiter: '{pattern}' (removed {match.end()} chars)")
            return cleaned
    
    # Check if output is contaminated with agent thinking but has no delimiter
    # This means the agent never finished and only has thinking logs
    if raw_output.strip().startswith(('Thought', 'Action:', 'Observation:')):
        logger.warning(f"Output appears to be contaminated agent thinking with no delimiter (length: {len(raw_output)})")
        logger.warning(f"First 200 chars: {raw_output[:200]}")
        return ""  # Return empty string - the actual content wasn't generated
    
    # No delimiter found - output is likely already clean
    return raw_output


def get_allowed_art_styles() -> List[str]:
    """
    Load allowed art styles from reference_manifest.yaml
    
    Returns:
        List of art style names (e.g., ['sci-fi', 'cyberpunk', 'noir', ...])
    """
    import os
    
    # Use CINEMA_ROOT environment variable, fallback to project root detection
    cinema_root = os.getenv('CINEMA_ROOT')
    if cinema_root:
        base_dir = Path(cinema_root)
    else:
        # Fallback: go up 4 levels from this file to project root
        base_dir = Path(__file__).parent.parent.parent.parent
    
    manifest_path = base_dir / "knowledge" / "art-styles" / "references" / "reference_manifest.yaml"
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        # Extract top-level keys (style names), filter out comments
        styles = [style for style in manifest.keys() if not style.startswith('#')]
        logger.info(f"Loaded {len(styles)} art styles from manifest")
        return styles
    except Exception as e:
        logger.error(f"Failed to load art styles from manifest: {e}")
        # Fallback to hardcoded list
        return [
            "sci-fi", "cyberpunk", "fantasy-rpg", "noir", "anime-manga",
            "pixel-art", "american-comic", "pop-art", "blueberry", "akira",
            "spiderverse", "arcane", "watchmen", "print_comic"
        ]
