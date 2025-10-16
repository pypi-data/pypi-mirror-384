"""
Aegis Vision - Cloud-native computer vision model training toolkit

A streamlined toolkit for training computer vision models (YOLO, etc.)
in cloud environments with built-in Wandb integration and dataset conversion.
"""

__version__ = "0.1.0"
__author__ = "Aegis AI Team"
__license__ = "MIT"

from aegis_vision.trainer import YOLOTrainer
from aegis_vision.converters import COCOConverter
from aegis_vision.utils import (
    get_device_info,
    setup_logging,
    detect_environment,
    get_kaggle_paths,
    ensure_directory,
    format_size,
    format_time,
)

__all__ = [
    "YOLOTrainer",
    "COCOConverter",
    "get_device_info",
    "setup_logging",
    "detect_environment",
    "get_kaggle_paths",
    "ensure_directory",
    "format_size",
    "format_time",
    "__version__",
]


