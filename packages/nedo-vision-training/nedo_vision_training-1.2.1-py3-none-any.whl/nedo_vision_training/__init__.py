"""
Nedo Vision Training Service Library

A comprehensive library for training AI models in the Nedo Vision platform.
This library provides tools and services for training computer vision models,
managing training workflows, and integrating with the broader Nedo Vision ecosystem.

Features:
- AI model training orchestration
- gRPC-based service communication
- AWS integration for cloud resources
- GPU monitoring and management
- Flexible training pipeline configuration

Example:
    >>> from nedo_vision_training import TrainingService
    >>> service = TrainingService()
    >>> # Configure and start training...
"""

from .training_service import TrainingService
from .exceptions import TrainingServiceError, ConfigurationError

__version__ = "1.2.1"
__author__ = "Willy Achmat Fauzi"
__email__ = "willy.achmat@gmail.com"
__license__ = "MIT"
__title__ = "nedo-vision-training"
__description__ = "A comprehensive training service library for AI models in the Nedo Vision platform"
__url__ = "https://gitlab.com/sindika/research/nedo-vision/nedo-vision-training-service"

__all__ = [
    "TrainingService", 
    "TrainingServiceError", 
    "ConfigurationError",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__title__",
    "__description__",
    "__url__",
] 