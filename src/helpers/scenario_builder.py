import logging
import time
from collections.abc import Generator
from copy import deepcopy

from src.gem.gem_input_dict_modifiers import ADJUSTMENT_FUNCS
from src.helpers.format_time_taken import format_time_taken
from src.models.gem_assessments import BaseAssessments, IndividualSensitivityInput
from src.models.settings import SensitivitySettings

logger = logging.getLogger(__name__)


def scenario_builder(
    base_assessments: BaseAssessments, config: SensitivitySettings, batch_size: int = 5000
) -> Generator[list[IndividualSensitivityInput]]:
    start_time = time.time()
    logging.info(f"Building scenarios for {len(base_assessments.assessments)} projects")
    current_batch: list[IndividualSensitivityInput] = []

    for scenario_name, sensitivity in config.sensitivities.items():
        set_sens = 0
        combinations = sensitivity.generate_combinations()
        total_sens = len(combinations) * len(base_assessments.assessments)
        logging.info(f"Building {len(combinations)} combinations for scenario: {scenario_name}")
        for combination in combinations:
            logging.debug(f"Building combination: {combination} for scenario: {scenario_name}")

            for base_assessment in base_assessments.assessments:
                if base_assessment.engine_input_json is None:
                    logging.debug(f"No engine input for project {base_assessment.project_id}")
                    current_batch.append(
                        IndividualSensitivityInput(
                            **base_assessment.model_dump(),
                            combination=combination,
                            scenario=scenario_name,
                        )
                    )
                else:
                    adjusted_input = deepcopy(base_assessment.engine_input_json)

                    for sweep in sensitivity.element_wise_parameter_sweep.values():
                        component = sweep.component
                        adjustment_type = sweep.type
                        if component not in ADJUSTMENT_FUNCS:
                            raise ValueError(f"Adjustment function not found for {component}")

                        value = combination.get(component)
                        if value is None:
                            raise ValueError(f"Value not found for {component}")

                        adjusted_input = ADJUSTMENT_FUNCS[component](adjusted_input, value, adjustment_type, config)
                    current_batch.append(
                        IndividualSensitivityInput(
                            **base_assessment.model_dump(exclude={"engine_input_json"}),
                            engine_input_json=adjusted_input,
                            combination=combination,
                            scenario=scenario_name,
                        )
                    )
                set_sens += 1

                logging.debug(
                    f"Scenario: {scenario_name}, Project: {base_assessment.project_id}, Combination: {combination}"
                )
                if len(current_batch) >= batch_size:
                    logging.info(
                        f"Built batch of sensitivity assessemnts. Total built: {set_sens} of "
                        f"{total_sens}"
                        f" in {format_time_taken(time.time() - start_time)}\n"
                        f"Expected time remaining:"
                        f"{format_time_taken((time.time() - start_time) / set_sens* (total_sens - set_sens))}"
                    )
                    yield current_batch
                    current_batch = []
    if current_batch:
        logging.info(
            f"Built batch of sensitivity assessemnts. Total built: {set_sens} of {total_sens}"
            f" in {format_time_taken(time.time() - start_time)}"
        )
        yield current_batch
