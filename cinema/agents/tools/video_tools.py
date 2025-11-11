"""
Video processing tools using ffmpeg.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class VideoTools:
    """Tools for video frame extraction and analysis."""

    @staticmethod
    def extract_frame(
        video_path: str,
        output_path: str,
        frame_position: str = "last",
    ) -> Optional[str]:
        """
        Extract a frame from video using ffmpeg.
        
        Args:
            video_path: Path to input video
            output_path: Path to save extracted frame
            frame_position: "first", "last", or timestamp like "00:00:01.5"
        
        Returns:
            Path to extracted frame or None if failed
        """
        video_file = Path(video_path)
        if not video_file.exists():
            logger.error(f"Video not found: {video_path}")
            return None
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if frame_position == "first":
                # Extract first frame
                cmd = [
                    "ffmpeg",
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-y",
                    str(output_path),
                ]
            elif frame_position == "last":
                # Extract last frame
                cmd = [
                    "ffmpeg",
                    "-sseof", "-1",
                    "-i", str(video_path),
                    "-update", "1",
                    "-q:v", "1",
                    "-y",
                    str(output_path),
                ]
            else:
                # Extract frame at specific timestamp
                cmd = [
                    "ffmpeg",
                    "-ss", frame_position,
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-y",
                    str(output_path),
                ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            
            if output_file.exists():
                logger.info(f"Extracted {frame_position} frame to: {output_path}")
                return str(output_path)
            else:
                logger.error(f"Frame extraction failed: {result.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to extract frame: {e}")
            return None

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[float]:
        """
        Get video duration in seconds.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Duration in seconds or None if failed
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            return None

    @staticmethod
    def detect_scene_changes(
        video_path: str,
        threshold: float = 0.3,
    ) -> list[float]:
        """
        Detect scene changes in video.
        
        Args:
            video_path: Path to video file
            threshold: Scene change detection threshold (0.0-1.0)
        
        Returns:
            List of timestamps where scene changes occur
        """
        try:
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-filter:v", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null",
                "-",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            
            # Parse scene change timestamps from ffmpeg output
            timestamps = []
            for line in result.stderr.split('\n'):
                if 'Parsed_showinfo' in line and 'pts_time:' in line:
                    try:
                        pts_time = line.split('pts_time:')[1].split()[0]
                        timestamps.append(float(pts_time))
                    except (IndexError, ValueError):
                        continue
            
            logger.info(f"Detected {len(timestamps)} scene changes")
            return timestamps
            
        except Exception as e:
            logger.error(f"Failed to detect scene changes: {e}")
            return []

    @staticmethod
    def trim_video(
        input_path: str,
        output_path: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> bool:
        """
        Trim video to specified time range.
        
        Args:
            input_path: Path to input video
            output_path: Path to save trimmed video
            start_time: Start time in seconds (None = from beginning)
            end_time: End time in seconds (None = to end)
        
        Returns:
            True if successful, False otherwise
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cmd = ["ffmpeg"]
            
            if start_time is not None:
                cmd.extend(["-ss", str(start_time)])
            
            cmd.extend(["-i", str(input_path)])
            
            if end_time is not None:
                if start_time is not None:
                    duration = end_time - start_time
                else:
                    duration = end_time
                cmd.extend(["-t", str(duration)])
            
            cmd.extend([
                "-c", "copy",
                "-y",
                str(output_path),
            ])
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Trimmed video saved to: {output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to trim video: {e.stderr}")
            return False

    @staticmethod
    def concat_videos(
        video_paths: list[str],
        output_path: str,
    ) -> bool:
        """
        Concatenate multiple videos.
        
        Args:
            video_paths: List of video file paths to concatenate
            output_path: Path to save concatenated video
        
        Returns:
            True if successful, False otherwise
        """
        if not video_paths:
            logger.error("No videos to concatenate")
            return False
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create concat file list
        concat_file = output_file.parent / "concat_list.txt"
        
        try:
            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{Path(video_path).absolute()}'\n")
            
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-y",
                str(output_path),
            ]
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Concatenated {len(video_paths)} videos to: {output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to concatenate videos: {e.stderr}")
            return False
        finally:
            if concat_file.exists():
                concat_file.unlink()
