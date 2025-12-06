#!/usr/bin/env python3
"""
Evaluate frame consistency between generated videos and keyframe images.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import imagehash
from PIL import Image

from cinema.agents.tools.compare_images import CompareImagesWithLLM, CompareImageHashes
from cinema.agents.tools.video_tools import VideoTools
from cinema.providers.shared import MediaLib
from cinema.transformers.screenplay_extractors import extract_all_stages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameConsistencyEvaluator:
    """Evaluates consistency between video frames and keyframe images."""

    def __init__(
        self,
        movie_id: str,
        base_dir: str = "./output",
        phash_threshold: int = 15,
        dhash_threshold: int = 15,
        use_llm: bool = True,
    ):
        self.movie_id = movie_id
        self.base_dir = Path(base_dir) / movie_id
        self.phash_threshold = phash_threshold
        self.dhash_threshold = dhash_threshold
        self.use_llm = use_llm
        self.video_tools = VideoTools()
        
        # Initialize comparators
        self.medialib = MediaLib()
        if use_llm:
            self.llm_comparator = CompareImagesWithLLM(
                medialib=self.medialib, 
                allow_insecure=True
            )

    def load_screenplay(self) -> Optional[dict]:
        """Load screenplay JSON from database."""
        from cinema.pipeline.job_tracker import JobTracker
        
        tracker = JobTracker()
        state = tracker.load_state(self.movie_id, str(self.base_dir.parent))
        
        if not state or not state.screenplay_dict:
            logger.error(f"No screenplay found for movie_id: {self.movie_id}")
            return None
        
        logger.info(f"Loaded screenplay from database for movie: {self.movie_id}")
        return state.screenplay_dict

    def compare_images(self, img1_path: str, img2_path: str) -> dict:
        """Compare two images using perceptual hashes."""
        img1 = Image.open(img1_path)
        img2 = Image.open(img2_path)
        
        phash1 = imagehash.phash(img1)
        phash2 = imagehash.phash(img2)
        phash_diff = int(phash1 - phash2)
        
        dhash1 = imagehash.dhash(img1)
        dhash2 = imagehash.dhash(img2)
        dhash_diff = int(dhash1 - dhash2)
        
        is_similar = (
            phash_diff <= self.phash_threshold and
            dhash_diff <= self.dhash_threshold
        )
        
        return {
            "phash_diff": phash_diff,
            "dhash_diff": dhash_diff,
            "is_similar": is_similar,
        }

    def evaluate_last_frame_consistency(self) -> dict:
        """
        Evaluate consistency between video last frames and keyframe images.
        
        Returns:
            Dictionary with evaluation results per scene
        """
        screenplay = self.load_screenplay()
        if not screenplay:
            return {}
        
        extracted = extract_all_stages(screenplay)
        video_stage = extracted["videos"]
        
        results = {}
        
        for video_spec in video_stage.videos:
            scene_id = video_spec.scene_id
            
            # Check if scene has last_frame
            if not video_spec.needs_last_frame():
                logger.info(f"Scene {scene_id}: No last_frame specified, skipping")
                continue
            
            # Paths
            video_path = self.base_dir / "videos" / f"{scene_id}.mp4"
            keyframe_path = self.base_dir / "images" / f"{scene_id}_last_frame.png"
            extracted_frame_path = self.base_dir / "evals" / f"{scene_id}_video_last_frame.png"
            
            if not video_path.exists():
                logger.warning(f"Scene {scene_id}: Video not found")
                results[scene_id] = {"status": "video_missing"}
                continue
            
            if not keyframe_path.exists():
                logger.warning(f"Scene {scene_id}: Keyframe not found")
                results[scene_id] = {"status": "keyframe_missing"}
                continue
            
            # Extract last frame from video
            logger.info(f"Scene {scene_id}: Extracting last frame from video")
            extracted_frame = self.video_tools.extract_frame(
                str(video_path),
                str(extracted_frame_path),
                frame_position="last",
            )
            
            if not extracted_frame:
                logger.error(f"Scene {scene_id}: Failed to extract frame")
                results[scene_id] = {"status": "extraction_failed"}
                continue
            
            # Compare frames with hash
            logger.info(f"Scene {scene_id}: Comparing frames (hash)")
            comparison = self.compare_images(str(keyframe_path), extracted_frame)
            
            result = {
                "status": "evaluated",
                "video_path": str(video_path),
                "keyframe_path": str(keyframe_path),
                "extracted_frame_path": extracted_frame,
                "hash_comparison": comparison,
            }
            
            # LLM comparison
            if self.use_llm:
                logger.info(f"Scene {scene_id}: Comparing frames (LLM)")
                llm_result = self.llm_comparator.run(
                    image_urls=[str(keyframe_path), extracted_frame],
                    action="Compare these two frames. Are they consistent? Describe any differences in composition, lighting, or content."
                )
                result["llm_comparison"] = {
                    "message": llm_result.message,
                    "evaluator": llm_result.evaluator,
                }
            
            results[scene_id] = result
            
            status = "✅ PASS" if comparison["is_similar"] else "❌ FAIL"
            logger.info(
                f"Scene {scene_id}: {status} "
                f"(phash={comparison['phash_diff']}, dhash={comparison['dhash_diff']})"
            )
        
        return results

    def evaluate_scene_transitions(self) -> dict:
        """
        Evaluate scene transitions by comparing adjacent video frames.
        
        Returns:
            Dictionary with transition evaluation results
        """
        screenplay = self.load_screenplay()
        if not screenplay:
            return {}
        
        extracted = extract_all_stages(screenplay)
        video_stage = extracted["videos"]
        image_stage = extracted["images"]
        
        results = {}
        videos = video_stage.videos
        
        for i in range(len(videos) - 1):
            curr_scene = videos[i]
            next_scene = videos[i + 1]
            
            curr_video_path = self.base_dir / "videos" / f"{curr_scene.scene_id}.mp4"
            next_video_path = self.base_dir / "videos" / f"{next_scene.scene_id}.mp4"
            
            if not curr_video_path.exists() or not next_video_path.exists():
                logger.warning(f"Transition {curr_scene.scene_id}->{next_scene.scene_id}: Videos missing")
                continue
            
            # Extract frames at transition boundary
            curr_last_frame_path = self.base_dir / "evals" / f"{curr_scene.scene_id}_transition_last.png"
            next_first_frame_path = self.base_dir / "evals" / f"{next_scene.scene_id}_transition_first.png"
            
            logger.info(f"Evaluating transition: {curr_scene.scene_id} -> {next_scene.scene_id}")
            
            # Extract last frame of current video
            self.video_tools.extract_frame(
                str(curr_video_path),
                str(curr_last_frame_path),
                frame_position="last",
            )
            
            # Extract first frame of next video
            self.video_tools.extract_frame(
                str(next_video_path),
                str(next_first_frame_path),
                frame_position="first",
            )
            
            # Compare with keyframe images
            curr_keyframe = self.base_dir / "images" / f"{curr_scene.scene_id}_last_frame.png"
            next_keyframe = self.base_dir / "images" / f"{next_scene.scene_id}_first_frame.png"
            
            transition_key = f"{curr_scene.scene_id}->{next_scene.scene_id}"
            results[transition_key] = {}
            
            # Compare current video last frame with keyframe
            if curr_keyframe.exists():
                comp1 = self.compare_images(str(curr_keyframe), str(curr_last_frame_path))
                results[transition_key]["curr_last_frame"] = comp1
            
            # Compare next video first frame with keyframe
            if next_keyframe.exists():
                comp2 = self.compare_images(str(next_keyframe), str(next_first_frame_path))
                results[transition_key]["next_first_frame"] = comp2
            
            # Compare transition boundary frames
            comp3 = self.compare_images(str(curr_last_frame_path), str(next_first_frame_path))
            results[transition_key]["transition_boundary"] = comp3
            
            # LLM comparison for transition
            if self.use_llm:
                logger.info(f"Transition {transition_key}: LLM analysis")
                llm_result = self.llm_comparator.run(
                    image_urls=[str(curr_last_frame_path), str(next_first_frame_path)],
                    action="Analyze this scene transition. Is it smooth? Describe any jarring changes in lighting, composition, or continuity."
                )
                results[transition_key]["llm_analysis"] = {
                    "message": llm_result.message,
                    "evaluator": llm_result.evaluator,
                }
            
            logger.info(
                f"Transition {transition_key}: "
                f"boundary_diff={comp3['phash_diff']}/{comp3['dhash_diff']}"
            )
        
        return results

    def run_evaluation(self) -> dict:
        """Run full evaluation suite."""
        logger.info(f"{'='*60}")
        logger.info(f"Frame Consistency Evaluation - Movie ID: {self.movie_id}")
        logger.info(f"{'='*60}")
        
        # Create evals directory
        evals_dir = self.base_dir / "evals"
        evals_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "movie_id": self.movie_id,
            "last_frame_consistency": self.evaluate_last_frame_consistency(),
            "scene_transitions": self.evaluate_scene_transitions(),
        }
        
        # Save results
        results_file = evals_dir / "frame_consistency_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Evaluation complete. Results saved to: {results_file}")
        logger.info(f"{'='*60}")
        
        return results


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python frame_consistency_eval.py <movie_id>")
        sys.exit(1)
    
    movie_id = sys.argv[1]
    evaluator = FrameConsistencyEvaluator(movie_id)
    evaluator.run_evaluation()


if __name__ == "__main__":
    main()
