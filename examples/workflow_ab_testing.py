"""
Example: A/B Testing Workflows

Demonstrates how to:
1. Generate videos with both interpolation and ingredients workflows
2. Compare results side-by-side
3. Review A/B test results
4. Build knowledge base from reviewed tests

This is useful for:
- Determining which workflow works best for different scene types
- Building training data for future improvements
- Quality comparison and evaluation
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from cinema.providers.gemini import GeminiMediaGen
from cinema.workflow.models import WorkflowConfig, WorkflowSelectionMode, VeoWorkflowType
from cinema.workflow.orchestrator import VeoWorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ABTestOrchestrator:
    """Generates videos with multiple workflows for comparison"""
    
    def __init__(self, gemini_client: GeminiMediaGen, config: WorkflowConfig):
        self.gemini = gemini_client
        self.config = config
    
    async def generate_ab_test(
        self,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Generate video with both interpolation and ingredients workflows.
        
        Returns:
            Dict mapping workflow_type -> video_path
        """
        results = {}
        scene_id = scene.get("scene_id", "unknown")
        
        # Test 1: Interpolation
        logger.info(f"🧪 A/B Test - Generating {scene_id} with INTERPOLATION...")
        try:
            orchestrator_interp = VeoWorkflowOrchestrator(
                self.gemini,
                WorkflowConfig(
                    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
                )
            )
            video_path, _ = await orchestrator_interp.generate_video_with_workflow(
                scene, assets
            )
            results["interpolation"] = video_path
            logger.info(f"✅ Interpolation video: {video_path}")
        except Exception as e:
            logger.error(f"❌ Interpolation failed: {e}")
            results["interpolation"] = None
        
        # Test 2: Ingredients
        logger.info(f"🧪 A/B Test - Generating {scene_id} with INGREDIENTS...")
        try:
            orchestrator_ingred = VeoWorkflowOrchestrator(
                self.gemini,
                WorkflowConfig(
                    selection_mode=WorkflowSelectionMode.ALWAYS_INGREDIENTS
                )
            )
            video_path, _ = await orchestrator_ingred.generate_video_with_workflow(
                scene, assets
            )
            results["ingredients"] = video_path
            logger.info(f"✅ Ingredients video: {video_path}")
        except Exception as e:
            logger.error(f"❌ Ingredients failed: {e}")
            results["ingredients"] = None
        
        # Save comparison manifest
        self._save_ab_test_manifest(scene, results)
        
        return results
    
    def _save_ab_test_manifest(
        self,
        scene: Dict[str, Any],
        results: Dict[str, str]
    ):
        """Save A/B test results for manual review"""
        import time
        
        output_dir = Path(self.config.ab_test_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        keyframes = scene.get("keyframe_description", {})
        camera = scene.get("cinematography", {}).get("camera_movement", {})
        
        manifest = {
            "scene_id": scene.get("scene_id"),
            "timestamp": time.time(),
            "results": results,
            "scene_metadata": {
                "duration": scene.get("duration"),
                "camera_movement": camera.get("movement_type"),
                "camera_description": camera.get("description"),
                "first_frame": keyframes.get("first_frame_prompt", "")[:100],
                "last_frame": keyframes.get("last_frame_prompt", "")[:100],
                "character_ids": scene.get("character_ids", []),
                "has_dialogue": bool(scene.get("dialogue"))
            },
            "review_notes": {
                "interpolation_quality": "",
                "interpolation_notes": "",
                "ingredients_quality": "",
                "ingredients_notes": "",
                "winner": "",
                "overall_notes": ""
            }
        }
        
        manifest_path = output_dir / f"{scene.get('scene_id')}_ab_test.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"📊 A/B test manifest saved: {manifest_path}")


class WorkflowKnowledgeBase:
    """Builds knowledge base from A/B test results"""
    
    def __init__(self, ab_test_dir: str):
        self.ab_test_dir = Path(ab_test_dir)
    
    def collect_reviewed_tests(self) -> List[Dict[str, Any]]:
        """Collect all A/B tests that have been manually reviewed"""
        reviewed = []
        
        if not self.ab_test_dir.exists():
            logger.warning(f"A/B test directory not found: {self.ab_test_dir}")
            return reviewed
        
        for manifest_file in self.ab_test_dir.glob("*_ab_test.json"):
            with open(manifest_file) as f:
                data = json.load(f)
            
            # Check if manually reviewed (has winner annotation)
            if data.get("review_notes", {}).get("winner"):
                reviewed.append(data)
        
        return reviewed
    
    def generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for fine-tuning LLM decision model"""
        reviewed = self.collect_reviewed_tests()
        
        training_data = []
        for test in reviewed:
            training_data.append({
                "scene_id": test["scene_id"],
                "scene_metadata": test["scene_metadata"],
                "winner": test["review_notes"]["winner"],
                "interpolation_quality": test["review_notes"]["interpolation_quality"],
                "ingredients_quality": test["review_notes"]["ingredients_quality"],
                "notes": test["review_notes"]["overall_notes"]
            })
        
        return training_data
    
    def export_knowledge_base(self, output_path: str):
        """Export knowledge base for future use"""
        training_data = self.generate_training_data()
        
        with open(output_path, "w") as f:
            json.dump({
                "version": "1.0",
                "total_samples": len(training_data),
                "training_data": training_data
            }, f, indent=2)
        
        logger.info(f"📚 Knowledge base exported: {output_path}")
        logger.info(f"   Total samples: {len(training_data)}")


def create_test_scenes():
    """Create sample scenes for A/B testing"""
    return [
        {
            "scene_id": "S1_dolly_push",
            "duration": 4.0,
            "description": "Dolly push-in on character",
            "cinematography": {
                "camera_movement": {
                    "movement_type": "dolly",
                    "description": "Smooth push in from medium to close-up"
                }
            },
            "keyframe_description": {
                "first_frame_prompt": "Medium shot of detective, neutral expression",
                "last_frame_prompt": "Close-up of detective, slight smile"
            },
            "character_ids": ["detective_001"]
        },
        {
            "scene_id": "S2_dialogue",
            "duration": 6.0,
            "description": "Two-person dialogue scene",
            "cinematography": {
                "camera_movement": {
                    "movement_type": "static",
                    "description": "Static medium shot"
                }
            },
            "keyframe_description": {
                "first_frame_prompt": "Detective and woman, both visible",
                "last_frame_prompt": "Same composition, different expressions"
            },
            "character_ids": ["detective_001", "woman_001"],
            "dialogue": "Of all the offices in this town..."
        },
        {
            "scene_id": "S3_pan_cityscape",
            "duration": 5.0,
            "description": "Pan across cityscape",
            "cinematography": {
                "camera_movement": {
                    "movement_type": "pan",
                    "description": "Smooth pan from left to right"
                }
            },
            "keyframe_description": {
                "first_frame_prompt": "Left side of cityscape, buildings on left",
                "last_frame_prompt": "Right side of cityscape, buildings on right"
            },
            "character_ids": []
        }
    ]


def create_sample_assets():
    """Create sample asset paths"""
    return {
        "S1_dolly_push_first_frame": "output/images/S1_first.png",
        "S1_dolly_push_last_frame": "output/images/S1_last.png",
        "S2_dialogue_first_frame": "output/images/S2_first.png",
        "S2_dialogue_last_frame": "output/images/S2_last.png",
        "S3_pan_cityscape_first_frame": "output/images/S3_first.png",
        "S3_pan_cityscape_last_frame": "output/images/S3_last.png",
        "detective_001_reference": "output/refs/detective.png",
        "woman_001_reference": "output/refs/woman.png"
    }


async def example_generate_ab_tests():
    """
    Example 1: Generate A/B tests for multiple scenes
    
    Creates videos with both workflows for comparison.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 1: Generate A/B Tests")
    logger.info("="*80)
    
    # Configure A/B testing
    config = WorkflowConfig(
        ab_test_enabled=True,
        ab_test_output_dir="output/ab_test"
    )
    
    gemini = GeminiMediaGen()
    ab_tester = ABTestOrchestrator(gemini, config)
    
    scenes = create_test_scenes()
    assets = create_sample_assets()
    
    all_results = {}
    
    for scene in scenes:
        scene_id = scene["scene_id"]
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing scene: {scene_id}")
        logger.info(f"  Camera: {scene['cinematography']['camera_movement']['movement_type']}")
        logger.info(f"  Duration: {scene['duration']}s")
        logger.info(f"{'='*60}")
        
        try:
            results = await ab_tester.generate_ab_test(scene, assets)
            all_results[scene_id] = results
            
            logger.info(f"\n📊 Results for {scene_id}:")
            logger.info(f"  Interpolation: {results.get('interpolation', 'FAILED')}")
            logger.info(f"  Ingredients: {results.get('ingredients', 'FAILED')}")
            
        except Exception as e:
            logger.error(f"❌ A/B test failed for {scene_id}: {e}")
    
    logger.info(f"\n✅ A/B testing complete!")
    logger.info(f"   Generated {len(all_results)} test sets")
    logger.info(f"   Manifests saved to: {config.ab_test_output_dir}")


async def example_review_ab_tests():
    """
    Example 2: Review A/B test results
    
    Shows how to manually review and annotate test results.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 2: Review A/B Test Results")
    logger.info("="*80)
    
    ab_test_dir = Path("output/ab_test")
    
    if not ab_test_dir.exists():
        logger.warning("No A/B tests found. Run example 1 first.")
        return
    
    logger.info(f"\nA/B test manifests in {ab_test_dir}:")
    
    for manifest_file in ab_test_dir.glob("*_ab_test.json"):
        with open(manifest_file) as f:
            data = json.load(f)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scene: {data['scene_id']}")
        logger.info(f"{'='*60}")
        logger.info(f"Camera: {data['scene_metadata']['camera_movement']}")
        logger.info(f"Duration: {data['scene_metadata']['duration']}s")
        logger.info(f"\nVideos:")
        logger.info(f"  Interpolation: {data['results'].get('interpolation', 'N/A')}")
        logger.info(f"  Ingredients: {data['results'].get('ingredients', 'N/A')}")
        
        # Check if reviewed
        winner = data['review_notes'].get('winner')
        if winner:
            logger.info(f"\n✅ Reviewed:")
            logger.info(f"  Winner: {winner}")
            logger.info(f"  Notes: {data['review_notes'].get('overall_notes', 'N/A')}")
        else:
            logger.info(f"\n⏳ Not yet reviewed")
            logger.info(f"\nTo review, edit: {manifest_file}")
            logger.info(f"  1. Watch both videos")
            logger.info(f"  2. Rate quality (1-5) for each")
            logger.info(f"  3. Set 'winner' to 'interpolation' or 'ingredients'")
            logger.info(f"  4. Add notes about why")


async def example_build_knowledge_base():
    """
    Example 3: Build knowledge base from reviewed tests
    
    Collects reviewed A/B tests and creates training data.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 3: Build Knowledge Base")
    logger.info("="*80)
    
    kb = WorkflowKnowledgeBase("output/ab_test")
    
    # Collect reviewed tests
    logger.info("\n📚 Collecting reviewed A/B tests...")
    reviewed = kb.collect_reviewed_tests()
    
    logger.info(f"   Found {len(reviewed)} reviewed tests")
    
    if not reviewed:
        logger.warning("\n⚠️  No reviewed tests found!")
        logger.info("   To create reviewed tests:")
        logger.info("   1. Run example 1 to generate A/B tests")
        logger.info("   2. Watch videos and annotate manifests")
        logger.info("   3. Run this example again")
        return
    
    # Show summary
    logger.info(f"\n📊 Review Summary:")
    interpolation_wins = sum(1 for t in reviewed if t['review_notes']['winner'] == 'interpolation')
    ingredients_wins = sum(1 for t in reviewed if t['review_notes']['winner'] == 'ingredients')
    
    logger.info(f"   Interpolation wins: {interpolation_wins}")
    logger.info(f"   Ingredients wins: {ingredients_wins}")
    
    # Generate training data
    logger.info(f"\n🔨 Generating training data...")
    training_data = kb.generate_training_data()
    
    for item in training_data:
        logger.info(f"\n  Scene: {item['scene_id']}")
        logger.info(f"    Camera: {item['scene_metadata']['camera_movement']}")
        logger.info(f"    Winner: {item['winner']}")
        logger.info(f"    Notes: {item['notes'][:60]}...")
    
    # Export knowledge base
    output_path = "output/workflow_knowledge_base.json"
    kb.export_knowledge_base(output_path)
    
    logger.info(f"\n💡 Next steps:")
    logger.info(f"   1. Use training data to improve LLM prompts")
    logger.info(f"   2. Identify patterns in winning workflows")
    logger.info(f"   3. Fine-tune decision criteria")


async def example_manual_review_template():
    """
    Example 4: Show manual review template
    
    Demonstrates how to fill out review notes.
    """
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 4: Manual Review Template")
    logger.info("="*80)
    
    template = {
        "scene_id": "S1_dolly_push",
        "timestamp": 1234567890,
        "results": {
            "interpolation": "output/S1_dolly_push_interpolation.mp4",
            "ingredients": "output/S1_dolly_push_ingredients.mp4"
        },
        "scene_metadata": {
            "duration": 4.0,
            "camera_movement": "dolly",
            "camera_description": "Smooth push in from medium to close-up"
        },
        "review_notes": {
            "interpolation_quality": "4",
            "interpolation_notes": "Smooth motion, good continuity, slight blur at end",
            "ingredients_quality": "3",
            "ingredients_notes": "Character consistent but motion feels less natural",
            "winner": "interpolation",
            "overall_notes": "Interpolation works well for this dolly shot. Smooth camera movement and good visual continuity."
        }
    }
    
    logger.info("\n📝 Review Template:")
    logger.info(json.dumps(template, indent=2))
    
    logger.info("\n📋 Review Guidelines:")
    logger.info("  Quality ratings (1-5):")
    logger.info("    5 = Excellent - Professional quality")
    logger.info("    4 = Good - Minor issues")
    logger.info("    3 = Acceptable - Noticeable issues")
    logger.info("    2 = Poor - Significant problems")
    logger.info("    1 = Failed - Unusable")
    
    logger.info("\n  What to evaluate:")
    logger.info("    - Motion smoothness")
    logger.info("    - Visual continuity")
    logger.info("    - Character consistency")
    logger.info("    - Prompt adherence")
    logger.info("    - Overall quality")


async def main():
    """Run all A/B testing examples"""
    logger.info("="*80)
    logger.info("A/B Testing Workflow Examples")
    logger.info("="*80)
    
    # Run examples
    await example_generate_ab_tests()
    await example_review_ab_tests()
    await example_build_knowledge_base()
    await example_manual_review_template()
    
    logger.info("\n" + "="*80)
    logger.info("All examples completed!")
    logger.info("="*80)
    
    logger.info("\n📚 Key Takeaways:")
    logger.info("  1. A/B testing helps determine best workflow for scene types")
    logger.info("  2. Manual review provides ground truth for quality")
    logger.info("  3. Knowledge base enables continuous improvement")
    logger.info("  4. Training data can improve LLM decisions")
    
    logger.info("\n🔄 A/B Testing Workflow:")
    logger.info("  1. Generate → Create videos with both workflows")
    logger.info("  2. Review → Watch and annotate quality")
    logger.info("  3. Learn → Build knowledge base from reviews")
    logger.info("  4. Improve → Use insights to refine decisions")


if __name__ == "__main__":
    asyncio.run(main())
