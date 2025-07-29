from pydantic import BaseModel

from src.models.enums.technologies import Technologies
from src.models.sensitivity import ScenarioSensitivity


class SensitivitySettings(BaseModel):
    folder: str
    technologies: list[Technologies]
    sensitivities: dict[str, ScenarioSensitivity]
