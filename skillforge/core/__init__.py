"""Core functionality for SkillForge.

This package contains the core components for course generation, command simulation,
and exercise validation.
"""

from skillforge.core.course_generator import CourseGenerator
from skillforge.core.session import SessionManager, find_saved_sessions
from skillforge.core.simulator import (
    CommandSimulator,
    SimulationResult,
    VirtualFileSystem,
)
from skillforge.core.validator import (
    ExerciseValidator,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    "CourseGenerator",
    "CommandSimulator",
    "SimulationResult",
    "VirtualFileSystem",
    "ExerciseValidator",
    "ValidationResult",
    "ValidationStatus",
    "SessionManager",
    "find_saved_sessions",
]
