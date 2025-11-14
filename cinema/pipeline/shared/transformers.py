"""
Prompt transformers for converting models to prompts.

Transformers follow the Strategy Pattern, allowing different prompt
generation strategies to be injected into generators.

This enables:
- Domain-specific prompt formatting (comics vs movies vs games)
- Easy testing with mock transformers
- Reusable generators across different domains
"""

import logging
from typing import Any, Union

from cinema.models.detective_output import CharacterProfile, PanelPrompt

logger = logging.getLogger(__name__)


# ============================================================================
# CHARACTER TRANSFORMERS
# ============================================================================

class ComicCharacterTransformer:
    """
    Transforms CharacterProfile to comic book character reference prompt.
    
    Strategy: Comic book art style with emphasis on visual consistency
    """
    
    def __init__(self, art_style: str = "Comic Book Style"):
        self.art_style = art_style
    
    def transform(self, model: Union[CharacterProfile, dict], **kwargs) -> str:
        """Transform character model to comic reference prompt"""
        
        # Handle dict (from JSON deserialization)
        if isinstance(model, dict):
            character = CharacterProfile.model_validate(model)
        else:
            character = model
        
        prompt = f"Full body character portrait in {self.art_style}. "
        prompt += f"Character: {character.name}. "
        prompt += f"Physical appearance: {character.physical_traits}. "
        
        if character.age:
            prompt += f"Age: {character.age}. "
        
        if character.ethnicity:
            prompt += f"Ethnicity: {character.ethnicity}. "
        
        if character.quirks:
            prompt += f"Distinctive features: {', '.join(character.quirks)}. "
        
        prompt += "Clear, consistent design suitable for multiple comic panels. "
        prompt += "Professional comic book illustration. "
        prompt += "Clean white background. "
        
        # Add negative prompts
        prompt += "\n\nNEGATIVE: text, labels, annotations, watermarks, signatures, "
        prompt += "low quality, blurry, distorted anatomy, bad hands, extra fingers, missing fingers, "
        prompt += "deformed limbs, bad proportions, malformed body, ugly face, "
        prompt += "bad pose, awkward stance, floating limbs, disconnected body parts."
        
        logger.debug(f"Character prompt for {character.name}: {prompt}...")
        
        return prompt


class MovieCharacterTransformer:
    """
    Transforms CharacterProfile to movie character sheet prompt.
    
    Strategy: Cinematic realism with emphasis on actor-like appearance
    """
    
    def __init__(self, cinematic_style: str = "Cinematic"):
        self.cinematic_style = cinematic_style
    
    def transform(self, model: Union[CharacterProfile, dict], **kwargs) -> str:
        """Transform character model to movie character sheet prompt"""
        
        # Handle dict (from JSON deserialization)
        if isinstance(model, dict):
            character = CharacterProfile.model_validate(model)
        else:
            character = model
        
        prompt = f"{self.cinematic_style} character portrait. "
        prompt += f"Professional headshot of {character.name}. "
        prompt += f"Appearance: {character.physical_traits}. "
        
        if character.age:
            prompt += f"Age: {character.age}. "
        
        if character.ethnicity:
            prompt += f"Ethnicity: {character.ethnicity}. "
        
        prompt += "Photorealistic, high quality, studio lighting. "
        prompt += "Neutral background. Professional actor headshot style."
        
        return prompt


class GameCharacterTransformer:
    """
    Transforms CharacterProfile to game character design prompt.
    
    Strategy: Game art style with emphasis on recognizable silhouette
    """
    
    def __init__(self, game_style: str = "Game Character Design"):
        self.game_style = game_style
    
    def transform(self, model: Union[CharacterProfile, dict], **kwargs) -> str:
        """Transform character model to game character design prompt"""
        
        # Handle dict (from JSON deserialization)
        if isinstance(model, dict):
            character = CharacterProfile.model_validate(model)
        else:
            character = model
        
        prompt = f"{self.game_style}. "
        prompt += f"Character concept art for {character.name}. "
        prompt += f"Design: {character.physical_traits}. "
        
        if character.age:
            prompt += f"Age: {character.age}. "
        
        if character.quirks:
            prompt += f"Unique traits: {', '.join(character.quirks)}. "
        
        prompt += "Strong silhouette, recognizable design. "
        prompt += "Multiple angles (front, side, back). "
        prompt += "Professional game character concept art."
        
        return prompt


# ============================================================================
# PANEL/SCENE TRANSFORMERS
# ============================================================================

class ComicPanelTransformer:
    """
    Transforms PanelPrompt to comic panel composition prompt.
    
    Strategy: Comic book panel with speech bubbles and sound effects
    """
    
    def __init__(self, art_style: str = "Comic Book Style"):
        self.art_style = art_style
    
    def transform(
        self, 
        model: Union[PanelPrompt, dict],
        character_names: list = None,
        **kwargs
    ) -> str:
        """Transform panel model to comic panel prompt"""
        
        # Handle dict (from JSON deserialization)
        if isinstance(model, dict):
            panel = PanelPrompt.model_validate(model)
        else:
            panel = model
        
        prompt = f"Create a comic book panel in {self.art_style}. "
        
        # Reference character images
        if character_names:
            for i, name in enumerate(character_names, 1):
                prompt += f"Use character from image {i} ({name}). "
            
            prompt += "Keep their appearance EXACTLY as shown in the reference images. "
            prompt += "Do not change their facial features, hair, or clothing. "
        
        # Add scene details
        prompt += f"\n\n{panel.shot_type.replace('_', ' ').title()} shot. "
        prompt += f"Scene: {panel.visual_description}. "
        prompt += f"Emotional tone: {panel.emotional_tone}. "
        
        if panel.dialogue:
            # Handle both list and string formats
            if isinstance(panel.dialogue, list):
                for dialogue_line in panel.dialogue:
                    if hasattr(dialogue_line, 'text'):
                        prompt += f"\n\nAdd speech bubble with text: '{dialogue_line.text}'. "
                    else:
                        prompt += f"\n\nAdd speech bubble with text: '{dialogue_line}'. "
            else:
                prompt += f"\n\nAdd speech bubble with text: '{panel.dialogue}'. "
        
        if panel.sound_effects:
            prompt += f"Add sound effect text: '{panel.sound_effects}'. "
        
        prompt += f"\n\nOrientation: {panel.orientation}. "
        prompt += "Maintain consistent comic book style throughout. "
        
        # Add negative prompts
        prompt += "\n\nNEGATIVE: low quality, blurry, distorted anatomy, bad hands, extra fingers, missing fingers, "
        prompt += "deformed limbs, bad proportions, malformed body, ugly face, "
        prompt += "bad pose, awkward stance, floating limbs, disconnected body parts, "
        prompt += "watermarks, signatures (except for intended speech bubbles and sound effects)."
        
        logger.debug(f"Panel prompt ({panel.shot_type}): {prompt}...")
        
        return prompt


class MovieSceneTransformer:
    """
    Transforms scene description to movie scene composition prompt.
    
    Strategy: Cinematic composition with professional cinematography
    """
    
    def __init__(self, cinematic_style: str = "Cinematic"):
        self.cinematic_style = cinematic_style
    
    def transform(
        self,
        model: Union[str, dict],
        character_names: list = None,
        shot_type: str = "Medium Shot",
        **kwargs
    ) -> str:
        """Transform scene description to movie scene prompt"""
        
        # Handle different input types
        if isinstance(model, dict):
            scene_description = model.get("description", str(model))
        else:
            scene_description = str(model)
        
        prompt = f"Create a {self.cinematic_style} scene. "
        
        # Reference character images
        if character_names:
            for i, name in enumerate(character_names, 1):
                prompt += f"Use character from image {i} ({name}). "
            
            prompt += "Keep their appearance EXACTLY as shown in the reference images. "
        
        # Add scene details
        prompt += f"\n\n{shot_type}. "
        prompt += f"Scene: {scene_description}. "
        prompt += "Professional cinematography. High quality, detailed rendering."
        
        return prompt


# ============================================================================
# SIMPLE TRANSFORMERS
# ============================================================================

class PassthroughTransformer:
    """
    Simple passthrough transformer that returns the input as-is.
    
    Strategy: No transformation, direct prompt usage
    """
    
    def transform(self, model: Any, **kwargs) -> str:
        """Return model as string"""
        if isinstance(model, str):
            return model
        elif isinstance(model, dict):
            return model.get("prompt", str(model))
        else:
            return str(model)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Character transformers
    "ComicCharacterTransformer",
    "MovieCharacterTransformer",
    "GameCharacterTransformer",
    
    # Panel/Scene transformers
    "ComicPanelTransformer",
    "MovieSceneTransformer",
    
    # Simple transformers
    "PassthroughTransformer",
]
