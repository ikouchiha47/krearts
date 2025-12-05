# Aspect Ratio Issues and Fixes

## Common Problems

### 1. **Squashed/Compressed Images**
**Problem**: Images appear vertically compressed or "squashed"
**Cause**: Panels generated at one aspect ratio, then resized to fit layout
**Terms**: 
- Aspect ratio distortion
- Vertical compression
- Squashing

**Fixes**:
- ✅ Generate panels at target size from the start
- ✅ Add framing instructions to prompts
- ✅ Use "fill frame" language in prompts
- ❌ Avoid: "letterboxing", "pillarboxing", "empty space"

### 2. **Letterboxing**
**Problem**: Black bars at top/bottom of image
**Cause**: Content doesn't fill vertical space
**Fix**: Prompt with "use full height", "no empty space at top/bottom"

### 3. **Pillarboxing**
**Problem**: Black bars on left/right sides
**Cause**: Content doesn't fill horizontal space
**Fix**: Prompt with "use full width", "no empty space on sides"

### 4. **Stretched Images**
**Problem**: Images appear vertically stretched or "tall"
**Cause**: Wrong aspect ratio applied during generation
**Fix**: Explicitly specify aspect ratio in config

## Prompting Techniques

### Positive Prompts (Use These):
```
- "Fill the entire frame naturally"
- "Use full vertical space"
- "Proper {aspect_ratio} composition"
- "Natural framing without compression"
- "Subjects should appear at correct proportions"
- "Frame composition to fill ENTIRE vertical space"
```

### Negative Prompts (Avoid These):
```
- "No letterboxing"
- "No pillarboxing"
- "No empty space at top/bottom"
- "No wasted vertical space"
- "Avoid compressed or squashed appearance"
```

## Technical Solutions

### 1. Panel Generation
```python
# Generate panels at exact target size
panel_width = (page_width - gutters) // cols
panel_height = (page_height - gutters) // rows

# Pass to Gemini with aspect ratio config
config = types.ImageConfig(aspect_ratio="4:5")
```

### 2. Composite Without Resize
```python
# Don't resize panels - generate at target size
# OR maintain aspect ratio during resize
panel.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
```

### 3. Prompt Engineering
```python
prompt = f"""
{visual_description}

FRAMING: {aspect_ratio} ({orientation})
- Fill entire frame naturally
- Use full vertical space
- No letterboxing or empty space
"""
```

## Current Implementation

**File**: `cinema/workflow/book_workflow.py`

**Approach**: Prompt-based aspect ratio enforcement
- Explicitly states aspect ratio and orientation
- Instructs to "fill ENTIRE vertical space naturally"
- Warns against letterboxing, compression, squashing
- Emphasizes natural, uncompressed composition

**Config**: `cinema/providers/gemini.py`
- Uses `ImageConfig(aspect_ratio="4:5")` for all generations
- Ensures Gemini respects the target aspect ratio

## Testing

```bash
# Regenerate pages with new prompts
python cinema/cmd/krearts.py chapters <workflow_id> --pages all

# Analyze aspect ratios
python cinema/cmd/examples/analyze_images.py <workflow_id>

# Check for compression
# Look for: subjects appearing squashed, empty space, letterboxing
```

## Best Practices

1. **Always specify aspect ratio** in both config and prompt
2. **Use positive framing language** ("fill frame") over negative ("no letterboxing")
3. **Generate at target size** when possible
4. **Test with moondream** to verify composition quality
5. **Iterate on prompts** if compression persists
