import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from google import genai
from google.genai import types
from PIL import Image

logger = logging.getLogger(__name__)

# Type alias for image inputs
ImageInput = Union[Image.Image, bytes, bytearray, str, types.ImageDict]


class GeminiMediaGen:
    def __init__(self):
        self.client: genai.Client = genai.Client()

    # generators

    def generate_content(
        self,
        prompt: str,
        reference_image: Optional[ImageInput] = None,
    ):
        """
        Generate image content with optional reference image for consistency.

        Args:
            prompt: Text prompt for image generation
            reference_image: Optional reference image for character/environment consistency

        Returns:
            Response from Gemini image generation
        """
        logger.info("🎨 Generating image with Gemini")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        logger.debug(f"Reference image provided: {reference_image is not None}")

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
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, ref_img],
            )
            logger.info("✅ Image generated successfully with reference")

        else:
            # Generate without reference - single string is also valid PartUnionDict
            logger.info("📸 Calling Gemini without reference (seed generation)")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt,
            )
            logger.info("✅ Image generated successfully without reference")

        return response

    def _normalize_duration(self, dur: float) -> int:
        if dur < 5.0:
            return 4
        if dur < 7.0:
            return 6

        return 8

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

    def generate_video(
        self,
        prompt: str,
        image: Optional[ImageInput],
        last_image: Optional[ImageInput] = None,
        duration: Optional[float] = None,
    ):
        logger.info("🎬 Generating video with Gemini Veo")
        logger.debug(f"Prompt: {prompt[:100]}...")
        logger.debug(f"Duration: {duration}s")
        logger.debug(f"Has last_image: {last_image is not None}")

        config: types.GenerateVideosConfigDict = {
            # "generate_audio": False,
        }

        # Normalize image inputs to the expected API payload (for both image and last_frame)
        image_payload = self.to_api_image(image)
        last_image_payload = (
            self.to_api_image(last_image) if last_image is not None else None
        )

        if last_image_payload:
            config["last_frame"] = last_image_payload

        if duration:
            normalized_duration = self._normalize_duration(duration)
            config["duration_seconds"] = normalized_duration
            logger.debug(f"Normalized duration: {duration}s -> {normalized_duration}s")

        logger.info("📹 Calling Gemini Veo API...")
        response = self.client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
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

    def render_video(self, out_file: str, response):
        logger.debug(f"Rendering video to: {out_file}")

        while not response.done:
            logger.info("Waiting for video generation to complete...")
            time.sleep(10)
            response = self.client.operations.get(response)

        video = response.response.generated_videos[0]

        logger.info(f"Downloading video to: {out_file}")
        # Download the video file using the client
        video_data = self.client.files.download(file=video.video)

        # Write the downloaded data to file
        with open(out_file, "wb") as f:
            f.write(video_data)

        logger.info(f"💾 Video saved to: {out_file}")
        return out_file


def read_image_from_path(full_path: Path):
    image = Image.open(str(full_path))
    return image
