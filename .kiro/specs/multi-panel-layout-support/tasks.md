# Implementation Plan

- [x] 1. Add ComicPage model to comic_output.py
  - Create ComicPage class with page identification fields (page_number, chapter, scene_number)
  - Add panel_arrangement field with layout type literals from panel_arrangements.md
  - Add panel_borders and panel_transition_style fields with appropriate literals
  - Add panels field with List[ComicPanel] constrained to 2-3 items using Pydantic validation
  - Add optional page_description field for overall composition notes
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2, 3.3, 3.4_

- [x] 2. Update ComicScene model for page-based structure
  - [x] 2.1 Add pages field to ComicScene model
    - Add pages: List[ComicPage] field to replace panels usage
    - Update docstring to reflect 2-4 pages per scene instead of 3-8 panels
    - _Requirements: 2.1, 2.2_
  
  - [x] 2.2 Maintain backward compatibility with panels field
    - Keep existing panels field but mark as deprecated in docstring
    - Add migration logic to auto-convert panels to pages if panels is populated
    - Log warning when migration occurs
    - _Requirements: 2.3_

- [x] 3. Update ComicBookOutput statistics
  - Add total_pages field to ComicBookOutput model
  - Update docstring with new expected output statistics (pages and panels)
  - Mark estimated_pages as deprecated in favor of total_pages
  - Add calculation logic to compute total_pages from all chapters
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 4. Update chapterbuilder task description
  - [x] 4.1 Add page grouping instructions to chapterbuilder task
    - Update task description to instruct agents to group panels into pages of 2-3
    - Add guidance on when to use 2-panel vs 3-panel layouts
    - Reference knowledge/layouts/panel_arrangements.md for layout patterns
    - _Requirements: 4.1, 4.2_
  
  - [x] 4.2 Add ComicPage examples to task description
    - Create example ComicPage structures showing different panel_arrangement types
    - Include examples of panel_borders and panel_transition_style usage
    - Show how to structure pages within scenes
    - _Requirements: 4.3_
  
  - [x] 4.3 Update expected output description
    - Change "3-8 panels per scene" to "2-4 pages per scene (4-12 panels total)"
    - Update panel count expectations to reflect page-based grouping
    - Maintain individual panel generation instructions
    - _Requirements: 4.4_

- [x] 5. Update ParallelComicGenerator for screenplay context
  - [x] 5.1 Add screenplay parameter to ParallelComicGenerator
    - Add screenplay: str parameter to __init__ method
    - Store screenplay as instance variable for passing to crews
    - _Requirements: 5.1_
  
  - [x] 5.2 Pass screenplay context to chapterbuilder crew
    - Update chapter processing to include screenplay in crew inputs
    - Pass both chapter_content and full screenplay to crew kickoff
    - Add logging for screenplay context passing
    - _Requirements: 5.2, 5.3_
  
  - [x] 5.3 Update statistics calculation for pages
    - Update total_pages calculation logic in result aggregation
    - Ensure page numbers are sequential across chapters
    - Add validation logging for page statistics
    - _Requirements: 6.1, 6.2_

- [x] 6. Verify flow.py to pass screenplay to generator
  - Modify handle_storyboarding method to pass screenplay to ParallelComicGenerator
  - Extract screenplay from state.output.screenplay
  - Pass screenplay parameter when creating ParallelComicGenerator instance
  - _Requirements: 5.1, 5.2_

- [x] 7. Add chapterbuilder task to tasks.yaml if not present
  - Check if chapterbuilder task exists in plotbuilder/tasks.yaml
  - If missing, create chapterbuilder task section with page-based instructions
  - If present, update existing task with page grouping instructions
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.3_

- [ ]* 8. Write unit tests for ComicPage model
  - Test ComicPage creation with valid 2-3 panel configurations
  - Test Pydantic validation rejects pages with <2 or >3 panels
  - Test all panel_arrangement literal values are accepted
  - Test all panel_borders and panel_transition_style values
  - Test ComicScene with pages field populated
  - Test backward compatibility migration from panels to pages
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3_

- [ ]* 9. Write integration tests for page generation
  - Test ParallelComicGenerator produces ComicPage objects
  - Test chapterbuilder crew generates pages with layout metadata
  - Test total_pages calculation in ComicBookOutput
  - Test page number continuity across scenes and chapters
  - _Requirements: 2.2, 5.2, 6.1, 6.2_
