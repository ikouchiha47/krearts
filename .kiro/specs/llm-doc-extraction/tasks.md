# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create main script file `extract_docs_llm.py`
  - Add required dependencies: `openai`, `python-dotenv`, `requests`
  - Create `.env.example` file for API key configuration
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement core HTML processing functionality
  - [x] 2.1 Create HTMLDocExtractor class with initialization
    - Initialize with API key, model, and output format parameters
    - Load environment variables using python-dotenv
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 2.2 Implement HTML file reading functionality
    - Read HTML files from disk with error handling
    - Handle multiple file processing sequentially
    - _Requirements: 1.1, 2.1, 2.4_

- [x] 3. Implement OpenAI API integration
  - [x] 3.1 Create LLM prompt generation system
    - Build structured prompts for documentation extraction
    - Include instructions for table of contents generation
    - Add format-specific instructions (markdown vs man-page)
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 7.2, 7.3_
  
  - [x] 3.2 Implement OpenAI API calls with error handling
    - Make API requests using openai library
    - Add retry logic with exponential backoff
    - Handle token limits and chunking for large files
    - _Requirements: 1.2, 2.4_

- [ ] 4. Implement content formatting and navigation
  - [ ] 4.1 Add table of contents generation
    - Extract headings and create TOC within first 200-500 lines
    - Add section numbers and indentation
    - Include line/page references
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 4.2 Add navigation helpers and cross-references
    - Add section numbers to all headings
    - Include anchor links for major sections
    - Add document summary after TOC
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 5. Implement output formatting options
  - [x] 5.1 Support markdown format output
    - Ensure proper markdown heading levels (h1-h6)
    - Format code blocks with triple backticks
    - Preserve lists and links in markdown format
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 7.3_
  
  - [x] 5.2 Support man-page format output
    - Use traditional man-page section headers
    - Maintain consistent section numbering
    - Preserve all content and structure information
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [ ] 6. Create command-line interface
  - [x] 6.1 Implement main CLI function
    - Accept input HTML file paths as arguments
    - Support configuration options (output format, model, etc.)
    - Provide clear usage instructions and help
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 6.2 Add file processing and output handling
    - Process single or multiple HTML files
    - Save formatted output to specified file path
    - Report processing status and errors
    - _Requirements: 1.4, 1.5, 2.2, 2.3_

- [ ] 7. Test and validate implementation
  - [ ] 7.1 Test with Veo documentation HTML files
    - Process the existing gemini-veo3.html and gemini-video-gen-basics.html files
    - Verify output quality and structure
    - Compare with current BeautifulSoup output
    - _Requirements: All requirements validation_
  
  - [ ] 7.2 Create usage documentation
    - Write README with setup and usage instructions
    - Document configuration options and examples
    - Include sample .env file setup
    - _Requirements: 8.5_