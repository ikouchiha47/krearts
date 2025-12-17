# Requirements Document

## Introduction

This feature enables real-time updates of chapter and page data in the UI during long-running chapter generation jobs. Currently, users must manually refresh the page to see newly generated chapters and pages. By extending the existing polling infrastructure to also refresh data endpoints, the UI will automatically display new content as it becomes available, providing a responsive user experience during generation.

## Glossary

- **Polling Infrastructure**: The existing `RunningJobProgress` component that polls job status every 3 seconds
- **Data Endpoints**: The REST API endpoints `/workflows/{id}/chapters` and `/workflows/{id}/pages` that return generated content
- **Chapter Generation Job**: A background job of type `book_chapters` that generates multiple chapters (typically 3 at a time)
- **Job Metadata**: The `metadata` field in job responses that contains `chapters_generated` array tracking which chapters have been completed
- **WorkflowPage**: The main UI component that displays workflow state, chapters, pages, and characters
- **Sidebar**: The left panel showing chapter thumbnails and the right panel showing character cards
- **Timeline View**: The GitHub-style activity grid showing chapter and page generation progress
- **Job Status Endpoint**: The `/workflows/{id}/jobs` endpoint that returns job status and metadata including progress information

## Requirements

### Requirement 1

**User Story:** As a user generating chapters, I want to see new chapters appear in the sidebar automatically, so that I can monitor progress without manual refreshing.

#### Acceptance Criteria

1. WHEN a chapter generation job is running THEN the system SHALL poll the job status endpoint every 3 seconds
2. WHEN the job metadata contains new chapter numbers in chapters_generated array THEN the system SHALL poll the chapters data endpoint
3. WHEN new chapter data is returned from the API THEN the system SHALL update the sidebar chapter list immediately
4. WHEN the sidebar updates THEN the system SHALL preserve the user's current chapter selection if any
5. WHEN the chapter generation job completes THEN the system SHALL perform one final data refresh

### Requirement 2

**User Story:** As a user generating chapters, I want to see page generation progress within chapters in real-time, so that I understand how far along each chapter is.

#### Acceptance Criteria

1. WHEN the job metadata indicates new chapters have been generated THEN the system SHALL poll the pages endpoint
2. WHEN new page data is returned from the API THEN the system SHALL update the pages view immediately
3. WHEN the timeline view is active THEN the system SHALL update the page completion boxes in real-time
4. WHEN a chapter's page count increases THEN the system SHALL reflect this in the chapter card metadata
5. WHEN all pages for a chapter complete THEN the system SHALL visually indicate chapter completion

### Requirement 3

**User Story:** As a user, I want the polling to be efficient and not cause performance issues, so that the UI remains responsive during generation.

#### Acceptance Criteria

1. WHEN polling is active THEN the system SHALL reuse the existing 3-second polling interval
2. WHEN the job metadata indicates changes THEN the system SHALL poll data endpoints only when necessary
3. WHEN a polling request fails THEN the system SHALL log the error and continue polling
4. WHEN the job completes or fails THEN the system SHALL stop polling data endpoints
5. WHEN the user navigates away from the workflow page THEN the system SHALL clean up polling intervals

### Requirement 4

**User Story:** As a user, I want the UI to feel real-time without requiring WebSocket infrastructure, so that the system remains simple and maintainable.

#### Acceptance Criteria

1. WHEN implementing real-time updates THEN the system SHALL use HTTP polling exclusively
2. WHEN the polling interval is 3 seconds THEN the system SHALL provide a sufficiently real-time experience
3. WHEN chapters complete THEN the system SHALL display them within 3 seconds of database persistence
4. WHEN the backend persists data THEN the system SHALL ensure it is immediately queryable via REST endpoints
5. WHEN the UI polls during generation THEN the system SHALL not introduce new backend infrastructure

### Requirement 5

**User Story:** As a developer, I want the polling mechanism to be reusable and well-structured, so that similar features can leverage the same pattern.

#### Acceptance Criteria

1. WHEN extending the polling hook THEN the system SHALL accept an optional data refresh callback
2. WHEN the data refresh callback is provided THEN the system SHALL invoke it on each polling cycle
3. WHEN the job completes THEN the system SHALL invoke both the completion callback and data refresh callback
4. WHEN the polling hook is reused THEN the system SHALL maintain backward compatibility with existing usage
5. WHEN implementing the callback THEN the system SHALL handle async operations correctly


### Requirement 6

**User Story:** As a user, I want to know which chapters are currently being generated, so that I can understand what the system is working on.

#### Acceptance Criteria

1. WHEN the job metadata contains chapters_generated array THEN the system SHALL compare it with the previous state
2. WHEN new chapter numbers appear in the array THEN the system SHALL identify them as newly completed
3. WHEN chapters are newly completed THEN the system SHALL trigger a data refresh for those specific chapters
4. WHEN the data refresh completes THEN the system SHALL update the UI to show the new chapters
5. WHEN no new chapters are detected THEN the system SHALL skip unnecessary data endpoint calls
