"""
Cinema Models - Screenplay Output Schema

This module defines the expected output format for the screenplay generation crew.

EXAMPLE RESPONSE:
================

{
    "title": "Tokyo Nights: A Travel Journey",
    "storyline": "A traveler explores iconic locations through seamless transitions",
    "caption": "Experience the world through cinematic match cuts",
    "video_config": {
        "total_duration": 15,
        "aspect_ratio": "16:9",
        "needs_voiceover": true,
        "needs_background_music": true,
        "voice_characteristics": "Calm, inspiring narrator",
        "music_description": "Upbeat travel music",
        "camera": "35mm",
        "lighting_consistency": "Natural lighting with warm tones"
    },
    "character_description": [
        {
            "id": 1,
            "physical_appearance": "Male, 28 years old, athletic build, short dark hair",
            "style": "Casual travel wear - comfortable but stylish",
            "target_alignment": "Universal appeal"
        }
    ],
    "scenes": [
        {
            "scene_id": "S1_Tokyo_Crossing",
            "duration": 3.5,
            "context": "Traveler walks through Shibuya crossing at night",
            "voiceover_text": "Every journey begins with a single step",
            "video_prompt": "Medium shot, Steadicam following. Traveler walks across Shibuya Crossing in Tokyo at night. Vibrant neon blue and pink lights reflecting off rain-slicked asphalt. Cinematic, photorealistic, 4K.",
            "negative_prompt": "low quality, cartoon, blurry",
            "characters": {"primary_character_id": 1},
            "keyframe_description": {
                "needs_keyframes": true,
                "first_frame_prompt": "Medium shot of traveler at Shibuya crossing, neon lights, night",
                "last_frame_prompt": "Close-up of traveler's foot mid-stride on wet pavement"
            },
            "generation_strategy": {
                "generation_method": "image_to_video",
                "reason": "Single keyframe with motion",
                "audio_handling": "ambient_only"
            }
        }
    ]
}

ACCEPTABLE VALUES:
==================

VideoConfig.aspect_ratio:
  - "9:16"  (vertical/mobile)
  - "16:9"  (horizontal/landscape)
  - "1:1"   (square)

Scene.generation_strategy.generation_method:
  - "text_to_video"                    (no keyframes, just prompt)
  - "image_to_video"                   (single keyframe + motion)
  - "first_last_frame_interpolation"  (two keyframes, interpolate between)
  - "image_stitch_ffmpeg"              (static images stitched together)

Scene.generation_strategy.audio_handling:
  - "veo_native"     (include dialogue in video generation prompt)
  - "silent"         (no audio at all)
  - "ambient_only"   (only environmental sounds, no dialogue)

CameraSetup.shot_type:
  - "wide shot", "medium shot", "close-up", "extreme close-up", "POV"

CameraSetup.camera_angle:
  - "eye-level", "low-angle", "high-angle", "dutch angle", "aerial"

CameraMovement.movement_type:
  - "static", "dolly shot", "tracking shot", "pan", "tilt", "crane shot", "handheld", "zoom"

Scene.energy_mood:
  - "high_energy", "moderate", "calm", "dramatic"

SceneFlow.transition_technique:
  - "match_cut_graphic"  (shape/composition match)
  - "match_cut_action"   (motion/action match)
  - "jump_cut"           (abrupt time/space jump)
  - "flow_cut"           (smooth continuation)
  - "smash_cut"          (dramatic contrast)
  - "action_cut"         (cut on action)
  - "montage_cut"        (series of quick cuts)

IMPORTANT NOTES:
================

1. KeyframeDescription.needs_keyframes should be TRUE only when:
   - Using first_last_frame_interpolation method
   - Scene has complex transitions requiring precise framing
   - Otherwise, set to FALSE and use text_to_video or image_to_video

2. Scene.video_prompt should be COMPLETE and include:
   - Camera setup (shot type, angle, lens)
   - Subject description (with character reference if applicable)
   - Action/motion description
   - Environment/context
   - Style keywords (cinematic, photorealistic, 4K, etc.)

3. Character IDs should be consistent across all scenes

4. Duration values are in seconds (float)

5. For character consistency, always reference character by ID in scenes
"""

from typing import Any, List, Literal, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VideoConfig(BaseModel):
    total_duration: int
    aspect_ratio: Literal["9:16", "16:9", "1:1"]
    needs_voiceover: bool = True
    needs_background_music: bool
    voice_characteristics: str
    music_description: str
    camera: Optional[str] = Field(
        default="35mm", description="Camera/lens used (e.g., 35mm, 50mm, wide-angle)"
    )
    lighting_consistency: Optional[str] = Field(
        default=None,
        description="Lighting guidelines for the entire video to prevent abrupt changes",
    )
    # audio_generation_strategy: Literal["veo_native", "post_production", "hybrid"] = Field(
    #     default="post_production",
    #     description="How to handle audio: veo_native (each scene generates own audio), post_production (silent videos + audio overlay), hybrid (mix of both)"
    # )
    full_voiceover_script: Optional[str] = Field(
        default=None,
        description="Complete voiceover script for the entire video (for post-production audio generation)",
    )


class ContentStrategy(BaseModel):
    primary_message: str
    target_emotion: str
    visual_continuity: str


class CharacterDescription(BaseModel):
    id: int
    physical_appearance: str
    style: str
    target_alignment: Optional[str] = None
    voice_characterstics: Optional[str] = None


class SceneCharacterMapping(TypedDict):
    primary_character_id: int


class SceneFlow(BaseModel):
    """Scene flow and transition information"""

    previous_scene: Optional[str] = Field(
        default=None, description="Previous scene ID or None if opening"
    )
    next_scene: Optional[str] = Field(
        default=None, description="Next scene ID or None if closing"
    )
    transition_technique: Optional[str] = Field(
        default=None,
        description="Transition type: match_cut_graphic, match_cut_action, jump_cut, flow_cut, smash_cut, action_cut, montage_cut",
    )
    visual_bridge_element: Optional[str] = Field(
        default=None,
        description="Specific element connecting scenes (e.g., 'headphone position', 'hand gesture')",
    )
    narrative_purpose: Optional[str] = Field(
        default=None, description="What this scene achieves in the story"
    )


class CameraSetup(BaseModel):
    """Camera setup for first frame"""

    shot_type: Optional[str] = Field(
        default="medium shot",
        description="wide shot, medium shot, close-up, extreme close-up, POV",
    )
    camera_angle: Optional[str] = Field(
        default="eye-level",
        description="eye-level, low-angle, high-angle, dutch angle, aerial",
    )
    camera_position: Optional[str] = Field(
        default=None, description="Specific position description"
    )
    focal_length: Optional[str] = Field(
        default="35mm", description="35mm, 50mm, 85mm, 24mm wide-angle, 100mm telephoto"
    )
    depth_of_field: Optional[str] = Field(
        default="shallow f/2.8", description="shallow f/2.8, deep f/8, etc."
    )
    focus_point: Optional[str] = Field(default=None, description="What's in focus")


class CameraMovement(BaseModel):
    """Camera movement details"""

    movement_type: Optional[str] = Field(
        default="static",
        description="static, dolly shot, tracking shot, pan, tilt, crane shot, handheld, zoom",
    )
    speed: Optional[str] = Field(
        default="medium", description="slow, medium, fast, gradual"
    )
    direction: Optional[str] = Field(
        default=None, description="forward, backward, left, right, up, down, circular"
    )
    purpose: Optional[str] = Field(
        default=None,
        description="Why this movement - build tension, reveal, follow action, etc.",
    )


class CameraConsistency(BaseModel):
    """Camera consistency guardrails for transitions"""

    critical_visual_anchors: Optional[str] = Field(
        default=None,
        description="Elements that MUST stay in same position for match cuts",
    )
    eye_line: Optional[str] = Field(
        default="horizontal center",
        description="horizontal center, offset left, offset right",
    )
    lighting_direction: Optional[str] = Field(
        default=None, description="front-left, side, backlit, etc."
    )
    compositional_notes: Optional[str] = Field(
        default=None, description="Specific framing requirements for transitions"
    )


class Cinematography(BaseModel):
    """Complete cinematography details for a scene"""

    camera_setup: Optional[CameraSetup] = None
    camera_movement: Optional[CameraMovement] = None
    camera_consistency: Optional[CameraConsistency] = None


class GenerationStrategy(BaseModel):
    """Strategy for generating this scene"""

    generation_method: str = Field(
        default="text_to_video",
        description="first_last_frame_interpolation, image_to_video, text_to_video, image_stitch_ffmpeg",
    )
    reason: Optional[str] = Field(
        default=None, description="Why this method was chosen"
    )
    duration_generate: Optional[float] = Field(
        default=None,
        description="Duration to generate with Veo (e.g., 4.0s minimum). Only set if different from scene duration.",
    )
    duration_trim: Optional[float] = Field(
        default=None,
        description="Duration to trim to after generation (e.g., 2.0s). Only set if trimming is needed.",
    )
    veo_features_used: Optional[List[str]] = Field(
        default=None,
        description="List of Veo features: first+last frame, reference images, timestamp prompting",
    )
    audio_handling: Literal["veo_native", "silent", "ambient_only"] = Field(
        default="ambient_only",
        description="How to handle audio for this scene: veo_native (include dialogue in prompt), silent (no audio), ambient_only (only environmental sounds)",
    )
    post_production_required: bool = Field(
        default=False, description="Whether post-production editing is needed"
    )
    post_production_notes: Optional[str] = Field(
        default=None,
        description="What editing is needed - hard cut, crossfade, color grade, audio overlay, trim to duration, etc.",
    )


class KeyframeDescription(BaseModel):
    """Keyframe image descriptions for Imagen generation"""

    needs_keyframes: bool = Field(
        default=False,
        description="Whether this scene needs keyframe generation (only true for transitions or interpolation)",
    )
    first_frame_prompt: Optional[str] = Field(
        default=None,
        description="Detailed Imagen prompt for first frame (only if needs_keyframes=True)",
    )
    last_frame_prompt: Optional[str] = Field(
        default=None,
        description="Detailed Imagen prompt for last frame (only if needs_keyframes=True or has transition to next scene)",
    )
    transition_frame_prompt: Optional[str] = Field(
        default=None,
        description="Intermediate frame for lighting/environment transitions between this scene and next",
    )


class AudioDetails(BaseModel):
    """Audio details for the scene"""

    dialogue_timing: Optional[str] = Field(
        default=None, description="Timing of dialogue (e.g., 00:00:00-00:00:02)"
    )
    dialogue_character: Optional[str] = Field(
        default=None, description="Character speaking"
    )
    voice_characteristics: Optional[str] = Field(
        default=None,
        description="Voice characteristics (confident, whispered, excited, etc.)",
    )
    dialogue_text: Optional[str] = Field(
        default=None, description="Exact dialogue words"
    )
    sfx_description: Optional[str] = Field(
        default=None, description="Sound effects needed"
    )
    sfx_timing: Optional[str] = Field(
        default=None, description="When sound effects occur"
    )
    ambient_soundscape: Optional[str] = Field(
        default=None, description="Background audio environment"
    )
    ambient_mood: Optional[str] = Field(
        default=None, description="How audio contributes to scene mood"
    )


class VisualContinuity(BaseModel):
    """Visual continuity anchors across scenes"""

    consistent_element: Optional[str] = Field(
        default=None, description="Product, character, object that persists"
    )
    character_id: Optional[str] = Field(
        default=None, description="Character ID if present"
    )
    color_palette: Optional[str] = Field(
        default=None, description="Dominant colors in this scene"
    )
    lighting: Optional[str] = Field(
        default=None, description="Lighting characteristics"
    )
    critical_match_points: Optional[str] = Field(
        default=None, description="For transitions to next scene"
    )


class TransitionScene(BaseModel):
    """Transition scene between two main scenes"""

    scene_id: str
    duration: float
    voiceover_text: Optional[str] = None
    voiceover_character: Optional[str] = None
    image_prompt: Optional[str] = ""
    action_prompt: Optional[str] = ""
    energy_mood: str = Field(
        default="moderate",
        description="Energy/mood of the transition: high_energy, moderate, calm, dramatic",
    )


class Scene(BaseModel):
    scene_id: str
    duration: float
    timing: Optional[str] = Field(
        default=None, description="Start-end timing in video (e.g., 00:00-00:02)"
    )
    scene_composition: str = "single_shot"
    scene_type: Optional[str] = "benefit"

    # Context and narrative
    context: Optional[str] = Field(
        default=None, description="Environment description and narrative purpose"
    )
    scene_flow: Optional[SceneFlow] = None

    # Audio/dialogue
    voiceover_text: Optional[str] = None
    voiceover_character: Optional[str] = None
    lip_sync: Optional[bool] = False
    audio_details: Optional[AudioDetails] = None

    # Visual prompts (legacy fields, kept for backward compatibility)
    # image_prompt: Optional[str] = ""
    # action_prompt: Optional[str] = ""

    # New structured fields
    cinematography: Optional[Cinematography] = None
    generation_strategy: Optional[GenerationStrategy] = None
    keyframe_description: Optional[KeyframeDescription] = None
    visual_continuity: Optional[VisualContinuity] = None

    # Video generation prompt fields
    video_prompt: Optional[str] = Field(
        default=None,
        description="COMPLETE compiled video generation prompt for. This should include ALL details from cinematography, audio, action, context, style in a single formatted prompt following Veo's structure: [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]",
    )
    negative_prompt: Optional[str] = Field(
        default=None, description="Negative prompt for video generation"
    )

    has_product: Optional[bool] = None
    characters: Optional[SceneCharacterMapping] = None

    transition_to_next: Optional[TransitionScene] = Field(
        default=None, description="Transition scene between current and next scene"
    )

    energy_mood: str = Field(
        default="moderate",
        description=(
            "Energy/mood of the scene: " "high_energy, moderate, calm, dramatic"
        ),
    )

    @field_validator("scene_composition", mode="before")
    @classmethod
    def fix_scene_composition(cls, v):
        allowed_values = ["single_shot", "montage_sequence"]
        if v in allowed_values:
            return v
        return "single_shot"

    def has_character(self):
        return self.characters is not None


class SubsceneInputSchema(BaseModel):
    present_scene_data: Scene
    brand_voice: str
    video_tone: str
    energy_mood: str
    scene_duration: int
    num_subscenes: int
    summary: str

    def to_crew(self) -> dict[str, Any]:
        return self.model_dump()


class SubScenes(BaseModel):
    scenes: list[Scene]


class AudioTrack(BaseModel):
    """Complete audio track for the entire video"""

    full_voiceover_script: str = Field(
        ..., description="Complete voiceover script with timing markers"
    )
    voice_characteristics: str = Field(
        ..., description="Voice characteristics for the entire video"
    )
    music_description: str = Field(
        ..., description="Background music description and progression"
    )
    audio_segments: Optional[List[str]] = Field(
        default=None,
        description="List of audio segments with timing as JSON strings",
    )


class CinematgrapherCrewOutput(BaseModel):
    title: str = Field(..., description="Catchy title for the video")
    storyline: str = Field(
        ..., description="Brief storyline for the detailed scenes and shots"
    )
    caption: str
    video_config: VideoConfig

    # Target audience information
    target_demographic: Optional[str] = Field(
        default=None, description="Target audience demographic"
    )
    cultural_context: Optional[str] = Field(
        default=None, description="Cultural context considerations"
    )
    emotions_invoked: Optional[str] = Field(
        default=None, description="Emotions the video should invoke"
    )

    # Visual style
    visual_style: Optional[str] = Field(
        default=None,
        description="Overall visual style (cinematic, documentary, artistic, commercial)",
    )

    # Character registry
    character_description: Optional[List[CharacterDescription]] = None

    # Overall energy/mood
    energy_mood: str = Field(
        default="moderate",
        description="Overall energy/mood of the video: high_energy, moderate, calm, dramatic",
    )

    # Complete audio track (for post-production approach)
    audio_track: Optional[AudioTrack] = Field(
        default=None,
        description="Complete audio track for the entire video (used when audio_generation_strategy is 'post_production')",
    )

    # Scenes
    scenes: List[Scene]

    # Generation manifest (optional, for tracking)
    generation_manifest: Optional[str] = Field(
        default=None,
        description="Manifest of all assets to be generated and their dependencies as JSON string",
    )
