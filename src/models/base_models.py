from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AssessmentCollection(
    BaseModel,
    Generic[T],
):
    assessments: list[T]

    def add(self, assessment: T) -> None:
        self.assessments.append(assessment)
