"""
Data models for SkillForge.

This package contains Pydantic models for representing courses, lessons,
exercises, configuration settings, and progress tracking.
"""

from .config import AppConfig, LLMConfig
from .course import Course
from .enums import Difficulty, LLMProvider, ProgressStatus
from .lesson import Exercise, Lesson
from .progress import CourseProgress, ExerciseProgress, LessonProgress

__all__ = [
    "Course",
    "Lesson",
    "Exercise",
    "AppConfig",
    "LLMConfig",
    "Difficulty",
    "LLMProvider",
    "ProgressStatus",
    "ExerciseProgress",
    "LessonProgress",
    "CourseProgress",
]
