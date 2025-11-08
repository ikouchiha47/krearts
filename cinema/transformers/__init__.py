"""
Transformers for extracting generation specs from screenplay output.
"""

from cinema.transformers.screenplay_extractors import (
    CharacterExtractor,
    CharacterGenerationStage,
    CharacterReference,
    ImageGenerationExtractor,
    ImageGenerationSpec,
    ImageGenerationStage,
    PostProductionEffect,
    PostProductionExtractor,
    PostProductionSpec,
    PostProductionStage,
    SceneImageSpecs,
    VideoGenerationExtractor,
    VideoGenerationSpec,
    VideoGenerationStage,
    extract_all_stages,
)

__all__ = [
    # Extractors
    "CharacterExtractor",
    "ImageGenerationExtractor",
    "VideoGenerationExtractor",
    "PostProductionExtractor",
    # Stage Classes
    "CharacterGenerationStage",
    "ImageGenerationStage",
    "VideoGenerationStage",
    "PostProductionStage",
    # Spec Models
    "CharacterReference",
    "ImageGenerationSpec",
    "SceneImageSpecs",
    "VideoGenerationSpec",
    "PostProductionSpec",
    "PostProductionEffect",
    # Convenience
    "extract_all_stages",
]
