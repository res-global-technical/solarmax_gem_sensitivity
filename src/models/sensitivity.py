from itertools import product

from pydantic import BaseModel

from src.models.enums.sensitivities import ScenarioComponents, SensitivityTypes


class ParameterDetails(BaseModel):
    component: ScenarioComponents
    type: SensitivityTypes
    values: list[float]


class ScenarioSensitivity(BaseModel):
    element_wise_parameter_sweep: dict[str, ParameterDetails]

    def generate_combinations(self) -> list[dict[ScenarioComponents, float]]:
        components = [sweep.component for sweep in self.element_wise_parameter_sweep.values()]
        value_lists = [sweep.values for sweep in self.element_wise_parameter_sweep.values()]
        return [dict(zip(components, combination)) for combination in product(*value_lists)]
