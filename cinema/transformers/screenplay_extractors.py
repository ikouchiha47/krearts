"""
Transformers to extract data from screenplay output for different generation stages.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ============================================================================
# Stage 0: Character Generation
# ============================================================================


class CharacterReference(BaseModel):
    """Character reference for generation"""

    id: int
    name: str
    description: str
    style_variations: Dict[str, str]


class CharacterGenerationStage(BaseModel):
    """Stage 0: Character reference image generation"""

    characters: List[CharacterReference]

    def get_character(self, char_id: int) -> Optional[CharacterReference]:
        """Get character by ID"""
        for char in self.characters:
            if char.id == char_id:
                return char

        return None

    def get_reference_prompts(self, char_id: int) -> Dict[str, str]:
        """
        Get reference image prompts for a character.

        Returns:
            Dict with keys: front, side, full_body
        """
        char = self.get_character(char_id)
        if not char:
            return {"front": "", "side": "", "full_body": ""}

        return {
            "front": f"Close-up studio portrait photograph of {char.description}. 50mm lens, shallow depth of field f/2.8. Neutral expression, looking directly at camera. Clean white background, professional studio lighting. Front view, centered, photorealistic, high detail. Aspect ratio: 1:1.",
            "side": f"Close-up studio portrait photograph of {char.description}. 50mm lens, shallow depth of field f/2.8. Neutral expression, side profile. Clean white background, professional studio lighting. Side view, centered, photorealistic, high detail. Aspect ratio: 1:1.",
            "full_body": f"Full body studio photograph of {char.description}. 35mm lens, deep focus f/8. Standing naturally in neutral pose. Clean white background, professional studio lighting. Full body view, centered, photorealistic, high detail. Aspect ratio: 3:4.",
        }


# ============================================================================
# Stage 1: Image Generation (Keyframes)
# ============================================================================


class ImageGenerationSpec(BaseModel):
    """Specification for generating a single image"""

    prompt: str
    aspect_ratio: str
    character_refs: List[int] = []


class SceneImageSpecs(BaseModel):
    """All images needed for a scene"""

    scene_id: str
    first_frame: Optional[ImageGenerationSpec] = None
    last_frame: Optional[ImageGenerationSpec] = None
    transition_frame: Optional[ImageGenerationSpec] = None

    def has_images(self) -> bool:
        """Check if scene needs any images"""
        return (
            self.first_frame is not None
            or self.last_frame is not None
            or self.transition_frame is not None
        )

    def get_image_count(self) -> int:
        """Get total number of images to generate"""
        count = 0

        if self.first_frame:
            count += 1
        if self.last_frame:
            count += 1
        if self.transition_frame:
            count += 1

        return count


class ImageGenerationStage(BaseModel):
    """Stage 1: Keyframe image generation"""

    scenes: List[SceneImageSpecs]
    aspect_ratio: str

    def get_scene(self, scene_id: str) -> Optional[SceneImageSpecs]:
        """Get scene images by ID"""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene

        return None

    def get_total_image_count(self) -> int:
        """Get total number of images to generate across all scenes"""
        return sum(scene.get_image_count() for scene in self.scenes)

    def get_scenes_needing_images(self) -> List[SceneImageSpecs]:
        """Get only scenes that need images"""
        return [scene for scene in self.scenes if scene.has_images()]


# ============================================================================
# Stage 2: Video Generation
# ============================================================================


class VideoGenerationSpec(BaseModel):
    """Specification for generating a video"""

    scene_id: str
    method: str  # "first_last_frame_interpolation", "image_to_video", "text_to_video"
    prompt: str
    negative_prompt: str
    duration: float
    aspect_ratio: str
    first_frame_image: Optional[str] = None
    last_frame_image: Optional[str] = None
    character_refs: List[int] = []
    audio_handling: str = "ambient_only"

    def needs_first_frame(self) -> bool:
        """Check if this video needs a first frame image"""
        return self.method in ["first_last_frame_interpolation", "image_to_video"]

    def needs_last_frame(self) -> bool:
        """Check if this video needs a last frame image"""
        return self.method == "first_last_frame_interpolation"

    def is_text_to_video(self) -> bool:
        """Check if this is pure text-to-video generation"""
        return self.method == "text_to_video"


class VideoGenerationStage(BaseModel):
    """Stage 2: Video generation"""

    videos: List[VideoGenerationSpec]
    aspect_ratio: str
    total_duration: float

    def get_video(self, scene_id: str) -> Optional[VideoGenerationSpec]:
        """Get video spec by scene ID"""
        for video in self.videos:
            if video.scene_id == scene_id:
                return video
        return None

    def get_videos_by_method(self, method: str) -> List[VideoGenerationSpec]:
        """Get all videos using a specific generation method"""
        return [v for v in self.videos if v.method == method]

    def get_text_to_video_scenes(self) -> List[VideoGenerationSpec]:
        """Get scenes using text-to-video generation"""
        return self.get_videos_by_method("text_to_video")

    def get_image_to_video_scenes(self) -> List[VideoGenerationSpec]:
        """Get scenes using image-to-video generation"""
        return self.get_videos_by_method("image_to_video")

    def get_interpolation_scenes(self) -> List[VideoGenerationSpec]:
        """Get scenes using first+last frame interpolation"""
        return self.get_videos_by_method("first_last_frame_interpolation")


# ============================================================================
# Stage 3: Post-Production
# ============================================================================


class PostProductionEffect(BaseModel):
    """A single post-production effect"""

    type: str  # "text_overlay", "color_grade", "audio_mix", etc.
    text: Optional[str] = None
    timing: Optional[str] = None
    params: Dict[str, Any] = {}


class PostProductionSpec(BaseModel):
    """Specification for post-production of a scene"""

    scene_id: str
    trim_to: Optional[float] = None
    transition_to_next: Optional[str] = None
    effects: List[PostProductionEffect] = []
    audio_clip: Optional[str] = None

    def needs_trimming(self) -> bool:
        """Check if video needs trimming"""
        return self.trim_to is not None

    def has_transition(self) -> bool:
        """Check if scene has transition to next"""
        return self.transition_to_next is not None

    def has_effects(self) -> bool:
        """Check if scene has any effects"""
        return len(self.effects) > 0

    def get_text_overlays(self) -> List[PostProductionEffect]:
        """Get only text overlay effects"""
        return [e for e in self.effects if e.type == "text_overlay"]


class PostProductionStage(BaseModel):
    """Stage 3: Post-production and assembly"""

    scenes: List[PostProductionSpec]

    def get_scene(self, scene_id: str) -> Optional[PostProductionSpec]:
        """Get post-production spec by scene ID"""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None

    def get_scenes_needing_trim(self) -> List[PostProductionSpec]:
        """Get scenes that need trimming"""
        return [s for s in self.scenes if s.needs_trimming()]

    def get_scenes_with_effects(self) -> List[PostProductionSpec]:
        """Get scenes that have effects"""
        return [s for s in self.scenes if s.has_effects()]

    def get_transition_map(self) -> Dict[str, str]:
        """
        Get mapping of scene_id to transition technique.

        Returns:
            Dict mapping scene_id to transition_technique
        """
        return {
            scene.scene_id: scene.transition_to_next or ""
            for scene in self.scenes
            if scene.has_transition()
        }


# ============================================================================
# Extractors (convert screenplay dict to stage objects)
# ============================================================================


class CharacterExtractor:
    """Extract character data for reference image generation"""

    @staticmethod
    def extract(screenplay: Dict[str, Any]) -> CharacterGenerationStage:
        """
        Extract character references from screenplay.

        Args:
            screenplay: Full screenplay output

        Returns:
            CharacterGenerationStage object
        """
        characters = []

        for char in screenplay.get("character_description", []):
            # Extract name from physical_appearance
            name = CharacterExtractor._extract_name(
                char.get("physical_appearance", "")
            )

            # Parse style variations
            style_variations = CharacterExtractor._parse_style_variations(
                char.get("style", "")
            )

            characters.append(
                CharacterReference(
                    id=char["id"],
                    name=name,
                    description=char.get("physical_appearance", ""),
                    style_variations=style_variations,
                )
            )

        return CharacterGenerationStage(characters=characters)

    @staticmethod
    def _extract_name(description: str) -> str:
        """Extract name from description like 'Liam, 32-year-old man...'"""
        # Name is usually first word before comma
        parts = description.split(",")
        if parts:
            return parts[0].strip()
        return "Character"

    @staticmethod
    def _parse_style_variations(style_text: str) -> Dict[str, str]:
        """
        Parse style variations from text like:
        'Office: white shirt. Gym: athletic wear.'
        """
        variations = {}

        # Split by periods or newlines
        parts = re.split(r"[.\n]", style_text)

        for part in parts:
            part = part.strip()
            if ":" in part:
                key, value = part.split(":", 1)
                variations[key.strip().lower()] = value.strip()

        # If no variations found, use as default
        if not variations and style_text:
            variations["default"] = style_text

        return variations


# ============================================================================
# Stage 1: Image Generation Extraction
# ============================================================================


class ImageGenerationExtractor:
    """Extract image generation specs for Imagen/Nano Banana"""

    @staticmethod
    def extract(screenplay: Dict[str, Any]) -> ImageGenerationStage:
        """
        Extract image generation specs for all scenes.

        Args:
            screenplay: Full screenplay output

        Returns:
            ImageGenerationStage object
        """
        aspect_ratio = screenplay.get("video_config", {}).get("aspect_ratio", "16:9")

        scene_images = []

        for scene in screenplay.get("scenes", []):
            keyframes = scene.get("keyframe_description", {})

            # Skip if no keyframes needed
            if not keyframes or not keyframes.get("needs_keyframes", True):
                continue

            scene_id = scene["scene_id"]
            character_refs = ImageGenerationExtractor._extract_character_ids(scene)

            # Build image specs
            first_frame = None
            last_frame = None
            transition_frame = None

            if keyframes.get("first_frame_prompt"):
                first_frame = ImageGenerationSpec(
                    prompt=keyframes["first_frame_prompt"],
                    aspect_ratio=aspect_ratio,
                    character_refs=character_refs,
                )

            if keyframes.get("last_frame_prompt"):
                last_frame = ImageGenerationSpec(
                    prompt=keyframes["last_frame_prompt"],
                    aspect_ratio=aspect_ratio,
                    character_refs=character_refs,
                )

            if keyframes.get("transition_frame_prompt"):
                transition_frame = ImageGenerationSpec(
                    prompt=keyframes["transition_frame_prompt"],
                    aspect_ratio=aspect_ratio,
                    character_refs=character_refs,
                )

            scene_images.append(
                SceneImageSpecs(
                    scene_id=scene_id,
                    first_frame=first_frame,
                    last_frame=last_frame,
                    transition_frame=transition_frame,
                )
            )

        return ImageGenerationStage(scenes=scene_images, aspect_ratio=aspect_ratio)

    @staticmethod
    def _extract_character_ids(scene: Dict[str, Any]) -> List[int]:
        """Extract character IDs from scene"""
        chars = scene.get("characters", {})

        if isinstance(chars, dict):
            if "primary_character_id" in chars:
                return [chars["primary_character_id"]]

        return []


# ============================================================================
# Stage 2: Video Generation Extraction
# ============================================================================


class VideoGenerationExtractor:
    """Extract video generation specs for Veo"""

    @staticmethod
    def extract(screenplay: Dict[str, Any]) -> VideoGenerationStage:
        """
        Extract video generation specs for all scenes.

        Args:
            screenplay: Full screenplay output

        Returns:
            VideoGenerationStage object
        """
        aspect_ratio = screenplay.get("video_config", {}).get("aspect_ratio", "16:9")
        total_duration = screenplay.get("video_config", {}).get("total_duration", 15)

        video_specs = []

        for scene in screenplay.get("scenes", []):
            scene_id = scene["scene_id"]
            gen_strategy = scene.get("generation_strategy", {})

            # Determine generation method
            method = gen_strategy.get("generation_method", "text_to_video")

            # Get prompts
            video_prompt = scene.get("video_prompt", "")
            negative_prompt = scene.get("negative_prompt", "")

            # Get duration
            duration = scene.get("duration", 4.0)

            # Determine image paths (if using first/last frame)
            first_frame_image = None
            last_frame_image = None

            if method in ["first_last_frame_interpolation", "image_to_video"]:
                first_frame_image = f"{scene_id}_first_frame.png"
                if method == "first_last_frame_interpolation":
                    last_frame_image = f"{scene_id}_last_frame.png"

            # Get character refs
            character_refs = VideoGenerationExtractor._extract_character_ids(scene)

            # Get audio handling
            audio_handling = gen_strategy.get("audio_handling", "ambient_only")

            video_specs.append(
                VideoGenerationSpec(
                    scene_id=scene_id,
                    method=method,
                    prompt=video_prompt,
                    negative_prompt=negative_prompt,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    first_frame_image=first_frame_image,
                    last_frame_image=last_frame_image,
                    character_refs=character_refs,
                    audio_handling=audio_handling,
                )
            )

        return VideoGenerationStage(
            videos=video_specs, aspect_ratio=aspect_ratio, total_duration=total_duration
        )

    @staticmethod
    def _extract_character_ids(scene: Dict[str, Any]) -> List[int]:
        """Extract character IDs from scene"""
        chars = scene.get("characters", {})

        if isinstance(chars, dict):
            if "primary_character_id" in chars:
                return [chars["primary_character_id"]]

        return []


# ============================================================================
# Stage 3: Post-Production Extraction
# ============================================================================


class PostProductionExtractor:
    """Extract post-production specs"""

    @staticmethod
    def extract(screenplay: Dict[str, Any]) -> PostProductionStage:
        """
        Extract post-production specs for all scenes.

        Args:
            screenplay: Full screenplay output

        Returns:
            PostProductionStage object
        """
        post_specs = []

        for scene in screenplay.get("scenes", []):
            scene_id = scene["scene_id"]
            gen_strategy = scene.get("generation_strategy", {})
            scene_flow = scene.get("scene_flow", {})

            # Get trim duration
            trim_to = gen_strategy.get("duration_trim")

            # Get transition technique
            transition_to_next = scene_flow.get("transition_technique")

            # Extract effects
            effects = PostProductionExtractor._extract_effects(scene)

            # Audio clip path
            audio_clip = f"{scene_id}_audio.mp3"

            post_specs.append(
                PostProductionSpec(
                    scene_id=scene_id,
                    trim_to=trim_to,
                    transition_to_next=transition_to_next,
                    effects=effects,
                    audio_clip=audio_clip,
                )
            )

        return PostProductionStage(scenes=post_specs)

    @staticmethod
    def _extract_effects(scene: Dict[str, Any]) -> List[PostProductionEffect]:
        """Extract post-production effects from scene"""
        effects = []

        # Extract from post_production_notes
        gen_strategy = scene.get("generation_strategy", {})
        notes = gen_strategy.get("post_production_notes") or ""

        # Parse "Super: 'TEXT' (timing)" patterns
        super_pattern = r"Super: ['\"]([^'\"]+)['\"] \(([^)]+)\)"
        for match in re.finditer(super_pattern, notes):
            effects.append(
                PostProductionEffect(
                    type="text_overlay", text=match.group(1), timing=match.group(2)
                )
            )

        return effects


# ============================================================================
# Convenience Function: Extract All
# ============================================================================


def extract_all_stages(screenplay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract data for all generation stages.

    Args:
        screenplay: Full screenplay output

    Returns:
        Dict with keys: characters, images, videos, post_production
    """
    return {
        "characters": CharacterExtractor.extract(screenplay),
        "images": ImageGenerationExtractor.extract(screenplay),
        "videos": VideoGenerationExtractor.extract(screenplay),
        "post_production": PostProductionExtractor.extract(screenplay),
        "video_config": {
            "aspect_ratio": screenplay.get("video_config", {}).get("aspect_ratio", "16:9"),
            "total_duration": screenplay.get("video_config", {}).get("total_duration", 15),
        },
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import json

    # Load screenplay
    with open("gemini_screenplay.md", "r") as f:
        content = f.read()
        screenplay = json.loads(content)

    # Extract for all stages
    extracted = extract_all_stages(screenplay)

    # Print characters
    print("=== CHARACTERS ===")
    for char in extracted["characters"]:
        print(f"- {char.name} (ID: {char.id})")
        print(f"  Description: {char.description}")
        print(f"  Styles: {char.style_variations}")
        print()

    # Print image specs
    print("=== IMAGE GENERATION ===")
    for scene_images in extracted["images"]:
        print(f"Scene: {scene_images.scene_id}")
        if scene_images.first_frame:
            print(f"  First frame: {scene_images.first_frame.prompt[:80]}...")
        if scene_images.last_frame:
            print(f"  Last frame: {scene_images.last_frame.prompt[:80]}...")
        print()

    # Print video specs
    print("=== VIDEO GENERATION ===")
    for video in extracted["videos"]:
        print(f"Scene: {video.scene_id}")
        print(f"  Method: {video.method}")
        print(f"  Duration: {video.duration}s")
        print(f"  Prompt: {video.prompt[:80]}...")
        print()

    # Print post-production specs
    print("=== POST-PRODUCTION ===")
    for post in extracted["post_production"]:
        print(f"Scene: {post.scene_id}")
        if post.trim_to:
            print(f"  Trim to: {post.trim_to}s")
        if post.transition_to_next:
            print(f"  Transition: {post.transition_to_next}")
        if post.effects:
            print(f"  Effects: {len(post.effects)} effects")
        print()
