# Requirements Document

## Introduction

This feature adds support for multi-panel page layouts in the comic book generation system. Currently, the system generates individual panels sequentially without considering how they should be arranged on physical comic pages. The `knowledge/layouts/panel_arrangements.md` file contains layout templates (horizontal, vertical, fractured, zoom-in progression, etc.) that describe how 2-3 panels should be composed together on a single page with specific visual arrangements, borders, and transitions.

This feature will introduce a `ComicPage` model that groups 2-3 panels together with layout metadata, enabling the system to generate multi-panel page compositions that follow the creative layout patterns defined in the knowledge base.

## Glossary

- **ComicPanel**: A single comic book panel with visual description, dialogue, and metadata
- **ComicPage**: A new model representing a physical comic page containing 2-3 panels with layout specifications
- **ComicScene**: A sequence of panels (or pages) in the same location/time
- **Panel Arrangement**: How panels are positioned on a page (horizontal, vertical, overlapping, etc.)
- **Panel Borders**: Visual style of borders between panels (clean, ragged, overlapping, etc.)
- **Panel Transition Style**: How panels interact visually (hard cuts, blended transitions, diagonal cuts, etc.)
- **ChapterBuilder**: A crew variant that processes single chapters with screenplay context
- **ParallelComicGenerator**: Orchestrator that processes chapters in parallel
- **Beat Plan**: A screenplay-specific structure (2-3 beats per scene) that is NOT used for comic generation

## Requirements

### Requirement 1

**User Story:** As a comic book generator, I want to group individual panels into multi-panel page layouts, so that I can create visually dynamic page compositions following established comic book design patterns.

#### Acceptance Criteria

1. THE System SHALL define a ComicPage model that contains 2-3 ComicPanel objects
2. THE ComicPage model SHALL include panel_arrangement field describing the layout pattern
3. THE ComicPage model SHALL include panel_borders field describing border styling
4. THE ComicPage model SHALL include panel_transition_style field describing visual transitions
5. THE ComicPage model SHALL include page_number field for sequential ordering
6. THE System SHALL NOT use the Beat Plan approach from screenplay task for comic generation

### Requirement 2

**User Story:** As a comic scene generator, I want scenes to contain pages instead of individual panels, so that the output structure reflects physical comic book page organization.

#### Acceptance Criteria

1. THE ComicScene model SHALL contain a list of ComicPage objects instead of ComicPanel objects
2. WHEN a scene is created, THE System SHALL group panels into pages of 2-3 panels each
3. THE System SHALL maintain backward compatibility by keeping the existing ComicPanel model unchanged
4. THE System SHALL ensure each page contains between 2 and 3 panels

### Requirement 3

**User Story:** As a layout designer, I want to specify different panel arrangement patterns, so that I can create varied and dynamic page compositions.

#### Acceptance Criteria

1. THE System SHALL support panel_arrangement values including "horizontal-2-panel", "horizontal-3-panel", "vertical-2-panel", "vertical-3-panel", "fractured-overlapping", "zoom-progression", "cross-over-bleed"
2. THE System SHALL support panel_borders values including "clean-sharp", "ragged-dynamic", "overlapping", "no-borders"
3. THE System SHALL support panel_transition_style values including "hard-cuts", "overlapping-scenes", "blended-transitions", "diagonal-cuts", "frame-within-frame"
4. THE System SHALL allow optional fields for layout metadata

### Requirement 4

**User Story:** As a task description writer, I want the chapterbuilder task to instruct agents to generate multi-panel pages, so that the output follows the new page-based structure.

#### Acceptance Criteria

1. THE chapterbuilder task description SHALL instruct agents to group panels into pages of 2-3 panels
2. THE task description SHALL reference the panel_arrangements.md knowledge base for layout patterns
3. THE task description SHALL provide examples of ComicPage structure with layout metadata
4. THE task description SHALL maintain instructions for individual panel generation

### Requirement 5

**User Story:** As a parallel comic generator, I want to pass screenplay context to the chapterbuilder crew, so that agents have full story context when expanding individual chapters.

#### Acceptance Criteria

1. THE ParallelComicGenerator SHALL accept a screenplay parameter containing the full novel text
2. WHEN processing a chapter, THE ParallelComicGenerator SHALL pass both chapter content and full screenplay to the crew
3. THE chapterbuilder task SHALL support receiving screenplay context as input
4. THE System SHALL support both knowledge-base and prompt-based screenplay context approaches

### Requirement 6

**User Story:** As a comic book output validator, I want the system to calculate page statistics, so that I can verify the output structure is correct.

#### Acceptance Criteria

1. THE ComicBookOutput model SHALL include total_pages field for page count
2. THE ComicChapter model SHALL calculate estimated_pages based on scene page counts
3. THE System SHALL update total_pages when chapters are added
4. THE System SHALL maintain existing panel and scene statistics

---

## References

- `cinema/models/comic_output.py` - Current output models
- `knowledge/layouts/panel_arrangements.md` - Layout pattern templates
- `cinema/agents/bookwriter/plotbuilder/tasks.yaml` - Task descriptions (chapterbuilder section)
- `cinema/pipeline/parallel_comic_generator.py` - Parallel processing orchestrator
- `cinema/agents/bookwriter/flow.py` - Flow integration


### Requirement 7

**User Story:** As a system architect, I want to clarify that Beat Plans are for screenplay output only, so that there is no confusion between screenplay beats and comic panels.

#### Acceptance Criteria

1. THE screenplay task SHALL continue to use Beat Plan structure for film/video output
2. THE chapterbuilder and stripper tasks SHALL NOT use Beat Plan structure
3. THE comic generation SHALL use ComicPage and ComicPanel models exclusively
4. THE System SHALL maintain clear separation between screenplay (Beat Plan) and comic (Page/Panel) workflows
