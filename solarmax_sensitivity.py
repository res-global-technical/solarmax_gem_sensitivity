import json
import logging
import os

from pydantic import BaseModel

from src.gem.gem_input_dict_modifiers import apply_energy_yield_sensitivity, override_solar_installed_dc_capacity, override_solar_installed_ac_capacity, override_land_area
from src.gem.gem_service import get_project_assessment, run_gem_assessments_asyncio
from src.helpers.scenario_builder import scenario_builder
from src.helpers.write_to_excel_template import write_results_to_template_excel_file
from src.models.enums.sensitivities import SensitivityTypes
from src.models.gem_assessments import BaseAssessment, BaseAssessments, SensitivityResults
from src.models.settings import SensitivitySettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("design_analysis.log", mode="w"),
    ],
)


class DesignOption(BaseModel):
    installed_capacity_dc: float
    energy_yield: float
    name: str
    land_area: float | None = None
    installed_capacity_ac: float | None = None


class ProjectAndAssessmentIds(BaseModel):
    project_id: int
    assessment_id: str


def create_base_assessment(
    base_assessment: BaseAssessment, design: DesignOption, config: SensitivitySettings
) -> BaseAssessment:
    if base_assessment.engine_input_json is None:
        raise ValueError("Base assessment has no engine input")
    engine_input = base_assessment.engine_input_json
    assessment = apply_energy_yield_sensitivity(
        engine_input, design.energy_yield, SensitivityTypes.OVERRIDE_VALUE, config
    )
    assessment = override_solar_installed_dc_capacity(
        assessment, design.installed_capacity_dc, SensitivityTypes.OVERRIDE_VALUE, config
    )
    if design.installed_capacity_ac is not None:
        assessment = override_solar_installed_ac_capacity(
            assessment, design.installed_capacity_ac, SensitivityTypes.OVERRIDE_VALUE, config
        )
    if design.land_area is not None:
        assessment = override_land_area(assessment, design.land_area, SensitivityTypes.OVERRIDE_VALUE, config)

    return BaseAssessment(
        project_id=base_assessment.project_id,
        project_name=f"{base_assessment.project_name} - Design: {design.name}",
        technology=base_assessment.technology,
        phase=base_assessment.phase,
        country=base_assessment.country,
        currency=base_assessment.currency,
        engine_input_json=assessment,
    )


def get_design_base_assessments(
    project_id: int, assessment_id: str, designs: list[DesignOption], config: SensitivitySettings
) -> list[BaseAssessment]:
    base_assessment = get_project_assessment(project_id, assessment_id)
    return [create_base_assessment(base_assessment, design, config) for design in designs]


if __name__ == "__main__":
    RESULTS_DIRECTORY = "results"
    with open("examples/solarmax_scenario.json") as f:
        config = SensitivitySettings(**json.load(f))

    with open("designs/design_options.json") as f:
        design_options = json.load(f)

    PROJECT_AND_ASSESSMENT_IDS = [
        ProjectAndAssessmentIds(**project) for project in design_options["project_assessments"]
    ]

    DESIGNS = {
        int(project_id): [DesignOption(**design) for design in designs]
        for project_id, designs in design_options["designs"].items()
    }
    design_assessments: list[BaseAssessment] = []
    for project_and_assessment_id in PROJECT_AND_ASSESSMENT_IDS:
        design_assessments.extend(
            get_design_base_assessments(
                project_and_assessment_id.project_id,
                project_and_assessment_id.assessment_id,
                DESIGNS[project_and_assessment_id.project_id],
                config,
            )
        )
    base_assessments = BaseAssessments(assessments=design_assessments)

    sensitivity_results = SensitivityResults(assessments=[])
    for batch_of_assessments in scenario_builder(base_assessments, config, batch_size=50000):
        for result in run_gem_assessments_asyncio(batch_of_assessments):
            sensitivity_results.add(result)

    output_name = "design_sensitivity"
    os.makedirs(RESULTS_DIRECTORY, exist_ok=True)

    with open(os.path.join(RESULTS_DIRECTORY, f"{output_name}_results.json"), "w") as f:
        f.write(sensitivity_results.model_dump_json(indent=2))

    write_results_to_template_excel_file(sensitivity_results, os.path.join(RESULTS_DIRECTORY, f"{output_name}.xlsx"))

    logging.info("Design sensitivity analysis complete")
