import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional, Union

from google import genai
from google.genai import types
from google.genai.types import Image as RefImage
from PIL import Image

from cinema.utils.rate_limiter import RateLimiterManager

logger = logging.getLogger(__name__)

# Type alias for image inputs
ImageInput = Union[Image.Image, bytes, bytearray, str, types.ImageDict]


class GeminiMediaGen:
    def __init__(self, rate_limiter: Optional[RateLimiterManager] = None):
        self.client: genai.Client = genai.Client()
        self.rate_limiter = rate_limiter or RateLimiterManager()

    # generators

    async def generate_content(
        self,
        prompt: str,
        reference_image: Optional[ImageInput] = None,
        aspect_ratio: Optional[str] = "4:5",
        **kwargs: Any
    ) -> types.GenerateContentResponse:
        """
        Generate image content with optional reference image for consistency.

        Args:
            prompt: Text prompt for image generation
            reference_image: Optional reference image for character/environment consistency
            aspect_ratio: Aspect ratio for generated image (default: "4:5" for portrait)

        Returns:
            Response from Gemini image generation
        """
        # Rate limit
        await self.rate_limiter.acquire("gemini-2.5-flash-image")

        logger.info("🎨 Generating image with Gemini")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        logger.debug(f"Reference image provided: {reference_image is not None}")
        logger.debug(f"Aspect ratio: {aspect_ratio}")

        if reference_image is not None:
            # Convert to PIL Image - contents needs PIL_Image, not ImageDict
            logger.debug("Converting reference image to PIL Image")

            if isinstance(reference_image, Image.Image):
                logger.debug("Reference is already PIL Image")
                ref_img = reference_image

            else:
                logger.debug(
                    f"Converting reference from type: {type(reference_image).__name__}"
                )

                # Use to_api_image to normalize, then convert back to PIL
                image_dict = self.to_api_image(reference_image)

                if image_dict and "image_bytes" in image_dict:
                    image_bytes = image_dict["image_bytes"]
                    if not image_bytes:
                        raise ValueError("ImageDict has empty image_bytes")

                    ref_img = Image.open(BytesIO(image_bytes))
                else:
                    raise ValueError("Failed to convert reference_image")

            # contents is list[PartUnionDict] where PartUnionDict = str | PIL_Image | ...
            # So we pass [str, PIL_Image] as list of parts
            logger.info("📸 Calling Gemini with reference image for consistency")
            logger.info(f"Prompt: {prompt}")
            
            # Build config with aspect ratio
            image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
            config = types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                image_config=image_config,
            )
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-2.5-flash-image",
                contents=[prompt, ref_img],
                config=config,
            )
            logger.info("✅ Image generated successfully with reference")

        else:
            # Generate without reference - single string is also valid PartUnionDict
            logger.info("📸 Calling Gemini without reference (seed generation)")
            
            # Build config with aspect ratio
            image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
            config = types.GenerateContentConfig(
                response_modalities=[types.Modality.IMAGE],
                image_config=image_config,
            )
            
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-2.5-flash-image",
                contents=prompt,
                config=config,
            )
            logger.info("✅ Image generated successfully without reference")

        return response

    async def generate_content_with_images(
        self, 
        images: list[Image.Image], 
        prompt: str, 
        aspect_ratio: Optional[str] = "9:16",
        **kwargs: Any
    ) -> types.GenerateContentResponse:
        """
        Generate image content using multiple reference images (ingredients to image).

        This is used for composing scenes with multiple character references.

        Args:
            images: List of PIL Images to use as references
            prompt: Text prompt for image generation
            **kwargs: Additional arguments (currently unused)

        Returns:
            Response from Gemini image generation
        """
        # Rate limit
        await self.rate_limiter.acquire("gemini-2.5-flash-image")

        logger.info(
            "🎨 Generating image with multiple references (ingredients to image)"
        )
        logger.debug(f"Number of reference images: {len(images)}")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        # Verify all images are PIL Images
        for i, img in enumerate(images):
            if not isinstance(img, Image.Image):
                logger.error(f"Image {i} is not a PIL Image: {type(img).__name__}")
                raise TypeError(f"Expected PIL Image, got {type(img).__name__}")

        # Build contents list: [prompt, image1, image2, ...]
        # contents is list[PartUnionDict] where PartUnionDict = str | PIL_Image | ...
        # contents = [prompt] + images

        logger.debug(f"Full prompt: {prompt}")

        image_config = types.ImageConfig(
            aspect_ratio=aspect_ratio,
        )
        config = types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE],
            image_config=image_config,
        )

        logger.info(f"📸 Calling Gemini with {len(images)} reference images")
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model="gemini-2.5-flash-image",
            contents=[prompt, *images],
            config=config,
        )
        logger.info("✅ Image generated successfully with multiple references")

        return response

    def _normalize_duration(self, dur: float) -> int:
        if dur < 3.0:
            return 2
        if dur < 5.0:
            return 4
        if dur < 7.0:
            return 6

        return 8

    async def detect_objects(
        self,
        image: ImageInput,
        labels: List[str],
        **kwargs: Any
    ) -> List[dict]:
        """
        Detect bounding boxes for specified objects in an image using Gemini.

        Args:
            image: Image to analyze (PIL Image, bytes, or path)
            labels: List of object labels to detect (e.g., ["Jack's face", "cigarette butt"])

        Returns:
            List of detected objects with bounding boxes:
            [
                {
                    "label": "Jack's face",
                    "box_2d": [y_min, x_min, y_max, x_max],
                    "confidence": 0.95
                },
                ...
            ]
        """
        # Rate limit
        await self.rate_limiter.acquire("gemini-2.0-flash-exp")

        logger.info(f"🔍 Detecting objects in image: {labels}")

        # Convert image to PIL if needed
        if isinstance(image, Image.Image):
            pil_image = image
        elif isinstance(image, (bytes, bytearray)):
            pil_image = Image.open(BytesIO(image))
        elif isinstance(image, str):
            pil_image = Image.open(image)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Get image dimensions for normalization
        img_width, img_height = pil_image.size

        # Build detection prompt
        labels_str = ", ".join([f'"{label}"' for label in labels])
        prompt = f"""Analyze this comic book panel image and identify the bounding boxes for these objects: {labels_str}.

For each object you can identify, provide:
1. The object label (exactly as provided)
2. Bounding box coordinates as [y_min, x_min, y_max, x_max] where:
   - Coordinates are normalized to 0-1000 range
   - [0, 0] is top-left corner
   - [1000, 1000] is bottom-right corner
3. Confidence score (0.0 to 1.0)

Return ONLY a JSON array with this structure:
[
  {{"label": "object name", "box_2d": [y_min, x_min, y_max, x_max], "confidence": 0.95}},
  ...
]

If an object is not visible or cannot be identified, omit it from the results.
Be precise with bounding boxes - they should tightly fit the object."""

        # Call Gemini for object detection
        config = types.GenerateContentConfig(
            response_modalities=[types.Modality.TEXT],
        )

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model="gemini-2.0-flash-exp",
            contents=[prompt, pil_image],
            config=config,
        )

        # Parse response
        response_text = (response.text or "").strip()
        logger.debug(f"Detection response: {response_text}")

        # Extract JSON from response (handle markdown code blocks)
        import json
        import re

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                logger.warning("No JSON array found in response")
                return []

        try:
            detections = json.loads(json_str)
            logger.info(f"✅ Detected {len(detections)} objects")
            return detections
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse detection response: {e}")
            logger.error(f"Response text: {response_text}")
            return []

    # helpers
    @staticmethod
    def to_api_image(img: Optional[ImageInput]) -> Optional[types.ImageDict]:
        """Normalize various image inputs to Google GenAI expected payload.

        Returns ImageDict with keys (mime_type, image_bytes) or None.
        """
        if img is None:
            return None

        # already properly typed
        if isinstance(img, dict):
            return img

        if isinstance(img, Image.Image):
            buf = BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            payload: types.ImageDict = {
                "mime_type": "image/png",
                "image_bytes": data,
            }
            return payload

        if isinstance(img, (bytes, bytearray)):
            payload: types.ImageDict = {
                "mime_type": "image/png",
                "image_bytes": bytes(img),
            }
            return payload

        if isinstance(img, str):  # assume path
            logger.debug(f"Loading image from path: {img}")
            with open(img, "rb") as f:
                data = f.read()

            payload: types.ImageDict = {
                "mime_type": "image/png",
                "image_bytes": data,
            }
            return payload

        # Unrecognized type
        logger.warning(f"Unrecognized image type: {type(img).__name__}")
        return None

    async def generate_video(
        self,
        prompt: str,
        image: Optional[ImageInput] = None,
        last_image: Optional[ImageInput] = None,
        reference_images: Optional[List[ImageInput]] = None,
        duration: Optional[float] = None,
    ):
        # Rate limit
        await self.rate_limiter.acquire("veo-3.1-generate-preview")

        logger.info(f"🐟🐟🐟🐟 dsfsfsfsfd {image}")
        logger.info("🎬 Generating video with Gemini Veo")
        logger.debug(f"Prompt: {prompt}...")
        logger.debug(f"Duration: {duration}s")
        logger.debug(f"Has image: {image is not None}")
        logger.debug(f"Has last_image: {last_image is not None}")
        logger.debug(f"Has reference_images: {reference_images is not None}")

        # Normalize image inputs
        image_payload = self.to_api_image(image) if image else None
        last_image_payload = self.to_api_image(last_image) if last_image else None

        # Build config
        config_kwargs = {}

        if last_image_payload:
            config_kwargs["last_frame"] = last_image_payload
            logger.debug("Added last_frame to config for interpolation")

        if reference_images:
            ref_list = []
            for ref_img in reference_images:
                ref_payload = self.to_api_image(ref_img)
                assert ref_payload is not None, "RefImageLoadFailed"

                ref_list.append(
                    types.VideoGenerationReferenceImage(
                        image=RefImage(**ref_payload),
                        reference_type=types.VideoGenerationReferenceType.ASSET,
                    )
                )

            config_kwargs["reference_images"] = ref_list
            logger.debug(f"Added {len(ref_list)} reference images")

        if duration:
            normalized_duration = self._normalize_duration(duration)
            config_kwargs["duration_seconds"] = normalized_duration
            logger.debug(f"Normalized duration: {duration}s -> {normalized_duration}s")

        config = types.GenerateVideosConfig(**config_kwargs) if config_kwargs else None

        logger.info("📹 Calling Gemini Veo API...")
        logger.debug("Model: veo-3.1-generate-preview")
        logger.debug(f"Has image: {image_payload is not None}")
        logger.debug(f"Has last_frame: {last_image_payload is not None}")
        logger.debug(
            f"Has reference_images: {len(config_kwargs.get('reference_images', [])) if 'reference_images' in config_kwargs else 0}"
        )

        response = await asyncio.to_thread(
            self.client.models.generate_videos,
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=image_payload,
            config=config,
        )
        logger.info("✅ Video generation initiated")

        return response

    # renderers

    def render_image(self, out_file: str, response):
        logger.debug(f"Rendering image to: {out_file}")
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)

            elif part.inline_data is not None:
                img = Image.open(BytesIO(part.inline_data.data))
                img.save(out_file)
                logger.info(f"💾 Image saved to: {out_file}")
                return img

        logger.error("Failed to render image")
        raise Exception("render_failed")

    async def render_video(self, out_file: str, response):
        logger.debug(f"Rendering video to: {out_file}")

        while not response.done:
            logger.info("Waiting for video generation to complete...")
            await asyncio.sleep(10)
            response = await asyncio.to_thread(self.client.operations.get, response)

        video = response.response.generated_videos[0]

        logger.info(f"Downloading video to: {out_file}")
        # Download the video file using the client
        video_data = await asyncio.to_thread(
            self.client.files.download, file=video.video
        )

        # Write the downloaded data to file
        with open(out_file, "wb") as f:
            f.write(video_data)

        logger.info(f"💾 Video saved to: {out_file}")
        return out_file


def read_image_from_path(full_path: Path):
    image = Image.open(str(full_path))
    return image
