"""Type definitions for the ImageBreak framework."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class ModelType(Enum):
    """Supported model types."""
    TEXT_GENERATION = "text_generation"
    IMAGE_GENERATION = "image_generation"
    MULTIMODAL = "multimodal"


class ResponseStatus(Enum):
    """Response status codes."""
    SUCCESS = 1
    BLOCKED_BY_FILTER = 0
    ERROR = -1
    TIMEOUT = -2


@dataclass
class ModelResponse:
    """Response from a model API call."""
    content: Optional[str] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    status: ResponseStatus = ResponseStatus.SUCCESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    

@dataclass
class PromptData:
    """Data structure for prompts and their metadata."""
    original_prompt: str
    altered_prompt: Optional[str] = None
    topic: Optional[str] = None
    policy_violations: List[str] = field(default_factory=list)
    generation_method: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModerationResult:
    """Result from content moderation analysis."""
    image_path: str
    labels: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    flagged: bool = False
    service: str = "unknown"
    

@dataclass
class TestResult:
    """Complete test result for a prompt."""
    prompt_data: PromptData
    model_name: str
    response: ModelResponse
    moderation_result: Optional[ModerationResult] = None
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    test_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BatchTestResults:
    """Results from a batch of tests."""
    results: List[TestResult]
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    

# Type aliases for common usage
PromptList = List[str]
PolicyText = str
APIKey = str 