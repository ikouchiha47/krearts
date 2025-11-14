"""
Content generators for pipeline stages.

All generators follow SOLID principles:
- SRP: Each generator has one responsibility
- OCP: Extend BaseGenerator without modifying it
- LSP: All generators can substitute BaseGenerator
- DIP: Depend on protocol abstractions, not concrete implementations

Shared by: movie_maker.py, detective_maker.py
"""

# import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Protocol, TypeVar

from cinema.models.detective_output import CharacterProfile

logger = logging.getLogger(__name__)


class RateLimiterProtocol(Protocol):
    """Protocol for rate limiting"""

    async def acquire(self, resource: str) -> None: ...


class ImageGeneratorProtocol(Protocol):
    """Protocol for image generation"""

    async def generate_content(self, prompt: str, **kwargs) -> Any: ...


class PromptTransformerProtocol(Protocol):
    """
    Protocol for transforming models to prompts.

    This allows injecting different transformers for different domains:
    - ComicCharacterTransformer: For comic book characters
    - MovieCharacterTransformer: For movie character sheets
    - GameCharacterTransformer: For game character designs
    - etc.

    Strategy Pattern: Encapsulates prompt generation algorithms
    """

    def transform(self, model: Any, **kwargs) -> str:
        """Transform a model (Pydantic, dict, etc.) into a prompt string"""
        ...


# ============================================================================
# BASE GENERATOR
# ============================================================================

T = TypeVar("T")


class BaseGenerator(ABC, Generic[T]):
    """
    content generator.
    """

    def __init__(self, rate_limiter: Optional[RateLimiterProtocol] = None):
        self.rate_limiter = rate_limiter

    @abstractmethod
    async def generate(self, **kwargs) -> T:
        """Generate content. Subclasses must implement."""
        pass

    async def _acquire_rate_limit(self, resource: str) -> None:
        """Acquire rate limit if configured"""
        if self.rate_limiter:
            await self.rate_limiter.acquire(resource)


class CharacterReferenceGenerator(BaseGenerator[Any]):
    """
    Generates character reference images for consistent appearance:
    - Inject ComicCharacterTransformer for comics
    - Inject MovieCharacterTransformer for movies
    - Inject GameCharacterTransformer for games

    Used by: detective_maker (comics), movie_maker (character sheets)
    """

    def __init__(
        self,
        image_generator: ImageGeneratorProtocol,
        transformer: PromptTransformerProtocol,
        rate_limiter: Optional[RateLimiterProtocol] = None,
    ):
        super().__init__(rate_limiter)
        self.image_generator = image_generator
        self.transformer = transformer

    async def generate(
        self,
        character: Any,  # Can be any model (CharacterProfile, dict, custom model, etc.)
        **kwargs,
    ) -> Any:
        """Generate character reference image using injected transformer"""
        await self._acquire_rate_limit("character-reference")

        # Use transformer to convert model to prompt (Strategy Pattern)
        prompt = self.transformer.transform(character, **kwargs)
        logger.info(f"Character prompt: {prompt}...")

        # return True
        return await self.image_generator.generate_content(prompt=prompt)

        # No more _build_prompt - delegated to transformer!
        # prompt += "Neutral expression, standing pose, plain background. "
        # prompt += "Professional character design. High quality, detailed illustration."

        # return prompt


class SimpleImageGenerator(BaseGenerator[Any]):
    """
    Generates images from text prompts (no character composition).
    """

    def __init__(
        self,
        image_generator: ImageGeneratorProtocol,
        rate_limiter: Optional[RateLimiterProtocol] = None,
    ):
        super().__init__(rate_limiter)
        self.image_generator = image_generator

    async def generate(self, prompt: str, **kwargs) -> Any:
        """Generate image from text prompt"""
        await self._acquire_rate_limit("simple-image")

        logger.info(f"Image prompt: {prompt}...")
        # return True
        return await self.image_generator.generate_content(prompt=prompt)
