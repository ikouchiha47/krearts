# Lighting Styles and Techniques

## Overview

Lighting is one of the most powerful tools in cinematography, shaping mood, directing attention, and creating visual hierarchy. This guide covers essential lighting styles for video generation.

---

## 1. Three-Point Lighting (Classic)

### Definition
Standard lighting setup using key light, fill light, and back light.

### Purpose
- Create dimensional, professional look
- Control shadows and highlights
- Establish subject clearly
- Industry standard for interviews/products

### Setup
```yaml
key_light:
  position: 45° from camera, slightly above subject
  intensity: brightest light (100%)
  purpose: main illumination

fill_light:
  position: opposite key light, near camera
  intensity: 30-50% of key light
  purpose: soften shadows

back_light:
  position: behind subject, above
  intensity: 75-100% of key light
  purpose: separate subject from background
```

### Veo Prompt Template
```
Three-point lighting setup. [Subject] illuminated by key light from 
[direction], soft fill light reducing shadows, back light creating 
separation from background. Professional, dimensional lighting. 
Balanced, clean aesthetic.
```

### Examples
```
Corporate Interview:
"Three-point lighting. Business professional in modern office. 
Key light from front-left at 45°, soft fill from right reducing shadows, 
back light creating hair light and separation. Professional, clean lighting. 
Balanced exposure, dimensional."

Product Photography:
"Three-point lighting setup. Premium watch on display. Key light from 
upper left highlighting face, fill light softening shadows on band, 
back light creating rim light on edges. Professional product lighting."
```

---

## 2. High-Key Lighting

### Definition
Bright, even lighting with minimal shadows and high overall exposure.

### Purpose
- Create cheerful, optimistic mood
- Suggest cleanliness and simplicity
- Commercial and beauty aesthetic
- Reduce drama, increase accessibility

### Characteristics
```yaml
exposure: bright, overexposed feel
shadows: minimal, soft
contrast: low
mood: happy, light, optimistic
```

### Veo Prompt Template
```
High-key lighting. Bright, even illumination with minimal shadows. 
[Scene description]. Cheerful, optimistic mood. Clean, commercial aesthetic.
Soft, diffused light. Low contrast.
```

### Examples
```
Beauty Commercial:
"High-key lighting. Model with glowing skin in white studio. 
Bright, even illumination from all sides, minimal shadows. 
Cheerful, optimistic mood. Clean beauty aesthetic. Soft, flattering light."

Tech Product:
"High-key lighting. Smartphone on white background. Bright, even 
illumination eliminating shadows. Clean, modern aesthetic. 
Commercial product photography. Crisp, minimal."
```

---

## 3. Low-Key Lighting

### Definition
Dark, dramatic lighting with strong shadows and low overall exposure.

### Purpose
- Create mystery and drama
- Suggest danger or sophistication
- Film noir aesthetic
- Emphasize contrast and mood

### Characteristics
```yaml
exposure: dark, underexposed feel
shadows: deep, hard
contrast: high
mood: dramatic, mysterious, tense
```

### Veo Prompt Template
```
Low-key lighting. Dark, dramatic illumination with deep shadows. 
[Scene description]. Mysterious, tense mood. Film noir aesthetic.
Hard, directional light. High contrast.
```

### Examples
```
Noir Portrait:
"Low-key lighting. Detective in dark office, single hard light from 
window creating dramatic shadows across face. Deep blacks, high contrast. 
Film noir aesthetic. Mysterious, tense mood."

Luxury Product:
"Low-key lighting. Luxury watch emerging from darkness. Single spotlight 
creating dramatic highlights, deep shadows. Sophisticated, premium aesthetic. 
High contrast, moody."
```

---

## 4. Natural/Available Light

### Definition
Using existing light sources without artificial lighting.

### Purpose
- Create authentic, realistic look
- Suggest documentary style
- Reduce production complexity
- Organic, unmanipulated aesthetic

### Types
- **Window Light**: Soft, directional
- **Golden Hour**: Warm, flattering
- **Overcast**: Even, diffused
- **Indoor Ambient**: Mixed sources

### Veo Prompt Template
```
Natural lighting. [Scene description] lit by [natural source]. 
Authentic, realistic illumination. [Soft/hard] natural light. 
Documentary aesthetic. Organic, unmanipulated.
```

### Examples
```
Window Light Portrait:
"Natural window lighting. Subject near large window, soft daylight 
illuminating face from side. Authentic, realistic look. Gentle shadows. 
Documentary aesthetic. Organic, beautiful."

Golden Hour Exterior:
"Natural golden hour lighting. Subject outdoors during sunset, warm 
sunlight from low angle. Glowing, flattering illumination. Soft shadows. 
Cinematic, beautiful natural light."
```

---

## 5. Rembrandt Lighting

### Definition
Lighting creating triangle of light on shadowed cheek, named after painter Rembrandt.

### Purpose
- Create dramatic, artistic portraits
- Add depth and dimension
- Classical, timeless aesthetic
- Sophisticated, painterly look

### Setup
```yaml
key_light:
  position: 45° from subject, 45° above
  creates: triangle of light on cheek
  shadow: nose shadow connects to cheek shadow
```

### Veo Prompt Template
```
Rembrandt lighting. [Subject] with key light at 45° creating signature 
triangle of light on shadowed cheek. Dramatic, painterly aesthetic. 
Classical portrait lighting. Sophisticated, dimensional.
```

### Examples
```
Portrait:
"Rembrandt lighting. Artist in studio, key light from upper left creating 
triangle of light on right cheek. Dramatic, painterly aesthetic. 
Deep shadows, classical portrait. Sophisticated, timeless."
```

---

## 6. Butterfly/Paramount Lighting

### Definition
Light directly in front and above subject, creating butterfly-shaped shadow under nose.

### Purpose
- Glamorous, beauty aesthetic
- Emphasize cheekbones
- Classic Hollywood style
- Flattering for most faces

### Setup
```yaml
key_light:
  position: directly in front, above subject
  creates: butterfly shadow under nose
  emphasizes: cheekbones, eyes
```

### Veo Prompt Template
```
Butterfly lighting. [Subject] with key light directly above creating 
butterfly shadow under nose. Glamorous, Hollywood aesthetic. 
Emphasizes cheekbones. Classic beauty lighting.
```

### Examples
```
Beauty Shot:
"Butterfly lighting. Model facing camera, light directly above creating 
butterfly shadow under nose. Glamorous, Hollywood aesthetic. 
Emphasizes cheekbones and eyes. Classic beauty lighting. Flattering, elegant."
```

---

## 7. Backlighting/Silhouette

### Definition
Light source behind subject, creating rim light or complete silhouette.

### Purpose
- Create dramatic silhouettes
- Add mystery and intrigue
- Separate subject from background
- Artistic, stylized look

### Types
- **Full Silhouette**: Subject completely dark
- **Rim Light**: Edge lighting with some detail
- **Halo Effect**: Glowing outline

### Veo Prompt Template
```
Backlighting. [Subject] with strong light from behind creating 
[silhouette/rim light]. [Dramatic/mysterious] aesthetic. 
Subject [separated/outlined] by backlight. Artistic, stylized.
```

### Examples
```
Dramatic Silhouette:
"Backlighting. Figure standing in doorway, bright light from behind 
creating complete silhouette. Dramatic, mysterious aesthetic. 
No front detail, pure shape. Film noir style."

Rim Light Portrait:
"Backlighting with rim light. Subject with strong light from behind 
creating glowing outline, subtle front fill maintaining detail. 
Dramatic separation from background. Cinematic, dimensional."
```

---

## 8. Side Lighting/Split Lighting

### Definition
Light from 90° to subject, illuminating one side while leaving other in shadow.

### Purpose
- Create drama and contrast
- Show texture and dimension
- Suggest duality or conflict
- Masculine, powerful aesthetic

### Veo Prompt Template
```
Side lighting. [Subject] illuminated from 90° angle, one side bright 
while other in shadow. Dramatic, high contrast. Split lighting creating 
duality. Powerful, masculine aesthetic.
```

### Examples
```
Dramatic Portrait:
"Side lighting. Character's face split by light from 90° angle, 
half illuminated half in shadow. Dramatic, high contrast. 
Suggests internal conflict. Powerful, intense aesthetic."

Product Texture:
"Side lighting. Leather product illuminated from side, emphasizing 
texture and craftsmanship. Hard light creating deep shadows. 
Dramatic, dimensional. Premium aesthetic."
```

---

## 9. Motivated Lighting

### Definition
Lighting that appears to come from visible or logical sources within scene.

### Purpose
- Create realistic, believable scenes
- Maintain immersion
- Suggest specific time/place
- Natural, unmanipulated feel

### Sources
- **Practical Lights**: Lamps, candles, screens
- **Windows**: Daylight sources
- **Fire**: Warm, flickering
- **Neon**: Colored, urban

### Veo Prompt Template
```
Motivated lighting from [source]. [Scene description] illuminated by 
visible [light source]. Realistic, believable lighting. Natural, 
diegetic light sources. Immersive, authentic.
```

### Examples
```
Desk Lamp Scene:
"Motivated lighting from desk lamp. Writer at night, warm light from 
visible desk lamp illuminating workspace. Realistic, intimate atmosphere. 
Natural light source. Cozy, authentic."

Window Light:
"Motivated lighting from large window. Office scene with natural daylight 
streaming through visible windows. Realistic, believable illumination. 
Soft, directional window light. Professional, natural."

Neon Urban:
"Motivated lighting from neon signs. Urban night scene, character 
illuminated by colored neon from visible storefronts. Realistic, 
atmospheric. Cyberpunk aesthetic. Colorful, moody."
```

---

## 10. Colored/Gel Lighting

### Definition
Using colored lights or gels to create specific moods or stylistic effects.

### Purpose
- Create emotional atmosphere
- Suggest genre or style
- Add visual interest
- Symbolic color meaning

### Color Psychology
```yaml
blue:
  mood: cold, technological, sad, calm
  use: sci-fi, corporate, night scenes

red:
  mood: danger, passion, anger, heat
  use: action, horror, romantic

green:
  mood: sickness, envy, nature, matrix
  use: sci-fi, horror, tech

orange/amber:
  mood: warm, nostalgic, sunset, cozy
  use: memories, comfort, golden hour

purple/magenta:
  mood: luxury, mystery, creative, neon
  use: nightlife, premium, artistic

cyan:
  mood: futuristic, clean, digital
  use: tech, sci-fi, modern
```

### Veo Prompt Template
```
Colored lighting, [color] tones. [Scene description] illuminated by 
[color] light creating [mood]. [Emotional/stylistic] atmosphere. 
[Genre] aesthetic.
```

### Examples
```
Cyberpunk Scene:
"Colored lighting, cyan and magenta tones. Urban alley illuminated by 
neon lights, cyan from left and magenta from right. Futuristic, 
atmospheric. Cyberpunk aesthetic. Moody, stylized."

Tech Product:
"Colored lighting, cool blue tones. Smartphone on display illuminated 
by blue light suggesting technology and innovation. Modern, clean aesthetic. 
Futuristic, premium."

Warm Memory:
"Colored lighting, warm amber tones. Flashback scene with golden-orange 
light creating nostalgic atmosphere. Warm, comforting mood. 
Memory aesthetic. Soft, dreamy."
```

---

## 11. Practical Lighting

### Definition
Using actual light sources visible in frame (lamps, candles, screens, etc.).

### Purpose
- Create realistic environments
- Add production value
- Motivate lighting naturally
- Enhance atmosphere

### Types
- **Lamps**: Warm, domestic
- **Candles**: Romantic, intimate
- **Screens**: Cool, modern
- **String Lights**: Festive, cozy
- **Neon**: Urban, stylized

### Veo Prompt Template
```
Practical lighting from [source]. [Scene description] with visible 
[light source] providing illumination. Realistic, atmospheric. 
Natural light sources in frame. [Mood] aesthetic.
```

### Examples
```
Cozy Interior:
"Practical lighting from table lamps and string lights. Living room 
scene with visible warm lamps and fairy lights creating cozy atmosphere. 
Realistic, inviting. Domestic, comfortable aesthetic."

Tech Workspace:
"Practical lighting from multiple monitors. Programmer at night, 
face illuminated by cool screen glow from visible displays. 
Realistic, modern. Tech aesthetic. Atmospheric, focused."
```

---

## 12. Hard vs Soft Light

### Hard Light

**Characteristics**:
- Sharp, defined shadows
- High contrast
- Dramatic, intense
- Small light source or direct sun

**Use Cases**:
- Drama and tension
- Film noir
- Masculine portraits
- Emphasize texture

**Prompt Template**:
```
Hard lighting. [Scene] with sharp, defined shadows. High contrast, 
dramatic illumination. Direct, undiffused light source. 
Intense, powerful aesthetic.
```

### Soft Light

**Characteristics**:
- Gradual, soft shadows
- Low contrast
- Flattering, gentle
- Large diffused source or overcast

**Use Cases**:
- Beauty and fashion
- Flattering portraits
- Commercial work
- Reduce drama

**Prompt Template**:
```
Soft lighting. [Scene] with gentle, gradual shadows. Low contrast, 
flattering illumination. Diffused, large light source. 
Gentle, beautiful aesthetic.
```

---

## Lighting for Different Scenarios

### Corporate/Professional
```
Three-point lighting, balanced and clean. Professional setting with 
even illumination, minimal shadows. Trustworthy, competent aesthetic.
```

### Beauty/Fashion
```
High-key or butterfly lighting. Bright, flattering illumination 
emphasizing features. Soft, diffused light. Glamorous, beautiful aesthetic.
```

### Drama/Film
```
Low-key or Rembrandt lighting. Dramatic shadows and contrast. 
Moody, cinematic illumination. Artistic, sophisticated aesthetic.
```

### Product Commercial
```
High-key three-point lighting. Clean, even illumination showcasing 
product details. Professional, commercial aesthetic. Minimal shadows.
```

### Tech/Innovation
```
Colored lighting with blue/cyan tones. Modern, futuristic illumination. 
Clean, technological aesthetic. Cool, innovative mood.
```

### Luxury/Premium
```
Low-key dramatic lighting. Sophisticated illumination with controlled 
shadows. Premium, exclusive aesthetic. Moody, elegant.
```

---

## Time of Day Lighting

### Golden Hour (Sunrise/Sunset)
```yaml
characteristics:
  - Warm, golden tones
  - Soft, directional light
  - Long shadows
  - Flattering, beautiful

prompt: "Golden hour lighting. Warm, golden sunlight from low angle. 
Soft, flattering illumination. Long shadows. Beautiful, cinematic."
```

### Blue Hour (Twilight)
```yaml
characteristics:
  - Cool blue tones
  - Soft, even light
  - Mysterious, calm
  - Transitional mood

prompt: "Blue hour lighting. Cool, blue twilight illumination. 
Soft, even light. Mysterious, calm atmosphere. Transitional, ethereal."
```

### Midday (Harsh Sun)
```yaml
characteristics:
  - Bright, intense
  - Hard shadows
  - High contrast
  - Challenging but dramatic

prompt: "Midday sun lighting. Bright, intense sunlight from above. 
Hard shadows, high contrast. Dramatic, powerful illumination."
```

### Overcast
```yaml
characteristics:
  - Soft, even light
  - Minimal shadows
  - Neutral tones
  - Flattering, easy

prompt: "Overcast lighting. Soft, even illumination from cloudy sky. 
Minimal shadows, gentle light. Flattering, natural aesthetic."
```

---

## Integration with Veo Generation

### Lighting in Prompts

**Be Specific**:
```
✅ "Three-point lighting with key from left, soft fill, rim backlight"
❌ "Good lighting"
```

**Describe Quality**:
```
✅ "Soft, diffused window light creating gentle shadows"
❌ "Window light"
```

**Include Mood**:
```
✅ "Dramatic low-key lighting creating mystery and tension"
❌ "Dark lighting"
```

**Mention Direction**:
```
✅ "Side lighting from 90° creating split face effect"
❌ "Side lighting"
```

---

## Best Practices

### 1. Match Lighting to Mood
- Bright = happy, optimistic, clean
- Dark = dramatic, mysterious, tense
- Warm = cozy, nostalgic, comfortable
- Cool = technological, modern, calm

### 2. Consider Subject
- Beauty: soft, flattering
- Drama: hard, contrasty
- Product: clean, even
- Documentary: natural, realistic

### 3. Use Color Purposefully
- Blue = tech, cold, night
- Orange = warm, sunset, cozy
- Red = danger, passion
- Green = nature, sickness, matrix

### 4. Motivate Your Lighting
- Make it believable
- Use visible sources when possible
- Match time of day
- Consider environment

### 5. Control Contrast
- High contrast = drama
- Low contrast = commercial
- Match to genre and mood

---

## Common Mistakes

### ❌ Wrong: Flat, Unmotivated Lighting
```
"Evenly lit scene with no direction or source"
```

### ✅ Right: Directional, Motivated Lighting
```
"Window light from left creating soft directional illumination"
```

### ❌ Wrong: Mismatched Mood
```
"Tense thriller scene with bright, cheerful high-key lighting"
```

### ✅ Right: Matched Mood
```
"Tense thriller scene with dramatic low-key lighting and deep shadows"
```

---

## Summary

Lighting creates mood and directs attention:

1. **Three-Point**: Professional standard
2. **High-Key**: Bright and cheerful
3. **Low-Key**: Dark and dramatic
4. **Natural**: Authentic and realistic
5. **Rembrandt**: Artistic and classical
6. **Butterfly**: Glamorous and flattering
7. **Backlighting**: Dramatic and mysterious
8. **Side Lighting**: Powerful and contrasty
9. **Motivated**: Realistic and immersive
10. **Colored**: Stylized and emotional
11. **Practical**: Atmospheric and real
12. **Hard/Soft**: Dramatic vs flattering

Choose lighting that serves your story and creates the right emotional impact.
