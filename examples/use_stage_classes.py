"""
Example: Using stage classes with object attributes.

This shows how to use the stage classes to access generation data
through clean object attributes.
"""

import json
from pathlib import Path

from cinema.transformers import extract_all_stages


def main():
    # Load screenplay
    screenplay_path = Path("gemini_screenplay.md")
    with open(screenplay_path, "r") as f:
        screenplay = json.loads(f.read())

    # Extract all stages
    extracted = extract_all_stages(screenplay)

    # ========================================================================
    # Stage 0: Character Generation
    # ========================================================================
    char_stage = extracted["characters"]
    print(f"Characters to generate: {len(char_stage.characters)}")

    for char in char_stage.characters:
        print(f"\n{char.name} (ID: {char.id})")
        print(f"  Description: {char.description}")

        # Get reference prompts
        prompts = char_stage.get_reference_prompts(char.id)
        print(f"  Front view: {prompts['front'][:60]}...")
        print(f"  Side view: {prompts['side'][:60]}...")
        print(f"  Full body: {prompts['full_body'][:60]}...")

    # ========================================================================
    # Stage 1: Image Generation
    # ========================================================================
    image_stage = extracted["images"]
    print(f"\n\nTotal images to generate: {image_stage.get_total_image_count()}")
    print(f"Scenes needing images: {len(image_stage.get_scenes_needing_images())}")

    for scene in image_stage.scenes:
        if scene.has_images():
            print(f"\n{scene.scene_id}: {scene.get_image_count()} images")

            if scene.first_frame:
                print(f"  First frame: {scene.first_frame.prompt[:60]}...")
                print(f"    Aspect ratio: {scene.first_frame.aspect_ratio}")
                print(f"    Character refs: {scene.first_frame.character_refs}")

            if scene.last_frame:
                print(f"  Last frame: {scene.last_frame.prompt[:60]}...")

    # ========================================================================
    # Stage 2: Video Generation
    # ========================================================================
    video_stage = extracted["videos"]
    print(f"\n\nTotal videos: {len(video_stage.videos)}")
    print(f"Total duration: {video_stage.total_duration}s")
    print(f"Aspect ratio: {video_stage.aspect_ratio}")

    # Group by method
    print(f"\nText-to-video: {len(video_stage.get_text_to_video_scenes())}")
    print(f"Image-to-video: {len(video_stage.get_image_to_video_scenes())}")
    print(f"Interpolation: {len(video_stage.get_interpolation_scenes())}")

    for video in video_stage.videos:
        print(f"\n{video.scene_id}")
        print(f"  Method: {video.method}")
        print(f"  Duration: {video.duration}s")
        print(f"  Needs first frame: {video.needs_first_frame()}")
        print(f"  Needs last frame: {video.needs_last_frame()}")
        print(f"  Character refs: {video.character_refs}")
        print(f"  Audio: {video.audio_handling}")

    # ========================================================================
    # Stage 3: Post-Production
    # ========================================================================
    post_stage = extracted["post_production"]
    print(f"\n\nPost-production scenes: {len(post_stage.scenes)}")
    print(f"Scenes needing trim: {len(post_stage.get_scenes_needing_trim())}")
    print(f"Scenes with effects: {len(post_stage.get_scenes_with_effects())}")

    # Get transition map
    transitions = post_stage.get_transition_map()
    print(f"\nTransitions:")
    for scene_id, technique in transitions.items():
        print(f"  {scene_id} → {technique}")

    # Show effects
    for scene in post_stage.get_scenes_with_effects():
        print(f"\n{scene.scene_id} effects:")
        for effect in scene.get_text_overlays():
            print(f"  - {effect.text} ({effect.timing})")


if __name__ == "__main__":
    main()
