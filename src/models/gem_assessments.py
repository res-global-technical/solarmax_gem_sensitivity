from typing import Any

from pydantic import BaseModel

from src.models.base_models import AssessmentCollection
from src.models.enums.error_reasons import ErrorReasons
from src.models.enums.sensitivities import ScenarioComponents
from src.models.gem_results import GemResult


class Project(BaseModel):
    project_id: str
    project_name: str
    technology: str
    phase: int
    country: str
    currency: str | None
    reason_for_no_assessment: ErrorReasons | None = None


class BaseAssessment(Project):
    engine_input_json: None | dict[str, Any]


class BaseAssessments(AssessmentCollection[BaseAssessment]):
    pass


class IndividualSensitivityInput(Project):
    combination: dict[ScenarioComponents, Any]
    scenario: str
    engine_input_json: None | dict[str, Any]


class IndividualSensitivityResult(Project):
    results: GemResult | None
    combination: dict[ScenarioComponents, Any]
    scenario: str


class SensitivityResults(AssessmentCollection[IndividualSensitivityResult]):
    pass
