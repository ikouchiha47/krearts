#!/usr/bin/env python3
"""
Setup script to create art style reference directories.

Run this to set up the directory structure for organizing reference images
from Blueberry, Akira, Spider-Verse, Arcane, and other comic styles.
"""

from cinema.workflow.art_style_references import create_reference_structure

if __name__ == "__main__":
    print("=" * 70)
    print("Art Style Reference Directory Setup")
    print("=" * 70)
    print()
    
    create_reference_structure()
    
    print()
    print("=" * 70)
    print("Setup Complete!")
    print("=" * 70)
