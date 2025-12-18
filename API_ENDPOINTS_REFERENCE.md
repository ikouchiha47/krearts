# API Endpoints Reference - State Machine Implementation

## Current Endpoints (No Changes to Routes)

### Workflow Management
```
GET    /workflows                          - List all workflows
GET    /workflows/{workflow_id}            - Get workflow state ✨ ENHANCED
GET    /workflows/{workflow_id}/jobs       - List jobs for workflow
GET    /workflows/{workflow_id}/chapters   - List chapters
GET    /workflows/{workflow_id}/pages      - List pages
GET    /workflows/{workflow_id}/characters - List characters
```

### Workflow Operations
```
POST   /workflows/book/init                     - Create workflow & generate storyline
POST   /workflows/{workflow_id}/content         - Generate novel (prose)
POST   /workflows/{workflow_id}/cover           - Generate book cover
POST   /workflows/{workflow_id}/characters/generate - Generate character images
POST   /workflows/{workflow_id}/characters/retry    - Retry character generation
POST   /workflows/{workflow_id}/chapters        - Generate comic chapters
POST   /workflows/{workflow_id}/pages           - Generate page images
```

### Job Status
```
GET    /jobs/{job_id}/status               - Get job status
```

---

## Enhanced Endpoint Details

### ✨ `GET /workflows/{workflow_id}` - ENHANCED

**What's New:**
- Added `charactersGenerated` field
- Added `availableActions` array
- Added `blockedActions` array

**Before (Current):**
```json
{
  "id": "workflow_xyz",
  "title": "My Story",
  "currentStage": "CONTENT",
  "screenplay": "...",
  "storyline": "...",
  "totalChapters": 10,
  "totalPages": 0,
  "chaptersGenerated": [],
  "pagesGenerated": [],
  "coverGenerated": false
}
```

**After (Enhanced):**
```json
{
  "id": "workflow_xyz",
  "title": "My Story",
  "currentStage": "CONTENT",
  "screenplay": "...",
  "storyline": "...",
  "totalChapters": 10,
  "totalPages": 0,
  "chaptersGenerated": [],
  "pagesGenerated": [],
  "coverGenerated": false,
  "charactersGenerated": false,           // ✨ NEW
  "availableActions": [                   // ✨ NEW
    {
      "action": "generate_characters",
      "endpoint": "POST /workflows/{workflow_id}/characters/generate",
      "description": "Generate character reference images (required for chapters)"
    }
  ],
  "blockedActions": [                     // ✨ NEW
    "generate_chapters",
    "generate_pages"
  ]
}
```

---

## Validation Error Response Format

When validation fails (e.g., trying to generate chapters without characters):

**Status Code:** `400 Bad Request`

**Response Body:**
```json
{
  "error": "prerequisite_not_met",
  "operation": "generate_chapters",
  "current_state": {
    "stage": "CONTENT",
    "storyline_done": true,
    "content_done": true,
    "characters_generated": false,
    "chapters_generated": [],
    "pages_generated": []
  },
  "missing_prerequisites": ["characters_generated"],
  "message": "Generate characters first - needed for consistent character appearance in pages",
  "available_actions": [
    {
      "action": "generate_characters",
      "endpoint": "POST /workflows/{workflow_id}/characters/generate",
      "description": "Generate character reference images (required for chapters)"
    }
  ],
  "blocked_actions": [
    "generate_chapters",
    "generate_pages"
  ]
}
```

---

## UI Integration Guide

### Using `availableActions` to Enable Buttons

```typescript
// Fetch workflow state
const workflow = await fetch(`/workflows/${workflowId}`).then(r => r.json());

// Enable/disable buttons based on available actions
const canGenerateCharacters = workflow.availableActions.some(
  a => a.action === 'generate_characters'
);

const canGenerateChapters = workflow.availableActions.some(
  a => a.action === 'generate_chapters'
);

// In your UI
<Button 
  disabled={!canGenerateCharacters}
  onClick={() => generateCharacters()}
>
  Generate Characters
</Button>

<Button 
  disabled={!canGenerateChapters}
  onClick={() => generateChapters()}
  title={!canGenerateChapters ? "Generate characters first" : ""}
>
  Generate Chapters
</Button>
```

### Handling Validation Errors

```typescript
try {
  const response = await fetch(`/workflows/${workflowId}/chapters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chapters: 'all' })
  });
  
  if (response.status === 400) {
    const error = await response.json();
    
    // Show user-friendly message
    showError(error.message);
    
    // Show available actions
    if (error.available_actions?.length > 0) {
      showSuggestions(error.available_actions);
    }
  }
} catch (err) {
  console.error(err);
}
```

---

## State Machine Flow

```
┌─────────────────────────────────────────────────────────────┐
│ POST /workflows/book/init                                    │
│   → Creates workflow                                         │
│   → Generates storyline (plot outline)                       │
│   → State: INIT → CONTENT                                    │
│   → Available: [generate_content]                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ POST /workflows/{workflow_id}/content                        │
│   → Generates novel (prose chapters from storyline)          │
│   → State: CONTENT → CONTENT_READY                           │
│   → Available: [generate_cover, generate_characters]         │
└─────────────────────────────────────────────────────────────┘
                          ↓
         ┌────────────────┴────────────────┐
         ↓                                  ↓
┌──────────────────────┐      ┌──────────────────────────┐
│ POST /cover          │      │ POST /characters/generate│
│   → Book cover image │      │   → Character references │
│   → Optional         │      │   → REQUIRED for chapters│
│   → State: +cover    │      │   → State: +characters   │
└──────────────────────┘      └──────────────────────────┘
                                           ↓
                          ┌─────────────────────────────────────┐
                          │ POST /chapters                       │
                          │   → Comic chapters (visual format)   │
                          │   → Requires: characters_generated   │
                          │   → State: CHAPTERS                  │
                          │   → Available: [generate_pages]      │
                          └─────────────────────────────────────┘
                                           ↓
                          ┌─────────────────────────────────────┐
                          │ POST /pages                          │
                          │   → Actual comic page images         │
                          │   → Requires: chapters_generated     │
                          │   → State: PAGES → COMPLETE          │
                          └─────────────────────────────────────┘
```

---

## Prerequisites Matrix

| Operation              | Requires                          | Blocks If Missing                    |
|------------------------|-----------------------------------|--------------------------------------|
| `generate_content`     | `storyline_done`                  | "Complete storyline generation first"|
| `generate_cover`       | `content_done`                    | "Generate novel content first"       |
| `generate_characters`  | `content_done`                    | "Generate novel content first"       |
| `generate_chapters`    | `content_done` + `characters_generated` | "Generate characters first" |
| `generate_pages`       | `chapters_generated` + `characters_generated` | "Generate chapters first" |

---

## Testing Endpoints

### Check Workflow State
```bash
curl http://localhost:8000/workflows/{workflow_id}
```

### Try Invalid Operation (Should Return 400)
```bash
# Try to generate chapters without characters
curl -X POST http://localhost:8000/workflows/{workflow_id}/chapters \
  -H "Content-Type: application/json" \
  -d '{"chapters": "all"}'

# Expected: 400 error with available_actions
```

### Check Job Status
```bash
curl http://localhost:8000/jobs/{job_id}/status
```

---

## Summary

**Key Points:**
1. ✅ No new endpoints - only enhancing existing `GET /workflows/{workflow_id}`
2. ✅ Validation happens at endpoint level (fast fail)
3. ✅ Clear error messages with guidance
4. ✅ UI can use `availableActions` to enable/disable buttons
5. ✅ `blockedActions` shows what's not available yet

**Route:** `GET /workflows/{workflow_id}` (existing, enhanced)
**NOT:** `GET /workflows/{workflow_id}/status` (not creating this)
