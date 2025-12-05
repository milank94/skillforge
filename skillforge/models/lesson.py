"""
Lesson and Exercise data models.

This module defines the structure for lessons and exercises in a course.
"""

from pydantic import BaseModel, Field


class Exercise(BaseModel):
    """
    Represents a single exercise within a lesson.

    An exercise is a hands-on task that the user must complete to demonstrate
    understanding of a specific concept.

    Attributes:
        id: Unique identifier for the exercise
        instruction: The task description presented to the user
        expected_output: Optional expected result (for validation)
        hints: List of hints to help the user if they get stuck
    """

    id: str = Field(..., description="Unique identifier for the exercise")
    instruction: str = Field(..., description="The task description for the user")
    expected_output: str | None = Field(
        None, description="Expected result for validation"
    )
    hints: list[str] = Field(default_factory=list, description="Hints to help the user")


class Lesson(BaseModel):
    """
    Represents a single lesson within a course.

    A lesson is a focused learning unit covering a specific topic or concept,
    containing multiple exercises for hands-on practice.

    Attributes:
        id: Unique identifier for the lesson
        title: The lesson title
        objectives: List of learning objectives for this lesson
        exercises: List of exercises in this lesson
    """

    id: str = Field(..., description="Unique identifier for the lesson")
    title: str = Field(..., description="The lesson title")
    objectives: list[str] = Field(
        ..., description="Learning objectives for this lesson"
    )
    exercises: list[Exercise] = Field(
        default_factory=list, description="Exercises in this lesson"
    )

    def get_exercise_by_id(self, exercise_id: str) -> Exercise | None:
        """
        Get an exercise by its ID.

        Args:
            exercise_id: The ID of the exercise to find

        Returns:
            The Exercise object if found, None otherwise
        """
        for exercise in self.exercises:
            if exercise.id == exercise_id:
                return exercise
        return None

    def get_exercise_by_index(self, index: int) -> Exercise | None:
        """
        Get an exercise by its index in the lesson.

        Args:
            index: The zero-based index of the exercise

        Returns:
            The Exercise object if index is valid, None otherwise
        """
        if 0 <= index < len(self.exercises):
            return self.exercises[index]
        return None

    def total_exercises(self) -> int:
        """
        Get the total number of exercises in the lesson.

        Returns:
            The number of exercises
        """
        return len(self.exercises)
