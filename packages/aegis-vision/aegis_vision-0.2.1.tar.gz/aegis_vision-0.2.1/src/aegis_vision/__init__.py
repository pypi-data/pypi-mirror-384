"""
Aegis Vision - Computer Vision Training Utilities

A Python package for training computer vision models on cloud platforms like Kaggle.
Focused on YOLO object detection with support for multiple model variants and export formats.
"""

__version__ = "0.2.0"
__author__ = "Aegis AI Team"
__license__ = "MIT"

from .trainer import YOLOTrainer
from .converters import COCOConverter, DatasetMerger
from .utils import (
    setup_logging,
    get_device_info,
    detect_environment,
    format_size,
    format_time,
)

__all__ = [
    "YOLOTrainer",
    "COCOConverter",
    "DatasetMerger",
    "setup_logging",
    "get_device_info",
    "detect_environment",
    "format_size",
    "format_time",
]
