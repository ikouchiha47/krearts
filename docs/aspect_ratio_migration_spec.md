# Aspect Ratio Migration Spec

## Goal
Migrate from 9:16/16:9 aspect ratios to 4:5/5:4 for comic book generation, with support for 3:4/4:3 as alternatives.

## Status: In Progress

---

## Completed ✅

### 1. Transparent Templates
- [x] Created `cinema/templates/transparent_3_4.png` (768x1024)
- [x] Created `cinema/templates/transparent_4_3.png` (1024x768)
- [x] Created `cinema/templates/transparent_4_5.png` (819x1024) - **DEFAULT**
- [x] Created `cinema/templates/transparent_5_4.png` (1024x819)

### 2. Knowledge Base
- [x] Updated `knowledge/layouts/panel_arrangements.md`:
  - Horizontal layouts: 16:9 → 5:4
  - Vertical layouts: 9:16 → 4:5

---

## Remaining Tasks

### 3. Character Generation Prompts
**File:** `cinema/workflow/character_manager.py`

**Changes needed:**
- [ ] Update `_build_character_prompt()` to use 4:5 aspect ratio for all views
- [ ] Add aspect ratio specification to prompts
- [ ] Use transparent template as reference image

**Example:**
```python
def _build_character_prompt(self, character_description, view):
    # Add: "4:5 aspect ratio (portrait orientation)"
    # Or pass transparent_4_5.png as reference
```

### 4. Panel Generation in Storyboard
**File:** `cinema/agents/bookwriter/storyboard/` (crew/tasks)

**Changes needed:**
- [ ] Find where panel aspect_ratio is specified
- [ ] Update default from "16:9" to "5:4" (landscape) or "4:5" (portrait)
- [ ] Ensure orientation field matches aspect ratio

**Search for:**
- `aspect_ratio` field in panel/page schemas
- Default values in task prompts
- Panel description templates

### 5. Image Generation API Calls
**File:** `cinema/workflow/book_workflow.py` (generate_pages method)

**Changes needed:**
- [ ] Add aspect ratio config parameter
- [ ] Pass aspect ratio to Gemini API if supported
- [ ] Document that Gemini should auto-detect from reference image

**Current location:** Line ~667 in `generate_pages()`
```python
response = await asyncio.to_thread(
    client.models.generate_content,
    model="gemini-2.5-flash-image",
    contents=contents,
    config={"response_modalities": ["IMAGE"]},  # Add aspect_ratio here?
)
```

### 6. Config Files (if any)
**Search needed:**
- [ ] Check `examples/scifi_config.json` for aspect ratio settings
- [ ] Check any other config files in `examples/`
- [ ] Check if aspect ratio is in workflow state

---

## Testing Plan

### Test 1: Character Generation
```bash
python cinema/cmd/krearts.py characters 6021a791
```
**Expected:** 5 characters × 4 views = 20 images at 4:5 aspect ratio

### Test 2: Chapter Generation
```bash
python cinema/cmd/krearts.py book 6021a791 --chapters 1
```
**Expected:** Chapter JSON with panels specifying 4:5 or 5:4 aspect ratios

### Test 3: Image Generation
```bash
python cinema/cmd/krearts.py chapters 6021a791 --pages 1
```
**Expected:** Panel images at 4:5 or 5:4 aspect ratio (not 9:16/16:9)

---

## Notes

- **Default aspect ratio:** 4:5 (portrait) for character references
- **Panel aspect ratios:** 
  - Vertical layouts: 4:5 (portrait)
  - Horizontal layouts: 5:4 (landscape)
- **Gemini API:** Should auto-detect aspect ratio from reference images
- **Transparent templates:** Available in `cinema/templates/` for all ratios

---

## Future: Imagen Support

When migrating from `gemini-2.5-flash-image` to `imagen-3.0`:
- [ ] Add explicit aspect ratio parameter to API call
- [ ] Test with all 4 aspect ratios (3:4, 4:3, 4:5, 5:4)
- [ ] Update config to allow per-workflow aspect ratio selection
