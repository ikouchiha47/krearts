# Requirements Document

## Introduction

This specification defines the migration of the bookwriter module from CrewAI to DSPy. The current bookwriter implementation uses CrewAI's ReACT-style 2-step prompting with sequential agent execution. This migration aims to leverage DSPy's advanced prompting techniques (Chain-of-Thought, Tree-of-Thought, Reflection) and parallel generation capabilities while maintaining compatibility with tools, knowledge bases, and structured outputs.

## Glossary

- **BookWriter**: The cinema.agents.bookwriter module responsible for detective story generation, critique, screenplay writing, and comic strip storyboarding (CrewAI implementation)
- **BookWriterDSPy**: The new cinema.agents.bookwriter_dspy module that will implement the same functionality using DSPy
- **DSPy**: A framework for programming language models with composable modules, optimizers, and structured prompting techniques
- **CrewAI**: The current framework using ReACT-style agents with sequential task execution
- **Flow**: CrewAI's state machine implementation for orchestrating multi-step agent workflows
- **Signature**: DSPy's type-safe interface defining inputs and outputs for LLM modules
- **Module**: DSPy's composable unit that wraps prompting logic with signatures
- **Tool**: External functions that agents can call (file reading, directory listing, etc.)
- **Knowledge Base**: Text file sources providing domain knowledge to agents
- **Structured Output**: Pydantic models defining the schema for LLM responses
- **CoT**: Chain-of-Thought prompting technique for step-by-step reasoning
- **ToT**: Tree-of-Thought prompting for exploring multiple reasoning paths
- **Reflection**: Self-critique and iterative improvement pattern

## Requirements

### Requirement 1: DSPy Framework Integration

**User Story:** As a developer, I want to use DSPy instead of CrewAI for the bookwriter module, so that I can leverage advanced prompting techniques and parallel generation.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL be implemented in a separate directory at cinema/agents/bookwriter_dspy
2. THE BookWriterDSPy System SHALL integrate DSPy as the primary LLM orchestration framework
3. THE BookWriterDSPy System SHALL support Chain-of-Thought (CoT) prompting for complex reasoning tasks
4. THE BookWriterDSPy System SHALL support Tree-of-Thought (ToT) prompting for exploring multiple narrative paths
5. THE BookWriterDSPy System SHALL support Reflection patterns for self-critique and iterative improvement
6. THE BookWriterDSPy System SHALL enable parallel generation of independent content (e.g., character descriptions, scene descriptions)
7. THE BookWriterDSPy System SHALL coexist with the existing cinema.agents.bookwriter CrewAI implementation

### Requirement 2: Tool Integration

**User Story:** As a developer, I want DSPy modules to access file system tools, so that agents can read knowledge base files and directory structures.

#### Acceptance Criteria

1. WHEN a DSPy Module requires file system access, THE BookWriterDSPy System SHALL provide DirectoryReadTool functionality
2. WHEN a DSPy Module requires file content access, THE BookWriterDSPy System SHALL provide FileReadTool functionality
3. THE BookWriterDSPy System SHALL wrap CrewAI tools as DSPy-compatible functions
4. THE BookWriterDSPy System SHALL maintain tool call logging and error handling
5. THE BookWriterDSPy System SHALL support tool result caching to avoid redundant file reads

### Requirement 3: Knowledge Base Integration

**User Story:** As a developer, I want DSPy modules to access knowledge bases, so that agents can reference domain expertise during generation.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL load knowledge base files from the knowledge directory
2. THE BookWriterDSPy System SHALL inject knowledge base content into DSPy module context
3. THE BookWriterDSPy System SHALL support selective knowledge loading based on task requirements
4. THE BookWriterDSPy System SHALL cache knowledge base content to improve performance
5. THE BookWriterDSPy System SHALL support knowledge base updates without system restart

### Requirement 4: Structured Output Support

**User Story:** As a developer, I want DSPy modules to generate structured outputs, so that downstream systems can reliably parse and process results.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL define DSPy Signatures with Pydantic output models
2. WHEN a DSPy Module generates output, THE BookWriterDSPy System SHALL validate against the defined schema
3. THE BookWriterDSPy System SHALL support DetectiveStoryOutput as a structured output type
4. THE BookWriterDSPy System SHALL support nested Pydantic models in output schemas
5. THE BookWriterDSPy System SHALL provide clear error messages when output validation fails

### Requirement 5: Detective Plot Builder Migration

**User Story:** As a developer, I want the DetectivePlotBuilder to use DSPy, so that it can leverage CoT reasoning for character development and plot construction.

#### Acceptance Criteria

1. THE DetectivePlotBuilder SHALL use DSPy Modules instead of CrewAI Agents
2. THE DetectivePlotBuilder SHALL apply Chain-of-Thought prompting for character backstory generation
3. THE DetectivePlotBuilder SHALL support parallel generation of multiple character profiles
4. THE DetectivePlotBuilder SHALL maintain compatibility with existing input schemas (DetectivePlotBuilderSchema)
5. THE DetectivePlotBuilder SHALL produce markdown output compatible with existing consumers

### Requirement 6: Plot Critique Migration

**User Story:** As a developer, I want the PlotCritique to use DSPy Reflection, so that it can iteratively improve storylines through self-critique.

#### Acceptance Criteria

1. THE PlotCritique SHALL use DSPy Reflection modules for iterative critique
2. THE PlotCritique SHALL evaluate storylines against detective story principles
3. THE PlotCritique SHALL generate actionable feedback with severity rankings
4. THE PlotCritique SHALL support binary PASS/FAIL verdicts
5. THE PlotCritique SHALL maintain compatibility with existing critique output format

### Requirement 7: Screenplay Writer Migration

**User Story:** As a developer, I want the ScreenplayWriter to use DSPy, so that it can generate industry-standard screenplay format with proper structure.

#### Acceptance Criteria

1. THE ScreenplayWriter SHALL use DSPy Modules for screenplay expansion
2. THE ScreenplayWriter SHALL generate screenplay format compliant with industry standards
3. THE ScreenplayWriter SHALL support configurable page length
4. THE ScreenplayWriter SHALL maintain art style consistency throughout the screenplay
5. THE ScreenplayWriter SHALL produce structured output compatible with downstream processors

### Requirement 8: Comic Strip Storyboarding Migration

**User Story:** As a developer, I want the ComicStripStoryBoarding to use DSPy, so that it can generate visual panel descriptions with parallel processing.

#### Acceptance Criteria

1. THE ComicStripStoryBoarding SHALL use DSPy Modules for panel generation
2. THE ComicStripStoryBoarding SHALL support parallel generation of independent panels
3. THE ComicStripStoryBoarding SHALL apply art style enhancements to visual descriptions
4. THE ComicStripStoryBoarding SHALL generate DetectiveStoryOutput with character and panel data
5. THE ComicStripStoryBoarding SHALL maintain visual continuity across panels

### Requirement 9: Flow Migration

**User Story:** As a developer, I want the StoryBuilder Flow to use DSPy orchestration, so that I can control the multi-step workflow with better observability.

#### Acceptance Criteria

1. THE StoryBuilder Flow SHALL orchestrate DSPy Modules instead of CrewAI Crews
2. THE StoryBuilder Flow SHALL maintain the same state machine logic (plan → critique → screenplay → storyboard)
3. THE StoryBuilder Flow SHALL support configurable retry limits for critique iterations
4. THE StoryBuilder Flow SHALL provide observable state transitions and logging
5. THE StoryBuilder Flow SHALL support skip_storyboard flag for early termination

### Requirement 10: LLM Provider Compatibility

**User Story:** As a developer, I want DSPy to work with existing LLM providers, so that I can use Gemini and other configured models.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL support Gemini models through DSPy
2. THE BookWriterDSPy System SHALL maintain compatibility with the existing LLMStore registry
3. THE BookWriterDSPy System SHALL support LLMPlannerIntent, LLMExecutorIntent, and LLMCritiqueIntent
4. THE BookWriterDSPy System SHALL handle rate limiting and error retry for LLM calls
5. THE BookWriterDSPy System SHALL support model switching without code changes

### Requirement 11: Performance Optimization

**User Story:** As a developer, I want DSPy to improve generation performance, so that storylines are created faster than with CrewAI.

#### Acceptance Criteria

1. WHEN generating independent content, THE BookWriterDSPy System SHALL execute DSPy Modules in parallel
2. THE BookWriterDSPy System SHALL cache knowledge base content to reduce file I/O
3. THE BookWriterDSPy System SHALL reuse compiled DSPy programs across multiple runs
4. THE BookWriterDSPy System SHALL provide performance metrics for each generation step
5. THE BookWriterDSPy System SHALL complete full storyline generation at least 20% faster than CrewAI baseline

### Requirement 12: Backward Compatibility

**User Story:** As a developer, I want to maintain existing interfaces, so that downstream systems continue to work without modification.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL maintain existing input schemas (DetectivePlotBuilderSchema, CritiqueSchema, etc.)
2. THE BookWriterDSPy System SHALL maintain existing output formats (markdown, JSON, Pydantic models)
3. THE BookWriterDSPy System SHALL maintain existing file output paths and naming conventions
4. THE BookWriterDSPy System SHALL support the same DirectorsContext configuration
5. THE BookWriterDSPy System SHALL provide drop-in replacement classes for existing bookwriter components

### Requirement 13: Testing and Validation

**User Story:** As a developer, I want comprehensive tests for DSPy migration, so that I can verify correctness and catch regressions.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL include unit tests for each DSPy Module
2. THE BookWriterDSPy System SHALL include integration tests for the complete StoryBuilder Flow
3. THE BookWriterDSPy System SHALL validate structured outputs against Pydantic schemas
4. THE BookWriterDSPy System SHALL compare DSPy outputs with CrewAI baseline for quality
5. THE BookWriterDSPy System SHALL achieve at least 90% test coverage for new DSPy code

### Requirement 14: Documentation and Examples

**User Story:** As a developer, I want clear documentation for DSPy usage, so that I can understand and extend the implementation.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL provide architecture documentation explaining DSPy design patterns
2. THE BookWriterDSPy System SHALL provide migration guide comparing CrewAI and DSPy approaches
3. THE BookWriterDSPy System SHALL provide example scripts demonstrating DSPy usage in cinema/cmd/examples
4. THE BookWriterDSPy System SHALL document tool integration patterns
5. THE BookWriterDSPy System SHALL document knowledge base integration patterns

### Requirement 15: Directory Structure and Organization

**User Story:** As a developer, I want a clean separation between CrewAI and DSPy implementations, so that I can maintain both systems independently.

#### Acceptance Criteria

1. THE BookWriterDSPy System SHALL be located in cinema/agents/bookwriter_dspy directory
2. THE BookWriterDSPy System SHALL have a parallel structure to cinema/agents/bookwriter
3. THE BookWriterDSPy System SHALL include modules for detective, critique, screenplay, and storyboard
4. THE BookWriterDSPy System SHALL include a flow module for orchestration
5. THE BookWriterDSPy System SHALL share common models from cinema/agents/bookwriter/models.py where appropriate
