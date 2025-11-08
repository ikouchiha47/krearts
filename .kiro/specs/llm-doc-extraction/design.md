# Design Document

## Overview

The LLM-based documentation extraction system will replace the current BeautifulSoup approach with an intelligent LLM-powered solution. The system will use OpenAI's API to process HTML files and generate well-structured documentation with table of contents, navigation helpers, and support for both markdown and man-page formats.

## Architecture

### High-Level Architecture
```
HTML Files → HTML Reader → OpenAI API → Content Processor → Output Writer → Formatted Documentation
```

### Components
1. **HTML Reader**: Reads HTML files from disk
2. **LLM Processor**: Sends HTML to OpenAI API with structured prompts
3. **Content Formatter**: Post-processes LLM output for consistency
4. **Output Writer**: Saves formatted documentation to file

## Components and Interfaces

### HTMLDocExtractor Class
- `__init__(api_key, model="gpt-4", output_format="markdown")`
- `extract_from_file(html_path, output_path, custom_instructions=None)`
- `extract_from_files(html_paths, output_path, custom_instructions=None)`

### LLMProcessor Class
- `process_html(html_content, format_type, custom_instructions)`
- `_build_prompt(html_content, format_type, custom_instructions)`
- `_call_openai_api(prompt)`

### ContentFormatter Class
- `format_output(raw_content, format_type)`
- `add_table_of_contents(content)`
- `add_section_numbers(content)`

## Data Models

### Configuration
```python
@dataclass
class ExtractionConfig:
    api_key: str
    model: str = "gpt-4"
    output_format: str = "markdown"  # "markdown" or "manpage"
    max_tokens: int = 4000
    temperature: float = 0.1
```

### Processing Result
```python
@dataclass
class ExtractionResult:
    success: bool
    content: str
    error_message: Optional[str] = None
    source_files: List[str] = None
```

## Error Handling

- **File Not Found**: Log error and continue with other files
- **API Errors**: Retry with exponential backoff (max 3 attempts)
- **Invalid HTML**: Log warning and attempt processing anyway
- **Token Limit**: Chunk large HTML files and process in parts

## Testing Strategy

### Unit Tests
- Test HTML reading functionality
- Test prompt generation
- Test content formatting
- Test configuration handling

### Integration Tests
- Test end-to-end extraction with sample HTML files
- Test API error handling
- Test multiple file processing

### Manual Testing
- Test with actual Veo documentation HTML files
- Verify output quality and structure
- Test both markdown and man-page formats

## Implementation Plan

1. **Core Structure**: Create main classes and interfaces
2. **OpenAI Integration**: Implement API calls with proper error handling
3. **Content Processing**: Add table of contents and navigation helpers
4. **Format Support**: Implement both markdown and man-page outputs
5. **CLI Interface**: Create simple command-line interface
6. **Testing**: Add comprehensive tests and validation