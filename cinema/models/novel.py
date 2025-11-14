"""
Novel parser for extracting chapters from markdown novels.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class NovelChapter:
    """Represents a single chapter from a novel"""
    number: int
    title: str
    content: str


@dataclass
class Novel:
    """Represents a complete novel with metadata and chapters"""
    title: str
    metadata: dict
    context: str
    setup: str
    chapters: List[NovelChapter]
    
    @classmethod
    def from_file(cls, path: str) -> 'Novel':
        """Load and parse a novel from a markdown file"""
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_str(f.read())
    
    @classmethod
    def from_str(cls, content: str) -> 'Novel':
        """Parse a novel from markdown string"""
        lines = content.split('\n')
        
        # Extract title (first # heading)
        title = ""
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Extract metadata section
        metadata = cls._extract_metadata(content)
        
        # Extract context section
        context = cls._extract_section(content, "## Context")
        
        # Extract setup section
        setup = cls._extract_section(content, "## Setup")
        
        # Extract chapters
        chapters = cls._extract_chapters(content)
        
        return cls(
            title=title,
            metadata=metadata,
            context=context,
            setup=setup,
            chapters=chapters
        )
    
    @staticmethod
    def _extract_metadata(content: str) -> dict:
        """Extract metadata from ## Metadata section"""
        metadata = {}
        
        # Find metadata section
        metadata_match = re.search(r'## Metadata\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if not metadata_match:
            return metadata
        
        metadata_text = metadata_match.group(1)
        
        # Parse key-value pairs (- Key: Value format)
        for line in metadata_text.split('\n'):
            line = line.strip()
            if line.startswith('- '):
                line = line[2:]  # Remove "- "
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        
        return metadata
    
    @staticmethod
    def _extract_section(content: str, section_header: str) -> str:
        """Extract content from a specific ## section"""
        pattern = rf'{re.escape(section_header)}\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    @staticmethod
    def _extract_chapters(content: str) -> List[NovelChapter]:
        """Extract all chapters from the novel"""
        chapters = []
        
        # Find all chapter headings (## Chapter N: Title or # Chapter N: Title)
        chapter_pattern = r'##? Chapter (\d+):\s*(.+?)(?=\n)'
        chapter_matches = list(re.finditer(chapter_pattern, content))
        
        for i, match in enumerate(chapter_matches):
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            
            # Extract chapter content (from this chapter to next chapter or end)
            start_pos = match.end()
            if i + 1 < len(chapter_matches):
                end_pos = chapter_matches[i + 1].start()
            else:
                end_pos = len(content)
            
            chapter_content = content[start_pos:end_pos].strip()
            
            chapters.append(NovelChapter(
                number=chapter_num,
                title=chapter_title,
                content=chapter_content
            ))
        
        return chapters
    
    def to_str(self) -> str:
        """Convert novel back to markdown string format"""
        parts = []
        
        # Title
        parts.append(f"# {self.title}\n")
        
        # Metadata
        if self.metadata:
            parts.append("## Metadata")
            for key, value in self.metadata.items():
                parts.append(f"  - {key}: {value}")
            parts.append("")
        
        # Context
        if self.context:
            parts.append("---\n")
            parts.append("## Context\n")
            parts.append(self.context)
            parts.append("")
        
        # Setup
        if self.setup:
            parts.append("---\n")
            parts.append("## Setup\n")
            parts.append(self.setup)
            parts.append("")
        
        # Chapters
        for chapter in self.chapters:
            parts.append("---\n")
            parts.append(f"## Chapter {chapter.number}: {chapter.title}\n")
            parts.append(chapter.content)
            parts.append("")
        
        return "\n".join(parts)
    
    def write_chapters_to_dir(self, base_dir: Path, run_id: str):
        """Write each chapter to a separate markdown file"""
        output_dir = base_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write metadata file
        metadata_file = output_dir / "metadata.md"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.title}\n\n")
            f.write("## Metadata\n\n")
            for key, value in self.metadata.items():
                f.write(f"- {key}: {value}\n")
            f.write(f"\n## Context\n\n{self.context}\n")
            f.write(f"\n## Setup\n\n{self.setup}\n")
        
        # Write each chapter
        for chapter in self.chapters:
            chapter_file = output_dir / f"chapter_{chapter.number:02d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# Chapter {chapter.number}: {chapter.title}\n\n")
                f.write(chapter.content)
        
        return output_dir
