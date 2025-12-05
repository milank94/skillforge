"""Core functionality for SkillForge.

This package contains the core components for course generation, command simulation,
and exercise validation.
"""

from skillforge.core.course_generator import CourseGenerator
from skillforge.core.simulator import (
    CommandSimulator,
    SimulationResult,
    VirtualFileSystem,
)

__all__ = [
    "CourseGenerator",
    "CommandSimulator",
    "SimulationResult",
    "VirtualFileSystem",
]
