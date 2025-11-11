"""
Learning session management models.

This module defines models for managing active learning sessions,
tracking the current state of a user's interaction with a course.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .course import Course
from .enums import SessionState
from .progress import CourseProgress


class LearningSession(BaseModel):
    """
    Manages an active learning session.

    A session represents a user's current interaction with a course,
    tracking the active state, current position, and linking to both
    the course content and progress tracking.

    Attributes:
        session_id: Unique identifier for this session
        course: The course being studied
        progress: Progress tracking for this course
        state: Current state of the session
        current_lesson_id: ID of the lesson currently being studied
        current_exercise_id: ID of the exercise currently being attempted
        created_at: When the session was created
        last_activity_at: Last time the session was active
        paused_at: When the session was paused (if applicable)
        completed_at: When the session was completed (if applicable)
    """

    session_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique session identifier",
    )
    course: Course = Field(..., description="The course being studied")
    progress: CourseProgress = Field(..., description="Progress tracking")
    state: SessionState = Field(
        default=SessionState.ACTIVE, description="Current session state"
    )
    current_lesson_id: Optional[str] = Field(None, description="Current lesson ID")
    current_exercise_id: Optional[str] = Field(None, description="Current exercise ID")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Session creation time"
    )
    last_activity_at: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )
    paused_at: Optional[datetime] = Field(
        None, description="When the session was paused"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When the session was completed"
    )
