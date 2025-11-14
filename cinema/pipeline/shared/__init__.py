"""
Shared pipeline components for movie_maker and detective_maker.

This module contains reusable generators, composers, transformers, and utilities
that follow SOLID principles and can be used by multiple pipelines.
"""

from cinema.pipeline.shared.generators import (
    BaseGenerator,
    CharacterReferenceGenerator,
    SimpleImageGenerator,
    PromptTransformerProtocol,
)
from cinema.pipeline.shared.composers import (
    PanelComposer,
    SceneComposer,
)
from cinema.pipeline.shared.transformers import (
    ComicCharacterTransformer,
    MovieCharacterTransformer,
    GameCharacterTransformer,
    ComicPanelTransformer,
    MovieSceneTransformer,
    PassthroughTransformer,
)

__all__ = [
    # Base classes
    "BaseGenerator",
    
    # Generators
    "CharacterReferenceGenerator",
    "SimpleImageGenerator",
    
    # Composers
    "PanelComposer",
    "SceneComposer",
    
    # Protocols
    "PromptTransformerProtocol",
    
    # Transformers (Strategy Pattern)
    "ComicCharacterTransformer",
    "MovieCharacterTransformer",
    "GameCharacterTransformer",
    "ComicPanelTransformer",
    "MovieSceneTransformer",
    "PassthroughTransformer",
]
