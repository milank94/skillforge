"""
Data models for SkillForge.

This package contains Pydantic models for representing courses, lessons,
exercises, configuration settings, progress tracking, and session management.
"""

from .config import AppConfig, LLMConfig
from .course import Course
from .enums import Difficulty, LLMProvider, ProgressStatus, SessionState
from .lesson import Exercise, Lesson
from .progress import CourseProgress, ExerciseProgress, LessonProgress
from .session import LearningSession

__all__ = [
    "Course",
    "Lesson",
    "Exercise",
    "AppConfig",
    "LLMConfig",
    "Difficulty",
    "LLMProvider",
    "ProgressStatus",
    "SessionState",
    "ExerciseProgress",
    "LessonProgress",
    "CourseProgress",
    "LearningSession",
]
