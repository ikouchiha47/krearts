"""
Logging configuration for Cinema workflow.

Two loggers:
1. Root logger -> file (all verbose logs including crew)
2. User logger -> stdout (clean user-facing output only)

CrewAI uses print() directly, so we redirect stdout/stderr to capture it.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from io import TextIOWrapper


# Initialize user logger at module level with console output
_user_logger = logging.getLogger('cinema.user')
_user_logger.setLevel(logging.INFO)
_user_logger.propagate = False

# Add console handler by default
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter('%(message)s'))
_user_logger.addHandler(_console_handler)


class TeeStream:
    """Stream that writes to both file and original stream"""
    def __init__(self, file_stream, original_stream):
        self.file_stream = file_stream
        self.original_stream = original_stream
    
    def write(self, data):
        self.file_stream.write(data)
        self.file_stream.flush()
        # Don't write to original - we want crew output only in file
        return len(data)
    
    def flush(self):
        self.file_stream.flush()
    
    def isatty(self):
        return False


def setup_logging(workflow_id: str = None, log_dir: str = "logs", suppress_crew_output: bool = True):
    """
    Setup dual logging system.
    
    Args:
        workflow_id: Workflow ID for log file naming
        log_dir: Directory for log files
        suppress_crew_output: If True, redirect crew stdout/stderr to log file
    
    Returns:
        tuple: (user_logger, log_file_path, cleanup_function)
    """
    # Create log directory
    log_path = Path(log_dir)
    if log_path.exists() and not log_path.is_dir():
        # If 'logs' exists as a file, use 'workflow_logs' instead
        log_path = Path("workflow_logs")
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if workflow_id:
        log_file = log_path / f"workflow_{workflow_id}_{timestamp}.log"
    else:
        log_file = log_path / f"cinema_{timestamp}.log"
    
    # Configure root logger (all logs to file ONLY)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # File handler - verbose format
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Save original stdout/stderr BEFORE any redirection
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Update the global user logger to also write to file
    # Remove existing console handler and replace with one using original stdout
    _user_logger.handlers.clear()
    
    user_console = logging.StreamHandler(original_stdout)
    user_console.setLevel(logging.INFO)
    user_formatter = logging.Formatter('%(message)s')
    user_console.setFormatter(user_formatter)
    _user_logger.addHandler(user_console)
    
    # User logger also writes to file
    _user_logger.addHandler(file_handler)
    
    # Redirect stdout/stderr to capture CrewAI print() calls
    cleanup_func = None
    if suppress_crew_output:
        # Open file for crew output
        crew_log_file = open(log_file, 'a', encoding='utf-8', buffering=1)  # Line buffered
        
        # Create tee streams
        tee_stdout = TeeStream(crew_log_file, original_stdout)
        tee_stderr = TeeStream(crew_log_file, original_stderr)
        
        # Redirect
        sys.stdout = tee_stdout
        sys.stderr = tee_stderr
        
        # Cleanup function to restore streams
        def cleanup():
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            crew_log_file.close()
        
        cleanup_func = cleanup
    
    # Log startup
    root_logger.info(f"Logging initialized: {log_file}")
    _user_logger.info(f"📝 Logs: {log_file}")
    
    return _user_logger, log_file, cleanup_func


def get_user_logger():
    """Get the user-facing logger"""
    return _user_logger


# Convenience functions for user output
def user_info(msg: str):
    """Log user-facing info message"""
    get_user_logger().info(msg)


def user_success(msg: str):
    """Log user-facing success message"""
    get_user_logger().info(f"✅ {msg}")


def user_error(msg: str):
    """Log user-facing error message"""
    get_user_logger().error(f"❌ {msg}")


def user_section(title: str):
    """Log section header"""
    logger = get_user_logger()
    logger.info("")
    logger.info("=" * 80)
    logger.info(title)
    logger.info("=" * 80)


def user_output(label: str, content: str, preview_length: int = 500):
    """
    Log user output with preview.
    
    Args:
        label: Label for the output (e.g., "Storyline", "Novel")
        content: Full content
        preview_length: Number of characters to show in preview
    """
    logger = get_user_logger()
    logger.info(f"\n{label}:")
    logger.info("-" * 80)
    
    if len(content) <= preview_length:
        logger.info(content)
    else:
        logger.info(content[:preview_length])
        logger.info(f"\n... ({len(content) - preview_length} more characters)")
        logger.info(f"\nTotal length: {len(content)} characters")
    
    logger.info("-" * 80)
