# Image Quality Options

## Current Setup

**Model**: `gemini-2.5-flash-image`
- Fast generation
- Good quality
- 500 RPM rate limit

## Gemini Image Generation Models

### Available Models (as of Nov 2024):
1. **gemini-2.5-flash-image** (current)
   - Fast, good quality
   - Best for rapid iteration
   - Lower cost

2. **gemini-2.0-flash-exp** 
   - Experimental, may have better quality
   - Slower generation
   - Higher cost

### Quality Control Options

#### 1. Aspect Ratio
- Currently: `4:5` (portrait) or `5:4` (landscape)
- Configurable in `examples/scifi_config.json`

#### 2. Prompt Engineering
- **Art style**: Defined in novel.md metadata
  - Example: "Rain-drenched neon noir, high-contrast shadows, holographic data overlays"
- **Shot types**: close-up, medium, wide, establishing
- **Camera angles**: eye-level, high-angle, low-angle, dutch-angle
- **Rendering style**: stylized-volumetric, realistic, painterly

#### 3. Character References
- Uses seeded generation (front view → other views)
- Maintains consistency across panels
- 4:5 aspect ratio for character sheets

#### 4. Panel Composition
- Layout: vertical-2-panel, vertical-3-panel, etc.
- Gutter spacing: 20px
- Page size: 1024x1280 (4:5)

## Image Quality Checklist

When reviewing generated images, check:

1. **Aspect Ratio**: Should be 4:5 (0.800 ratio)
2. **Art Style Consistency**: Matches the defined style
3. **Character Consistency**: Characters look the same across panels
4. **Composition**: Panels are well-arranged
5. **Visual Clarity**: Details are visible and clear
6. **Color Palette**: Matches the scene description
7. **Lighting**: Appropriate for the mood/setting

## Improving Quality

### Option 1: Better Prompts
- Add more specific visual details
- Include lighting descriptions
- Specify color palettes
- Reference specific art styles

### Option 2: Model Selection
- Try different Gemini models (if available)
- Adjust generation parameters

### Option 3: Post-Processing
- Add text overlays for dialogue
- Adjust colors/contrast
- Composite panels with better spacing

### Option 4: Regeneration
- Delete specific pages and regenerate
- Adjust prompts in chapter JSON
- Use different character references

## Commands

```bash
# Review pages
python cinema/cmd/examples/review_pages.py <workflow_id>

# Regenerate specific pages
python cinema/cmd/krearts.py chapters <workflow_id> --pages 1,2,3

# Regenerate all pages
python cinema/cmd/krearts.py chapters <workflow_id> --pages all

# Regenerate characters
python cinema/cmd/krearts.py characters <workflow_id>

# Regenerate chapter (with new prompts)
python cinema/cmd/krearts.py book <workflow_id> --chapters 1
```

## Notes

- Gemini doesn't have explicit "quality" or "resolution" parameters
- Quality is primarily controlled through prompt engineering
- Character references help maintain consistency
- Art style from novel.md is automatically applied
