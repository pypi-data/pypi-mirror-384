"""
Utility functions for Aegis Vision
"""

import os
import sys
import logging
from typing import Dict, Optional
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )


def get_device_info() -> Dict[str, any]:
    """
    Get information about available compute devices
    
    Returns:
        Dictionary containing device information
    """
    import torch
    
    info = {
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "device_name": None,
        "compute_capability": None,
    }
    
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        info["compute_capability"] = f"{capability[0]}.{capability[1]}"
    
    return info


def detect_environment() -> str:
    """
    Detect the current execution environment
    
    Returns:
        Environment name: 'kaggle', 'colab', 'local'
    """
    if os.path.exists('/kaggle'):
        return 'kaggle'
    elif os.path.exists('/content') and os.path.exists('/usr/local/lib/python3.10/dist-packages/google/colab'):
        return 'colab'
    else:
        return 'local'


def get_kaggle_paths() -> Dict[str, Path]:
    """
    Get standard Kaggle paths
    
    Returns:
        Dictionary of Kaggle paths
    """
    return {
        "input": Path("/kaggle/input"),
        "working": Path("/kaggle/working"),
        "temp": Path("/kaggle/temp"),
    }


def ensure_directory(path: str) -> Path:
    """
    Ensure directory exists, create if necessary
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def format_size(bytes: int) -> str:
    """
    Format bytes to human-readable size
    
    Args:
        bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def format_time(seconds: float) -> str:
    """
    Format seconds to human-readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {secs}s"
    
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m {secs}s"


