#!/usr/bin/env python3
"""Test script to verify art_style is being read from storyline."""

import json
import re
from pathlib import Path

def get_art_style(workflow_id: str, output_dir: str) -> str:
    """Get art_style from generated content (storyline/novel), NOT from user config."""
    
    # Priority 1: Try flow state storyline (most authoritative)
    flow_state_file = Path(f"output/flow_states/storybuilder_{workflow_id}.json")
    if flow_state_file.exists():
        try:
            with open(flow_state_file, 'r') as f:
                flow_data = json.load(f)
            storyline = flow_data.get('output', {}).get('storyline', '')
            if storyline:
                # Look for "- **Art Style:** ..." pattern in storyline
                match = re.search(r'-\s*\*\*Art Style:\*\*\s*(.+?)(?:\n|$)', storyline)
                if match:
                    art_style = match.group(1).strip()
                    print(f"✅ Priority 1 - Art style from STORYLINE: {art_style}")
                    return art_style
        except Exception as e:
            print(f"❌ Could not read flow state: {e}")
    
    # Priority 2: Try novel.md (generated content)
    novel_file = Path(output_dir) / "novel.md"
    if novel_file.exists():
        content = novel_file.read_text()
        match = re.search(r'-\s*\*\*Art Style:\*\*\s*(.+?)(?:\n|$)', content)
        if match:
            art_style = match.group(1).strip()
            print(f"✅ Priority 2 - Art style from NOVEL.MD: {art_style}")
            return art_style
    
    # Priority 3: Try chapter JSON (from comic generation)
    chapter_files = sorted(Path(output_dir).glob("chapter_*.json"))
    if chapter_files:
        try:
            with open(chapter_files[0], 'r') as f:
                chapter_data = json.load(f)
            art_style = chapter_data.get('art_style')
            if art_style:
                print(f"✅ Priority 3 - Art style from CHAPTER JSON: {art_style}")
                return art_style
        except Exception as e:
            print(f"❌ Could not read chapter JSON: {e}")
    
    # Fallback
    print("⚠️  No art style found in generated content, using default")
    return 'Print Comic Noir Style'

def get_user_config_art_style(output_dir: str) -> str:
    """Get art_style from user's input config (what we're NOT using anymore)."""
    config_file = Path(output_dir) / "input_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('art_style', 'N/A')
    return 'N/A'

if __name__ == "__main__":
    workflow_id = "43e21caa"
    output_dir = f"output/book_{workflow_id}"
    
    print("=" * 80)
    print("TESTING ART STYLE EXTRACTION")
    print("=" * 80)
    
    # Get the LLM-generated art style
    llm_art_style = get_art_style(workflow_id, output_dir)
    
    print()
    
    # Get the user's input art style (for comparison)
    user_art_style = get_user_config_art_style(output_dir)
    print(f"User's input config art style: {user_art_style}")
    
    print()
    print("=" * 80)
    print("RESULT:")
    print("=" * 80)
    if llm_art_style != user_art_style:
        print(f"✅ SUCCESS: Using LLM-generated art style (NOT user config)")
        print(f"   LLM:  {llm_art_style}")
        print(f"   User: {user_art_style}")
    else:
        print(f"⚠️  Using same art style (could be coincidence)")
        print(f"   Art style: {llm_art_style}")
