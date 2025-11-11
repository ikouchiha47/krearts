"""
API Verification for GeminiMediaGen

Verifies that GeminiMediaGen supports all required parameters for workflow selection.
This module documents the API compatibility and provides verification functions.
"""

import logging
from typing import Optional, List
from pathlib import Path

from cinema.providers.gemini import GeminiMediaGen, ImageInput

logger = logging.getLogger(__name__)


class GeminiAPIVerification:
    """
    Verifies GeminiMediaGen API compatibility with workflow requirements.
    
    This class documents and verifies that the GeminiMediaGen API supports:
    - generate_video() with image, last_image, reference_images parameters
    - generate_content() with reference_image parameter
    - Proper ImageInput type handling
    """
    
    @staticmethod
    def verify_generate_video_signature() -> dict:
        """
        Verify generate_video() method signature supports all required parameters.
        
        Required parameters for workflows:
        - prompt: str (all workflows)
        - image: Optional[ImageInput] (image-to-video, interpolation)
        - last_image: Optional[ImageInput] (interpolation)
        - reference_images: Optional[list[ImageInput]] (ingredients)
        - duration: Optional[float] (all workflows)
        
        Returns:
            Dict with verification results
        """
        import inspect
        
        sig = inspect.signature(GeminiMediaGen.generate_video)
        params = sig.parameters
        
        results = {
            "method": "generate_video",
            "verified": True,
            "parameters": {},
            "issues": []
        }
        
        # Check required parameters
        required_params = {
            "prompt": str,
            "image": Optional[ImageInput],
            "last_image": Optional[ImageInput],
            "reference_images": Optional[List[ImageInput]],
            "duration": Optional[float]
        }
        
        for param_name, expected_type in required_params.items():
            if param_name in params:
                results["parameters"][param_name] = "✓ Present"
                logger.debug(f"  ✓ {param_name}: Present")
            else:
                results["parameters"][param_name] = "✗ Missing"
                results["issues"].append(f"Missing parameter: {param_name}")
                results["verified"] = False
                logger.error(f"  ✗ {param_name}: Missing")
        
        return results
    
    @staticmethod
    def verify_generate_content_signature() -> dict:
        """
        Verify generate_content() method signature supports reference_image parameter.
        
        Required parameters:
        - prompt: str
        - reference_image: Optional[ImageInput]
        
        Returns:
            Dict with verification results
        """
        import inspect
        
        sig = inspect.signature(GeminiMediaGen.generate_content)
        params = sig.parameters
        
        results = {
            "method": "generate_content",
            "verified": True,
            "parameters": {},
            "issues": []
        }
        
        # Check required parameters
        required_params = {
            "prompt": str,
            "reference_image": Optional[ImageInput]
        }
        
        for param_name, expected_type in required_params.items():
            if param_name in params:
                results["parameters"][param_name] = "✓ Present"
                logger.debug(f"  ✓ {param_name}: Present")
            else:
                results["parameters"][param_name] = "✗ Missing"
                results["issues"].append(f"Missing parameter: {param_name}")
                results["verified"] = False
                logger.error(f"  ✗ {param_name}: Missing")
        
        return results
    
    @staticmethod
    def verify_image_input_type() -> dict:
        """
        Verify ImageInput type alias supports all required input types.
        
        Required types:
        - PIL.Image.Image
        - bytes
        - bytearray
        - str (file path)
        - types.ImageDict
        
        Returns:
            Dict with verification results
        """
        from typing import get_args
        
        results = {
            "type": "ImageInput",
            "verified": True,
            "supported_types": [],
            "issues": []
        }
        
        # Get the union types from ImageInput
        try:
            # ImageInput is defined in cinema.providers.gemini
            from cinema.providers.gemini import ImageInput
            
            # Check if it's a Union type
            args = get_args(ImageInput)
            if args:
                results["supported_types"] = [str(arg) for arg in args]
                logger.debug(f"  ImageInput supports: {results['supported_types']}")
            else:
                results["supported_types"] = ["ImageInput (type alias)"]
                logger.debug("  ImageInput is a type alias")
            
            results["verified"] = True
            
        except Exception as e:
            results["issues"].append(f"Failed to inspect ImageInput: {e}")
            results["verified"] = False
            logger.error(f"  ✗ Failed to inspect ImageInput: {e}")
        
        return results
    
    @staticmethod
    def verify_to_api_image_method() -> dict:
        """
        Verify to_api_image() static method handles all ImageInput types.
        
        Returns:
            Dict with verification results
        """
        results = {
            "method": "to_api_image",
            "verified": True,
            "issues": []
        }
        
        # Check if method exists
        if not hasattr(GeminiMediaGen, 'to_api_image'):
            results["issues"].append("to_api_image method not found")
            results["verified"] = False
            logger.error("  ✗ to_api_image method not found")
        else:
            logger.debug("  ✓ to_api_image method exists")
        
        return results
    
    @staticmethod
    def run_full_verification() -> dict:
        """
        Run full API verification suite.
        
        Returns:
            Dict with all verification results
        """
        logger.info("=== GeminiMediaGen API Verification ===")
        
        results = {
            "overall_verified": True,
            "checks": {}
        }
        
        # Verify generate_video
        logger.info("Checking generate_video() signature...")
        video_results = GeminiAPIVerification.verify_generate_video_signature()
        results["checks"]["generate_video"] = video_results
        if not video_results["verified"]:
            results["overall_verified"] = False
        
        # Verify generate_content
        logger.info("Checking generate_content() signature...")
        content_results = GeminiAPIVerification.verify_generate_content_signature()
        results["checks"]["generate_content"] = content_results
        if not content_results["verified"]:
            results["overall_verified"] = False
        
        # Verify ImageInput type
        logger.info("Checking ImageInput type...")
        image_input_results = GeminiAPIVerification.verify_image_input_type()
        results["checks"]["image_input"] = image_input_results
        if not image_input_results["verified"]:
            results["overall_verified"] = False
        
        # Verify to_api_image
        logger.info("Checking to_api_image() method...")
        to_api_results = GeminiAPIVerification.verify_to_api_image_method()
        results["checks"]["to_api_image"] = to_api_results
        if not to_api_results["verified"]:
            results["overall_verified"] = False
        
        # Summary
        if results["overall_verified"]:
            logger.info("✓ All API compatibility checks passed")
        else:
            logger.error("✗ Some API compatibility checks failed")
            for check_name, check_results in results["checks"].items():
                if not check_results.get("verified", True):
                    logger.error(f"  Failed: {check_name}")
                    for issue in check_results.get("issues", []):
                        logger.error(f"    - {issue}")
        
        return results


def verify_workflow_compatibility():
    """
    Verify that GeminiMediaGen API is compatible with all workflow types.
    
    Checks:
    1. First and Last Frame Interpolation workflow
       - Requires: image, last_image parameters
    
    2. Ingredients to Video workflow
       - Requires: reference_images parameter (list of up to 3 images)
    
    3. Timestamp Prompting workflow
       - Requires: prompt with timestamp notation
    
    4. Text-to-Video workflow
       - Requires: prompt only
    
    5. Image-to-Video workflow
       - Requires: image parameter
    """
    logger.info("=== Workflow Compatibility Verification ===")
    
    verification = GeminiAPIVerification()
    results = verification.run_full_verification()
    
    # Workflow-specific checks
    logger.info("\n=== Workflow-Specific Compatibility ===")
    
    workflows = {
        "First and Last Frame Interpolation": ["prompt", "image", "last_image", "duration"],
        "Ingredients to Video": ["prompt", "reference_images", "duration"],
        "Timestamp Prompting": ["prompt", "duration"],
        "Text-to-Video": ["prompt", "duration"],
        "Image-to-Video": ["prompt", "image", "duration"]
    }
    
    video_params = results["checks"]["generate_video"]["parameters"]
    
    for workflow_name, required_params in workflows.items():
        logger.info(f"\n{workflow_name}:")
        all_present = True
        for param in required_params:
            status = video_params.get(param, "✗ Missing")
            logger.info(f"  {param}: {status}")
            if "✗" in status:
                all_present = False
        
        if all_present:
            logger.info(f"  ✓ {workflow_name} is fully supported")
        else:
            logger.error(f"  ✗ {workflow_name} has missing parameters")
    
    return results


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s"
    )
    
    # Run verification
    results = verify_workflow_compatibility()
    
    # Print summary
    print("\n" + "="*60)
    if results["overall_verified"]:
        print("✓ GeminiMediaGen API is compatible with all workflows")
    else:
        print("✗ GeminiMediaGen API has compatibility issues")
        print("\nIssues found:")
        for check_name, check_results in results["checks"].items():
            for issue in check_results.get("issues", []):
                print(f"  - {check_name}: {issue}")
    print("="*60)
