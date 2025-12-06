# LLM Documentation Extractor

A tool that uses OpenAI's API to intelligently extract and format technical documentation from HTML files.

## Features

- Extracts clean documentation content from HTML files
- Generates table of contents with section numbering
- Supports both markdown and man-page output formats
- Processes multiple files and combines them
- Filters out navigation, headers, footers, and other boilerplate content

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Basic usage:
```bash
python extract_docs_llm.py docs/gemini-veo3.html -o output.md
```

### Process multiple files:
```bash
python extract_docs_llm.py docs/*.html -o combined_docs.md
```

### Use man-page format:
```bash
python extract_docs_llm.py docs/gemini-veo3.html -o output.txt --format manpage
```

### Use different model:
```bash
python extract_docs_llm.py docs/gemini-veo3.html -o output.md --model gpt-3.5-turbo
```

### Add custom instructions:
```bash
python extract_docs_llm.py docs/gemini-veo3.html -o output.md --instructions "Focus on API examples and code snippets"
```

## Options

- `html_files`: One or more HTML files to process
- `-o, --output`: Output file path (required)
- `--format`: Output format (`markdown` or `manpage`, default: `markdown`)
- `--model`: OpenAI model to use (default: `gpt-4`)
- `--instructions`: Custom extraction instructions

## Example

```bash
# Extract Veo documentation
python extract_docs_llm.py docs/gemini-veo3.html docs/gemini-video-gen-basics.html -o veo_docs_clean.md
```

This will create a clean, well-structured markdown document with:
- Table of contents
- Section numbering
- Navigation helpers
- Filtered content (no navigation/boilerplate)
- Combined content from both files