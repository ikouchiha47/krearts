# Art Style Reference Index

Quick reference for all available art styles, their key characteristics, and typical panel density.

## Style Comparison Chart

| Style | Panel Density | Key Visual Feature | Sound Effects Style |
|-------|--------------|-------------------|-------------------|
| **Blueberry** | 8-9 panels | Ligne claire, Western detail | Minimal, integrated |
| **Akira** | 6-8 panels | Motion lines, mechanical detail | Large, dramatic Japanese |
| **Spider-Verse** | 3-5 panels | Halftone dots, chromatic aberration | 3D integrated text |
| **Anime-Manga** | 4-6 panels | Expressive eyes, speed lines | Emotional onomatopoeia |
| **Cyberpunk** | 4-6 panels | Neon lighting, rain | Tech-styled fonts |
| **Noir** | 5-7 panels | High contrast B&W, shadows | Stark, minimal |
| **Arcane** | 3-5 panels | Painterly brushwork | Minimal, visual focus |
| **Watchmen** | 9 panels (strict) | 3x3 grid, symmetry | Restrained, symbolic |
| **American Comic** | 5-7 panels | Bold lines, heroic poses | Classic POW/BAM |
| **Print Comic** | 6-9 panels | Ben-Day dots, flat colors | Bold with exclamation |
| **Pop Art** | 1-4 panels | Large dots, primary colors | HUGE, art element |
| **Sci-Fi** | 5-6 panels | Clean tech, bright | Technical fonts |
| **Fantasy RPG** | 4-6 panels | Magic effects, detail | Medieval style |
| **Pixel Art** | 4-6 panels | Visible pixels, limited colors | 8-bit game fonts |

## Sound Effects Quick Reference

### Universal Impact Sounds
- Light hit: `POW` `BOP` `THWACK`
- Heavy hit: `WHAM` `BAM` `CRASH`
- Explosion: `BOOM` `KA-BOOM` `BRAKKA-DOOM`

### Style-Specific Sounds

**Japanese (Akira/Manga)**
- `ドン` (DON) - Impact
- `ゴゴゴ` (GOGOGO) - Menacing aura
- `ドキドキ` (DOKIDOKI) - Heartbeat

**Spider-Verse**
- `THWIP` - Web shooting
- `GLITCH` - Dimension effects

**Western/Noir**
- `BLAM` - Gunshot
- `CRACK` - Breaking

## Directory Structure

```
references/
├── INDEX.md (this file)
├── reference_manifest.yaml
├── blueberry/
│   ├── README.md
│   └── images/
├── akira/
│   ├── README.md
│   └── images/
├── spiderverse/
│   ├── README.md
│   └── images/
├── anime-manga/
│   ├── README.md
│   └── images/
├── cyberpunk/
│   ├── README.md
│   └── images/
├── noir/
│   ├── README.md
│   └── images/
├── arcane/
│   ├── README.md
│   └── images/
├── watchmen/
│   ├── README.md
│   └── images/
├── american-comic/
│   ├── README.md
│   └── images/
├── print_comic/
│   ├── README.md
│   └── images/
├── pop-art/
│   ├── README.md
│   └── images/
├── sci-fi/
│   ├── README.md
│   └── images/
├── fantasy-rpg/
│   ├── README.md
│   └── images/
└── pixel-art/
    ├── README.md
    └── images/
```

## Adding Reference Images

1. Navigate to the style's `images/` subdirectory
2. Add JPG, PNG, or WebP images
3. Update the style's README.md with reverse prompt analysis
4. Update `reference_manifest.yaml` with new reference entries

## Reverse Prompt Workflow

When analyzing a reference image:

1. **Identify Key Elements**
   - Art style markers (line weight, coloring technique)
   - Composition elements (angle, framing)
   - Technical details (halftones, gradients, textures)

2. **Document in README**
   ```markdown
   ### Image: example.jpg
   **Source**: [where you found it]
   **Key Elements**: [what makes it this style]
   **Analyzed Prompt**:
   ```
   [your reverse-engineered prompt]
   ```
   ```

3. **Test and Refine**
   - Generate images using the prompt
   - Compare to reference
   - Iterate on prompt language
