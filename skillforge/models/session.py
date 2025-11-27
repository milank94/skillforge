"""
Learning session management models.

This module defines models for managing active learning sessions,
tracking the current state of a user's interaction with a course.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .course import Course
from .enums import SessionState
from .progress import CourseProgress

if TYPE_CHECKING:
    from .lesson import Exercise, Lesson


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

    def get_current_lesson(self) -> "Optional[Lesson]":
        """
        Get the Lesson object for the current lesson.

        Returns:
            The current Lesson if current_lesson_id is set, None otherwise
        """
        if self.current_lesson_id:
            return self.course.get_lesson_by_id(self.current_lesson_id)
        return None

    def get_current_exercise(self) -> "Optional[Exercise]":
        """
        Get the Exercise object for the current exercise.

        Returns:
            The current Exercise if both current_lesson_id and
            current_exercise_id are set, None otherwise
        """
        if self.current_lesson_id and self.current_exercise_id:
            lesson = self.get_current_lesson()
            if lesson:
                return lesson.get_exercise_by_id(self.current_exercise_id)
        return None

    def pause(self) -> None:
        """
        Pause the learning session.

        Sets the session state to PAUSED and records the pause timestamp.
        """
        self.state = SessionState.PAUSED
        self.paused_at = datetime.now()
        self.last_activity_at = datetime.now()

    def resume(self) -> None:
        """
        Resume a paused learning session.

        Sets the session state back to ACTIVE and updates activity timestamp.
        """
        self.state = SessionState.ACTIVE
        self.last_activity_at = datetime.now()

    def complete(self) -> None:
        """
        Mark the learning session as completed.

        Sets the session state to COMPLETED and records the completion timestamp.
        """
        self.state = SessionState.COMPLETED
        self.completed_at = datetime.now()
        self.last_activity_at = datetime.now()

    def abandon(self) -> None:
        """
        Mark the learning session as abandoned.

        Sets the session state to ABANDONED and updates activity timestamp.
        """
        self.state = SessionState.ABANDONED
        self.last_activity_at = datetime.now()

    def update_activity(self) -> None:
        """
        Update the last activity timestamp to now.

        Call this method whenever the user interacts with the session.
        """
        self.last_activity_at = datetime.now()
