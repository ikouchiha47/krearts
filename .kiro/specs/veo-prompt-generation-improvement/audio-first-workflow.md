# Audio-First Video Generation Workflow

## Overview

This workflow generates voiceover audio first, then uses transcription analysis to automatically determine scene timing and boundaries. This eliminates manual audio sync work and ensures consistent voice quality across all scenes.

## Workflow Steps

```
1. Generate Full Audio (11Labs)
   ↓
2. Transcribe with Timestamps (Whisper/Gemini)
   ↓
3. Analyze & Detect Scene Boundaries
   ↓
4. Segment Audio into Scene Clips
   ↓
5. Update Scene Durations
   ↓
6. Generate Videos (Veo, silent/SFX only)
   ↓
7. Mix Audio Clips to Videos
   ↓
8. Final Video Output
```

## Detailed Implementation

### Step 1: Generate Full Audio

```python
from elevenlabs import generate, Voice

def generate_full_voiceover(screenplay: CinematgrapherCrewOutput) -> AudioFile:
    """
    Generate complete voiceover audio for entire screenplay.
    
    Returns:
        AudioFile with complete audio track
    """
    # Combine all voiceover text from scenes
    full_script = []
    for scene in screenplay.scenes:
        if scene.voiceover_text:
            full_script.append({
                "scene_id": scene.scene_id,
                "text": scene.voiceover_text,
                "character": scene.voiceover_character
            })
    
    # Generate single continuous audio track
    audio = generate(
        text=" ".join([s["text"] for s in full_script]),
        voice=Voice(
            voice_id="your_voice_id",
            settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75
            )
        ),
        model="eleven_multilingual_v2"
    )
    
    # Save to file
    audio_path = "output/full_voiceover.mp3"
    save(audio, audio_path)
    
    return AudioFile(path=audio_path, duration=get_duration(audio))
```

### Step 2: Transcribe with Timestamps

```python
import whisper
from typing import List, Dict

def transcribe_with_timestamps(audio_path: str) -> List[Dict]:
    """
    Transcribe audio with word-level timestamps.
    
    Returns:
        List of word segments with start/end times
    """
    # Load Whisper model
    model = whisper.load_model("base")
    
    # Transcribe with word timestamps
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        language="en"
    )
    
    # Extract word-level timing
    words = []
    for segment in result["segments"]:
        for word in segment.get("words", []):
            words.append({
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "confidence": word.get("probability", 1.0)
            })
    
    return words

# Alternative: Use Gemini for transcription
def transcribe_with_gemini(audio_path: str) -> List[Dict]:
    """
    Use Gemini API for transcription with timestamps.
    """
    from google import genai
    
    client = genai.Client()
    
    # Upload audio file
    audio_file = client.files.upload(path=audio_path)
    
    # Transcribe with timestamps
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            audio_file,
            "Transcribe this audio with word-level timestamps in JSON format: "
            "[{\"word\": \"text\", \"start\": 0.0, \"end\": 0.5}, ...]"
        ]
    )
    
    # Parse JSON response
    import json
    return json.loads(response.text)
```

### Step 3: Analyze & Detect Scene Boundaries

```python
from typing import List, Tuple

def detect_scene_boundaries(
    words: List[Dict],
    screenplay: CinematgrapherCrewOutput,
    pause_threshold: float = 0.5  # seconds
) -> List[Tuple[float, float, str]]:
    """
    Detect scene boundaries based on pauses and script structure.
    
    Args:
        words: Word-level transcription with timestamps
        screenplay: Original screenplay with scene structure
        pause_threshold: Minimum pause duration to consider as boundary
    
    Returns:
        List of (start_time, end_time, scene_id) tuples
    """
    boundaries = []
    current_scene_idx = 0
    scene_start = 0.0
    
    # Get expected scene texts
    scene_texts = [
        scene.voiceover_text.strip()
        for scene in screenplay.scenes
        if scene.voiceover_text
    ]
    
    # Track current position in transcript
    transcript_text = " ".join([w["word"] for w in words])
    
    for i, scene_text in enumerate(scene_texts):
        # Find where this scene's text appears in transcript
        scene_words = scene_text.split()
        
        # Match scene text to word timestamps
        scene_word_matches = []
        for j, word in enumerate(words):
            if word["word"].strip().lower() in [w.lower() for w in scene_words]:
                scene_word_matches.append(word)
        
        if scene_word_matches:
            scene_start = scene_word_matches[0]["start"]
            scene_end = scene_word_matches[-1]["end"]
            
            # Look for pause after scene
            if i < len(words) - 1:
                next_word_idx = words.index(scene_word_matches[-1]) + 1
                if next_word_idx < len(words):
                    pause_duration = words[next_word_idx]["start"] - scene_end
                    if pause_duration > pause_threshold:
                        # Natural pause detected, use it as boundary
                        scene_end = words[next_word_idx]["start"]
            
            boundaries.append((
                scene_start,
                scene_end,
                screenplay.scenes[i].scene_id
            ))
    
    return boundaries

# Alternative: Use LLM for intelligent boundary detection
def detect_boundaries_with_llm(
    words: List[Dict],
    screenplay: CinematgrapherCrewOutput
) -> List[Tuple[float, float, str]]:
    """
    Use LLM to intelligently detect scene boundaries.
    """
    from google import genai
    
    client = genai.Client()
    
    # Format transcript with timestamps
    transcript = "\n".join([
        f"[{w['start']:.2f}s] {w['word']}"
        for w in words
    ])
    
    # Format expected scenes
    scenes_text = "\n".join([
        f"Scene {i+1} ({scene.scene_id}): {scene.voiceover_text}"
        for i, scene in enumerate(screenplay.scenes)
        if scene.voiceover_text
    ])
    
    prompt = f"""
    Given this timestamped transcript:
    {transcript}
    
    And these expected scenes:
    {scenes_text}
    
    Identify the start and end timestamps for each scene.
    Return JSON: [{{"scene_id": "S1", "start": 0.0, "end": 2.1}}, ...]
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=prompt
    )
    
    import json
    boundaries_data = json.loads(response.text)
    
    return [
        (b["start"], b["end"], b["scene_id"])
        for b in boundaries_data
    ]
```

### Step 4: Segment Audio into Scene Clips

```python
from pydub import AudioSegment
import os

def segment_audio(
    audio_path: str,
    boundaries: List[Tuple[float, float, str]],
    output_dir: str = "output/audio_clips"
) -> Dict[str, str]:
    """
    Segment audio file into scene-aligned clips.
    
    Args:
        audio_path: Path to full audio file
        boundaries: List of (start, end, scene_id) tuples
        output_dir: Directory to save clips
    
    Returns:
        Dict mapping scene_id to audio clip path
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load full audio
    audio = AudioSegment.from_file(audio_path)
    
    clips = {}
    
    for start, end, scene_id in boundaries:
        # Convert seconds to milliseconds
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        
        # Extract clip
        clip = audio[start_ms:end_ms]
        
        # Save clip
        clip_path = os.path.join(output_dir, f"{scene_id}_audio.mp3")
        clip.export(clip_path, format="mp3")
        
        clips[scene_id] = clip_path
    
    return clips
```

### Step 5: Update Scene Durations

```python
def update_scene_durations(
    screenplay: CinematgrapherCrewOutput,
    boundaries: List[Tuple[float, float, str]]
) -> CinematgrapherCrewOutput:
    """
    Update scene durations to match actual audio timing.
    
    Args:
        screenplay: Original screenplay
        boundaries: Detected scene boundaries
    
    Returns:
        Updated screenplay with corrected durations
    """
    # Create mapping of scene_id to duration
    duration_map = {
        scene_id: end - start
        for start, end, scene_id in boundaries
    }
    
    # Update each scene
    for scene in screenplay.scenes:
        if scene.scene_id in duration_map:
            actual_duration = duration_map[scene.scene_id]
            
            # Update duration
            scene.duration = actual_duration
            
            # Update timing string
            start_time = sum(
                duration_map[s.scene_id]
                for s in screenplay.scenes[:screenplay.scenes.index(scene)]
                if s.scene_id in duration_map
            )
            end_time = start_time + actual_duration
            
            scene.timing = f"{format_timestamp(start_time)}-{format_timestamp(end_time)}"
    
    return screenplay

def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"
```

### Step 6: Generate Videos (Silent/SFX Only)

```python
def generate_silent_videos(
    screenplay: CinematgrapherCrewOutput,
    audio_clips: Dict[str, str]
) -> Dict[str, str]:
    """
    Generate Veo videos without dialogue (SFX/ambient only).
    
    Args:
        screenplay: Updated screenplay with correct durations
        audio_clips: Pre-generated audio clips (not used in Veo, but for reference)
    
    Returns:
        Dict mapping scene_id to video path
    """
    from google import genai
    import time
    
    client = genai.Client()
    videos = {}
    
    for scene in screenplay.scenes:
        # Modify prompt to exclude dialogue
        veo_prompt = scene.veo_prompt or scene.action_prompt
        
        # Remove any dialogue from prompt
        # (dialogue is typically in quotes)
        import re
        veo_prompt_no_dialogue = re.sub(r'"[^"]*"', '', veo_prompt)
        
        # Add SFX/ambient if specified
        if scene.audio_details:
            if scene.audio_details.sfx_description:
                veo_prompt_no_dialogue += f" SFX: {scene.audio_details.sfx_description}"
            if scene.audio_details.ambient_soundscape:
                veo_prompt_no_dialogue += f" Ambient noise: {scene.audio_details.ambient_soundscape}"
        
        # Generate video
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=veo_prompt_no_dialogue,
            config={
                "duration_seconds": round(scene.duration),
                "aspect_ratio": screenplay.video_config.aspect_ratio,
                "negative_prompt": "dialogue, voiceover, speech, talking"
            }
        )
        
        # Poll until complete
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
        
        # Download video
        video = operation.response.generated_videos[0]
        video_path = f"output/videos/{scene.scene_id}_video.mp4"
        client.files.download(file=video.video)
        video.video.save(video_path)
        
        videos[scene.scene_id] = video_path
    
    return videos
```

### Step 7: Mix Audio Clips to Videos

```python
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

def mix_audio_to_videos(
    videos: Dict[str, str],
    audio_clips: Dict[str, str],
    screenplay: CinematgrapherCrewOutput,
    output_path: str = "output/final_video.mp4"
) -> str:
    """
    Mix pre-segmented audio clips back to videos.
    
    Args:
        videos: Dict mapping scene_id to video path
        audio_clips: Dict mapping scene_id to audio clip path
        screenplay: Screenplay with scene order
        output_path: Path for final output video
    
    Returns:
        Path to final video
    """
    final_clips = []
    
    for scene in screenplay.scenes:
        scene_id = scene.scene_id
        
        if scene_id not in videos:
            continue
        
        # Load video
        video_clip = VideoFileClip(videos[scene_id])
        
        # Load corresponding audio
        if scene_id in audio_clips:
            audio_clip = AudioFileClip(audio_clips[scene_id])
            
            # Replace video audio with pre-generated audio
            video_clip = video_clip.set_audio(audio_clip)
        
        final_clips.append(video_clip)
    
    # Concatenate all clips
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Write final video
    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=24
    )
    
    return output_path
```

### Step 8: Complete Pipeline

```python
def audio_first_pipeline(screenplay: CinematgrapherCrewOutput) -> str:
    """
    Complete audio-first video generation pipeline.
    
    Args:
        screenplay: Input screenplay
    
    Returns:
        Path to final video
    """
    print("Step 1: Generating full voiceover audio...")
    audio_file = generate_full_voiceover(screenplay)
    
    print("Step 2: Transcribing with timestamps...")
    words = transcribe_with_timestamps(audio_file.path)
    
    print("Step 3: Detecting scene boundaries...")
    boundaries = detect_scene_boundaries(words, screenplay)
    
    print("Step 4: Segmenting audio into clips...")
    audio_clips = segment_audio(audio_file.path, boundaries)
    
    print("Step 5: Updating scene durations...")
    updated_screenplay = update_scene_durations(screenplay, boundaries)
    
    print("Step 6: Generating videos (silent/SFX only)...")
    videos = generate_silent_videos(updated_screenplay, audio_clips)
    
    print("Step 7: Mixing audio clips to videos...")
    final_video = mix_audio_to_videos(videos, audio_clips, updated_screenplay)
    
    print(f"Complete! Final video: {final_video}")
    return final_video
```

## Benefits

1. **Consistent Voice Quality**: 11Labs generates entire voiceover in one pass
2. **Automatic Timing**: No manual sync work needed
3. **Natural Pacing**: Audio timing drives video generation
4. **Reduced Latency**: Audio generation is fast, happens once upfront
5. **Flexible Editing**: Audio clips are pre-segmented for easy editing

## Considerations

1. **Audio Quality**: 11Labs audio must be high quality (no re-encoding)
2. **Transcription Accuracy**: Whisper/Gemini must accurately detect boundaries
3. **Veo Duration Limits**: Scenes must fit within 4-8 second Veo limits
4. **Pause Detection**: Algorithm must handle various pause patterns
5. **Scene Alignment**: Boundary detection must match script structure

## Alternative: Hybrid Approach

If you want to keep some Veo audio (SFX/ambient):

```python
def hybrid_audio_mix(
    veo_video_path: str,
    elevenlabs_audio_path: str,
    output_path: str
) -> str:
    """
    Mix 11Labs voiceover with Veo's SFX/ambient audio.
    """
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
    
    # Load video with Veo audio
    video = VideoFileClip(veo_video_path)
    veo_audio = video.audio
    
    # Load 11Labs voiceover
    vo_audio = AudioFileClip(elevenlabs_audio_path)
    
    # Reduce Veo audio volume (keep SFX/ambient at lower level)
    veo_audio = veo_audio.volumex(0.3)
    
    # Mix both audio tracks
    mixed_audio = CompositeAudioClip([veo_audio, vo_audio])
    
    # Set mixed audio to video
    final_video = video.set_audio(mixed_audio)
    
    # Export
    final_video.write_videofile(output_path)
    
    return output_path
```

This keeps Veo's natural SFX while using 11Labs for dialogue.
