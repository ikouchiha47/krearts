"""
Art Style Reference Image Management

Handles loading and managing reference images for different art styles
(Blueberry, Akira, Spider-Verse, Arcane, etc.)

Supports two modes:
1. Automatic selection based on scene context (LLM-driven)
2. Manual selection using labeled references (hash mapping)
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image
import yaml

logger = logging.getLogger(__name__)


class ArtStyleReferenceManager:
    """Manages reference images for different art styles."""
    
    # Map art style keywords to reference directories
    STYLE_MAP = {
        "blueberry": "knowledge/art-styles/references/blueberry",
        "moebius": "knowledge/art-styles/references/blueberry",  # Same style
        "akira": "knowledge/art-styles/references/akira",
        "otomo": "knowledge/art-styles/references/akira",  # Same artist
        "spider-verse": "knowledge/art-styles/references/spiderverse",
        "spiderverse": "knowledge/art-styles/references/spiderverse",
        "into the spider-verse": "knowledge/art-styles/references/spiderverse",
        "arcane": "knowledge/art-styles/references/arcane",
        "noir": "knowledge/art-styles/references/noir",
        "watchmen": "knowledge/art-styles/references/watchmen",
        "print comic": "knowledge/art-styles/references/print_comic",
        "halftone": "knowledge/art-styles/references/print_comic",
    }
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the reference manager.
        
        Args:
            base_dir: Base directory for the project (defaults to CINEMA_ROOT env var or auto-detection)
        """
        if base_dir is None:
            import os
            # Use CINEMA_ROOT environment variable if set
            cinema_root = os.getenv('CINEMA_ROOT')
            if cinema_root:
                base_dir = Path(cinema_root)
            else:
                # Fallback: auto-detect project root by finding the directory containing 'knowledge'
                current = Path(__file__).parent
                while current != current.parent:
                    if (current / "knowledge").exists():
                        base_dir = current
                        break
                    current = current.parent
                else:
                    # Final fallback to current working directory
                    base_dir = Path.cwd()
        
        self.base_dir = base_dir
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load the reference manifest YAML file."""
        manifest_path = self.base_dir / "knowledge/art-styles/references/reference_manifest.yaml"
        
        if not manifest_path.exists():
            logger.warning(f"Reference manifest not found: {manifest_path}")
            return {}
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            logger.debug(f"Loaded reference manifest with {len(manifest)} styles")
            return manifest
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return {}
    
    def load_references(
        self,
        art_style: str,
        max_references: int = 3,
        required: bool = False
    ) -> List[Image.Image]:
        """
        Load reference images for the specified art style (simple mode).
        
        This loads the first N available references without context-based selection.
        For context-aware selection, use load_references_for_scene().
        
        Args:
            art_style: Art style description (e.g., "Blueberry European Comic Style")
            max_references: Maximum number of reference images to load
            required: If True, raise error if no references found
        
        Returns:
            List of PIL Images (up to max_references)
        
        Raises:
            FileNotFoundError: If required=True and no references found
        """
        logger.info(f"Loading reference images for art style: {art_style}")
        
        # Find matching style directory
        ref_dir = self._find_reference_directory(art_style)
        
        if not ref_dir:
            msg = f"No reference directory found for style: {art_style}"
            if required:
                raise FileNotFoundError(msg)
            logger.info(msg)
            return []
        
        if not ref_dir.exists():
            msg = f"Reference directory does not exist: {ref_dir}"
            if required:
                raise FileNotFoundError(msg)
            logger.warning(msg)
            return []
        
        # Load reference images
        references = []
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
        
        for ext in image_extensions:
            for img_file in sorted(ref_dir.glob(ext)):
                if len(references) >= max_references:
                    break
                
                try:
                    img = Image.open(img_file)
                    references.append(img)
                    logger.info(f"  ✅ Loaded reference: {img_file.name}")
                except Exception as e:
                    logger.warning(f"  ⚠️  Failed to load {img_file.name}: {e}")
            
            if len(references) >= max_references:
                break
        
        if not references:
            msg = f"No valid reference images found in: {ref_dir}"
            if required:
                raise FileNotFoundError(msg)
            logger.warning(msg)
        else:
            logger.info(f"  📸 Loaded {len(references)} reference images")
        
        return references
    
    def load_references_for_scene(
        self,
        art_style: str,
        shot_type: Optional[str] = None,
        scene_type: Optional[str] = None,
        panel_arrangement: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        max_references: int = 3
    ) -> List[Image.Image]:
        """
        Load reference images based on scene context (context-aware selection).
        
        This method uses the manifest to select the most appropriate references
        based on shot type, scene type, panel arrangement, and emotional tone.
        
        Args:
            art_style: Art style description
            shot_type: Shot type (e.g., "close-up", "wide", "establishing")
            scene_type: Scene type (e.g., "action", "dialogue", "atmospheric")
            panel_arrangement: Panel layout (e.g., "grid-9-panel", "horizontal-3-panel")
            emotional_tone: Emotional tone (e.g., "tense", "dramatic", "relaxed")
            max_references: Maximum number of references to load
        
        Returns:
            List of PIL Images selected based on context
        """
        logger.info(f"Loading context-aware references for: {art_style}")
        logger.debug(f"  Shot: {shot_type}, Scene: {scene_type}, Layout: {panel_arrangement}, Tone: {emotional_tone}")
        
        # Find style key
        style_key = self._find_style_key(art_style)
        if not style_key or style_key not in self.manifest:
            logger.warning(f"Style not found in manifest: {art_style}")
            return self.load_references(art_style, max_references)
        
        style_data = self.manifest[style_key]
        references_data = style_data.get('references', {})
        
        if not references_data:
            logger.warning(f"No references defined for style: {style_key}")
            return self.load_references(art_style, max_references)
        
        # Score each reference based on context match
        scored_refs = []
        for ref_name, ref_info in references_data.items():
            score = self._score_reference(
                ref_info,
                shot_type,
                scene_type,
                panel_arrangement,
                emotional_tone
            )
            scored_refs.append((ref_name, ref_info, score))
        
        # Sort by score (highest first)
        scored_refs.sort(key=lambda x: x[2], reverse=True)
        
        # Load top N references
        ref_dir = self._find_reference_directory(art_style)
        if not ref_dir or not ref_dir.exists():
            logger.warning(f"Reference directory not found: {ref_dir}")
            return []
        
        loaded_refs = []
        for ref_name, ref_info, score in scored_refs[:max_references]:
            if score == 0:
                continue  # Skip references with no match
            
            file_name = ref_info.get('file')
            if not file_name:
                continue
            
            file_path = ref_dir / file_name
            if not file_path.exists():
                logger.warning(f"  ⚠️  Reference file not found: {file_name}")
                continue
            
            try:
                img = Image.open(file_path)
                loaded_refs.append(img)
                logger.info(f"  ✅ Loaded {ref_name} (score: {score}): {file_name}")
            except Exception as e:
                logger.warning(f"  ⚠️  Failed to load {file_name}: {e}")
        
        # If no context matches, fall back to general references
        if not loaded_refs:
            logger.info("  No context matches, loading general references")
            return self.load_references(art_style, max_references)
        
        logger.info(f"  📸 Loaded {len(loaded_refs)} context-aware references")
        return loaded_refs
    
    def _score_reference(
        self,
        ref_info: Dict[str, Any],
        shot_type: Optional[str],
        scene_type: Optional[str],
        panel_arrangement: Optional[str],
        emotional_tone: Optional[str]
    ) -> int:
        """
        Score a reference based on how well it matches the context.
        
        Returns:
            Score (higher is better match)
        """
        use_for = ref_info.get('use_for', [])
        if not use_for:
            return 0
        
        score = 0
        
        # Check for "all" - general reference (low priority)
        if "all" in use_for:
            score += 1
        
        # Check shot type match
        if shot_type and shot_type.lower() in [u.lower() for u in use_for]:
            score += 10
        
        # Check scene type match
        if scene_type and scene_type.lower() in [u.lower() for u in use_for]:
            score += 10
        
        # Check panel arrangement match (highest priority)
        if panel_arrangement and panel_arrangement.lower() in [u.lower() for u in use_for]:
            score += 20
        
        # Check emotional tone match
        if emotional_tone and emotional_tone.lower() in [u.lower() for u in use_for]:
            score += 5
        
        return score
    
    def get_reference_by_label(
        self,
        art_style: str,
        label: str
    ) -> Optional[Image.Image]:
        """
        Get a specific reference image by its label (manual hash mapping).
        
        This allows direct access to specific references without context matching.
        
        Args:
            art_style: Art style description
            label: Reference label (e.g., "motion_lines", "character_closeup")
        
        Returns:
            PIL Image if found, None otherwise
        
        Example:
            >>> manager = ArtStyleReferenceManager()
            >>> ref = manager.get_reference_by_label("akira", "motion_lines")
        """
        style_key = self._find_style_key(art_style)
        if not style_key or style_key not in self.manifest:
            logger.warning(f"Style not found: {art_style}")
            return None
        
        style_data = self.manifest[style_key]
        references_data = style_data.get('references', {})
        
        if label not in references_data:
            logger.warning(f"Label '{label}' not found for style '{style_key}'")
            logger.info(f"Available labels: {list(references_data.keys())}")
            return None
        
        ref_info = references_data[label]
        file_name = ref_info.get('file')
        
        if not file_name:
            logger.warning(f"No file specified for label '{label}'")
            return None
        
        ref_dir = self._find_reference_directory(art_style)
        if not ref_dir or not ref_dir.exists():
            logger.warning(f"Reference directory not found: {ref_dir}")
            return None
        
        file_path = ref_dir / file_name
        if not file_path.exists():
            logger.warning(f"Reference file not found: {file_path}")
            return None
        
        try:
            img = Image.open(file_path)
            logger.info(f"✅ Loaded reference '{label}': {file_name}")
            return img
        except Exception as e:
            logger.error(f"Failed to load reference '{label}': {e}")
            return None
    
    def list_reference_labels(self, art_style: str) -> Dict[str, str]:
        """
        List all available reference labels for a style.
        
        Args:
            art_style: Art style description
        
        Returns:
            Dict mapping label -> purpose description
        """
        style_key = self._find_style_key(art_style)
        if not style_key or style_key not in self.manifest:
            return {}
        
        style_data = self.manifest[style_key]
        references_data = style_data.get('references', {})
        
        return {
            label: ref_info.get('purpose', 'No description')
            for label, ref_info in references_data.items()
        }
    
    def _find_style_key(self, art_style: str) -> Optional[str]:
        """Find the manifest key for the given art style."""
        art_style_lower = art_style.lower()
        
        # Direct match in manifest
        for key in self.manifest.keys():
            if key in art_style_lower:
                return key
        
        # Check STYLE_MAP
        for keyword, _ in self.STYLE_MAP.items():
            if keyword in art_style_lower:
                # Extract style name from path
                return keyword.replace("-", "").replace(" ", "")
        
        return None
    
    def _find_reference_directory(self, art_style: str) -> Optional[Path]:
        """
        Find the reference directory for the given art style.
        
        Args:
            art_style: Art style description
        
        Returns:
            Path to reference directory, or None if not found
        """
        art_style_lower = art_style.lower()
        
        # Check each keyword in the style map
        for keyword, rel_path in self.STYLE_MAP.items():
            if keyword in art_style_lower:
                full_path = self.base_dir / rel_path
                logger.debug(f"  Matched keyword '{keyword}' -> {rel_path}")
                return full_path
        
        logger.debug(f"  No keyword match found for: {art_style}")
        return None
    
    def list_available_styles(self) -> List[str]:
        """
        List all available art styles with reference images.
        
        Returns:
            List of style names that have reference directories
        """
        available = []
        
        for keyword, rel_path in self.STYLE_MAP.items():
            full_path = self.base_dir / rel_path
            if full_path.exists():
                # Count images
                image_count = sum(
                    1 for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]
                    for _ in full_path.glob(ext)
                )
                if image_count > 0:
                    available.append(f"{keyword} ({image_count} images)")
        
        return available
    
    def setup_reference_directories(self):
        """
        Create reference directory structure if it doesn't exist.
        
        This is a helper method to set up the directory structure for
        organizing reference images.
        """
        base_ref_dir = self.base_dir / "knowledge/art-styles/references"
        
        # Create directories for each style
        styles = [
            "blueberry",
            "akira",
            "spiderverse",
            "arcane",
            "noir",
            "watchmen",
            "print_comic"
        ]
        
        for style in styles:
            style_dir = base_ref_dir / style
            style_dir.mkdir(parents=True, exist_ok=True)
            
            # Create README in each directory
            readme = style_dir / "README.md"
            if not readme.exists():
                readme.write_text(f"""# {style.title()} Reference Images

Add 2-3 reference images here to influence the art style.

## Recommended Images:
- Panel examples showing the characteristic style
- Character design references
- Layout/composition examples
- Color palette references (if applicable)

## Supported Formats:
- JPG/JPEG
- PNG
- WebP

## Usage:
These images will be automatically loaded when generating pages with
the "{style}" art style.
""")
        
        logger.info(f"✅ Reference directory structure created at: {base_ref_dir}")
        return base_ref_dir


def create_reference_structure():
    """
    Standalone function to create reference directory structure.
    
    Run this to set up the directories for organizing reference images.
    """
    manager = ArtStyleReferenceManager()
    base_dir = manager.setup_reference_directories()
    
    print(f"\n✅ Reference directories created at: {base_dir}")
    print("\nNext steps:")
    print("1. Add 2-3 reference images to each style directory")
    print("2. Use descriptive filenames (e.g., 'panel_example_1.jpg')")
    print("3. Reference images will be automatically loaded during generation")
    print("\nAvailable style directories:")
    for style_dir in sorted(base_dir.iterdir()):
        if style_dir.is_dir():
            print(f"  - {style_dir.name}/")


if __name__ == "__main__":
    # Create reference directory structure
    create_reference_structure()
