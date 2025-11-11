"""
Character Reference Manager with Seeding Chain

Manages character reference image generation using a seeding chain pattern
where the front view acts as the canonical reference for all subsequent
character-related image generations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from cinema.providers.gemini import GeminiMediaGen

logger = logging.getLogger(__name__)


class CharacterReferenceManager:
    """
    Manages character reference generation with seeding chain.

    The seeding chain ensures consistent character appearance:
    1. Generate front view (canonical, no reference)
    2. Generate side view (seeded from front)
    3. Generate full_body (seeded from front)
    4. All future generations use front as reference
    """

    def __init__(self, gemini_client: GeminiMediaGen):
        """
        Initialize CharacterReferenceManager.

        Args:
            gemini_client: GeminiMediaGen instance for image generation
        """
        self.gemini = gemini_client
        self.character_cache: Dict[str, Dict[str, str]] = {}
        # Structure: {char_id: {"front": path, "side": path, "full_body": path}}

        logger.info("CharacterReferenceManager initialized")

    async def generate_character_references(
        self,
        character_id: str,
        character_description: Dict[str, Any],
        output_dir: str,
        include_back_view: bool = True,
    ) -> Dict[str, str]:
        """
        Generate all character reference views using seeding chain.

        Seeding chain:
        1. Front view - (canonical) - no reference
        2. Full view - seeded from front
        3. Side view - seeded from front
        4. Back view - seeded from front (optional)

        Args:
            character_id: Unique character identifier
            character_description: Character metadata with keys:
                - physical_appearance: str
                - style: str
            output_dir: Directory to save reference images
            include_back_view: Whether to generate back view (default: True)

        Returns:
            Dict mapping view -> image_path
            Example: {"front": "...", "side": "...", "full_body": "...", "back": "..."}
        """
        logger.info(f"🎭 Generating character references for {character_id}")
        logger.info("   Using seeding chain pattern")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # Step 1: Generate front view (canonical, no reference)
        logger.info("📸 Step 1/3: Generating canonical front view")
        front_prompt = self._build_character_prompt(
            character_description,
            view="front",
        )
        logger.debug(f"Front view prompt: {front_prompt[:100]}...")

        front_response = await self.gemini.generate_content(
            prompt=front_prompt,
            reference_image=None,
            # No reference for canonical view
        )

        front_path = str(output_path / f"{character_id}_front.png")
        self.gemini.render_image(front_path, front_response)
        results["front"] = front_path

        logger.info(f"✅ Front view saved: {front_path}")

        # Step 2: Generate side view (seeded from front)
        logger.info("📸 Step 2/3: Generating side view (seeded from front)")
        side_prompt = self._build_character_prompt(
            character_description,
            view="side",
        )
        logger.debug(f"Side view prompt: {side_prompt[:100]}...")
        logger.debug(f"Using reference: {front_path}")

        side_response = await self.gemini.generate_content(
            prompt=side_prompt,
            reference_image=front_path,  # ← Seeded from front
        )

        side_path = str(output_path / f"{character_id}_side.png")
        self.gemini.render_image(side_path, side_response)
        results["side"] = side_path

        logger.info(f"✅ Side view saved: {side_path}")

        # Step 3: Generate full body (seeded from front)
        logger.info("📸 Step 3/3: Generating full body (seeded from front)")
        full_body_prompt = self._build_character_prompt(
            character_description,
            view="full_body",
        )
        logger.debug(f"Full body prompt: {full_body_prompt[:100]}...")
        logger.debug(f"Using reference: {front_path}")

        full_body_response = await self.gemini.generate_content(
            prompt=full_body_prompt,
            reference_image=front_path,
        )

        full_body_path = str(output_path / f"{character_id}_full_body.png")
        self.gemini.render_image(full_body_path, full_body_response)
        results["full_body"] = full_body_path

        logger.info(f"✅ Full body saved: {full_body_path}")

        include_back_view = True

        # Step 4: Generate back view (seeded from front) - OPTIONAL
        if include_back_view:
            logger.info("📸 Step 4/4: Generating back view (seeded from front)")
            back_prompt = self._build_character_prompt(
                character_description, view="back"
            )
            logger.debug(f"Back view prompt: {back_prompt[:100]}...")
            logger.debug(f"Using reference: {front_path}")

            back_response = await self.gemini.generate_content(
                prompt=back_prompt,
                reference_image=front_path,
            )

            back_path = str(output_path / f"{character_id}_back.png")
            self.gemini.render_image(back_path, back_response)
            results["back"] = back_path

            logger.info(f"✅ Back view saved: {back_path}")

        # Cache for future use
        self.character_cache[character_id] = results
        logger.info(f"💾 Cached references for {character_id}")

        return results

    def _build_character_prompt(
        self, character_description: Dict[str, Any], view: str
    ) -> str:
        """
        Build character reference prompt for specific view.

        Args:
            character_description: Character metadata
            view: One of "front", "side", "full_body"

        Returns:
            Formatted prompt string
        """
        appearance = character_description.get("physical_appearance", "")
        style = character_description.get("style", "")

        base = f"{appearance}, {style}"

        if view == "front":
            return f"""Neutral portrait photograph of {base}. 
Front view, centered, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K."""

        elif view == "side":
            return f"""Side profile photograph of {base}. 
90-degree side view, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view."""

        elif view == "full_body":
            return f"""Full body photograph of {base}. 
Standing pose, front view, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view."""

        elif view == "back":
            return f"""Back view photograph of {base}. 
Rear view showing back of head and shoulders, neutral pose, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view (hair, clothing, build)."""

        else:
            raise ValueError(f"Unknown view type: {view}")

    async def generate_keyframe_with_character(
        self, scene_prompt: str, character_id: str, output_path: str
    ) -> str:
        """
        Generate scene keyframe with character consistency.

        Uses the cached front view as reference to ensure character
        appearance matches across all scenes.

        Args:
            scene_prompt: Scene-specific prompt (e.g., "Alex walking in Tokyo...")
            character_id: Character identifier (must be in cache)
            output_path: Path to save generated keyframe

        Returns:
            Path to generated keyframe image

        Raises:
            ValueError: If character_id not in cache
        """
        if character_id not in self.character_cache:
            raise ValueError(
                f"Character {character_id} not in cache. "
                f"Call generate_character_references() first."
            )

        front_ref = self.character_cache[character_id]["front"]

        logger.info("📸 Generating keyframe with character consistency")
        logger.debug(f"   Scene prompt: {scene_prompt[:100]}...")
        logger.debug(f"   Character reference: {front_ref}")

        response = await self.gemini.generate_content(
            prompt=scene_prompt, reference_image=front_ref  # ← Use canonical front view
        )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        self.gemini.render_image(output_path, response)
        logger.info(f"✅ Keyframe saved: {output_path}")

        return output_path

    async def generate_moodboard_with_character(
        self,
        scene_description: str,
        character_id: str,
        output_path: str,
    ) -> str:
        """
        Generate scene-specific moodboard with character.

        Creates a moodboard image that combines the scene environment
        with the character, maintaining character consistency through
        the front view reference.

        Args:
            scene_description: Scene/environment description
                Example: "Tokyo Shibuya crossing at night, neon lights, rainy pavement"
            character_id: Character identifier (must be in cache)
            output_path: Path to save generated moodboard

        Returns:
            Path to generated moodboard image

        Raises:
            ValueError: If character_id not in cache
        """
        if character_id not in self.character_cache:
            raise ValueError(
                f"Character {character_id} not in cache. "
                f"Call generate_character_references() first."
            )

        front_ref = self.character_cache[character_id]["front"]

        logger.info("🎨 Generating moodboard with character consistency")
        logger.debug(f"   Scene description: {scene_description[:100]}...")
        logger.debug(f"   Character reference: {front_ref}")

        response = await self.gemini.generate_content(
            prompt=scene_description,
            reference_image=front_ref,  # ← Character-consistent moodboard
        )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        self.gemini.render_image(output_path, response)
        logger.info(f"✅ Moodboard saved: {output_path}")

        return output_path

    def get_canonical_reference(self, character_id: str) -> str:
        """
        Get the canonical (front view) reference for a character.

        The front view is the canonical reference used for all
        character-consistent image and video generation.

        Args:
            character_id: Character identifier

        Returns:
            Path to front view reference image

        Raises:
            ValueError: If character_id not in cache
        """
        if character_id not in self.character_cache:
            raise ValueError(
                f"Character {character_id} not in cache. "
                f"Call generate_character_references() first."
            )

        return self.character_cache[character_id]["front"]

    def get_all_references(self, character_id: str) -> Dict[str, str]:
        """
        Get all reference views for a character.

        Args:
            character_id: Character identifier

        Returns:
            Dict mapping view -> image_path
            Example: {"front": "...", "side": "...", "full_body": "..."}

        Raises:
            ValueError: If character_id not in cache
        """
        if character_id not in self.character_cache:
            raise ValueError(
                f"Character {character_id} not in cache. "
                f"Call generate_character_references() first."
            )

        return self.character_cache[character_id].copy()

    def has_character(self, character_id: str) -> bool:
        """
        Check if character references are cached.

        Args:
            character_id: Character identifier

        Returns:
            True if character is in cache, False otherwise
        """
        return character_id in self.character_cache

    def get_cached_characters(self) -> list[str]:
        """
        Get list of all cached character IDs.

        Returns:
            List of character IDs
        """
        return list(self.character_cache.keys())

    def clear_cache(self):
        """Clear all cached character references."""
        self.character_cache.clear()
        logger.info("Character cache cleared")

    def get_reference_for_shot(self, character_id: str, shot_description: str) -> str:
        """
        Select the appropriate character reference based on shot description.

        Intelligently selects front/side/back/full_body based on keywords
        in the shot description.

        Args:
            character_id: Character identifier
            shot_description: Description of the shot (e.g., "POV from behind")

        Returns:
            Path to the most appropriate reference view

        Raises:
            ValueError: If character_id not in cache
        """
        if character_id not in self.character_cache:
            raise ValueError(
                f"Character {character_id} not in cache. "
                f"Call generate_character_references() first."
            )

        refs = self.character_cache[character_id]
        shot_lower = shot_description.lower()

        # Check for back/behind shots
        back_keywords = [
            "from behind",
            "back view",
            "rear view",
            "pov",
            "following",
            "walks away",
            "over shoulder",
            "behind",
        ]
        if any(keyword in shot_lower for keyword in back_keywords):
            if "back" in refs:
                logger.info(f"🎯 Using back view for: {shot_description[:50]}...")
                return refs["back"]
            else:
                logger.warning("⚠️  Back view requested but not available, using front")

        # Check for side shots
        side_keywords = ["side view", "profile", "side angle", "90 degree", "side shot"]
        if any(keyword in shot_lower for keyword in side_keywords):
            logger.info(f"🎯 Using side view for: {shot_description[:50]}...")
            return refs["side"]

        # Check for full body shots
        full_body_keywords = [
            "full body",
            "wide shot",
            "establishing",
            "full figure",
            "full shot",
        ]
        if any(keyword in shot_lower for keyword in full_body_keywords):
            logger.info(f"🎯 Using full body for: {shot_description[:50]}...")
            return refs["full_body"]

        # Default to front view (canonical)
        logger.info(f"🎯 Using front view (default) for: {shot_description[:50]}...")
        return refs["front"]

    async def generate_from_screenplay(
        self, screenplay: Dict[str, Any], output_dir: str
    ) -> Dict[int, Dict[str, str]]:
        """
        Generate character references based on enhanced screenplay.

        Reads required_views from character description (populated by ScreenplayEnhancer).
        Generates only the views that are actually needed.

        Args:
            screenplay: Enhanced screenplay with required_views in character_description
            output_dir: Directory to save reference images

        Returns:
            Dict mapping character_id -> {view: path}
            Example: {1: {"front": "...", "back": "..."}, 2: {...}}
        """
        all_results = {}

        for character in screenplay.get("character_description", []):
            char_id = character.get("id")
            if char_id is None:
                logger.warning("Character missing 'id' field, skipping")
                continue

            # Get required views from enhanced screenplay
            required_views = character.get("required_views", ["front"])

            if not required_views:
                logger.warning(
                    f"⚠️  No required_views for character {char_id}, using default"
                )
                required_views = ["front"]

            logger.info(
                f"📸 Generating {len(required_views)} views for character {char_id}: {required_views}"
            )

            # Generate only required views
            results = await self._generate_views(
                character_id=f"CHAR_{char_id}",
                character_description=character,
                required_views=required_views,
                output_dir=output_dir,
            )

            all_results[char_id] = results

        return all_results

    async def _generate_views(
        self,
        character_id: str,
        character_description: Dict[str, Any],
        required_views: List[str],
        output_dir: str,
    ) -> Dict[str, str]:
        """
        Generate only the required character views using seeding chain.

        Always generates front first (canonical), then seeds other views from it.

        Args:
            character_id: Character identifier
            character_description: Character metadata
            required_views: List of view names to generate
            output_dir: Directory to save images

        Returns:
            Dict mapping view -> image_path
        """
        results = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Ensure front is first (canonical)
        if "front" not in required_views:
            required_views.insert(0, "front")

        # Step 1: Generate front view (canonical)
        logger.info(f"📸 Generating canonical front view for {character_id}")
        front_prompt = self._build_character_prompt(character_description, "front")
        front_response = await self.gemini.generate_content(
            prompt=front_prompt, reference_image=None
        )
        front_path = str(output_path / f"{character_id}_front.png")
        self.gemini.render_image(front_path, front_response)
        results["front"] = front_path
        logger.info(f"✅ Front view: {front_path}")

        # Step 2+: Generate other required views (seeded from front)
        for view in required_views:
            if view == "front":
                continue  # Already generated

            logger.info(
                f"📸 Generating {view} view for {character_id} (seeded from front)"
            )
            view_prompt = self._build_character_prompt(character_description, view)
            view_response = await self.gemini.generate_content(
                prompt=view_prompt,
                reference_image=front_path,  # ← Seeded from canonical front
            )
            view_path = str(output_path / f"{character_id}_{view}.png")
            self.gemini.render_image(view_path, view_response)
            results[view] = view_path
            logger.info(f"✅ {view.capitalize()} view: {view_path}")

        # Cache all generated views
        self.character_cache[character_id] = results

        return results

    async def generate_keyframe_smart(
        self,
        scene_prompt: str,
        character_id: str,
        output_path: str,
        shot_description: Optional[str] = None,
    ) -> str:
        """
        Generate keyframe with automatically selected character reference.

        Intelligently selects front/side/back/full_body based on shot description.
        If shot_description is not provided, uses scene_prompt for detection.

        Args:
            scene_prompt: Scene-specific prompt for image generation
            character_id: Character identifier (must be in cache)
            output_path: Path to save generated keyframe
            shot_description: Optional shot description for reference selection
                If None, uses scene_prompt for keyword detection

        Returns:
            Path to generated keyframe image

        Raises:
            ValueError: If character_id not in cache
        """
        # Select appropriate reference
        description_for_selection = shot_description or scene_prompt
        reference_path = self.get_reference_for_shot(
            character_id, description_for_selection
        )

        logger.info(f"📸 Generating keyframe with smart reference selection")
        logger.debug(f"   Scene prompt: {scene_prompt[:100]}...")
        logger.debug(f"   Selected reference: {reference_path}")

        response = await self.gemini.generate_content(
            prompt=scene_prompt, reference_image=reference_path
        )

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        self.gemini.render_image(output_path, response)
        logger.info(f"✅ Keyframe saved: {output_path}")

        return output_path
