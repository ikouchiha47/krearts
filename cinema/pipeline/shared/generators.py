"""
Content generators for pipeline stages.

All generators follow SOLID principles:
- SRP: Each generator has one responsibility
- OCP: Extend BaseGenerator without modifying it
- LSP: All generators can substitute BaseGenerator
- DIP: Depend on protocol abstractions, not concrete implementations

Shared by: movie_maker.py, detective_maker.py
"""

import asyncio
import json
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Optional, Protocol, TypeVar

from cinema.models.detective_output import CharacterProfile

logger = logging.getLogger(__name__)


async def generate_character_images_for_workflow(workflow_id: str, job_id: str):
    """Generate character images for a workflow from chapter data"""
    from cinema.pipeline.movie_maker import VisualCharacterBuilder
    from cinema.pipeline.state import PipelineState, JobType
    from cinema.jobs.storage import get_job_repository

    job_repo = get_job_repository()
    logger.info(f"Starting character generation for workflow {workflow_id} (job {job_id})")

    # Check if this is a forced regeneration (retry)
    job = job_repo.get(job_id)
    force_regenerate = job.metadata.get("force_regenerate", False) if job else False
    if force_regenerate:
        logger.info("  🔄 Force regeneration enabled - will overwrite existing images")

    try:
        # Get characters from database (parsed from storyline)
        from cinema.db.characters import CharacterStore
        from cinema.workflow.storyline_integration import StorylineIntegration
        
        store = CharacterStore()
        integration = StorylineIntegration()
        
        characters = store.get_all_characters(workflow_id)
        
        # Fallback: If characters not in DB, parse from storyline and save
        if not characters:
            logger.info(f"⚠️  No characters in database, parsing from storyline...")
            try:
                storyline = integration.get_storyline_from_db(workflow_id)
                parsed = integration.parse_and_store_characters(workflow_id, storyline)
                characters = parsed.characters
                logger.info(f"✅ Parsed and saved {len(characters)} characters")
            except Exception as e:
                raise ValueError(f"No characters found in database and failed to parse storyline: {e}")
        
        char_ids = store.get_character_ids(workflow_id)
        world_context = integration.get_world_context_text(workflow_id)
        
        logger.info(f"📚 Loaded {len(characters)} characters from database")
        logger.info(f"🌍 World context: {len(world_context)} chars")
        
        # Get art style from storyline metadata
        art_style = integration.get_art_style(workflow_id)
        logger.info(f"🎨 Art style: {art_style}")

        output_dir = Path("output") / workflow_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build character descriptions with full context
        character_description = []
        for char_id, character in zip(char_ids, characters):
            character_description.append({
                "id": char_id,
                "character_full_text": character.full_text,  # Full formatted character details
                "world_context": world_context,  # Full world era context
                "art_style": art_style,
            })

        state = PipelineState(
            movie_id=workflow_id,
            base_dir=output_dir,
            characters_dir=output_dir / "characters",
            images_dir=output_dir / "images",
            videos_dir=output_dir / "videos",
            audio_dir=output_dir / "audio",
            output_dir=output_dir / "final",
            screenplay_dict={"character_description": character_description},
        )
        state.ensure_directories()

        from cinema.pipeline.state import Job as PipelineJob
        import uuid

        for char_desc in character_description:
            char_id = char_desc["id"]  # Use proper ID format from database
            for view in ["front", "side", "full_body", "back"]:
                job = PipelineJob(
                    id=str(uuid.uuid4()),
                    type=JobType.CHARACTER,
                    character_id=char_id,
                    metadata={"view": view, "force_regenerate": force_regenerate},
                )
                state.add_job(job)

        builder = VisualCharacterBuilder()
        await builder.run(state)

        # Save generated images using repository
        from cinema.comics.character_storage import get_character_image_repository
        
        char_repo = get_character_image_repository()
        characters_dir = output_dir / "characters"
        
        # Find all generated character images
        for char_id, character in zip(char_ids, characters):
            character_name = character.name.replace(" ", "_")
            
            # Save each view type (including collage)
            for view in ['front', 'side', 'full_body', 'back', 'collage']:
                image_path = characters_dir / f"{char_id}_{view}.png"
                if image_path.exists():
                    char_repo.save_character_image(
                        workflow_id=workflow_id,
                        character_id=char_id,  # Use proper ID format
                        character_name=character.name,
                        view_type=view,
                        image_path=str(image_path)
                    )

        job = job_repo.get(job_id)
        if job:
            job.status = "completed"
            job.metadata = {"characters_generated": len(characters)}
            job_repo.save(job)
        
        logger.info(f"✅ Character generation complete for {workflow_id}")

    except Exception as e:
        job = job_repo.get(job_id)
        if job:
            job.status = "failed"
            job.error = str(e)
            job_repo.save(job)
        logger.exception("Character generation failed")


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
