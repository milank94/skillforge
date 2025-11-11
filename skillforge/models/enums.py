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
