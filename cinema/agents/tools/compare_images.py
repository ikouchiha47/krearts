from typing import Any, List, Literal, Optional, Protocol

import imagehash
from crewai.tools.base_tool import BaseTool
from crewai.utilities import I18N
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from PIL import Image
from pydantic import BaseModel, Field

from cinema.providers.shared import MediaLib

i18n = I18N()


class AnalyzeImageToolSchema(BaseModel):
    image_urls: List[str] = Field(
        ...,
        description="List of image URLs to analyze",
    )
    action: Optional[str] = Field(
        default=None,
        description="Optional context or question about the images",
    )


class ImageAnalyzerTemplateProvider:
    def build_action(self, action: str, **kwargs):
        raise NotImplementedError

    def build_image(self, image_urls: list[str], **kwargs):
        raise NotImplementedError


class OpenAIImageBlockProvider(ImageAnalyzerTemplateProvider):
    def build_image(self, image_urls: list[str], **kwargs):
        from pathlib import Path
        
        encoded_images = kwargs.get("encoded_images", [])
        blocks = []
        
        for i, image_path in enumerate(image_urls):
            if i < len(encoded_images) and encoded_images[i]:
                blocks.append({
                    "type": "image",
                    "base64": encoded_images[i]["data"],
                    "mime_type": encoded_images[i]["mime_type"],
                })
            else:
                blocks.append({
                    "type": "image",
                    "url": image_path,
                })
        
        return blocks

    def build_action(self, action: str, **kwargs):
        return {
            "type": "text",
            "text": action,
        }


class AnthropicImageBlockProvider(ImageAnalyzerTemplateProvider):
    def build_image(self, image_urls: list[str], **kwargs):
        from pathlib import Path
        
        encoded_images = kwargs.get("encoded_images", [])
        blocks = []
        
        for i, image_path in enumerate(image_urls):
            if i < len(encoded_images) and encoded_images[i]:
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": encoded_images[i]["mime_type"],
                        "data": encoded_images[i]["data"],
                    },
                })
            else:
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": image_path,
                    },
                })
        
        return blocks

    def build_action(self, action: str, **kwargs):
        return {
            "type": "text",
            "text": action,
        }


_default_action = """
You are given two images.
List out the difference between them based on:
- colors
- lighting
- objects
- shot type
- environment/scene
- action (what is going on in the scene)
- verdict: summary of the comparison
"""

class ComparisonResults(BaseModel):
    message: str
    pscore: Any
    dscore: Any
    diff: int
    evaluator: Literal["llm", "compute"] = "llm"

class Comparator(Protocol):
    def run(
        self,
        image_urls: list[str],
        action: Optional[str] = None,
    ) -> ComparisonResults:
        ...

class CompareImagesWithLLM(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    model: str = "openai:gpt-4.1"
    chat_templ_provider: ImageAnalyzerTemplateProvider = OpenAIImageBlockProvider()
    args_schema: type[BaseModel] = AnalyzeImageToolSchema

    medialib: MediaLib
    allow_insecure: bool = False

    def run(
        self,
        image_urls: list[str],
        action: Optional[str] = None,
    ) -> ComparisonResults:
        from pathlib import Path
        from cinema.agents.tools.image_tools import ImageTools
        
        action = action or _default_action

        llm = init_chat_model(model=self.model)

        urls = self.medialib.images()

        if self.allow_insecure:
            urls.extend(image_urls)

        if len(urls) < 2:
            return ComparisonResults(
                message="Nothing To Compare",
                evaluator="llm",
                diff=-1,
                pscore=0,
                dscore=0,
            )

        # Encode local images using ImageTools
        encoded_images = []
        for url in urls:
            if Path(url).exists():
                encoded_images.append(ImageTools.encode_image_to_base64(url))
            else:
                encoded_images.append(None)
        
        prompt = ChatPromptTemplate(
            [
                {
                    "role": "user",
                    "content": [
                        *self.chat_templ_provider.build_image(urls, encoded_images=encoded_images),
                        self.chat_templ_provider.build_action(action),
                    ],
                },
            ]
        )

        chain = prompt | llm
        response = chain.invoke({"image_urls": urls})

        return ComparisonResults(
            message=response.text(),
            evaluator="llm",
            diff=0,
            pscore=0,
            dscore=0,
        )


class CompareImageHashes(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    medialib: MediaLib
    allow_insecure: bool = False
    phash_threshold: int = 10
    dhash_threshold: int = 10

    def run(
        self,
        image_urls: list[str],
        action: Optional[str] = None,
    ) -> ComparisonResults:
        
        urls = self.medialib.image_urls
        if self.allow_insecure:
            urls.extend(image_urls)

        if len(urls) < 2:
            return ComparisonResults(
                message="Nothing To Compare",
                evaluator="compute",
                diff=-1,
                pscore=0,
                dscore=0,
            )

        # Load images
        images = [Image.open(url) for url in urls[0:2]]
        
        # Calculate hashes
        phash_diff = self.phash(images)
        dhash_diff = self.dhash(images)
        
        # Determine similarity
        is_similar = (phash_diff <= self.phash_threshold and 
                     dhash_diff <= self.dhash_threshold)
        
        message = (
            f"Images are {'similar' if is_similar else 'different'}. "
            f"PHashScore: {phash_diff}, DHashScore: {dhash_diff}"
        )

        return ComparisonResults(
            message=message,
            evaluator="compute",
            diff=int(not is_similar),
            pscore=phash_diff,
            dscore=dhash_diff,
        )

    def phash(self, images: list) -> int:
        """Calculates phash difference between 2 images"""
        assert len(images) > 1, "InSufficientParameters"
        
        hash1 = imagehash.phash(images[0])
        hash2 = imagehash.phash(images[1])
        
        return hash1 - hash2

    def dhash(self, images: list) -> int:
        """Calculates dhash difference between 2 images"""
        assert len(images) > 1, "InSufficientParameters"
        
        hash1 = imagehash.dhash(images[0])
        hash2 = imagehash.dhash(images[1])
        
        return hash1 - hash2


class CompareImagesTool(BaseTool):
    """Tool for comparing two images"""

    name: str = "CompareImage"  # type: ignore
    description: str = (
        "See images to understand their content, you can optionally "
        "ask a question about the images"
    )
    # type: ignore

    model: str = "openai:gpt-4.1"
    chat_templ_provider: ImageAnalyzerTemplateProvider = OpenAIImageBlockProvider()
    args_schema: type[BaseModel] = AnalyzeImageToolSchema

    medialib: MediaLib
    allow_insecure: bool = False

    def _run(
        self,
        image_urls: list[str],
        action: Optional[str] = None,
        **kwargs,
    ) -> str:
        action = action or _default_action

        llm = init_chat_model(model=self.model)

        urls = self.medialib.images()

        if self.allow_insecure:
            urls.extend(image_urls)

        if len(urls) < 2:
            return "Nothing to compare"

        urls = urls[0:2]

        # Encode local images using ImageTools
        from pathlib import Path
        from cinema.agents.tools.image_tools import ImageTools
        
        encoded_images = []
        for url in urls:
            if Path(url).exists():
                encoded_images.append(ImageTools.encode_image_to_base64(url))
            else:
                encoded_images.append(None)
        
        prompt = ChatPromptTemplate(
            [
                {
                    "role": "user",
                    "content": [
                        *self.chat_templ_provider.build_image(urls, encoded_images=encoded_images),
                        self.chat_templ_provider.build_action(action),
                    ],
                },
            ]
        )

        chain = prompt | llm
        response = chain.invoke({"image_urls": urls})

        return response.text()
