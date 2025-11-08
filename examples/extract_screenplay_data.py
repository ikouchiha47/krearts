"""
Example: Extract generation specs from screenplay output.

This shows how to use the transformers to extract only what you need
for each generation stage.
"""

import json
from pathlib import Path

from cinema.transformers import extract_all_stages


def main():
    # Load screenplay output
    screenplay_path = Path("gemini_screenplay.md")

    if not screenplay_path.exists():
        print(f"Error: {screenplay_path} not found")
        return

    with open(screenplay_path, "r") as f:
        content = f.read()
        screenplay = json.loads(content)

    # Extract for all stages
    print("Extracting generation specs...")
    extracted = extract_all_stages(screenplay)

    # ========================================================================
    # Stage 0: Character Generation
    # ========================================================================
    print("\n" + "=" * 80)
    print("STAGE 0: CHARACTER REFERENCE GENERATION")
    print("=" * 80)

    for char in extracted["characters"]:
        print(f"\nCharacter: {char.name} (ID: {char.id})")
        print(f"Description: {char.description}")
        print("Style Variations:")
        for context, style in char.style_variations.items():
            print(f"  - {context}: {style}")

        print("\nGenerate 3 reference images:")
        print(f"  1. Front view: {char.description}, neutral expression, white background")
        print(f"  2. Side profile: {char.description}, side view, white background")
        print(f"  3. Full body: {char.description}, standing naturally, white background")

    # ========================================================================
    # Stage 1: Image Generation (Keyframes)
    # ========================================================================
    print("\n" + "=" * 80)
    print("STAGE 1: KEYFRAME IMAGE GENERATION (Imagen/Nano Banana)")
    print("=" * 80)

    for scene_images in extracted["images"]:
        print(f"\nScene: {scene_images.scene_id}")

        if scene_images.first_frame:
            print(f"\n  First Frame:")
            print(f"    Aspect Ratio: {scene_images.first_frame.aspect_ratio}")
            print(f"    Character Refs: {scene_images.first_frame.character_refs}")
            print(f"    Prompt: {scene_images.first_frame.prompt[:100]}...")

        if scene_images.last_frame:
            print(f"\n  Last Frame:")
            print(f"    Aspect Ratio: {scene_images.last_frame.aspect_ratio}")
            print(f"    Character Refs: {scene_images.last_frame.character_refs}")
            print(f"    Prompt: {scene_images.last_frame.prompt[:100]}...")

        if scene_images.transition_frame:
            print(f"\n  Transition Frame:")
            print(f"    Prompt: {scene_images.transition_frame.prompt[:100]}...")

    # ========================================================================
    # Stage 2: Video Generation
    # ========================================================================
    print("\n" + "=" * 80)
    print("STAGE 2: VIDEO GENERATION (Veo)")
    print("=" * 80)

    for video in extracted["videos"]:
        print(f"\nScene: {video.scene_id}")
        print(f"  Method: {video.method}")
        print(f"  Duration: {video.duration}s")
        print(f"  Aspect Ratio: {video.aspect_ratio}")
        print(f"  Audio Handling: {video.audio_handling}")

        if video.first_frame_image:
            print(f"  First Frame Image: {video.first_frame_image}")
        if video.last_frame_image:
            print(f"  Last Frame Image: {video.last_frame_image}")

        if video.character_refs:
            print(f"  Character References: {video.character_refs}")

        print(f"  Prompt: {video.prompt[:100]}...")
        print(f"  Negative Prompt: {video.negative_prompt}")

    # ========================================================================
    # Stage 3: Post-Production
    # ========================================================================
    print("\n" + "=" * 80)
    print("STAGE 3: POST-PRODUCTION")
    print("=" * 80)

    for post in extracted["post_production"]:
        print(f"\nScene: {post.scene_id}")

        if post.trim_to:
            print(f"  Trim to: {post.trim_to}s")

        if post.transition_to_next:
            print(f"  Transition to next: {post.transition_to_next}")

        if post.effects:
            print(f"  Effects:")
            for effect in post.effects:
                print(f"    - {effect['type']}: '{effect['text']}' ({effect['timing']})")

        if post.audio_clip:
            print(f"  Audio clip: {post.audio_clip}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Characters: {len(extracted['characters'])}")
    print(f"Scenes with images: {len(extracted['images'])}")
    print(f"Videos to generate: {len(extracted['videos'])}")
    print(f"Post-production scenes: {len(extracted['post_production'])}")
    print(f"Total duration: {extracted['video_config']['total_duration']}s")
    print(f"Aspect ratio: {extracted['video_config']['aspect_ratio']}")


if __name__ == "__main__":
    main()
