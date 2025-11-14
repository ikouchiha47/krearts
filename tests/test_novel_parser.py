#!/usr/bin/env python3
"""Test the novel parser"""

from cinema.models.novel import Novel

# Test parsing novel.md
novel = Novel.from_file("novel.md")

print(f"Title: {novel.title}")
print(f"Metadata: {novel.metadata}")
print(f"Context length: {len(novel.context)} chars")
print(f"Setup length: {len(novel.setup)} chars")
print(f"Number of chapters: {len(novel.chapters)}")
print()

for chapter in novel.chapters[:3]:  # Show first 3 chapters
    print(f"Chapter {chapter.number}: {chapter.title}")
    print(f"  Content length: {len(chapter.content)} chars")
    print(f"  First 100 chars: {chapter.content[:100]}...")
    print()
