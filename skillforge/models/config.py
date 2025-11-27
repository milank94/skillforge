"""
Configuration data models.

This module defines the structure for application and LLM configuration.
"""

from pydantic import BaseModel, Field

from .enums import LLMProvider


class LLMConfig(BaseModel):
    """
    Configuration for LLM (Large Language Model) integration.

    Attributes:
        provider: LLM provider (LLMProvider enum)
        model: Model identifier (e.g., "claude-sonnet-4-5-20250929")
        temperature: Sampling temperature for response generation (0.0-1.0)
    """

    provider: LLMProvider = Field(..., description="LLM provider")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(
        0.7, description="Sampling temperature (0.0-1.0)", ge=0.0, le=1.0
    )


class AppConfig(BaseModel):
    """
    Application-wide configuration settings.

    Attributes:
        llm: LLM configuration settings
        data_dir: Directory for storing user data and progress
    """

    llm: LLMConfig = Field(..., description="LLM configuration")
    data_dir: str = Field(
        "~/.skillforge", description="Directory for user data and progress"
    )
