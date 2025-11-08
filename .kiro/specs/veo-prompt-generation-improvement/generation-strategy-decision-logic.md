# Generation Strategy Decision Logic

## The Problem

For scenes < 2 seconds, we need to decide:
- **Option A**: Generate images + ffmpeg stitch (cheap, fast, but static)
- **Option B**: Generate 4s video + trim (expensive, slow, but dynamic)
- **Option C**: Generate multiple short videos + edit (most expensive, most control)

## Veo 3.1 Constraints (Hard Limits)

From the docs:
- **Minimum duration**: 4 seconds
- **Maximum duration**: 8 seconds
- **Supported durations**: 4s, 6s, 8s only
- **Cost**: ~$0.10-0.30 per generation (varies by model)
- **Generation time**: 11 seconds to 6 minutes

## Decision Tree

```
Scene Duration < 4s?
├─ YES → Is there significant motion/action?
│   ├─ YES → Generate 4s video, trim to needed duration
│   │   └─ Reason: Motion requires video generation
│   │
│   └─ NO → Is it a static shot or slow movement?
│       ├─ Static/Minimal → Generate 2 images (first+last), ffmpeg crossfade
│       │   └─ Reason: Cheaper, faster, sufficient quality
│       │
│       └─ Slow movement → Generate 4s video, trim
│           └─ Reason: Subtle motion needs video
│
└─ NO (≥4s) → Generate video at exact duration
    └─ Use 4s, 6s, or 8s based on scene needs
```

## Detailed Decision Criteria

### Criterion 1: Motion Complexity Score

Calculate a "motion score" for each scene:

```python
def calculate_motion_score(scene):
    score = 0
    
    # Camera movement
    if "dolly" in scene.camera_movement or "tracking" in scene.camera_movement:
        score += 3
    elif "pan" in scene.camera_movement or "tilt" in scene.camera_movement:
        score += 2
    elif "zoom" in scene.camera_movement or "push" in scene.camera_movement:
        score += 2
    elif "static" in scene.camera_movement:
        score += 0
    
    # Subject action
    if "running" in scene.action or "jumping" in scene.action:
        score += 3
    elif "walking" in scene.action or "moving" in scene.action:
        score += 2
    elif "typing" in scene.action or "gesturing" in scene.action:
        score += 1
    elif "sitting" in scene.action or "standing" in scene.action:
        score += 0
    
    # Environmental dynamics
    if "wind" in scene.context or "rain" in scene.context:
        score += 1
    if "crowd" in scene.context or "traffic" in scene.context:
        score += 1
    
    return score

# Decision logic
if scene.duration < 4:
    motion_score = calculate_motion_score(scene)
    
    if motion_score >= 4:
        strategy = "generate_4s_video_and_trim"
    elif motion_score >= 2:
        strategy = "generate_4s_video_and_trim"  # Border case
    else:
        strategy = "generate_images_and_stitch"
else:
    strategy = "generate_video_exact_duration"
```

### Criterion 2: Cost-Benefit Analysis

| Strategy | Cost | Time | Quality | Best For |
|----------|------|------|---------|----------|
| **Image Stitch** | $0.02 (2 images) | ~5s | Static/Slow | Duration < 2s, motion_score < 2 |
| **4s Video Trim** | $0.10-0.30 | 11s-6min | High | Duration < 4s, motion_score ≥ 2 |
| **Exact Video** | $0.10-0.30 | 11s-6min | High | Duration ≥ 4s |
| **Multi-Video Edit** | $0.30-0.90 | 30s-18min | Highest | Complex montages |

### Criterion 3: Scene Type Classification

```python
SCENE_TYPE_STRATEGIES = {
    # Static or near-static scenes
    "establishing_shot": {
        "duration_threshold": 3.0,
        "below_threshold": "image_stitch",  # Slow pan/tilt works with images
        "above_threshold": "video_generation"
    },
    
    # Product shots
    "product_reveal": {
        "duration_threshold": 2.5,
        "below_threshold": "image_stitch",  # Rotation can be faked with images
        "above_threshold": "video_generation"
    },
    
    # Action scenes
    "action": {
        "duration_threshold": 1.0,  # Even 1s needs video
        "below_threshold": "video_generation_trim",
        "above_threshold": "video_generation"
    },
    
    # Dialogue scenes
    "dialogue": {
        "duration_threshold": 2.0,
        "below_threshold": "video_generation_trim",  # Lip sync needs video
        "above_threshold": "video_generation"
    },
    
    # Transition shots
    "transition": {
        "duration_threshold": 1.5,
        "below_threshold": "image_stitch",  # Crossfades work well
        "above_threshold": "video_generation"
    },
    
    # Montage cuts
    "montage_cut": {
        "duration_threshold": 1.0,
        "below_threshold": "image_stitch",  # Quick cuts can be images
        "above_threshold": "video_generation_trim"
    }
}
```

## Practical Examples from Your Screenplay

### Scene 1: Office Focus (2.0s)

**Analysis**:
- Duration: 2.0s (< 4s threshold)
- Camera: Slow dolly-in (motion_score +2)
- Subject: Subtle facial movements (motion_score +1)
- Total motion_score: 3

**Decision**: Generate 4s video, trim to 2s
**Reasoning**: Camera movement requires smooth video generation

**Alternative (if budget constrained)**: 
- Generate 2 keyframes with subtle expression difference
- Use ffmpeg with motion interpolation:
```bash
ffmpeg -loop 1 -t 2 -i first_frame.png \
       -loop 1 -t 2 -i last_frame.png \
       -filter_complex "[0][1]blend=all_expr='A*(1-T/2)+B*(T/2)':shortest=1" \
       -t 2 output.mp4
```

### Scene 4A: Office Typing (1.3s)

**Analysis**:
- Duration: 1.3s (< 4s threshold)
- Camera: Static (motion_score +0)
- Subject: Typing hands (motion_score +1)
- Total motion_score: 1

**Decision**: Generate 2 images, ffmpeg stitch
**Reasoning**: 
- Very short duration
- Low motion complexity
- Cost savings: $0.02 vs $0.10-0.30
- Quality sufficient for quick cut

**Implementation**:
```bash
# Generate 2 images showing typing progression
# Image 1: Hands starting to type
# Image 2: Hands mid-type (slightly different position)

ffmpeg -loop 1 -t 0.65 -i typing_start.png \
       -loop 1 -t 0.65 -i typing_mid.png \
       -filter_complex "[0][1]xfade=transition=fade:duration=0.3:offset=0.35" \
       -t 1.3 S4A_typing.mp4
```

### Scene 4B: Running Feet (1.3s)

**Analysis**:
- Duration: 1.3s (< 4s threshold)
- Camera: Tracking shot (motion_score +3)
- Subject: Running feet (motion_score +3)
- Total motion_score: 6

**Decision**: Generate 4s video, trim to 1.3s
**Reasoning**: 
- High motion complexity
- Tracking shot requires smooth video
- Running motion needs natural movement
- Worth the extra cost for quality

### Scene 4C: Gym Sweat (1.4s)

**Analysis**:
- Duration: 1.4s (< 4s threshold)
- Camera: Static (motion_score +0)
- Subject: Wiping sweat (motion_score +1)
- Total motion_score: 1

**Decision**: Generate 2 images, ffmpeg stitch
**Reasoning**:
- Minimal motion
- Static camera
- Quick cut context (quality bar lower)
- Cost savings

### Scene 5: Product Reveal (2.5s)

**Analysis**:
- Duration: 2.5s (< 4s threshold)
- Camera: Orbital rotation (motion_score +3)
- Subject: Static product (motion_score +0)
- Total motion_score: 3

**Decision**: Generate 4s video, trim to 2.5s
**Reasoning**:
- Smooth rotation critical for premium feel
- Product shot needs high quality
- Camera movement requires video

## Hybrid Strategy: Best of Both Worlds

For montage sequences like Scene 4, use a **hybrid approach**:

```python
montage_strategy = {
    "S4A_OfficeTyping": {
        "method": "image_stitch",
        "cost": "$0.02",
        "time": "5s",
        "reason": "Static camera, minimal motion, quick cut"
    },
    "S4B_RunningFeet": {
        "method": "video_trim",
        "cost": "$0.15",
        "time": "30s",
        "reason": "High motion, tracking shot, needs smooth movement"
    },
    "S4C_GymSweat": {
        "method": "image_stitch",
        "cost": "$0.02",
        "time": "5s",
        "reason": "Static camera, minimal motion, quick cut"
    }
}

# Total montage cost: $0.19 (vs $0.45 if all video)
# Total montage time: 40s (vs 90s if all video)
# Quality: Optimized per shot type
```

## Implementation Algorithm

```python
def determine_generation_strategy(scene):
    """
    Determines the optimal generation strategy for a scene.
    
    Returns:
        strategy: "video_exact" | "video_trim" | "image_stitch"
        params: dict with generation parameters
    """
    
    # Step 1: Check duration constraints
    if scene.duration >= 4:
        return {
            "strategy": "video_exact",
            "duration": round_to_veo_duration(scene.duration),  # 4, 6, or 8
            "method": "veo_generation",
            "cost_estimate": 0.15,
            "time_estimate": 60
        }
    
    # Step 2: Calculate motion score
    motion_score = calculate_motion_score(scene)
    
    # Step 3: Check scene type
    scene_type = classify_scene_type(scene)
    type_config = SCENE_TYPE_STRATEGIES.get(scene_type, {})
    threshold = type_config.get("duration_threshold", 2.0)
    
    # Step 4: Decision logic
    if scene.duration < threshold and motion_score < 2:
        # Image stitching is viable
        return {
            "strategy": "image_stitch",
            "num_images": 2,
            "method": "imagen_generation",
            "stitch_method": "ffmpeg_crossfade",
            "cost_estimate": 0.02,
            "time_estimate": 5
        }
    else:
        # Video generation required
        return {
            "strategy": "video_trim",
            "generate_duration": 4,  # Minimum Veo duration
            "trim_to": scene.duration,
            "method": "veo_generation",
            "cost_estimate": 0.15,
            "time_estimate": 60
        }

def round_to_veo_duration(duration):
    """Round to nearest valid Veo duration: 4, 6, or 8 seconds."""
    if duration <= 5:
        return 4
    elif duration <= 7:
        return 6
    else:
        return 8
```

## Cost-Benefit Summary for Your 15s Ad

### Original Approach (All Video Generation)
- S1 (2s): Generate 4s video → $0.15
- S2 (3s): Generate 4s video → $0.15
- S3 (3s): Generate 4s video → $0.15
- S4A (1.3s): Generate 4s video → $0.15
- S4B (1.3s): Generate 4s video → $0.15
- S4C (1.4s): Generate 4s video → $0.15
- S5 (2.5s): Generate 4s video → $0.15

**Total**: $1.05, ~7 minutes generation time

### Optimized Hybrid Approach
- S1 (2s): Generate 4s video → $0.15 (motion required)
- S2 (3s): Generate 4s video → $0.15 (motion required)
- S3 (3s): Generate 4s video → $0.15 (motion required)
- S4A (1.3s): Image stitch → $0.02 (static, quick cut)
- S4B (1.3s): Generate 4s video → $0.15 (high motion)
- S4C (1.4s): Image stitch → $0.02 (static, quick cut)
- S5 (2.5s): Generate 4s video → $0.15 (rotation required)

**Total**: $0.79 (25% savings), ~5 minutes generation time

## When to Override the Algorithm

**Always use video generation if**:
1. Client specifically requests high-end quality
2. Scene is a hero moment (product reveal, emotional climax)
3. Lip-sync dialogue is present
4. Complex camera movements (dolly, crane, tracking)
5. Budget is not a constraint

**Always use image stitching if**:
1. Rapid montage with many cuts (< 1s each)
2. Static establishing shots
3. Transition frames between scenes
4. Budget is very constrained
5. Fast iteration/testing phase

## Recommendation for Your System

Implement a **configurable strategy selector**:

```python
class GenerationStrategySelector:
    def __init__(self, budget_mode="balanced"):
        """
        budget_mode: "premium" | "balanced" | "economy"
        """
        self.budget_mode = budget_mode
        self.thresholds = {
            "premium": {"motion_threshold": 1, "duration_threshold": 1.0},
            "balanced": {"motion_threshold": 2, "duration_threshold": 2.0},
            "economy": {"motion_threshold": 4, "duration_threshold": 3.0}
        }
    
    def select_strategy(self, scene):
        config = self.thresholds[self.budget_mode]
        motion_score = calculate_motion_score(scene)
        
        if scene.duration >= 4:
            return "video_exact"
        elif motion_score >= config["motion_threshold"]:
            return "video_trim"
        elif scene.duration < config["duration_threshold"]:
            return "image_stitch"
        else:
            return "video_trim"
```

This gives you control over the cost-quality trade-off while maintaining consistent logic.

---

## The Answer to Your Question

**"How do we know if it's less than 2s we need image gen + ffmpeg vs generating video and cutting it?"**

**Answer**: 
1. Calculate motion complexity score
2. Check scene type and context
3. Apply decision tree based on motion score + duration
4. For quick cuts in montages: default to image stitch unless high motion
5. For hero moments: always use video generation
6. Let the user configure budget mode (premium/balanced/economy)

The key insight: **It's not just about duration - it's about motion complexity relative to duration and context.**
