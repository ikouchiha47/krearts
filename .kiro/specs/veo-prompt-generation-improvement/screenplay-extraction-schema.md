# Screenplay Extraction Schema

## Purpose
Extract structured, actionable data from the markdown screenplay for automated generation pipeline.

## Why a Neural Net Would Be Better

**Current approach**: Rule-based markdown parsing + LLM generation
**Problem**: 
- LLMs hallucinate structure
- Inconsistent field extraction
- Can't learn from feedback
- Expensive (multiple LLM calls)

**Neural net approach**:
- **Fine-tuned T5/BART model** (sequence-to-sequence)
- **Input**: Raw screenplay markdown
- **Output**: Structured JSON
- **Training data**: 100-500 examples of screenplay → JSON pairs
- **Benefits**:
  - Consistent extraction
  - Learns patterns (e.g., "dolly shot" → camera_movement.type = "dolly")
  - Fast inference (~100ms vs 5-10s for LLM)
  - Cheap (self-hosted or $0.001/call)
  - Can fine-tune on your specific screenplay style

**Training approach**:
1. Generate 100-200 screenplay examples (varied styles)
2. Manually create gold-standard JSON for each
3. Fine-tune T5-base or BART-base
4. Validate on held-out test set
5. Deploy as API endpoint

**Alternative**: Use a **classifier ensemble**:
- Scene type classifier (hook/problem/solution/benefit/cta)
- Transition type classifier (match_cut/smash_cut/etc.)
- Generation method classifier (first_last_frame/text_to_video/etc.)
- Then assemble JSON from classifier outputs

---

## JSON Structure

```json
{
  "video_context": {
    "title": "THE SEAMLESS SHIFT",
    "target_demographic": "Urban professionals, 25-40",
    "duration": 17.5,
    "aspect_ratio": "16:9",
    "overall_energy": "high_energy",
    "lighting_guidelines": "Cool office → bright daylight → golden hour",
    "camera": "Arri Alexa simulation, 50mm + 24mm"
  },
  
  "characters": [
    {
      "id": "CHAR_MAX",
      "name": "MAX",
      "physical_appearance": "30-year-old man, mixed race, athletic build, short dark hair, light brown skin",
      "reference_images_required": ["front_portrait", "side_profile", "full_body"]
    }
  ],
  
  "scenes": [
    {
      "scene_id": "S1_PROBLEM",
      "scene_type": "problem",
      "duration": 3.0,
      "timing": {"start": 0.0, "end": 3.0},
      "composition": "single_shot",
      "energy": "dramatic",
      
      "transition": {
        "from_previous": null,
        "to_next": "smash_cut",
        "visual_bridge": "Black headphone earcup position",
        "technique_notes": "Earcup must be in exact same position for S2 match"
      },
      
      "characters_present": ["CHAR_MAX"],
      
      "cinematography": {
        "shot_type": "extreme close-up",
        "camera_angle": "eye-level",
        "focal_length": "100mm telephoto",
        "depth_of_field": "f/1.8",
        "camera_movement": {
          "type": "dolly",
          "speed": "medium",
          "direction": "backward"
        }
      },
      
      "generation_method": "first_last_frame_interpolation",
      "generation_reason": "Requires smooth dolly movement over 3s",
      "veo_features": ["first_last_frame", "reference_images"],
      
      "prompts": {
        "first_frame_imagen": "Macro photograph of a sleek, matte black performance headphone earcup pressed against the ear of a tense, athletic man (30s, mixed race). The earcup fills the top-left quadrant of the frame, highly detailed texture. Shallow depth of field (f/1.8). Harsh, cool blue-white fluorescent office lighting. Photorealistic, 4K, cinematic style. Aspect ratio: 16:9.",
        
        "last_frame_imagen": "Cinematic medium shot of MAX (30s, mixed race, wearing crisp dark polo) typing intensely at a sleek, minimalist modern office desk. He is wincing slightly. Background is blurred with multiple cubicles, ringing phones, and bright monitors. Cool, high-contrast fluorescent lighting. Camera is eye-level, 50mm lens. High-energy, documentary style. Aspect ratio: 16:9.",
        
        "veo_prompt": "Dolly shot pulling back slowly from an extreme close-up of a black headphone earcup against the ear of MAX (30s, mixed race, tense expression) to a medium shot revealing him typing intensely at a modern office desk surrounded by chaotic noise. Harsh, cool blue-white overhead fluorescent lighting creating sharp shadows and high contrast. 50mm lens, shallow depth of field focusing on MAX's frustrated face. Cinematic tension, high drama.\n\nAmbient noise: LOUD, DISTORTED SOUND of KEYBOARD CLATTERING, PHONES RINGING, CHATTER.\nVoiceover (MAX, strained, low): \"Focus is fragile.\"",
        
        "negative_prompt": "Cartoon, low quality, soft focus, warm colors, vintage filter, excessive lens flare."
      },
      
      "audio": {
        "dialogue": [
          {
            "character": "MAX",
            "timing": "00:00-00:03",
            "voice_characteristics": "Strained, low, determined whisper",
            "text": "Focus is fragile."
          }
        ],
        "sfx": "LOUD, distorted keyboard clattering, phones ringing",
        "ambient": "Harsh, overwhelming office noise"
      },
      
      "post_production": {
        "required": true,
        "notes": "Hard cut to S2. Apply heavy audio distortion for first 1.5s",
        "trim_to": null,
        "color_grade": "Cool, high-contrast",
        "text_overlays": []
      },
      
      "visual_anchors": {
        "consistent_element": "Black headphone earcup",
        "position": "Top-left quadrant",
        "color_palette": "Cool blues, whites, dark grays",
        "lighting": "Harsh overhead fluorescent"
      }
    },
    
    {
      "scene_id": "S2_SOLUTION",
      "scene_type": "solution",
      "duration": 4.0,
      "timing": {"start": 3.0, "end": 7.0},
      "composition": "single_shot",
      "energy": "high_energy",
      
      "transition": {
        "from_previous": "smash_cut",
        "to_next": "montage_cut",
        "visual_bridge": "Headphone earcup - EXACT position match from S1",
        "technique_notes": "First frame must match S1 last frame earcup position"
      },
      
      "characters_present": ["CHAR_MAX"],
      
      "cinematography": {
        "shot_type": "extreme close-up to medium",
        "camera_angle": "eye-level",
        "focal_length": "100mm telephoto",
        "depth_of_field": "f/1.8",
        "camera_movement": {
          "type": "tracking",
          "speed": "fast",
          "direction": "parallel to subject"
        }
      },
      
      "generation_method": "text_to_video",
      "generation_reason": "Requires sustained fast action (running) and tracking shot",
      "veo_features": ["reference_images"],
      
      "prompts": {
        "first_frame_imagen": "Macro photograph of a sleek, matte black performance headphone earcup pressed against the ear of MAX (30s, mixed race). Sweat beads are visible near the padding. The earcup is positioned in the exact same top-left quadrant as S1. Background is blurred green trees and intense bright sunlight (f/1.8). High-saturation daylight, photorealistic, cinematic style. Aspect ratio: 16:9.",
        
        "veo_prompt": "Fast, handheld tracking shot following MAX (30s, athletic build, wearing sleek gray running gear) running intensely along a sun-drenched city park path. Start with an extreme close-up on the sweat-beaded earcup, quickly pulling back to a medium close-up following his profile. Bright, high-saturation sunlight creating rim lighting on sweat and sharp focus on his determined face. Action-packed, high energy.\n\nSound: Deep, pulsing electronic MUSIC BEAT overrides all ambient noise.\nVoiceover (MAX, breathy, focused): \"But the world doesn't stop for your flow.\"",
        
        "negative_prompt": "Cartoon, low quality, motion blur artifacts, soft focus, slow movement, rain."
      },
      
      "audio": {
        "dialogue": [
          {
            "character": "MAX",
            "timing": "00:03-00:07",
            "voice_characteristics": "Breathless, focused, determined",
            "text": "But the world doesn't stop for your flow."
          }
        ],
        "sfx": "Heavy breathing (subtle)",
        "ambient": "Deep pulsing electronic music"
      },
      
      "post_production": {
        "required": true,
        "notes": "Hard cut from S1. Music starts instantly at high volume",
        "trim_to": null,
        "color_grade": "High-saturation daylight",
        "text_overlays": []
      },
      
      "visual_anchors": {
        "consistent_element": "Black headphone earcup, CHAR_MAX",
        "position": "Top-left quadrant (matching S1)",
        "color_palette": "Bright greens, warm sunlight, gray gear",
        "lighting": "High-saturation daylight"
      }
    },
    
    {
      "scene_id": "S3_MONTAGE",
      "scene_type": "benefit",
      "duration": 4.5,
      "timing": {"start": 7.0, "end": 11.5},
      "composition": "montage_sequence",
      "energy": "very_high_energy",
      
      "transition": {
        "from_previous": "hard_cut",
        "to_next": "flow_cut",
        "visual_bridge": "Headphone earcup in consistent position across all 3 shots",
        "technique_notes": "Graphical match cuts - earcup position is anchor"
      },
      
      "sub_scenes": [
        {
          "sub_scene_id": "S3A_OFFICE",
          "duration": 1.5,
          "generation_method": "image_stitch_ffmpeg",
          "generation_reason": "Minimal motion (scrolling), under 2s, static camera",
          
          "prompts": {
            "first_frame_imagen": "Extreme close-up macro photograph of MAX's ear and the matte black headphone earcup (centered in the top-left quadrant, filling 30% of the frame). MAX's index finger scrolls rapidly on a sleek black mouse wheel, illuminated by bright monitor light. Background is blurred office setting. Cool blue/white lighting, sharp focus (f/2.8). Cinematic, photorealistic. Aspect ratio: 16:9.",
            
            "last_frame_imagen": "Same composition, finger position slightly different on mouse wheel. Aspect ratio: 16:9.",
            
            "ffmpeg_command": "ffmpeg -loop 1 -t 0.75 -i S3A_first.png -loop 1 -t 0.75 -i S3A_last.png -filter_complex \"[0][1]xfade=transition=fade:duration=0.3:offset=0.45\" -t 1.5 S3A_office.mp4"
          }
        },
        
        {
          "sub_scene_id": "S3B_RUNNING",
          "duration": 1.5,
          "generation_method": "video_trim",
          "generation_reason": "High motion (running), requires video generation despite <2s",
          
          "prompts": {
            "veo_prompt": "Static extreme close-up shot focused on the black headphone earcup. MAX's neck muscles visibly tense and relax slightly with exertion. Fast motion blur in the background suggesting high speed running. Bright, harsh daylight, high contrast.",
            
            "veo_config": {
              "duration": 4,
              "trim_to": 1.5
            }
          }
        },
        
        {
          "sub_scene_id": "S3C_WATERFRONT",
          "duration": 1.5,
          "generation_method": "image_stitch_ffmpeg",
          "generation_reason": "Minimal motion (head tilt), under 2s, static camera",
          
          "prompts": {
            "first_frame_imagen": "Extreme close-up macro photograph of MAX's ear and the matte black headphone earcup (centered in the top-left quadrant, filling 30% of the frame). MAX's face is relaxed, eyes closed, head tilted slightly upwards. Warm, golden hour light bathes the scene. Background is a soft blur of sunset colors over water. Very shallow focus (f/1.4). Serene, cinematic portrait. Aspect ratio: 16:9.",
            
            "last_frame_imagen": "Same composition, head tilted slightly more, deeper breath. Aspect ratio: 16:9.",
            
            "ffmpeg_command": "ffmpeg -loop 1 -t 0.75 -i S3C_first.png -loop 1 -t 0.75 -i S3C_last.png -filter_complex \"[0][1]xfade=transition=fade:duration=0.3:offset=0.45\" -t 1.5 S3C_waterfront.mp4"
          },
          
          "audio": {
            "dialogue": [
              {
                "character": "MAX",
                "timing": "00:10-00:11.5",
                "voice_characteristics": "Satisfied, calm whisper",
                "text": "So you need to take control."
              }
            ]
          }
        }
      ],
      
      "post_production": {
        "required": true,
        "notes": "Hard cuts between S3A, S3B, S3C. Ensure earcup position matches across all 3",
        "assembly_order": ["S3A_OFFICE", "S3B_RUNNING", "S3C_WATERFRONT"]
      }
    },
    
    {
      "scene_id": "S4_CTA",
      "scene_type": "cta",
      "duration": 6.0,
      "timing": {"start": 11.5, "end": 17.5},
      "composition": "single_shot",
      "energy": "calm",
      
      "transition": {
        "from_previous": "flow_cut",
        "to_next": "fade_out",
        "visual_bridge": "Golden hour lighting, calm atmosphere",
        "technique_notes": "Smooth transition from S3C warmth"
      },
      
      "characters_present": ["CHAR_MAX"],
      
      "cinematography": {
        "shot_type": "wide shot",
        "camera_angle": "eye-level",
        "focal_length": "24mm wide-angle",
        "depth_of_field": "f/8",
        "camera_movement": {
          "type": "dolly",
          "speed": "slow",
          "direction": "forward"
        }
      },
      
      "generation_method": "text_to_video",
      "generation_reason": "Requires smooth tracking shot over 6s",
      "veo_features": ["reference_images"],
      
      "prompts": {
        "veo_prompt": "Slow dolly tracking shot following MAX (30s, satisfied expression, walking calmly) along a waterfront pier during the golden hour sunset. MAX takes a deep, satisfied breath and adjusts the volume dial on his headphones. Warm, dramatic golden lighting, deep focus capturing the serene water reflections and vast horizon. Cinematic, resolved mood.\n\nVoiceover (MAX, confident, warm): \"One pair. Zero compromises.\"",
        
        "negative_prompt": "Cartoon, low quality, unnatural colors, distorted product shape."
      },
      
      "audio": {
        "dialogue": [
          {
            "character": "MAX",
            "timing": "00:13-00:14.5",
            "voice_characteristics": "Confident, warm, conclusive",
            "text": "One pair. Zero compromises."
          }
        ],
        "sfx": "Satisfied breath/sigh, faint volume dial click",
        "ambient": "Cinematic orchestral music swell"
      },
      
      "post_production": {
        "required": true,
        "notes": "Cut to product close-up at 00:14.5, fade out at 00:17.5",
        "text_overlays": [
          {
            "text": "[PRODUCT NAME] - Your Shift, Unlocked.",
            "timing": "00:15.5-00:17.5",
            "style": "Clean sans-serif, white text"
          }
        ]
      }
    }
  ],
  
  "generation_manifest": {
    "character_references": [
      {
        "asset_id": "REF_CHAR_MAX_FRONT",
        "character_id": "CHAR_MAX",
        "type": "front_portrait",
        "imagen_prompt": "Neutral front-facing portrait of MAX: 30-year-old man, mixed race, athletic build, short dark hair, light brown skin. Neutral expression, even lighting, plain background. Photorealistic, high detail. Aspect ratio: 1:1.",
        "output_filename": "char_max_front.png"
      },
      {
        "asset_id": "REF_CHAR_MAX_SIDE",
        "character_id": "CHAR_MAX",
        "type": "side_profile",
        "imagen_prompt": "Side profile portrait of MAX: 30-year-old man, mixed race, athletic build, short dark hair, light brown skin. Neutral expression, even lighting, plain background. Photorealistic, high detail. Aspect ratio: 1:1.",
        "output_filename": "char_max_side.png"
      }
    ],
    
    "keyframes": [
      {
        "asset_id": "KEY_S1_FIRST",
        "scene_id": "S1_PROBLEM",
        "frame_type": "first_frame",
        "imagen_prompt": "[Full prompt from S1]",
        "output_filename": "s1_first_frame.png",
        "dependencies": []
      },
      {
        "asset_id": "KEY_S1_LAST",
        "scene_id": "S1_PROBLEM",
        "frame_type": "last_frame",
        "imagen_prompt": "[Full prompt from S1]",
        "output_filename": "s1_last_frame.png",
        "dependencies": []
      }
    ],
    
    "videos": [
      {
        "asset_id": "VID_S1",
        "scene_id": "S1_PROBLEM",
        "generation_method": "first_last_frame_interpolation",
        "veo_model": "veo-3.1-generate-preview",
        "veo_prompt": "[Full prompt from S1]",
        "negative_prompt": "[Negative prompt from S1]",
        "config": {
          "duration": 4,
          "aspect_ratio": "16:9",
          "resolution": "720p",
          "first_frame_asset_id": "KEY_S1_FIRST",
          "last_frame_asset_id": "KEY_S1_LAST",
          "reference_image_asset_ids": ["REF_CHAR_MAX_FRONT", "REF_CHAR_MAX_SIDE"]
        },
        "output_filename": "s1_problem_raw.mp4",
        "dependencies": ["KEY_S1_FIRST", "KEY_S1_LAST", "REF_CHAR_MAX_FRONT", "REF_CHAR_MAX_SIDE"]
      }
    ],
    
    "post_production_tasks": [
      {
        "task_id": "TRIM_S1",
        "type": "trim",
        "input_assets": ["VID_S1"],
        "parameters": {"trim_to": 3.0},
        "output_filename": "s1_problem_final.mp4"
      },
      {
        "task_id": "ASSEMBLE_S3",
        "type": "final_assembly",
        "input_assets": ["S3A_OFFICE", "S3B_RUNNING", "S3C_WATERFRONT"],
        "parameters": {"cut_type": "hard_cut"},
        "output_filename": "s3_montage_final.mp4"
      },
      {
        "task_id": "FINAL_EDIT",
        "type": "final_assembly",
        "input_assets": ["s1_problem_final.mp4", "s2_solution_final.mp4", "s3_montage_final.mp4", "s4_cta_final.mp4"],
        "parameters": {
          "transitions": ["smash_cut", "hard_cut", "flow_cut"],
          "audio_mix": true,
          "color_grade": true
        },
        "output_filename": "THE_SEAMLESS_SHIFT_final.mp4"
      }
    ]
  },
  
  "cost_estimate": {
    "total_imagen_calls": 8,
    "total_veo_calls": 3,
    "estimated_cost_usd": 0.61,
    "estimated_time_minutes": 4.5
  }
}
```

## Key Improvements in This Structure:

1. **Sub-scenes for montages**: S3 is properly broken down
2. **Generation method per shot**: Clear decision for each
3. **Dependencies tracked**: Know what to generate first
4. **Post-production tasks**: Explicit editing instructions
5. **Cost estimation**: Track budget
6. **Actionable prompts**: Ready to send to APIs

## Neural Net Training Data Format:

```
Input (markdown): [Full screenplay text]
Output (JSON): [Structured JSON above]

Training pairs: 100-500 examples
Model: T5-base or BART-base fine-tuned
Inference time: ~100ms
Cost: $0.001/call (self-hosted) vs $0.10-0.50/call (LLM)
```

This would be **10-50x cheaper and 50-100x faster** than using an LLM for extraction.