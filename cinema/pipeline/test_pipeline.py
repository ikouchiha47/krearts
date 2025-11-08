"""
Tests for pipeline infrastructure.
"""

import asyncio
import tempfile
from pathlib import Path

from cinema.pipeline.job_tracker import JobTracker
from cinema.pipeline.pipeline import Pipeline, Runner
from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState


# Mock runners for testing
class AddOneRunner(Runner[int, int]):
    async def run(self, inputs: int) -> int:
        return inputs + 1


class MultiplyByTwoRunner(Runner[int, int]):
    async def run(self, inputs: int) -> int:
        return inputs * 2


class ToStringRunner(Runner[int, str]):
    async def run(self, inputs: int) -> str:
        return f"Result: {inputs}"


async def test_basic_pipeline():
    """Test basic pipeline chaining"""
    print("Testing basic pipeline...")

    pipeline = (
        Pipeline()
        .then(AddOneRunner())
        .then(MultiplyByTwoRunner())
        .then(ToStringRunner())
    )

    result = await pipeline.execute(5)
    assert result == "Result: 12", f"Expected 'Result: 12', got '{result}'"

    print("✓ Basic pipeline works")


async def test_pipeline_state():
    """Test pipeline state management"""
    print("\nTesting pipeline state...")

    state = PipelineState.create("test_movie", "./test_output")

    # Test directory paths
    assert state.movie_id == "test_movie"
    assert state.base_dir == Path("./test_output/test_movie")
    assert state.characters_dir == Path("./test_output/test_movie/characters")

    # Test job management
    job = Job(
        id="test_job_1",
        type=JobType.CHARACTER,
        character_id=1,
        metadata={"view": "front"},
    )

    state.add_job(job)
    assert len(state.jobs) == 1

    retrieved = state.get_job("test_job_1")
    assert retrieved is not None
    assert retrieved.id == "test_job_1"

    # Test stage completion
    assert not state.is_stage_complete(JobType.CHARACTER)
    state.mark_stage_complete(JobType.CHARACTER)
    assert state.is_stage_complete(JobType.CHARACTER)

    print("✓ Pipeline state works")


def test_job_tracker():
    """Test job tracker persistence"""
    print("\nTesting job tracker...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        tracker = JobTracker(db_path)

        # Create and save a job
        job = Job(
            id="test_job_1",
            type=JobType.IMAGE,
            scene_id="scene_1",
            metadata={"frame_type": "first_frame"},
        )

        tracker.save_job(job, "test_movie")

        # Retrieve job
        retrieved = tracker.get_job("test_job_1")
        assert retrieved is not None
        assert retrieved.id == "test_job_1"
        assert retrieved.scene_id == "scene_1"

        # Update status
        tracker.update_job_status("test_job_1", JobStatus.COMPLETED)

        retrieved = tracker.get_job("test_job_1")
        assert retrieved.status == JobStatus.COMPLETED

        # Test state persistence
        state = PipelineState.create("test_movie_2", "./test_output")
        state.add_job(
            Job(
                id="job_1",
                type=JobType.VIDEO,
                scene_id="scene_1",
            )
        )
        state.mark_stage_complete(JobType.SCREENPLAY)

        tracker.save_state(state)

        # Load state
        loaded = tracker.load_state("test_movie_2", "./test_output")
        assert loaded is not None
        assert loaded.movie_id == "test_movie_2"
        assert loaded.screenplay_complete
        assert len(loaded.jobs) == 1

        # Test progress tracking
        progress = tracker.get_progress("test_movie")
        assert progress["total"] == 1
        assert progress["completed"] == 1

        print("✓ Job tracker works")

    finally:
        Path(db_path).unlink(missing_ok=True)


async def test_state_runner():
    """Test runner that modifies state"""
    print("\nTesting state runner...")

    class AddJobRunner(Runner[PipelineState, PipelineState]):
        async def run(self, inputs: PipelineState) -> PipelineState:
            state = inputs
            job = Job(
                id=f"job_{len(state.jobs) + 1}",
                type=JobType.IMAGE,
                scene_id="scene_1",
            )
            state.add_job(job)
            return state

    class CompleteJobsRunner(Runner[PipelineState, PipelineState]):
        async def run(self, inputs: PipelineState) -> PipelineState:
            state = inputs
            for job in state.jobs:
                job.status = JobStatus.COMPLETED
            return state

    # Build pipeline
    pipeline = Pipeline().then(AddJobRunner()).then(CompleteJobsRunner())

    # Execute
    initial_state = PipelineState.create("test_movie", "./test_output")
    final_state = await pipeline.execute(initial_state)

    assert len(final_state.jobs) == 1
    assert final_state.jobs[0].status == JobStatus.COMPLETED

    print("✓ State runner works")


def test_path_helpers():
    """Test path helper methods"""
    print("\nTesting path helpers...")

    state = PipelineState.create("test_movie", "./test_output")

    # Character paths
    char_path = state.get_character_image_path(1, "front")
    assert char_path == Path("./test_output/test_movie/characters/char_1_front.png")

    # Scene image paths
    img_path = state.get_scene_image_path("scene_1", "first_frame")
    assert img_path == Path("./test_output/test_movie/images/scene_1_first_frame.png")

    # Video paths
    video_path = state.get_scene_video_path("scene_1")
    assert video_path == Path("./test_output/test_movie/videos/scene_1.mp4")

    # Audio paths
    audio_path = state.get_scene_audio_path("scene_1")
    assert audio_path == Path("./test_output/test_movie/audio/scene_1.mp3")

    # Final video path
    final_path = state.get_final_video_path()
    assert final_path == Path("./test_output/test_movie/output/test_movie_final.mp4")

    print("✓ Path helpers work")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Pipeline Tests")
    print("=" * 60)

    await test_basic_pipeline()
    await test_pipeline_state()
    test_job_tracker()
    await test_state_runner()
    test_path_helpers()

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
