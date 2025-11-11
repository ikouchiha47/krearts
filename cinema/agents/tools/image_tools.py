"""
Image manipulation tools for the cinema pipeline.
"""

import base64
import logging
from pathlib import Path
from typing import Literal, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class ImageEncoder:
    """Encodes images to base64 for API transmission."""

    @staticmethod
    def encode_image(image_path: str) -> dict:
        """
        Encode an image file to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with base64 data and mime_type
        """
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine mime type
        ext = path.suffix.lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        return {
            "base64": image_data,
            "mime_type": mime_type,
        }

    @staticmethod
    def encode_images(image_paths: list[str]) -> list[dict]:
        """
        Encode multiple images to base64.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of dictionaries with base64 data and mime_type
        """
        return [ImageEncoder.encode_image(path) for path in image_paths]


class ImageTools:
    """Tools for image manipulation and processing."""

    @staticmethod
    def compress_image(
        input_path: str,
        output_path: Optional[str] = None,
        quality: int = 85,
        max_size: Optional[tuple[int, int]] = None,
        format: Optional[Literal["JPEG", "PNG"]] = None,
    ) -> str:
        """
        Compress an image while maintaining format (JPEG or PNG only).
        
        Args:
            input_path: Path to input image
            output_path: Path to save compressed image (defaults to overwriting input)
            quality: Compression quality (1-100, only for JPEG)
            max_size: Optional (width, height) to resize to while maintaining aspect ratio
            format: Force output format (JPEG or PNG), defaults to input format
            
        Returns:
            Path to compressed image
        """
        input_path_obj = Path(input_path)
        
        if not input_path_obj.exists():
            raise FileNotFoundError(f"Input image not found: {input_path_obj}")
        
        # Load image
        img = Image.open(input_path_obj)
        
        # Determine output format
        if format is None:
            # Use input format, but only support JPEG/PNG
            if img.format in ["JPEG", "JPG"]:
                format = "JPEG"
            elif img.format == "PNG":
                format = "PNG"
            else:
                # Default to PNG for other formats
                format = "PNG"
                logger.warning(f"Unsupported format {img.format}, converting to PNG")
        
        # Resize if max_size specified
        if max_size:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {img.size}")
        
        # Determine output path
        if output_path is None:
            output_path_obj = input_path_obj
        else:
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with compression
        save_kwargs = {}
        
        if format == "JPEG":
            # Convert RGBA to RGB for JPEG
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            
            save_kwargs = {
                "format": "JPEG",
                "quality": quality,
                "optimize": True,
            }
        elif format == "PNG":
            save_kwargs = {
                "format": "PNG",
                "optimize": True,
                "compress_level": 9,
            }
        
        img.save(output_path_obj, **save_kwargs)
        
        # Log compression results
        original_size = input_path_obj.stat().st_size
        compressed_size = output_path_obj.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(
            f"Compressed {input_path_obj.name}: "
            f"{original_size / 1024:.1f}KB -> {compressed_size / 1024:.1f}KB "
            f"({ratio:.1f}% reduction)"
        )
        
        return str(output_path_obj)

    @staticmethod
    def batch_compress(
        input_dir: str,
        output_dir: Optional[str] = None,
        quality: int = 85,
        max_size: Optional[tuple[int, int]] = None,
        pattern: str = "*.png",
    ) -> list[str]:
        """
        Compress all images in a directory.
        
        Args:
            input_dir: Directory containing images
            output_dir: Output directory (defaults to input_dir)
            quality: Compression quality
            max_size: Optional max dimensions
            pattern: Glob pattern for files to process
            
        Returns:
            List of compressed image paths
        """
        input_dir_obj = Path(input_dir)
        output_dir_obj = Path(output_dir) if output_dir else input_dir_obj
        output_dir_obj.mkdir(parents=True, exist_ok=True)
        
        compressed_files = []
        
        for img_path in input_dir_obj.glob(pattern):
            if not img_path.is_file():
                continue
            
            output_path_obj = output_dir_obj / img_path.name
            
            try:
                result = ImageTools.compress_image(
                    str(img_path),
                    str(output_path_obj),
                    quality=quality,
                    max_size=max_size,
                )
                compressed_files.append(result)
            except Exception as e:
                logger.error(f"Failed to compress {img_path}: {e}")
        
        logger.info(f"Compressed {len(compressed_files)} images")
        return compressed_files

    @staticmethod
    def encode_image_to_base64(image_path: str) -> dict:
        """
        Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with 'data' (base64 string) and 'mime_type'
        """
        import base64
        
        img_path = Path(image_path)
        
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        
        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        ext = img_path.suffix.lower()
        mime_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        return {
            "data": image_data,
            "mime_type": mime_type,
        }

    @staticmethod
    def get_image_info(image_path: str) -> dict:
        """
        Get information about an image.
        
        Args:
            image_path: Path to image
            
        Returns:
            Dictionary with image info (format, size, mode, file_size)
        """
        img_path = Path(image_path)
        
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")
        
        img = Image.open(img_path)
        
        return {
            "format": img.format,
            "size": img.size,
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "file_size_kb": img_path.stat().st_size / 1024,
        }
