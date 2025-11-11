#!/usr/bin/env python3
"""
LLM-based documentation extraction tool.
Extracts and formats technical documentation from HTML files using OpenAI API.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import openai
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# Prompt templates as constants
MAIN_PROMPT_TEMPLATE = """
You are an expert technical documentation processor. Extract and format the ACTUAL CONTENT from the provided HTML.

**CRITICAL INSTRUCTION: DO NOT MAKE UP OR HALLUCINATE CONTENT. Extract ONLY what is actually present in the HTML.**

**STRUCTURE REQUIREMENTS:**
1. Start with a clear, descriptive H1 heading that describes the topic (e.g., "Continuity Editing in Film", "Screen Direction Techniques")
2. Create a comprehensive Table of Contents after the H1
3. Add section numbers to all headings (1., 1.1, 1.2, 2., 2.1, etc.)
4. Add a brief document summary after the TOC

**CONTENT REQUIREMENTS:**
1. Extract ONLY the main article/documentation content from the HTML
2. Preserve ALL technical information, definitions, rules, techniques, and examples that are actually in the HTML
3. Maintain the original hierarchical structure of headings and sections
4. Keep all links, but format them properly for {output_format}
5. Preserve any embedded videos, images, or code examples mentioned in the content
6. **IMPORTANT**: If the HTML is about filmmaking, cinematography, or editing techniques, extract that content - do NOT replace it with generic software documentation

{format_instructions}

**NAVIGATION HELPERS:**
1. Number all sections consistently throughout the document
2. Make the document easily parseable by both humans and AI systems

**EXCLUSIONS:**
- Navigation menus and breadcrumbs
- Header and footer content
- Social media sharing buttons
- Advertisement content
- Cookie notices and legal disclaimers
- Author bio sections (unless part of main content)

{custom_instructions_section}

**HTML CONTENT TO PROCESS:**
{html_content}

**REMINDER: Extract the ACTUAL content from the HTML above. Do not invent or hallucinate content. If the HTML is about filmmaking techniques like continuity editing or the 180 degree rule, that's what you should extract. Start with a clear, descriptive H1 heading.**
"""

CHUNK_PROMPT_TEMPLATE = """
You are processing chunk {chunk_num} of {total_chunks} from a large HTML document. 
Extract and format the documentation content from this chunk, maintaining consistency with the overall document structure.

{context_section}

**PROCESSING GUIDELINES:**
1. Extract the main documentation content from this HTML chunk
2. Preserve headings, code examples, and technical information
3. Maintain proper {output_format} formatting
4. If this is not chunk 1, continue section numbering from previous chunks
5. Ensure smooth transitions and avoid duplicate content

{format_instructions}

{custom_instructions_section}

**HTML CHUNK TO PROCESS:**
{chunk_content}

Extract and format the content from this chunk, ensuring it integrates seamlessly with the previous chunks.
"""

CONTEXT_SECTION_TEMPLATE = """
**CONTEXT FROM PREVIOUS CHUNKS:**
{context_summary}

**IMPORTANT**: Continue the document structure and section numbering from where the previous chunks left off.
"""

MARKDOWN_FORMAT_INSTRUCTIONS = """
**MARKDOWN FORMAT REQUIREMENTS:**
- Use standard markdown heading levels (# for h1, ## for h2, ### for h3, etc.) up to h6
- Add a blank line before AND after every heading for better readability
- Format ALL code blocks with triple backticks and appropriate language tags:
  ```python
  code here
  ```
- Use single backticks for inline code: `variable_name`
- Format unordered lists with hyphens (-) and proper indentation
- Format ordered lists with numbers (1., 2., 3.) and proper indentation
- Format links as [link text](URL)
- Use **bold** for emphasis and *italics* where appropriate
- Preserve table formatting using markdown table syntax
- Add cross-references between related sections where appropriate
- Ensure proper spacing between sections and elements
- Always add blank lines around headings to improve document structure
"""

MANPAGE_FORMAT_INSTRUCTIONS = """
**MAN-PAGE FORMAT REQUIREMENTS:**
- Use traditional man-page section headers in UPPERCASE:
  * NAME - Brief description of the tool/feature
  * SYNOPSIS - Usage syntax and basic commands
  * DESCRIPTION - Detailed explanation of functionality
  * OPTIONS - Command-line options and parameters
  * EXAMPLES - Usage examples and code samples
  * SEE ALSO - Related documentation and references
  * NOTES - Additional important information
  * BUGS - Known issues or limitations
  * AUTHOR - Attribution information
- Maintain consistent section numbering throughout the document
- Use proper indentation for subsections (3-4 spaces for level 2, 7-8 spaces for level 3+)
- Format code examples with consistent indentation (7-8 spaces from left margin)
- Use bullet points (·) for unordered lists with proper indentation
- Preserve all technical content and structure information
- Keep cross-references and navigation helpers
- Ensure the document follows traditional Unix man-page conventions
"""


@dataclass
class ExtractionConfig:
    """Configuration for documentation extraction."""

    api_key: str
    model: str = "gpt-4o"
    output_format: str = "markdown"  # "markdown" or "manpage"
    max_tokens: int = 16000
    temperature: float = 0.1


@dataclass
class ExtractionResult:
    """Result of documentation extraction."""

    success: bool
    content: str
    error_message: Optional[str] = None
    source_files: Optional[List[str]] = None


class ContentFormatter:
    """Handles post-processing and formatting of extracted content."""

    def __init__(self, output_format: str = "markdown"):
        self.output_format = output_format

    def format_content(self, content: str) -> str:
        """Apply format-specific formatting to content."""

        if self.output_format == "markdown":
            return self._format_markdown(content)
        elif self.output_format == "manpage":
            return self._format_manpage(content)
        else:
            return content

    def _format_markdown(self, content: str) -> str:
        """Apply markdown-specific formatting."""
        # Ensure proper heading levels (h1-h6)

        content = self._normalize_markdown_headings(content)

        # Ensure code blocks are properly formatted
        content = self._format_code_blocks(content)

        # Ensure lists are properly formatted
        content = self._format_lists(content)

        # Ensure links are properly formatted
        content = self._format_links(content)

        return content

    def _format_manpage(self, content: str) -> str:
        """Apply man-page specific formatting."""

        content = self._convert_to_manpage_sections(content)
        content = self._format_manpage_headings(content)
        content = self._format_manpage_code_blocks(content)
        content = self._format_manpage_lists(content)

        return content

    def _convert_to_manpage_sections(self, content: str) -> str:
        """Convert content to use traditional man-page section headers."""

        lines = content.split("\n")
        formatted_lines = []
        section_mapping = {
            "table of contents": "CONTENTS",
            "overview": "DESCRIPTION",
            "introduction": "DESCRIPTION",
            "description": "DESCRIPTION",
            "getting started": "SYNOPSIS",
            "usage": "SYNOPSIS",
            "examples": "EXAMPLES",
            "options": "OPTIONS",
            "configuration": "OPTIONS",
            "parameters": "OPTIONS",
            "see also": "SEE ALSO",
            "references": "SEE ALSO",
            "notes": "NOTES",
            "bugs": "BUGS",
            "author": "AUTHOR",
            "copyright": "COPYRIGHT",
        }

        for line in lines:
            # Convert top-level headings to man-page sections
            heading_match = re.match(r"^#\s+(.*)", line, re.IGNORECASE)
            if heading_match:
                title = heading_match.group(1).lower().strip()
                manpage_section = section_mapping.get(title, title.upper())
                line = manpage_section

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_manpage_headings(self, content: str) -> str:
        """Format headings for man-page style."""
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            # Convert markdown headings to man-page style
            heading_match = re.match(r"^(#{2,})\s+(.*)", line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)

                # Sub-sections in man-pages are typically indented
                if level == 2:
                    line = f"   {title}"
                elif level >= 3:
                    indent = "       " * (level - 2)
                    line = f"{indent}{title}"

            # Ensure section headers are uppercase and standalone
            if line.strip() and line.isupper() and not line.startswith(" "):
                # Add spacing around section headers
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append("")
                formatted_lines.append(line)
                formatted_lines.append("")
                continue

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_manpage_code_blocks(self, content: str) -> str:
        """Format code blocks for man-page style."""

        # Convert markdown code blocks to indented blocks
        def replace_code_block(match):
            code_content = match.group(1)
            indented_lines = [f"       {line}" for line in code_content.split("\n")]
            return "\n" + "\n".join(indented_lines) + "\n"

        content = re.sub(
            r"```[^\n]*\n(.*?)\n```", replace_code_block, content, flags=re.DOTALL
        )

        # Convert inline code to plain text (man-pages don't have inline code formatting)
        content = re.sub(r"`([^`]+)`", r"\1", content)

        return content

    def _format_manpage_lists(self, content: str) -> str:
        """Format lists for man-page style."""
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            # Convert markdown lists to man-page style
            list_match = re.match(r"^(\s*)[-*+]\s*(.*)", line)
            if list_match:
                _, item_content = list_match.groups()
                # Use consistent indentation for list items
                line = f"       - {item_content}"

            # Convert numbered lists
            num_list_match = re.match(r"^(\s*)(\d+)\.\s*(.*)", line)
            if num_list_match:
                _, num, item_content = num_list_match.groups()
                line = f"       {num}. {item_content}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _normalize_markdown_headings(self, content: str) -> str:
        """Ensure headings use proper markdown levels (# ## ### etc.)."""
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            # Convert any HTML-style headings to markdown
            def replace_heading(match):
                level = int(match.group(1))
                content = match.group(2)
                return f"{'#' * level} {content}"

            line = re.sub(r"<h([1-6])[^>]*>(.*?)</h[1-6]>", replace_heading, line)

            # Ensure heading levels don't exceed 6
            heading_match = re.match(r"^(#{1,})\s*(.*)", line)
            if heading_match:
                hashes, title = heading_match.groups()
                if len(hashes) > 6:
                    hashes = "#" * 6

                line = f"{hashes} {title}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_code_blocks(self, content: str) -> str:
        """Ensure code blocks use triple backticks with language tags."""
        # Replace any HTML code blocks with markdown
        content = re.sub(
            r'<pre><code[^>]*class="language-([^"]*)"[^>]*>(.*?)</code></pre>',
            r"```\1\n\2\n```",
            content,
            flags=re.DOTALL,
        )

        # Replace generic HTML code blocks
        content = re.sub(
            r"<pre><code[^>]*>(.*?)</code></pre>",
            r"```\n\1\n```",
            content,
            flags=re.DOTALL,
        )

        # Replace inline code
        content = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", content)

        # Ensure proper spacing around code blocks
        content = re.sub(r"```([^\n]*)\n([^`]+)```", r"```\1\n\2\n```", content)

        return content

    def _format_lists(self, content: str) -> str:
        """Ensure lists are properly formatted in markdown."""
        lines = content.split("\n")
        formatted_lines = []
        in_list = False

        for line in lines:
            # Convert HTML lists to markdown
            if "<ul>" in line or "<ol>" in line:
                in_list = True
                continue
            elif "</ul>" in line or "</ol>" in line:
                in_list = False
                continue
            elif in_list and "<li>" in line:
                # Extract list item content
                item_content = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", line)
                formatted_lines.append(item_content)
                continue

            # Ensure proper markdown list formatting
            list_match = re.match(r"^(\s*)[-*+]\s*(.*)", line)
            if list_match:
                indent, content_part = list_match.groups()
                line = f"{indent}- {content_part}"

            # Handle numbered lists
            num_list_match = re.match(r"^(\s*)(\d+)\.\s*(.*)", line)
            if num_list_match:
                indent, num, content_part = num_list_match.groups()
                line = f"{indent}{num}. {content_part}"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _format_links(self, content: str) -> str:
        """Ensure links are properly formatted in markdown."""
        # Convert HTML links to markdown
        content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", content)

        # Ensure proper markdown link format
        # This regex handles cases where links might not be properly formatted
        content = re.sub(r"\[([^\]]+)\]\s*\(([^)]+)\)", r"[\1](\2)", content)

        return content


class HTMLDocExtractor:
    """Main class for extracting documentation from HTML files using LLM."""

    def __init__(self, config: ExtractionConfig):
        """Initialize the extractor with configuration."""
        self.config = config
        self.client = openai.OpenAI(api_key=config.api_key)
        self.formatter = ContentFormatter(config.output_format)

    def extract_from_file(
        self,
        html_path: str,
        output_path: str,
        custom_instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract documentation from a single HTML file."""
        return self.extract_from_files([html_path], output_path, custom_instructions)

    def extract_from_files(
        self,
        html_paths: List[str],
        output_path: str,
        custom_instructions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract documentation from multiple HTML files."""
        try:
            all_content = []
            processed_files = []

            for html_path in html_paths:
                try:
                    # Read HTML file
                    html_content = self._read_html_file(html_path)

                    # Process with LLM
                    processed_content = self._process_html_with_llm(
                        html_content, html_path, custom_instructions
                    )

                    all_content.append(processed_content)
                    processed_files.append(html_path)

                except Exception as e:
                    print(f"Warning: Failed to process {html_path}: {e}")
                    continue

            if not all_content:
                return ExtractionResult(
                    success=False,
                    content="",
                    error_message="No files were successfully processed",
                )

            # Combine all content
            combined_content = self._combine_content(all_content, processed_files)

            # Write output
            self._write_output(combined_content, output_path)

            return ExtractionResult(
                success=True, content=combined_content, source_files=processed_files
            )

        except Exception as e:
            return ExtractionResult(success=False, content="", error_message=str(e))

    def _read_html_file(self, html_path: str) -> str:
        """Read HTML content from file."""
        path = Path(html_path)
        if not path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _process_html_with_llm(
        self,
        html_content: str,
        source_file: str,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Process HTML content using LLM."""
        print(f"Processing {source_file} (size: {len(html_content)} chars)")

        # Extract just the body content to reduce size but keep all text
        body_content = self._extract_body_text(html_content)
        print(f"Body content size: {len(body_content)} chars")

        # Check if content is too large and needs chunking
        if len(body_content) > 400000:  # More generous threshold since we're using body text
            print("File is large, using smart chunked processing...")
            return self._process_large_html(
                body_content, source_file, custom_instructions
            )

        prompt = self._build_prompt(body_content, custom_instructions)

        try:
            response = self._call_openai_api(prompt)
            return self._format_response(response, source_file)
        except Exception as e:
            if "context_length_exceeded" in str(e) or "maximum context length" in str(
                e
            ):
                print("Context length exceeded, switching to chunked processing...")
                return self._process_large_html(
                    body_content, source_file, custom_instructions
                )
            raise Exception(f"LLM processing failed for {source_file}: {e}")

    def _process_large_html(
        self,
        html_content: str,
        source_file: str,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """Process large HTML files by intelligently chunking content."""
        print("Processing large HTML file with smart chunking...")

        # First, try to extract just the main content area to reduce size
        main_content = self._extract_main_content_area(html_content)

        # If still too large, chunk it intelligently
        if len(main_content) > 150000:  # Still too large for reliable processing
            chunks = self._smart_chunk_html(main_content, max_chunk_size=100000)
            print(f"Split content into {len(chunks)} chunks")

            processed_chunks = []
            context_summary = ""

            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}...")

                # Build prompt with context from previous chunks
                chunk_prompt = self._build_chunk_prompt(
                    chunk, custom_instructions, i + 1, len(chunks), context_summary
                )
                processed_chunk = self._call_openai_api(chunk_prompt)
                processed_chunks.append(processed_chunk)

                # Update context summary for next chunk
                if i < len(chunks) - 1:  # Don't need context for the last chunk
                    context_summary = self._extract_context_summary(processed_chunk)

            # Combine all processed chunks
            combined_content = self._combine_processed_chunks(processed_chunks)
            return self._format_response(combined_content, source_file)
        else:
            # Content is manageable size after main content extraction
            prompt = self._build_prompt(main_content, custom_instructions)
            response = self._call_openai_api(prompt)
            return self._format_response(response, source_file)

    def _extract_body_text(self, html_content: str) -> str:
        """Extract body content with minimal cleaning - just remove scripts and styles."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove only scripts and styles
            for element in soup(["script", "style"]):
                element.decompose()

            # Get the body element
            body = soup.find("body")
            if body:
                print("Extracted body content")
                return str(body)
            else:
                print("No body found, using entire document")
                return str(soup)

        except Exception as e:
            print(f"BeautifulSoup parsing failed: {e}, using raw HTML")
            # Fallback: just remove script and style tags with regex
            cleaned = re.sub(
                r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE
            )
            cleaned = re.sub(
                r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
            )
            return cleaned

    def _extract_main_content_area(self, html_content: str) -> str:
        """Extract the main content area from HTML using Beautiful Soup."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove unwanted elements
            for element in soup(
                ["script", "style", "nav", "aside"]
            ):
                element.decompose()

            # Remove elements with navigation-related classes/ids (but be more selective)
            nav_selectors = [
                '[class*="navigation"]',
                '[class*="menu-"]',
                '[class*="sidebar"]',
                '[class*="breadcrumb"]',
                '[id*="navigation"]',
                '[id*="menu"]',
                '[id*="sidebar"]',
                '[id*="breadcrumb"]',
            ]

            for selector in nav_selectors:
                for element in soup.select(selector):
                    element.decompose()

            # Look for main content containers in order of preference
            main_selectors = [
                "main",
                "article",
                '[role="main"]',
                '[role="article"]',
                ".entry-content",
                ".post-content",
                ".article-content",
                ".main-single-post",
                ".content-area",
                "#content",
                "#main-content",
                ".page-content",
            ]

            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    print(f"Found main content using selector: {selector}")
                    # Get text preview to verify we have real content
                    text_preview = main_element.get_text()[:200].strip()
                    print(f"Content preview: {text_preview[:100]}...")
                    return str(main_element)

            # If no main content found, return the body or the whole cleaned document
            body = soup.find("body")
            if body:
                print("Using body content")
                text_preview = body.get_text()[:200].strip()
                print(f"Content preview: {text_preview[:100]}...")
                return str(body)
            else:
                print("Using entire cleaned document")
                return str(soup)

        except Exception as e:
            print(f"BeautifulSoup parsing failed: {e}, falling back to regex")
            # Fallback to regex-based cleaning
            return self._regex_clean_html(html_content)

    def _regex_clean_html(self, html_content: str) -> str:
        """Fallback regex-based HTML cleaning."""
        cleaned = html_content

        # Remove scripts, styles, navigation
        cleaned = re.sub(
            r"<script[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<nav[^>]*>.*?</nav>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<header[^>]*>.*?</header>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )
        cleaned = re.sub(
            r"<footer[^>]*>.*?</footer>", "", cleaned, flags=re.DOTALL | re.IGNORECASE
        )

        return cleaned

    def _smart_chunk_html(
        self, html_content: str, max_chunk_size: int = 100000
    ) -> List[str]:
        """Intelligently chunk HTML content using Beautiful Soup at semantic boundaries."""
        if len(html_content) <= max_chunk_size:
            return [html_content]

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            chunks = []
            current_chunk_elements = []
            current_chunk_size = 0

            # Find all top-level content elements (sections, articles, divs with substantial content)
            content_elements = self._find_chunkable_elements(soup)

            for element in content_elements:
                element_size = len(str(element))

                # If this single element is too large, we need to split it further
                if element_size > max_chunk_size:
                    # Save current chunk if it has content
                    if current_chunk_elements:
                        chunks.append(self._elements_to_html(current_chunk_elements))
                        current_chunk_elements = []
                        current_chunk_size = 0

                    # Split the large element into smaller pieces
                    sub_chunks = self._split_large_element(element, max_chunk_size)
                    chunks.extend(sub_chunks)

                # If adding this element would exceed the limit, save current chunk
                elif (
                    current_chunk_size + element_size > max_chunk_size
                    and current_chunk_elements
                ):
                    chunks.append(self._elements_to_html(current_chunk_elements))
                    current_chunk_elements = [element]
                    current_chunk_size = element_size
                else:
                    # Add element to current chunk
                    current_chunk_elements.append(element)
                    current_chunk_size += element_size

            # Add the last chunk if it has content
            if current_chunk_elements:
                chunks.append(self._elements_to_html(current_chunk_elements))

            return chunks if chunks else [html_content]

        except Exception as e:
            print(f"Smart chunking failed: {e}, falling back to simple chunking")
            return self._simple_chunk_html(html_content, max_chunk_size)

    def _find_chunkable_elements(self, soup):
        """Find elements that make good chunk boundaries."""
        # Look for semantic elements first
        chunkable = soup.find_all(["section", "article", "div"], recursive=False)

        # If no semantic elements, look for headings and their following content
        if not chunkable:
            chunkable = []
            for element in soup.children:
                if hasattr(element, "name") and element.name:
                    chunkable.append(element)

        return chunkable

    def _split_large_element(self, element, max_size: int) -> List[str]:
        """Split a large element into smaller chunks."""
        # Try to split by child elements first
        children = list(element.children)
        if len(children) > 1:
            chunks = []
            current_elements = []
            current_size = 0

            for child in children:
                if hasattr(child, "name") and child.name:  # Skip text nodes
                    child_size = len(str(child))
                    if current_size + child_size > max_size and current_elements:
                        # Create chunk from current elements
                        chunk_soup = BeautifulSoup("", "html.parser")
                        wrapper = chunk_soup.new_tag(element.name)
                        for elem in current_elements:
                            wrapper.append(elem.extract())
                        chunk_soup.append(wrapper)
                        chunks.append(str(chunk_soup))

                        current_elements = [child]
                        current_size = child_size
                    else:
                        current_elements.append(child)
                        current_size += child_size

            # Add remaining elements
            if current_elements:
                chunk_soup = BeautifulSoup("", "html.parser")
                wrapper = chunk_soup.new_tag(element.name)
                for elem in current_elements:
                    wrapper.append(elem.extract())
                chunk_soup.append(wrapper)
                chunks.append(str(chunk_soup))

            return chunks
        else:
            # Can't split further, just return as is (will be truncated)
            return [str(element)]

    def _elements_to_html(self, elements) -> str:
        """Convert a list of elements to HTML string."""
        soup = BeautifulSoup("", "html.parser")
        for element in elements:
            soup.append(element.extract())
        return str(soup)

    def _simple_chunk_html(self, html_content: str, max_chunk_size: int) -> List[str]:
        """Simple fallback chunking method."""
        chunks = []
        for i in range(0, len(html_content), max_chunk_size):
            chunks.append(html_content[i : i + max_chunk_size])
        return chunks

    def _build_chunk_prompt(
        self,
        chunk_content: str,
        custom_instructions: Optional[str],
        chunk_num: int,
        total_chunks: int,
        context_summary: str = "",
    ) -> str:
        """Build a prompt for processing a single chunk with context from previous chunks."""
        context_section = ""
        if context_summary and chunk_num > 1:
            context_section = CONTEXT_SECTION_TEMPLATE.format(
                context_summary=context_summary
            )

        custom_instructions_section = ""
        if custom_instructions:
            custom_instructions_section = "**ADDITIONAL INSTRUCTIONS:**\n{}\n".format(
                custom_instructions
            )

        format_instructions = (
            MARKDOWN_FORMAT_INSTRUCTIONS
            if self.config.output_format == "markdown"
            else MANPAGE_FORMAT_INSTRUCTIONS
        )

        return CHUNK_PROMPT_TEMPLATE.format(
            chunk_num=chunk_num,
            total_chunks=total_chunks,
            context_section=context_section,
            output_format=self.config.output_format,
            format_instructions=format_instructions,
            custom_instructions_section=custom_instructions_section,
            chunk_content=chunk_content,
        )

    def _extract_context_summary(self, processed_content: str) -> str:
        """Extract a summary of the processed content to provide context for the next chunk."""
        # Extract the last few headings and key information
        lines = processed_content.split("\n")
        context_lines = []

        # Look for headings and important structural elements
        for line in lines[-50:]:  # Look at last 50 lines
            line = line.strip()
            if line.startswith("#") or line.startswith("**") or line.isupper():
                context_lines.append(line)

        # Also include the last paragraph or two for context
        last_content = []
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith("#"):
                last_content.append(line)
                if len(last_content) >= 3:  # Get a few lines of context
                    break

        context_summary = "Recent headings and structure:\n" + "\n".join(
            context_lines[-5:]
        )
        if last_content:
            context_summary += "\n\nLast content:\n" + "\n".join(reversed(last_content))

        return context_summary

    def _combine_processed_chunks(self, processed_chunks: List[str]) -> str:
        """Combine processed chunks into a coherent document."""
        if not processed_chunks:
            return ""

        if len(processed_chunks) == 1:
            return processed_chunks[0]

        # Combine chunks with proper spacing
        combined = []
        for i, chunk in enumerate(processed_chunks):
            if i > 0:
                # Add some spacing between chunks, but not too much
                combined.append("\n\n")
            combined.append(chunk.strip())

        return "".join(combined)

    def _build_prompt(
        self, html_content: str, custom_instructions: Optional[str] = None
    ) -> str:
        """Build the prompt for LLM processing."""
        format_instructions = (
            MARKDOWN_FORMAT_INSTRUCTIONS
            if self.config.output_format == "markdown"
            else MANPAGE_FORMAT_INSTRUCTIONS
        )

        custom_instructions_section = ""
        if custom_instructions:
            custom_instructions_section = "**ADDITIONAL INSTRUCTIONS:**\n{}\n".format(
                custom_instructions
            )

        return MAIN_PROMPT_TEMPLATE.format(
            output_format=self.config.output_format,
            format_instructions=format_instructions,
            custom_instructions_section=custom_instructions_section,
            html_content=html_content,
        )

    def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API with retry logic."""
        max_retries = 3

        print(f"Making API call (prompt length: {len(prompt)} chars)...")

        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries}")
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert technical documentation processor.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    timeout=120,  # 2 minute timeout
                )

                content = response.choices[0].message.content
                if content is None:
                    raise Exception("OpenAI API returned empty content")

                print("API call successful!")
                return content

            except Exception as e:
                print(f"API call failed: {e}")
                if attempt == max_retries - 1:
                    raise e

                # Exponential backoff
                import time

                time.sleep(2**attempt)
                continue

        # This should never be reached due to the exception handling above
        raise Exception("Failed to get response from OpenAI API after all retries")

    def _format_response(self, response: str, source_file: str) -> str:
        """Format the LLM response."""
        filename = Path(source_file).name

        # Clean up the response
        cleaned_response = response.strip()

        # Apply format-specific formatting
        formatted_content = self.formatter.format_content(cleaned_response)

        # Extract the first H1 heading from the content to use as title
        # If the LLM already created a good H1, use it; otherwise create one
        lines = formatted_content.split('\n')
        has_h1 = False
        for line in lines[:10]:  # Check first 10 lines
            if line.strip().startswith('# ') and not line.lower().startswith('# table of contents'):
                has_h1 = True
                break

        if not has_h1:
            # Create a descriptive header from filename
            # Convert "studiobinder-continuity.html" -> "Continuity Editing in Film"
            title = self._generate_title_from_filename(filename)
            if self.config.output_format == "markdown":
                header = f"# {title}\n\n"
            else:
                header = f"NAME\n    {title}\n\n"
            return header + formatted_content
        
        return formatted_content

    def _generate_title_from_filename(self, filename: str) -> str:
        """Generate a human-readable title from filename."""
        # Remove extension
        name = Path(filename).stem
        
        # Remove common prefixes
        name = name.replace('studiobinder-', '')
        
        # Convert hyphens to spaces and title case
        title = name.replace('-', ' ').replace('_', ' ').title()
        
        # Add context for filmmaking docs
        filmmaking_terms = {
            'continuity': 'Continuity Editing in Film',
            'screen direction': 'Screen Direction in Film',
            'depth of field': 'Depth of Field in Cinematography',
            'shot composition': 'Shot Composition Rules',
            'shotcomposition rules': 'Shot Composition Rules',
            'storyboarding': 'Storyboarding for Film',
            'walter rules': "Walter Murch's Rule of Six",
            'listing shots': 'Shot List Creation',
        }
        
        # Check if we have a better title
        name_lower = name.lower()
        for key, better_title in filmmaking_terms.items():
            if key in name_lower:
                return better_title
        
        return title

    def _combine_content(self, content_list: List[str], source_files: List[str]) -> str:
        """Combine content from multiple files."""
        if len(content_list) == 1:
            return content_list[0]

        combined = []
        for i, (content, source_file) in enumerate(zip(content_list, source_files)):
            if i > 0:
                combined.append("\n\n" + "=" * 80 + "\n")

            filename = Path(source_file).name
            combined.append(f"# Content from {filename}\n\n")
            combined.append(content)

        return "".join(combined)

    def _write_output(self, content: str, output_path: str) -> None:
        """Write content to output file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    """Main CLI function."""
    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Extract and format documentation from HTML files using LLM"
    )
    parser.add_argument("html_files", nargs="+", help="HTML files to process")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "--format",
        choices=["markdown", "manpage"],
        default="markdown",
        help="Output format",
    )
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use")
    parser.add_argument("--instructions", help="Custom extraction instructions")

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please create a .env file with your OpenAI API key")
        sys.exit(1)

    # Create configuration
    config = ExtractionConfig(
        api_key=api_key, model=args.model, output_format=args.format
    )

    # Create extractor and process files
    extractor = HTMLDocExtractor(config)
    result = extractor.extract_from_files(
        args.html_files, args.output, args.instructions
    )

    if result.success:
        print(f"✓ Documentation extracted to: {args.output}")
        if result.source_files:
            print(f"  Processed files: {', '.join(result.source_files)}")
    else:
        print(f"✗ Extraction failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
