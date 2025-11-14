"""
Content composers for multi-image generation.

Composers handle complex image generation that requires multiple inputs,
such as combining character references with scene descriptions.

All composers follow SOLID principles:
- SRP: Each composer has one responsibility
- OCP: Extend BaseGenerator without modifying it
- LSP: All composers can substitute BaseGenerator
- DIP: Depend on protocol abstractions

Shared by: movie_maker.py, detective_maker.py
"""

import logging
from typing import Any, List, Optional, Protocol, Union

from PIL import Image

from cinema.models.detective_output import PanelPrompt
from cinema.pipeline.shared.generators import BaseGenerator, RateLimiterProtocol

logger = logging.getLogger(__name__)

# ============================================================================
# PROTOCOLS (Dependency Inversion Principle)
# ============================================================================

class MultiImageComposerProtocol(Protocol):
    """Protocol for multi-image composition ("ingredients to image")"""
    async def generate_content_with_images(
        self, 
        images: List[Image.Image], 
        prompt: str,
        **kwargs
    ) -> Any:
        ...


# ============================================================================
# PANEL COMPOSER (Comic Book Panels)
# ============================================================================

class PanelComposer(BaseGenerator[Any]):
    """
    Composes comic panels using character references.
    
    Uses Strategy Pattern with injected transformer for domain-specific prompts.
    Uses Gemini's "ingredients to image" feature to combine:
    - Character reference images
    - Scene description
    - Art style
    
    SOLID Principles:
    - SRP: Only composes comic panels
    - OCP: Extends BaseGenerator, accepts any transformer
    - LSP: Can substitute BaseGenerator
    - DIP: Depends on protocols (MultiImageComposerProtocol, PromptTransformerProtocol)
    
    Strategy Pattern:
    - Inject ComicPanelTransformer for comics
    - Inject MovieSceneTransformer for movies
    
    Used by: detective_maker (comic panels), movie_maker (scene keyframes)
    """
    
    def __init__(
        self,
        composer: MultiImageComposerProtocol,
        transformer: 'PromptTransformerProtocol',  # Forward reference
        rate_limiter: Optional[RateLimiterProtocol] = None
    ):
        super().__init__(rate_limiter)
        self.composer = composer
        self.transformer = transformer
    
    async def generate(
        self,
        panel: Any,  # Can be any model (PanelPrompt, SceneDescription, dict, etc.)
        character_images: List[Image.Image],
        character_names: List[str],
        **kwargs
    ) -> Any:
        """Compose panel with character references using injected transformer"""
        await self._acquire_rate_limit("panel-composition")
        
        # Use transformer to convert model to prompt (Strategy Pattern)
        prompt = self.transformer.transform(panel, character_names=character_names, **kwargs)
        logger.debug(f"Panel composition prompt: {prompt[:100]}...")
        
        return await self.composer.generate_content_with_images(
            images=character_images,
            prompt=prompt
        )
    # No more _build_composition_prompt - delegated to transformer!


# ============================================================================
# SCENE COMPOSER (Movie Scenes)
# ============================================================================

class SceneComposer(BaseGenerator[Any]):
    """
    Composes movie scenes using character references and scene descriptions.
    
    Uses Strategy Pattern with injected transformer for domain-specific prompts.
    Similar to PanelComposer but optimized for cinematic scenes.
    
    SOLID Principles:
    - SRP: Only composes movie scenes
    - OCP: Extends BaseGenerator, accepts any transformer
    - LSP: Can substitute BaseGenerator
    - DIP: Depends on protocols (MultiImageComposerProtocol, PromptTransformerProtocol)
    
    Strategy Pattern:
    - Inject MovieSceneTransformer for movies
    - Inject different transformers for different cinematic styles
    
    Used by: movie_maker (scene keyframes)
    """
    
    def __init__(
        self,
        composer: MultiImageComposerProtocol,
        transformer: 'PromptTransformerProtocol',  # Forward reference
        rate_limiter: Optional[RateLimiterProtocol] = None
    ):
        super().__init__(rate_limiter)
        self.composer = composer
        self.transformer = transformer
    
    async def generate(
        self,
        scene: Any,  # Can be any model (SceneDescription, dict, string, etc.)
        character_images: List[Image.Image],
        character_names: List[str],
        **kwargs
    ) -> Any:
        """Compose cinematic scene with character references using injected transformer"""
        await self._acquire_rate_limit("scene-composition")
        
        # Use transformer to convert model to prompt (Strategy Pattern)
        prompt = self.transformer.transform(scene, character_names=character_names, **kwargs)
        logger.debug(f"Scene composition prompt: {prompt[:100]}...")
        
        return await self.composer.generate_content_with_images(
            images=character_images,
            prompt=prompt
        )
    # No more _build_scene_prompt - delegated to transformer!
