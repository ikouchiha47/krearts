import time

from google import genai
from google.genai import types
from PIL import Image


def generate_image_from_text(
    client,
    prompt,
    output="generated_image.png",
):
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt],
        config={"response_modalities": ["IMAGE"]},
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)

        elif part.inline_data is not None:
            image = part.as_image()
            image.save(f"output/tests/veo/{output}")

            return image


def generate_video_from_text(
    client,
    prompt,
    output="veo3_with_text_input.mp4",
):
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
    )

    # Poll the operation status until the video is ready.
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the generated video.
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save(f"output/tests/veo/{output}")

    print("Generated video saved to dialogue_example.mp4")


def generate_video_from_image(
    client,
    prompt,
    image,
    output="veo3_with_image_input.mp4",
):
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        image=image.parts[0].as_image(),
    )

    # Poll the operation status until the video is ready.
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save(f"output/tests/veo/{output}")
    print("Generated video saved to veo3_with_image_input.mp4")


def generate_video_interpolate(
    client, prompt, first_image, last_image, output="veo3_with_interpolation.mp4"
):
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        image=first_image,
        config=types.GenerateVideosConfig(
            last_frame=last_image,
        ),
    )

    # Poll the operation status until the video is ready.
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save(f"output/tests/veo/{output}")
    print("Generated video saved to veo3_with_interpolation.mp4")


def generate_with_ingredients(
    client,
    prompt,
    references: list,
    output="veo3_with_reference_images",
):
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        config=types.GenerateVideosConfig(
            reference_images=[*references],
        ),
    )

    # Poll the operation status until the video is ready.
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save(f"output/tests/veo/{output}.mp4")
    print(f"Generated video saved to {output}.mp4")


def build_images(prompts):
    images = []
    for prompt, out in prompts:
        print(prompt, out)
        images.append(
            generate_image_from_text(client, prompt=prompt, output=f"{out}.png")
        )

    assert len(images) == len(prompts), ""
    return images


def load_images(prompts):
    images = []

    for _, out in prompts:
        Image.open(f"output/tests/veo/{out}.png")

        images.append(
            types.Image.from_file(
                location=f"output/tests/veo/{out}.png",
                mime_type="image/png",
            )
        )

    return images


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    client = genai.Client()

    prompts = [
        (
            "A traveler walks through the famous Shibuya crossing in Tokyo at night. Anime style",
            "scene_1",
        ),
        (
            "The traveler walks down a charming cobblestone street in Paris during golden hour. The Eiffel Tower visible in the distant background. Anime style",
            "scene_2",
        ),
        (
            "The traveler walks through an ornate Moroccan archway in Marrakech. Intricate Islamic geometric patterns frame the shot. Anime style",
            "scene_3",
        ),
        (
            "The circular archway transitions to the iconic white-domed churches of Santorini against a stunning sunset. The traveler stands at the edge, arms spread wide, silhouetted against the orange and pink sky. Anime style",
            "scene_4",
        ),
        (
            "A 16:9 extra-wide shot of a futuristic battlefield in a detailed anime style. "
            "The camera is at a high angle, looking down from behind a massive army of hundreds of humanoid robots as they march towards a glowing, futuristic city on the distant horizon."
            "The foreground is a futuristic barren land, slick with rain. "
            "The scene is set on a dark, stormy night, with dramatic, moody lighting from the rain, robot optics, and the glowing city gates."
            "The robots are scaled appropriately for a ground invasion. The focus is entirely on the epic scale of the robot horde and the desolate landscape; no people or hero characters are visible.",
            "scene_5"
        ),
        (
            "A 16:9 extra-wide shot in a detailed anime style, viewed from a closer perspective just above the glowing futuristic city gates." 
            "The camera looks outward over a futuristic barren land, slick with heavy rain on a dark, stormy night. "
            "In the mid-ground and extending into the distance, a massive army of hundreds of humanoid robots, scaled appropriately for ground combat, advances menacingly towards the city." 
            "The city's fortified walls and prominent central gates are in the immediate foreground, illuminated by vibrant neon lights (magenta and cyan)." 
            "Dramatic, moody lighting emanates from the rain, scattered robot optics, and the city's glowing structures. The focus is on the imminent invasion of the overwhelming robot horde and the imposing defenses of the city. "
            "**No people or hero characters are visible.**",
            "scene_6"
        ),
    ]

    character_prompts = [
        (
            "Animated male character, Spider-Verse art style, athletic and lean build, dynamic pose suggesting readiness for sword combat, confident and focused expression. "
            "Exaggerated musculature, sharp angles, and stylized anatomy consistent with the film's aesthetic. "
            "He wears a fitted, futuristic-fantasy tunic and trousers, with intricate detailing and layered fabrics." 
            "The coloring uses Ben-Day dots and halftone patterns for shading, creating depth without smooth gradients."
            "Strong, graphic outlines define his form, with chromatic aberration subtly visible at the edges of colors. "
            "The character is animated on twos, giving a slightly snappier, illustrated feel. "
            "The background is a clean, neutral studio grey, out of focus."
            "No weapons are present. Highly detailed, cinematic lighting, vibrant color palette.",
            "character_1",
        )
    ]

    ingredients_prompts = [
        (
            "A dagger made up blue stone hardend by steel, Anime style. Only dagger and nothing else",
            "dagger_1",
        )
    ]

    # images = build_images(prompts=prompts)
    images = load_images(prompts=prompts)
    characters = load_images(prompts=character_prompts)
    ingredients = load_images(prompts=ingredients_prompts)

    # generate_video_interpolate(
    #     client=client,
    #     first_image=images[2],
    #     last_image=images[3],
    #     output="scene_3_4.mp4",
    #     prompt=(
    #         "Fast tracking shot, low-angle close-up (35mm lens, deep depth of field f/8) following the legs and feet of the traveler (ARYA) wearing a dark green jacket and backpack, walking quickly and rhythmically through the chaotic, neon-lit Shibuya Crossing in Tokyo."
    #         "Action match cut while travelling between the two places"
    #         "The movement is fast and purposeful. The final frame must show the left foot at the apex of its stride, centered perfectly for a match cut. Cool blue and magenta cinematic color grading. Dynamic, energetic, anime style"
    #     ),
    # )

    time.sleep(60)

    # NOTE: Important: wrap the image in VideoGenerationReferenceImage
    references = [
        types.VideoGenerationReferenceImage(
            image=img,
            reference_type="asset",  # type: ignore[arg-type]
        )
        for img in [characters[0], ingredients[0], images[5]]
    ]
    generate_with_ingredients(
        client=client,
        references=references,
        output="battlefield_lotr_epic",
        prompt=(
            "Using the provided character, dagger, and battlefield images: "
            "An epic 16:9 cinematic battle sequence in detailed anime style. Lord of the Rings Helm's Deep cinematography. "
            "CAMERA: Start with high aerial establishing shot looking down at the futuristic battlefield from 200 feet above. "
            "Slowly descend straight down toward the warrior at the center. "
            "End on a heroic low-angle medium shot of the warrior, blue dagger raised high. "
            "SUBJECT: Legendary warrior with blue stone dagger stands at the center of a rain-soaked battlefield. "
            "Hundreds of enemy robots surround him, advancing from all sides. "
            "ACTION: As camera descends, warrior shifts into combat stance. Blue dagger begins to glow with energy. "
            "Rain falls heavily across the scene. Lightning flashes in the background. "
            "STYLE: Epic fantasy battle cinematography. Dramatic heroic framing. "
            "LIGHTING: Dark stormy night. Neon city glow illuminates the background. "
            "Robot optics create scattered points of red light. Lightning provides dramatic rim lighting. "
            "AMBIANCE: Cinematic color grading with deep shadows and vibrant neon highlights. "
            "Professional smooth camera movement. 16:9 aspect ratio."
        )
    )

    # Action match cut: Paris to Marrakech walking transition
    # generate_video_interpolate(
    #     client=client,
    #     first_image=images[1],  # Paris scene
    #     last_image=images[2],   # Marrakech scene
    #     output="paris_marrakech_match_cut",
    #     prompt=(
    #         "An 8-second 16:9 cinematic travel sequence with action match cut in anime style. "
    #         "TIMING: 0-4 seconds Paris, 4-8 seconds Marrakech. Match cut occurs at exactly 4 seconds. "
    #         "SUBJECT: A traveler in casual travel attire walking with steady, rhythmic stride. "
    #         "FIRST LOCATION (0-4s): The traveler walks down a charming cobblestone street in Paris during golden hour. "
    #         "Warm amber and orange tones bathe the scene. The Eiffel Tower is visible in the distant background. "
    #         "CAMERA MOVEMENT: Medium tracking shot following the traveler from behind and slightly to the side. "
    #         "Camera maintains consistent distance and framing as traveler walks forward. "
    #         "ACTION MATCH CUT (at 4s): The traveler's right foot steps forward mid-stride. "
    #         "This exact foot position and body posture must be perfectly matched across the cut. "
    #         "SECOND LOCATION (4-8s): The same traveler continues the walking motion through an ornate Moroccan archway in Marrakech. "
    #         "Intricate Islamic geometric patterns frame the shot. Warm desert lighting with rich terracotta and blue tile colors. "
    #         "CAMERA MOVEMENT: Same medium tracking shot continues seamlessly. Camera maintains identical framing and distance. "
    #         "STYLE: Cinematic travel documentary aesthetic in anime style. Smooth, professional camera work. "
    #         "COMPOSITION: Medium shot throughout, traveler centered in frame during both locations. "
    #         "CON: The walking rhythm, pace, and body movement must be identical across the match cut. "
    #         "The transition should feel seamless, as if the traveler walked from Paris directly into Marrakech. "
    #         "AMBIANCE: Golden hour warmth in Paris transitions to warm desert afternoon in Marrakech. "
    #         "Maintain consistent lighting quality across the cut for visual continuity."
    #     )
    # )