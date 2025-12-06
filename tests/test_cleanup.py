#!/usr/bin/env python3
"""Test text cleanup"""

from cinema.models.storyline import Character

# Test the cleanup
text = "He couldn't protect Eddie—his career"
print('Before:', repr(text))

cleaned = Character._clean_text(text)
print('After:', repr(cleaned))

# Check if it worked
assert chr(8212) not in cleaned, "Em-dash not replaced"
assert chr(8217) not in cleaned, "Curly quote not replaced"
print("✅ Cleanup works!")
