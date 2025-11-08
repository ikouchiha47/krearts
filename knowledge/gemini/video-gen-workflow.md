# Documentation extracted from gemini-veo3-blog-workflow.html

# Table of Contents

1. [Document Summary](#document-summary)
2. [Introduction](#introduction)
3. [Veo 3.1 Model Capabilities](#veo-31-model-capabilities)
   3. 1. [Core Generation Features](#core-generation-features)
   3. 2. [Advanced Creative Controls](#advanced-creative-controls)
4. [A Formula for Effective Prompts](#a-formula-for-effective-prompts)
5. [Essential Prompting Techniques](#essential-prompting-techniques)
   5. 1. [The Language of Cinematography](#the-language-of-cinematography)
   5. 2. [Directing the Soundstage](#directing-the-soundstage)
   5. 3. [Mastering Negative Prompts](#mastering-negative-prompts)
   5. 4. [Prompt Enhancement with Gemini](#prompt-enhancement-with-gemini)
6. [Advanced Creative Workflows](#advanced-creative-workflows)
   6. 1. [Workflow 1: The Dynamic Transition with "First and Last Frame"](#workflow-1-the-dynamic-transition-with-first-and-last-frame)
   6. 2. [Workflow 2: Building a Dialogue Scene with "Ingredients to Video"](#workflow-2-building-a-dialogue-scene-with-ingredients-to-video)
   6. 3. [Workflow 3: Timestamp Prompting](#workflow-3-timestamp-prompting)
7. [Start Creating with Veo 3.1 in Vertex AI](#start-creating-with-veo-31-in-vertex-ai)

- --

# Document Summary

This document provides a comprehensive guide to using Veo 3.1, a state-of-the-art model for video generation. It covers the model's capabilities, effective prompting techniques, and advanced workflows to maximize creative control. The guide is designed for developers and creators looking to leverage Veo 3.1's features in their projects, offering detailed instructions and examples to enhance video generation processes.

- --

# Introduction

If a picture is worth a thousand words, a video is worth a million. For creators, generative video holds the promise of bringing any story or concept to life. However, the reality has often been a frustrating cycle of "prompt and pray" – typing a prompt and hoping for a usable result, with little to no control over character consistency, cinematic quality, or narrative coherence.

This guide is a framework for directing [Veo 3.1](https://blog.google/technology/ai/veo-updates-flow), our latest model that marks a shift from simple generation to creative control. Veo 3.1 builds on Veo 3, with stronger prompt adherence and improved audiovisual quality when turning images into videos.

What you'll learn in this guide:

- **Learn** Veo 3.1's full range of capabilities on Vertex AI.
- **Implement** a formula to direct scenes with consistent characters and styles.
- **Direct** video and sound using professional cinematic techniques.
- **Execute** complex ideas by combining Veo with Gemini 2.5 Flash Image (Nano Banana) in advanced workflows.

- --

# Veo 3.1 Model Capabilities

First, it’s essential to understand the model's full range of capabilities. [Veo 3.1](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation) brings audio to existing capabilities to help you craft the perfect scene. These features are experimental and actively improving, and we’re excited to see what you create as we iterate based on your feedback.

## 3.1. Core Generation Features

- **High-fidelity video:** Generate video at 720p or 1080p resolution.
- **Aspect ratio:** 16:9 or 9:16
- **Variable clip length:** Create clips of 4, 6, or 8 seconds.
- **Rich audio & dialogue:** Veo 3.1 excels at generating realistic, synchronized sound, from multi-person conversations to precisely timed sound effects, all guided by the prompt.
- **Complex scene comprehension:** The model has a deeper understanding of narrative structure and cinematic styles, enabling it to better depict character interactions and follow storytelling cues.

## 3.2. Advanced Creative Controls

- **Improved image-to-video:** Animate a source image with greater prompt adherence and enhanced audio-visual quality.
- **Consistent elements with "ingredients to video":** Provide reference images of a scene, character, object, or style to maintain a consistent aesthetic across multiple shots. This feature now includes audio generation.
- **Seamless transitions with "first and last frame":** Generate a natural video transition between a provided start image and end image, complete with audio.
- **Add/remove object:** Introduce new objects or remove existing ones from a generated video. Veo preserves the scene's original composition.
- **Digital watermarking:** All generated videos are marked with SynthID to indicate the content is AI-generated.

Note: **Add/remove object** currently utilizes the Veo 2 model and does not generate audio.

- --

# A Formula for Effective Prompts

A structured prompt yields consistent, high-quality results. Consider this five-part formula for optimal control.

- *[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]**

- **Cinematography:** Define the camera work and shot composition.
- **Subject:** Identify the main character or focal point.
- **Action:** Describe what the subject is doing.
- **Context:** Detail the environment and background elements.
- **Style & ambiance:** Specify the overall aesthetic, mood, and lighting.

- Example prompt:* Medium shot, a tired corporate worker, rubbing his temples in exhaustion, in front of a bulky 1980s computer in a cluttered office late at night. The scene is lit by the harsh fluorescent overhead lights and the green glow of the monochrome monitor. Retro aesthetic, shot as if on 1980s color film, slightly grainy.

- --

# Essential Prompting Techniques

Mastering these core techniques will give you granular control over every aspect of your generation.

## 5.1. The Language of Cinematography

The `[Cinematography]` element of your prompt is the most powerful tool for conveying tone and emotion.

- **Camera movement:** Dolly shot, tracking shot, crane shot, aerial view, slow pan, POV shot.

- Crane shot example*

Prompt: Crane shot starting low on a lone hiker and ascending high above, revealing they are standing on the edge of a colossal, mist-filled canyon at sunrise, epic fantasy style, awe-inspiring, soft morning light.

- **Composition:** Wide shot, close-up, extreme close-up, low angle, two-shot.
- **Lens & focus:** Shallow depth of field, wide-angle lens, soft focus, macro lens, deep focus.

- Shallow depth of field example*

Prompt: Close-up with very shallow depth of field, a young woman's face, looking out a bus window at the passing city lights with her reflection faintly visible on the glass, inside a bus at night during a rainstorm, melancholic mood with cool blue tones, moody, cinematic.

## 5.2. Directing the Soundstage

Veo 3.1 can generate a complete soundtrack based on your text instructions.

- **Dialogue:** Use quotation marks for specific speech (e.g., *A woman says, "We have to leave now."*).
- **Sound effects (SFX):** Describe sounds with clarity (e.g., *SFX: thunder cracks in the distance*).
- **Ambient noise:** Define the background soundscape (e.g., *Ambient noise: the quiet hum of a starship bridge*).

## 5.3. Mastering Negative Prompts

To refine your output, describe what you wish to exclude. For example, specify "a desolate landscape with no buildings or roads" instead of "no man-made structures".

## 5.4. Prompt Enhancement with Gemini

If you need to add more detail, use Gemini to analyze and enrich a simple prompt with more descriptive and cinematic language.

- --

# Advanced Creative Workflows

While a single, detailed prompt is powerful, a multi-step workflow offers unparalleled control by breaking down the creative process into manageable stages. The following workflows demonstrate how to combine Veo 3.1's new capabilities with Gemini 2.5 Flash Image (Nano Banana) to execute complex visions.

## 6.1. Workflow 1: The Dynamic Transition with "First and Last Frame"

This technique allows you to create a specific and controlled camera movement or transformation between two distinct points of view.

- *Step 1: Create the starting frame:** Use Gemini 2.5 Flash Image to generate your initial shot.

Gemini 2.5 Flash Image prompt:

“Medium shot of a female pop star singing passionately into a vintage microphone. She is on a dark stage, lit by a single, dramatic spotlight from the front. She has her eyes closed, capturing an emotional moment. Photorealistic, cinematic.”

- *Step 2: Create the ending frame:** Generate a second, complementary image with Gemini 2.5 Flash Image, such as a different POV angle.

Gemini 2.5 Flash Image prompt:

“POV shot from behind the singer on stage, looking out at a large, cheering crowd. The stage lights are bright, creating lens flare. You can see the back of the singer's head and shoulders in the foreground. The audience is a sea of lights and silhouettes. Energetic atmosphere.”

- *Step 3: Animate with Veo.** Input both images into Veo using the **First and Last Frame** feature. In your prompt, describe the transition and the audio you want.

Veo 3.1 prompt: “The camera performs a smooth 180-degree arc shot, starting with the front-facing view of the singer and circling around her to seamlessly end on the POV shot from behind her on stage. The singer sings “when you look me in the eyes, I can see a million stars.”

## 6.2. Workflow 2: Building a Dialogue Scene with "Ingredients to Video"

This workflow is ideal for creating a multi-shot scene with consistent characters engaged in conversation, leveraging Veo 3.1's ability to craft a dialogue.

- *Step 1: Generate your "ingredients":** Create reference images using Gemini 2.5 Flash Image for your characters and the setting.

- *Step 2: Compose the scene:** Use the **Ingredients to Video** feature with the relevant reference images.

Prompt “Using the provided images for the detective, the woman, and the office setting, create a medium shot of the detective behind his desk. He looks up at the woman and says in a weary voice, "Of all the offices in this town, you had to walk into mine."

Prompt: “Using the provided images for the detective, the woman, and the office setting, create a shot focusing on the woman. A slight, mysterious smile plays on her lips as she replies, "You were highly recommended."

## 6.3. Workflow 3: Timestamp Prompting

This workflow allows you to direct a complete, multi-shot sequence with precise cinematic pacing, all within a single generation. By assigning actions to timed segments, you can efficiently create a full scene with multiple distinct shots, saving time and ensuring visual consistency.

Prompt example:

```plaintext
[00:00-00:02] Medium shot from behind a young female explorer with a leather satchel and messy brown hair in a ponytail, as she pushes aside a large jungle vine to reveal a hidden path.
[00:02-00:04] Reverse shot of the explorer's freckled face, her expression filled with awe as she gazes upon ancient, moss-covered ruins in the background. SFX: The rustle of dense leaves, distant exotic bird calls.
[00:04-00:06] Tracking shot following the explorer as she steps into the clearing and runs her hand over the intricate carvings on a crumbling stone wall. Emotion: Wonder and reverence.
[00:06-00:08] Wide, high-angle crane shot, revealing the lone explorer standing small in the center of the vast, forgotten temple complex, half-swallowed by the jungle. SFX: A swelling, gentle orchestral score begins to play.

```

- --

# Start Creating with Veo 3.1 in Vertex AI

You now have the framework to direct Veo with precision. The best way to master these techniques is to apply them for real-world use cases.

For developers and enterprise users, the improved Veo 3.1 model is available in preview on [Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation) via the API. This allows you to experiment with these advanced prompting workflows and build powerful, controlled video generation capabilities directly into your own applications.

- --

- Thanks to Anish Nangia, Sabareesh Chinta, and Wafae Bakkali for their contributions to prompting guidance for customers.*