#!/usr/bin/env python3
"""
Test character extraction from storyline.
"""

from pathlib import Path
from cinema.models.storyline import Storyline


def test_character_extraction(flow_id: str = "43e21caa"):
    """Test extracting characters from a flow state"""
    
    print(f"Loading storyline from flow: {flow_id}")
    print("=" * 80)
    
    # Load storyline
    storyline = Storyline.from_flow_state(flow_id)
    
    print(f"Title: {storyline.title}")
    print(f"Subtitle: {storyline.subtitle}")
    print(f"Characters found: {len(storyline.characters)}")
    print()
    
    # Display each character
    for i, char in enumerate(storyline.characters, 1):
        print(f"Character {i}: {char.name}")
        print(f"  Role: {char.role}")
        print(f"  Age: {char.age}")
        print(f"  Ethnicity: {char.ethnicity}")
        print(f"  Quirks: {len(char.quirks)}")
        print(f"  Backstory length: {len(char.backstory)} chars")
        print(f"  Motivations: {char.motivations[:100]}..." if len(char.motivations) > 100 else f"  Motivations: {char.motivations}")
        print(f"  Long-term goals: {char.long_term_goals[:100]}..." if len(char.long_term_goals) > 100 else f"  Long-term goals: {char.long_term_goals}")
        print()
    
    # Save characters to JSON
    output_dir = Path(f"output/book_{flow_id}/characters_extracted")
    print(f"Saving characters to: {output_dir}")
    saved_files = storyline.save_characters(output_dir)
    
    print(f"Saved {len(saved_files)} files:")
    for filepath in saved_files:
        print(f"  - {filepath.name}")
    
    print()
    print("=" * 80)
    print("✅ Character extraction successful!")
    
    # Test character lookup
    print()
    print("Testing character lookup:")
    detective = storyline.get_characters_by_role("detective")
    print(f"  Detectives: {[d.name for d in detective]}")
    
    killer = storyline.get_characters_by_role("killer")
    print(f"  Killers: {[k.name for k in killer]}")
    
    victim = storyline.get_characters_by_role("victim")
    print(f"  Victims: {[v.name for v in victim]}")
    
    return storyline


if __name__ == "__main__":
    import sys
    
    flow_id = sys.argv[1] if len(sys.argv) > 1 else "43e21caa"
    storyline = test_character_extraction(flow_id)
