# Cinematic Transitions and Techniques Vocabulary

## Quick Reference: When to Use Each Transition

| Transition Type | Duration | Motion Level | Use Case | Generation Method |
|----------------|----------|--------------|----------|-------------------|
| **match_cut_graphic** | Any | Any | Visual element alignment | Separate videos, precise composition |
| **match_cut_action** | Any | High | Continuous action | Separate videos, action timing |
| **jump_cut** | < 2s | Low-Medium | Time passage, energy | Image stitch or trimmed video |
| **flow_cut** | Any | Medium | Smooth continuity | Separate videos, natural flow |
| **smash_cut** | Any | Any | Dramatic contrast | Separate videos, hard cut |
| **action_cut** | Any | High | Same action, different angle | Separate videos, action sync |
| **montage_cut** | < 2s each | Varies | Rapid sequence | Multiple generations, edit together |

---

## Detailed Transition Definitions

### 1. Match Cut - Graphic

**What it is**: Visual elements stay in the same screen position across the cut

**Creative Purpose**: Create visual continuity, show transformation, connect disparate scenes

**Generation Method**:
```yaml
method: separate_videos_with_composition_control
steps:
  - Generate Scene A with element in specific position (document exact coordinates)
  - Generate Scene B with same element in EXACT same position
  - Hard cut in post-production at matching frame
veo_features:
  - first_last_frame (for precise composition)
  - reference_images (for character/object consistency)
post_production: Hard cut, no transition effect
```

**Prompt Requirements**:
- First scene last frame: "The [element] is positioned in the [exact position, e.g., bottom-right quadrant]"
- Second scene first frame: "The [element] is positioned in the EXACT same [position] as previous scene (CRITICAL for match cut)"

**Example**:
```
Scene 1: Office - Headphone earcup in bottom-right quadrant
Scene 2: Gym - Headphone earcup in bottom-right quadrant (same position)
Technique: Graphical match cut on headphone position
```

**When to Use**:
- Showing product in different contexts
- Connecting thematically related scenes
- Creating visual rhythm
- Demonstrating versatility

---

### 2. Match Cut - Action

**What it is**: Cut during continuous movement/action

**Creative Purpose**: Maintain momentum, show progression, create seamless flow

**Generation Method**:
```yaml
method: separate_videos_with_action_timing
steps:
  - Generate Scene A ending with specific action (e.g., hand reaching)
  - Generate Scene B starting with continuation of action (e.g., hand grabbing)
  - Cut at peak of action in post
veo_features:
  - timestamp_prompting (for precise action timing)
  - reference_images (for character consistency)
post_production: Cut on action beat
```

**Prompt Requirements**:
- First scene: "Character [action] reaching its peak at end of clip"
- Second scene: "Character continues [action] from the exact moment, seamlessly"

**Example**:
```
Scene 1: Hand reaching for door handle
Scene 2: Hand opening door (different location)
Technique: Match on action - hand movement continues
```

**When to Use**:
- Transitioning between locations during same action
- Showing cause and effect
- Maintaining energy and pace

---

### 3. Jump Cut

**What it is**: Abrupt cut showing same subject at different moment, OR rapid context changes with constant subject, OR same action/position with different subjects

**Creative Purpose**: Show time passage, create energy, demonstrate versatility, show legacy/tradition through repetition

**Generation Method**:
```yaml
method: depends_on_duration_and_motion
decision_tree:
  - if duration < 2s AND motion minimal:
      method: image_stitch_ffmpeg
      reason: "Quick cut, static subject"
  - if duration < 2s AND motion significant:
      method: video_trim
      reason: "Quick cut but needs motion"
  - if duration >= 2s AND action_sequence:
      method: text_to_video_per_cut
      reason: "Each subject needs full action (stance → execution)"
  - if duration >= 4s:
      method: text_to_video
post_production: Hard cuts, no transition
```

**Prompt Requirements**:
- Maintain subject framing and position
- Change background/context/time OR change subject
- Keep subject appearance consistent (use reference images)
- For action sequences: maintain identical camera position and framing

**Example - Product Versatility**:
```
Scene: Product showcase
- Cut 1: Watch on office desk (1.2s)
- Cut 2: Watch on gym locker (1.2s)  
- Cut 3: Watch on dinner table (1.2s)
Technique: Jump cuts showing versatility
Method: 3 separate image generations, ffmpeg stitch
```

**Example - Action Sequence (Same Action, Different Subjects)**:
```
Scene: Cricket batting montage
- Cut 1: Steve Smith batting stance → cover drive (2.0s)
- Cut 2: Joe Root batting stance → straight drive (2.5s)
- Cut 3: Pat Cummins batting stance → pull shot (2.0s)
- Cut 4: Ben Stokes batting stance → hook shot (2.5s)
Technique: Jump cuts showing legacy through repetition
Method: 4 separate video generations, identical framing
CRITICAL: Camera position, player position in frame, and framing must be IDENTICAL across all cuts
```

**When to Use**:
- Rapid product demonstrations
- Showing time passage
- High-energy sequences
- Demonstrating versatility
- Showing legacy/tradition through repeated action with different people
- Sports promos showing multiple athletes doing same action

---

### 4. Flow Cut

**What it is**: Smooth transition maintaining emotional/visual continuity

**Creative Purpose**: Gentle scene changes, maintain mood, natural progression

**Generation Method**:
```yaml
method: separate_videos_with_crossfade
steps:
  - Generate Scene A
  - Generate Scene B with compatible lighting/mood
  - Apply subtle crossfade in post (0.3-0.5s)
veo_features:
  - Compatible lighting between scenes
  - Similar color palettes
post_production: Crossfade or soft cut
```

**Prompt Requirements**:
- Maintain similar lighting temperature
- Compatible color palettes
- Smooth emotional progression

**Example**:
```
Scene 1: Artist painting in studio (warm lighting)
Scene 2: Finished painting displayed in gallery (warm lighting)
Technique: Flow cut maintains creative continuity
```

**When to Use**:
- Calm, contemplative sequences
- Showing progression
- Maintaining emotional tone

---

### 5. Smash Cut

**What it is**: Abrupt, jarring cut between contrasting scenes

**Creative Purpose**: Create dramatic impact, surprise, emphasize contrast

**Generation Method**:
```yaml
method: separate_videos_hard_cut
steps:
  - Generate Scene A
  - Generate Scene B (or black frame)
  - Hard cut with no transition
veo_features: none (contrast is in editing)
post_production: Hard cut, possibly with audio sting
```

**Prompt Requirements**:
- Maximize contrast (lighting, energy, mood)
- No need for visual continuity
- Can cut to/from black

**Example**:
```
Scene 1: Intense gym workout (high energy, loud)
Scene 2: Black screen (0.5s)
Scene 3: Calm product shot (minimal, quiet)
Technique: Smash cut to black for dramatic reset
```

**When to Use**:
- Dramatic tone shifts
- Ending montages
- Creating surprise
- Emphasizing contrast

---

### 6. Action Cut

**What it is**: Cut during action, same environment, different angle

**Creative Purpose**: Show action from multiple perspectives, build tension

**Generation Method**:
```yaml
method: separate_videos_same_environment
steps:
  - Generate Scene A with action from angle 1
  - Generate Scene B with same action from angle 2
  - Cut during action peak
veo_features:
  - Same environment/lighting
  - Synchronized action timing
post_production: Cut on action beat
```

**Prompt Requirements**:
- Maintain environment consistency
- Synchronize action timing
- Different camera angles

**Example**:
```
Scene 1: Boxer throwing punch (wide shot)
Scene 2: Fist connecting with bag (close-up)
Technique: Action cut shows same moment, different angle
```

**When to Use**:
- Action sequences
- Building tension
- Showing detail
- Dynamic pacing

---

### 7. Montage Cut

**What it is**: Series of rapid cuts showing progression or multiple moments

**Creative Purpose**: Compress time, show variety, demonstrate versatility

**Generation Method**:
```yaml
method: multiple_separate_generations
decision_per_shot:
  - if shot_duration < 2s AND motion minimal:
      method: image_generation
  - if shot_duration < 2s AND motion significant:
      method: video_trim
  - if shot_duration >= 4s:
      method: video_generation
post_production: Edit all shots together with hard cuts
```

**Prompt Requirements**:
- Each shot is separate generation
- Maintain subject consistency (reference images)
- Vary backgrounds/contexts
- Keep subject framing consistent

**Example - Product Versatility**:
```
Montage: Headphones in action
- Shot 1: Office desk (1.3s) - image stitch
- Shot 2: Running outdoors (1.3s) - video trim (motion)
- Shot 3: Gym locker (1.4s) - image stitch
Technique: Montage cuts demonstrate versatility
Total: 4.0s, 3 separate generations
```

**When to Use**:
- Product demonstrations
- Showing progression
- High-energy sequences
- Demonstrating versatility

---

## Energy/Mood to Transition Mapping

### High Energy Videos
**Recommended Transitions**:
- jump_cut (fast pacing, 150-250ms per cut)
- action_cut (dynamic, 200-300ms)
- montage_cut (rapid sequence, < 2s per shot)

**Avoid**:
- flow_cut (too slow)
- Long crossfades

### Moderate Energy Videos
**Recommended Transitions**:
- flow_cut (balanced, 250-400ms)
- action_cut (controlled energy)
- match_cut_action (smooth progression)

**Avoid**:
- Excessive jump cuts
- Smash cuts (unless intentional)

### Calm/Serene Videos
**Recommended Transitions**:
- flow_cut (slow, 400-700ms)
- match_cut_graphic (visual poetry)
- Crossfades (0.5-1.0s)

**Avoid**:
- jump_cut (too jarring)
- smash_cut (too aggressive)

### Dramatic Videos
**Recommended Transitions**:
- smash_cut (impact, 200-500ms)
- match_cut_action (tension)
- action_cut (intensity)

**Avoid**:
- flow_cut (reduces tension)
- Soft crossfades

---

## Generation Decision Tree

```
For each scene transition:

1. Identify the transition technique needed
   └─> Look up technique in this vocabulary

2. Check scene duration
   ├─ < 2s → Consider image stitch (if minimal motion)
   ├─ < 4s → Generate 4s video, trim
   └─ >= 4s → Generate at exact duration

3. Check if match cut
   ├─ YES → Generate separate videos with precise composition
   │        Document exact element positions
   │        Use reference images for consistency
   └─ NO → Generate based on duration rules

4. Check motion complexity
   ├─ High motion → Always use video generation
   ├─ Medium motion → Video generation preferred
   └─ Minimal motion → Image stitch viable for < 2s

5. Post-production requirements
   ├─ Match cuts → Hard cut at matching frame
   ├─ Flow cuts → Crossfade (0.3-0.5s)
   ├─ Smash cuts → Hard cut, no transition
   ├─ Jump cuts → Hard cut, no transition
   └─ Montage → Edit all shots together
```

---

## Common Mistakes to Avoid

### ❌ Wrong: Trying to generate match cut in single video
```
"Camera pans from office to gym, headphone stays in same position"
```
**Why wrong**: Veo generates continuous shots, not edited sequences

### ✅ Right: Generate two separate videos
```
Video 1: Office scene, headphone in bottom-right
Video 2: Gym scene, headphone in bottom-right (same position)
Post: Hard cut between them
```

---

### ❌ Wrong: Using flow cut for high-energy montage
```
Scene 1 → Scene 2 → Scene 3 (all with crossfades)
```
**Why wrong**: Crossfades slow down pacing, reduce energy

### ✅ Right: Use jump cuts or montage cuts
```
Scene 1 → Scene 2 → Scene 3 (hard cuts, 150ms each)
```

---

### ❌ Wrong: Generating 1s video directly
```
"Generate 1 second video of product"
```
**Why wrong**: Veo minimum is 4s

### ✅ Right: Generate 4s, trim in post OR use image stitch
```
Option A: Generate 4s video, trim to 1s
Option B: Generate 2 images, ffmpeg stitch to 1s
```

---

## Integration with Veo 3.1 Features

### First + Last Frame (Interpolation)
**Best for**:
- match_cut_graphic (precise composition)
- flow_cut (smooth transitions)
- Scenes with specific start/end states

**How to use**:
1. Generate first frame with Imagen
2. Generate last frame with Imagen (matching composition for match cuts)
3. Use both as keyframes for Veo generation
4. Veo interpolates the motion between them

### Reference Images
**Best for**:
- Character consistency across jump cuts
- Product consistency in montages
- match_cut_action with same character

**How to use**:
1. Generate character/product reference images (3 max)
2. Include in all Veo generations featuring that character/product
3. Maintains appearance across different scenes

### Timestamp Prompting
**Best for**:
- action_cut (precise action timing)
- Complex single-shot sequences
- Scenes with multiple beats

**How to use**:
```
[00:00-00:02] Character reaches for door
[00:02-00:04] Character opens door and steps through
[00:04-00:06] Character looks back over shoulder
```

---

## Advanced Jump Cut Pattern: Action Sequence with Different Subjects

### Pattern: Same Action, Different People

**What it is**: A specific jump cut technique where multiple different subjects perform the same action in the exact same screen position, creating a rhythmic visual pattern that emphasizes tradition, legacy, or universality.

**Key Characteristics**:
1. **Identical framing**: Camera position, angle, and focal length remain constant
2. **Same screen position**: Subject positioned in exact same location in frame
3. **Same action**: Each subject performs the same or similar action (e.g., batting, jumping, dancing)
4. **Different subjects**: Only the person changes between cuts
5. **Rhythmic timing**: Cuts happen at similar points in the action cycle

**Generation Requirements**:
```yaml
method: multiple_separate_video_generations
requirements:
  - Each cut is a separate video generation (2-3s each)
  - Use reference images for each subject
  - Prompts must specify EXACT camera position and framing
  - Document player/subject position coordinates
  - Each video shows complete action cycle
composition_control:
  - "Subject positioned in center frame"
  - "Camera angle: [exact angle, e.g., side-on from square leg]"
  - "Focal length: [exact, e.g., 85mm]"
  - "Subject's [body part] positioned at [screen position]"
post_production:
  - Hard cuts between each video
  - No transition effects
  - Cut timing can be on action beat or at completion
```

**Prompt Template**:
```
CUT 1: [Shot type], [focal length], [depth of field]. [Subject 1 description] 
positioned in [exact screen position]. [Action description]. [Lighting]. 
CRITICAL: Document exact framing for replication.

CUT 2: IDENTICAL camera position and framing to Cut 1. [Subject 2 description] 
in EXACT same screen position. [Action description]. Same lighting and composition.

CUT 3: IDENTICAL camera position and framing to Cut 1. [Subject 3 description] 
in EXACT same screen position. [Action description]. Same lighting and composition.
```

**Example Use Cases**:
1. **Sports Promos**: Multiple athletes performing signature moves
2. **Brand Heritage**: Different generations using same product
3. **Dance/Movement**: Different dancers performing same choreography
4. **Workplace**: Different employees at same desk/position
5. **Product Demo**: Different users demonstrating same feature

**Example - Cricket Batting**:
```
Scene: The Ashes Legends
Duration: 9.0s total (4 cuts)

Cut 1 (2.0s): Steve Smith
- Medium shot, 85mm, f/2.8
- Side-on angle from square leg
- Player centered in frame
- Action: Batting stance → cover drive → follow-through
- Stadium lighting, dramatic shadows

Cut 2 (2.5s): Joe Root
- IDENTICAL framing to Cut 1
- Player in EXACT same position
- Action: Batting stance → straight drive → follow-through
- Same lighting

Cut 3 (2.0s): Pat Cummins
- IDENTICAL framing to Cut 1
- Player in EXACT same position
- Action: Batting stance → pull shot → follow-through
- Same lighting

Cut 4 (2.5s): Ben Stokes
- IDENTICAL framing to Cut 1
- Player in EXACT same position
- Action: Batting stance → hook shot → follow-through
- Same lighting

Effect: Creates rhythmic pattern emphasizing the timeless tradition 
of The Ashes and the legacy of great batsmen.
```

**Common Mistakes**:
❌ Varying camera angle between cuts
❌ Different subject positions in frame
❌ Inconsistent lighting
❌ Different focal lengths
❌ Trying to generate all cuts in one video

**Best Practices**:
✅ Generate each cut as separate video
✅ Use reference images for each subject
✅ Document exact camera specs in first prompt
✅ Copy camera specs exactly for subsequent cuts
✅ Test first cut before generating others
✅ Keep action timing consistent (2-3s per cut)
✅ Use hard cuts in post-production
✅ Consider audio rhythm matching visual rhythm

---

## Practical Examples from Real Ads

### Example 1: Product Versatility (Headphones)
```
Structure: 15s ad, high energy
Transitions: match_cut_graphic + montage_cut

Scene 1 (2s): Office - Close-up, headphones on
  → match_cut_graphic (headphone position)
Scene 2 (3s): Gym - Close-up, headphones on (same position)
  → match_cut_graphic (headphone band to horizon)
Scene 3 (3s): Running - Medium shot, headphones visible
  → montage_cut (rapid sequence)
Scene 4 (4s): Montage - 3 quick cuts (office/run/gym)
  - 4A (1.3s): Office typing - image stitch
  - 4B (1.3s): Running feet - video trim
  - 4C (1.4s): Gym sweat - image stitch
  → smash_cut to black
Scene 5 (2.5s): Product reveal - Slow rotation

Generation Strategy:
- S1: 4s video, trim to 2s (camera movement)
- S2: 4s video, trim to 3s (camera movement)
- S3: 4s video, trim to 3s (tracking shot)
- S4A: 2 images, ffmpeg stitch (static)
- S4B: 4s video, trim to 1.3s (motion)
- S4C: 2 images, ffmpeg stitch (static)
- S5: First+last frame, 4s trim to 2.5s (rotation)

Total generations: 5 videos + 4 images
Total cost: ~$0.80
Total time: ~5 minutes
```

### Example 2: Emotional Story (Watch)
```
Structure: 12s ad, moderate energy
Transitions: flow_cut + match_cut_action

Scene 1 (3s): Morning routine - Medium shot
  → flow_cut (smooth progression)
Scene 2 (3s): Business meeting - Close-up on watch
  → match_cut_action (hand gesture continues)
Scene 3 (3s): Evening dinner - Two-shot
  → flow_cut (emotional continuity)
Scene 4 (3s): Product close-up - Macro shot

Generation Strategy:
- All scenes 4s duration (no trimming needed)
- Use reference images for character consistency
- Crossfade transitions (0.4s each)

Total generations: 4 videos
Total cost: ~$0.60
Total time: ~4 minutes
```

---

## Summary: Key Takeaways

1. **Transitions are creative techniques**, not optimization problems
2. **Match cuts require separate generations** with precise composition control
3. **Duration < 2s + minimal motion** = consider image stitch
4. **Duration < 4s + motion** = generate 4s video, trim in post
5. **Montages = multiple separate generations**, edited together
6. **Energy/mood determines transition pacing** and type
7. **Reference the vocabulary** when writing prompts
8. **Document exact positions** for match cuts
9. **Use Veo features** (first+last frame, reference images) strategically
10. **Post-production is essential** - not everything happens in generation
