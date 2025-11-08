from typing import List, Optional

from crewai.tools.base_tool import BaseTool
from crewai.utilities import I18N
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
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
        return [
            {
                "type": "image",
                "url": image_url,
            }
            for image_url in image_urls
        ]

    def build_action(self, action: str, **kwargs):
        return {
            "type": "text",
            "text": action,
        }


class AnthropicImageBlockProvider(ImageAnalyzerTemplateProvider):
    def build_image(self, image_urls: list[str], **kwargs):
        return [
            {
                "type": "image",
                "source": {
                    "type": "url",
                    "url": image_url,
                },
            }
            for image_url in image_urls
        ]

    def build_action(self, action: str, **kwargs):
        return {
            "type": "text",
            "text": action,
        }


_default_action = """
Please generate a detailed description from given list of images,
including all visual elements, context, and any notable details
you can observe.

## Guidelines for Image Analysis:
- If the detected image is a person, generate a description of the person which describes their age, race, appearance, and hair.
- If the detected image is a product, generate details describing the product, brand, name and other marketing relevant details.
- If multiple objects (e.g., person and product) are present, describe each separately, ensuring the person's description is detailed for character extraction, and the product description covers all marketing-relevant elements.
- If the detected image is something else, generate general details.

"""


class AnalyzeImagesTool(BaseTool):
    """Tool for adding images to the content"""

    name: str = "AnalyzeImage"  # type: ignore
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

        prompt = ChatPromptTemplate(
            [
                {
                    "role": "user",
                    "content": [
                        *self.chat_templ_provider.build_image(urls),
                        self.chat_templ_provider.build_action(action),
                    ],
                },
            ]
        )

        chain = prompt | llm
        response = chain.invoke({"image_urls": image_urls})

        return response.text()
