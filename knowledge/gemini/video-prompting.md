# Documentation extracted from gemini-video-gen-basics.html

# Generate Videos with Veo 3.1 in Gemini API

[Veo 3.1](https://deepmind.google/models/veo/) is Google's state-of-the-art model for generating high-fidelity, 8-second 720p or 1080p videos featuring stunning realism and natively generated audio. You can access this model programmatically using the Gemini API. To learn more about the available Veo model variants, see the [Model Versions](#model-versions) section.

Veo 3.1 excels at a wide range of visual and cinematic styles and introduces several new capabilities:

- **Video extension**: Extend videos that were previously generated using Veo.
- **Frame-specific generation**: Generate a video by specifying the first and last frames.
- **Image-based direction**: Use up to three reference images to guide the content of your generated video.

For more information about writing effective text prompts for video generation, see the [Veo prompt guide](#prompt-guide).

## Text to Video Generation

Choose an example to see how to generate a video with dialogue, cinematic realism, or creative animation:

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""

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
generated_video.video.save("dialogue_example.mp4")
print("Generated video saved to dialogue_example.mp4")

```

## Image to Video Generation

The following code demonstrates generating an image using [Gemini 2.5 Flash Image aka Nano Banana](https://deepmind.google/models/veo/), then using that image as the starting frame for generating a video with Veo 3.1.

```python
import time
from google import genai

client = genai.Client()

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"

# Step 1: Generate an image with Nano Banana.
image = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config={"response_modalities": ['IMAGE']}
)

# Step 2: Generate video with Veo 3.1 using the image.
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
video.video.save("veo3_with_image_input.mp4")
print("Generated video saved to veo3_with_image_input.mp4")

```

### Using Reference Images

Veo 3.1 now accepts up to 3 reference images to guide your generated video's content. Provide images of a person, character, or product to preserve the subject's appearance in the output video.

```python
import time
from google import genai

client = genai.Client()

prompt = "The video opens with a medium, eye-level shot of a beautiful woman with dark hair and warm brown eyes..."

dress_reference = types.VideoGenerationReferenceImage(
  image=dress_image,  # Generated separately with Nano Banana
  reference_type="asset"
)

sunglasses_reference = types.VideoGenerationReferenceImage(
  image=glasses_image,  # Generated separately with Nano Banana
  reference_type="asset"
)

woman_reference = types.VideoGenerationReferenceImage(
  image=woman_image,  # Generated separately with Nano Banana
  reference_type="asset"
)

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    config=types.GenerateVideosConfig(
      reference_images=[dress_reference, glasses_reference, woman_reference],
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
video.video.save("veo3.1_with_reference_images.mp4")
print("Generated video saved to veo3.1_with_reference_images.mp4")

```

### Using First and Last Frames

Veo 3.1 lets you create videos using interpolation, or specifying the first and last frames of the video.

```python
import time
from google import genai

client = genai.Client()

prompt = "A cinematic, haunting video. A ghostly woman with long white hair and a flowing dress swings gently on a rope swing..."

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt=prompt,
    image=first_image,  # Generated separately with Nano Banana
    config=types.GenerateVideosConfig(
      last_frame=last_image  # Generated separately with Nano Banana
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
video.video.save("veo3.1_with_interpolation.mp4")
print("Generated video saved to veo3.1_with_interpolation.mp4")

```

## Extending Veo Videos

Use Veo 3.1 to extend videos that you previously generated with Veo by 7 seconds and up to 20 times.

Input video limitations:

- Veo-generated videos only up to 141 seconds long.
- Gemini API only supports video extensions for Veo-generated videos.
- Input videos are expected to have a certain length, aspect ratio, and dimensions:
  - Aspect ratio: 9:16 or 16:9
  - Resolution: 720p
  - Video length: 141 seconds or less

The output of the extension is a single video combining the user input video and the generated extended video for up to 148 seconds of video.

```python
import time
from google import genai

client = genai.Client()

prompt = "Track the butterfly into the garden as it lands on an orange origami flower. A fluffy white puppy runs up and gently pats the flower."

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    video=butterfly_video,
    prompt=prompt,
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        resolution="720p"
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
video.video.save("veo3.1_extension.mp4")
print("Generated video saved to veo3.1_extension.mp4")

```

For information about writing effective text prompts for video generation, see the [Veo prompt guide](#extend-prompt).

## Handling Asynchronous Operations

Video generation is a computationally intensive task. When you send a request to the API, it starts a long-running job and immediately returns an `operation` object. You must then poll until the video is ready, which is indicated by the `done` status being true.

The core of this process is a polling loop, which periodically checks the job's status.

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

# After starting the job, you get an operation object.
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A cinematic shot of a majestic lion in the savannah.",
)

# Alternatively, you can use operation.name to get the operation.
operation = types.GenerateVideosOperation(name=operation.name)

# This loop checks the job status every 10 seconds.
while not operation.done:
    time.sleep(10)
    # Refresh the operation object to get the latest status.
    operation = client.operations.get(operation)

# Once done, the result is in operation.response.
# ... process and download your video ...

```

## Veo API Parameters and Specifications

These are the parameters you can set in your API request to control the video generation process.

| Parameter | Description | Veo 3.1 & Veo 3.1 Fast | Veo 3 & Veo 3 Fast | Veo 2 |
|-----------|-------------|------------------------|-------------------|-------|
| `prompt` | The text description for the video. Supports audio cues. | `string` | `string` | `string` |
| `negativePrompt` | Text describing what not to include in the video. | `string` | `string` | `string` |
| `image` | An initial image to animate. | `Image` object | `Image` object | `Image` object |
| `lastFrame` | The final image for an interpolation video to transition. Must be used in combination with the `image` parameter. | `Image` object | `Image` object | `Image` object |
| `referenceImages` | Up to three images to be used as style and content references. | `VideoGenerationReferenceImage` object (Veo 3.1 only) | n/a | n/a |
| `video` | Video to be used for video extension. | `Video` object | n/a | n/a |
| `aspectRatio` | The video's aspect ratio. | `"16:9"` (default, 720p & 1080p), `"9:16"`(720p & 1080p) | `"16:9"` (default, 720p & 1080p), `"9:16"` (720p & 1080p) | `"16:9"` (default, 720p), `"9:16"` (720p) |
| `resolution` | The video's aspect ratio. | `"720p"` (default), `"1080p"` (only supports 8s duration) `"720p"` only for extension | `"720p"` (default), `"1080p"` (16:9 only) | Unsupported |
| `durationSeconds` | Length of the generated video. | `"4"`, `"6"`, `"8"`. Must be "8" when using extension or interpolation (supports both 16:9 and 9:16), and when using `referenceImages` (only supports 16:9) | `"4"`, `"6"`, `"8"` | `"5"`, `"6"`, `"8"` |
| `personGeneration` | Controls the generation of people. (See [Limitations](#limitations) for region restrictions) | Text-to-video & Extension: `"allow_all"` only Image-to-video, Interpolation, & Reference images: `"allow_adult"` only | Text-to-video: `"allow_all"` only Image-to-video: `"allow_adult"` only | Text-to-video: `"allow_all"`, `"allow_adult"`, `"dont_allow"` Image-to-video: `"allow_adult"`, and `"dont_allow"` |

Note that the `seed` parameter is also available for Veo 3 models. It doesn't guarantee determinism, but slightly improves it.

You can customize your video generation by setting parameters in your request. For example, you can specify `negativePrompt` to guide the model.

```python
import time
from google import genai
from google.genai import types

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="A cinematic shot of a majestic lion in the savannah.",
    config=types.GenerateVideosConfig(negative_prompt="cartoon, drawing, low quality"),
)

# Poll the operation status until the video is ready.
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Download the generated video.
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("parameters_example.mp4")
print("Generated video saved to parameters_example.mp4")

```

## Veo Prompt Guide

This section contains examples of videos you can create using Veo, and shows you how to modify prompts to produce distinct results.

### Safety Filters

Veo applies safety filters across Gemini to help ensure that generated videos and uploaded photos don't contain offensive content. Prompts that violate our [terms and guidelines](https://developers.google.com/site-policies) are blocked.

### Prompt Writing Basics

Good prompts are descriptive and clear. To get the most out of Veo, start with identifying your core idea, refine your idea by adding keywords and modifiers, and incorporate video-specific terminology into your prompts.

The following elements should be included in your prompt:

- **Subject**: The object, person, animal, or scenery that you want in your video, such as *cityscape*, *nature*, *vehicles*, or *puppies*.
- **Action**: What the subject is doing (for example, *walking*, *running*, or *turning their head*).
- **Style**: Specify creative direction using specific film style keywords, such as *sci-fi*, *horror film*, *film noir*, or animated styles like *cartoon*.
- **Camera positioning and motion**: [Optional] Control the camera's location and movement using terms like *aerial view*, *eye-level*, *top-down shot*, *dolly shot*, or *worms eye*.
- **Composition**: [Optional] How the shot is framed, such as *wide shot*, *close-up*, *single-shot* or *two-shot*.
- **Focus and lens effects**: [Optional] Use terms like *shallow focus*, *deep focus*, *soft focus*, *macro lens*, and *wide-angle lens* to achieve specific visual effects.
- **Ambiance**: [Optional] How the color and light contribute to the scene, such as *blue tones*, *night*, or *warm tones*.

#### More Tips for Writing Prompts

- **Use descriptive language**: Use adjectives and adverbs to paint a clear picture for Veo.
- **Enhance the facial details**: Specify facial details as a focus of the photo like using the word *portrait* in the prompt.

- For more comprehensive prompting strategies, visit [Introduction to prompt design](https://developers.google.com/gemini-api/docs/prompting-intro).*

### Prompting for Audio

With Veo 3, you can provide cues for sound effects, ambient noise, and dialogue. The model captures the nuance of these cues to generate a synchronized soundtrack.

- **Dialogue**: Use quotes for specific speech. (Example: "This must be the key," he murmured.)
- **Sound Effects (SFX)**: Explicitly describe sounds. (Example: tires screeching loudly, engine roaring.)
- **Ambient Noise**: Describe the environment's soundscape. (Example: A faint, eerie hum resonates in the background.)

These videos demonstrate prompting Veo 3's audio generation with increasing levels of detail.

### Prompting with Reference Images

You can use one or more images as inputs to guide your generated videos, using Veo's [image-to-video](https://developers.google.com/gemini-api/docs/video#generate-from-images) capabilities. Veo uses the input image as the initial frame. Select an image closest to what you envision as the first scene of your video to animate everyday objects, bring drawings and paintings to life, and add movement and sound to nature scenes.

### Prompting for Extension

To extend your Veo-generated video with Veo 3.1, use the video as an input along with an optional text prompt. Extend finalizes the final second or 24 frames of your video and continues the action.

Note that voice is not able to be effectively extended if it's not present in the last 1 second of video.

### Example Prompts and Output

This section presents several prompts, highlighting how descriptive details can elevate the outcome of each video.

#### Icicles

This video demonstrates how you can use the elements of [prompt writing basics](#basics) in your prompt.

#### Man on the Phone

These videos demonstrate how you can revise your prompt with increasingly specific details to get Veo to refine the output to your liking.

#### Snow Leopard

These examples show you how to refine your prompts by each basic element.

### Negative Prompts

Negative prompts specify elements you *don't* want in the video.

- ❌ Don't use instructive language like *no* or *don't*. (e.g., "No walls").
- ✅ Do describe what you don't want to see. (e.g., "wall, frame").

### Aspect Ratios

Veo lets you specify the aspect ratio for your video.

## Limitations

- **Request latency**: Min: 11 seconds; Max: 6 minutes (during peak hours).
- **Regional limitations**: In EU, UK, CH, MENA locations, the following are the allowed values for `personGeneration`:
  - Veo 3: `allow_adult` only.
  - Veo 2: `dont_allow` and `allow_adult`. Default is `dont_allow`.
- **Video retention**: Generated videos are stored on the server for 2 days, after which they are removed. To save a local copy, you must download your video within 2 days of generation. Extended videos are treated as newly generated videos.
- **Watermarking**: Videos created by Veo are watermarked using [SynthID](https://deepmind.google/technologies/synthid/), our tool for watermarking and identifying AI-generated content. Videos can be verified using the [SynthID](https://deepmind.google/science/synthid/) verification platform.
- **Safety**: Generated videos are passed through safety filters and memorization checking processes that help mitigate privacy, copyright and bias risks.
- **Audio error**: Veo 3.1 will sometimes block a video from generating because of safety filters or other processing issues with the audio. You will not be charged if your video is blocked from generating.

## Model Features

| Feature | Description | Veo 3.1 & Veo 3.1 Fast | Veo 3 & Veo 3 Fast | Veo 2 |
|---------|-------------|------------------------|-------------------|-------|
| **Audio** | Natively generates audio with video. | Natively generates audio with video. | ✔️ Always on | ❌ Silent only |
| **Input Modalities** | The type of input used for generation. | Text-to-Video, Image-to-Video, Video-to-Video | Text-to-Video, Image-to-Video | Text-to-Video, Image-to-Video |
| **Resolution** | The output resolution of the video. | 720p & 1080p (8s length only) 720p only when using video extension. | 720p & 1080p (16:9 only) | 720p |
| **Frame Rate** | The output frame rate of the video. | 24fps | 24fps | 24fps |
| **Video Duration** | Length of the generated video. | 8 seconds, 6 seconds, 4 seconds 8 seconds only when using reference images | 8 seconds | 5-8 seconds |
| **Videos per Request** | Number of videos generated per request. | 1 | 1 | 1 or 2 |
| **Status & Details** | Model availability and further details. | [Preview](https://developers.google.com/gemini-api/docs/models#preview) | [Stable](https://developers.google.com/gemini-api/docs/models#veo-3) | [Stable](https://developers.google.com/gemini-api/docs/models#latest-stable) |

## Model Versions

Check out the [Pricing](https://developers.google.com/gemini-api/docs/pricing#veo-3.1) and [Rate limits](https://developers.google.com/gemini-api/docs/rate-limits) pages for more Veo model-specific usage details.

Veo Fast versions allow developers to create videos with sound while maintaining high quality and optimizing for speed and business use cases. They're ideal for backend services that programmatically generate ads, tools for rapid A/B testing of creative concepts, or apps that need to quickly produce social media content.

## What's Next

- Get started with the Veo 3.1 API by experimenting in the [Veo Quickstart Colab](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started_Veo.ipynb) and the [Veo 3.1 applet](https://aistudio.google.com/apps/bundled/veo_studio).
- Learn how to write even better prompts with our [Introduction to prompt design](https://developers.google.com/gemini-api/docs/prompting-intro).