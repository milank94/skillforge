"""
Enumerations for constant values.

This module defines enums for difficulty levels, LLM providers, and other
constant values used throughout the application.
"""

from enum import Enum


class Difficulty(str, Enum):
    """
    Course difficulty levels.

    Inherits from str to allow direct string comparison and serialization.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LLMProvider(str, Enum):
    """
    Supported LLM providers.

    Inherits from str to allow direct string comparison and serialization.
    """

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ProgressStatus(str, Enum):
    """
    Status of progress through a learning component.

    Inherits from str to allow direct string comparison and serialization.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionState(str, Enum):
    """
    State of an active learning session.

    Inherits from str to allow direct string comparison and serialization.
    """

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
