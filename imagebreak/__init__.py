"""
ImageBreak: A framework for testing AI model safety and content moderation systems.

This package provides tools to evaluate how well AI models handle potentially harmful
prompts and helps researchers identify vulnerabilities in content filtering systems.
"""

__version__ = "1.0.1"
__author__ = "ImageBreak Contributors"
__email__ = "ardada2468@gmail.com"

from .core.framework import ImageBreakFramework
from .core.config import Config
from .types import ModelResponse, TestResult, PromptData, ResponseStatus
from .models.openai_model import OpenAIModel
from .models.gemini_model import GeminiModel

__all__ = [
    "ImageBreakFramework",
    "Config", 
    "ModelResponse",
    "TestResult",
    "PromptData",
    "ResponseStatus",
    "OpenAIModel",
    "GeminiModel",
] 