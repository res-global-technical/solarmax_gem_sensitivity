import asyncio
import logging
import os
import time
import uuid
from collections.abc import Generator
from copy import deepcopy
from datetime import date, datetime

import httpx
from resgem import GemApiClient, GemApiClientException
from resgem.models import AssessmentModel
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from src.helpers.format_time_taken import format_time_taken
from src.models.enums.error_reasons import ErrorReasons
from src.models.env_variables_config import environment_variables
from src.models.gem_assessments import (
    BaseAssessment,
    BaseAssessments,
    IndividualSensitivityInput,
    IndividualSensitivityResult,
)
from src.models.gem_results import GemResult
from src.models.settings import SensitivitySettings

logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

TODAY = datetime.now().isoformat()


def _get_gem_api_client() -> GemApiClient:
    return GemApiClient(
        api_base_url=environment_variables.gem_api_base_url,
        client_id=environment_variables.gem_client_id,
        client_secret=environment_variables.gem_client_secret,
        user_agent=environment_variables.gem_user_agent,
    )


def _basic_assessment_validation(
    assessment: AssessmentModel, project_name: str, project_id: int
) -> tuple[bool, ErrorReasons | None]:
    if assessment.imported:
        logging.warning(f"Live assessment is imported for {project_name} ({project_id})")
        return False, ErrorReasons.EXCEL_IMPORT
    if (
        assessment.results.data_dict.get("project_sale_date", "") <= TODAY
        or assessment.results.data_dict.get("financial_close", "") <= TODAY
    ):
        logging.warning(
            f"Live assessment Sale date is not valid for {project_name} ({project_id})" "[Sale date is in the past]"
        )
        return False, ErrorReasons.SALE_DATE_IN_PAST
    return True, None


def _engine_input_validation(
    engine_input: dict, project_name: str, project_id: int
) -> tuple[bool, ErrorReasons | None]:
    electricity_price_forecast = engine_input.get("electricity_price", {}).get("forecast", {})
    if electricity_price_forecast is None or len(electricity_price_forecast) == 0:
        logging.warning(f"No electricity Price forecast for {project_name} ({project_id})")
        return False, ErrorReasons.NO_ELECTRICITY_PRICES
    return True, None


def get_project_assessment(project_id: int, assessment_id: str) -> BaseAssessment:
    with _get_gem_api_client() as gem:
        error_message, status_code, assessment = gem.get_assessment(
            parent_id=str(project_id), assessment_id=assessment_id
        )
        if error_message:
            logging.error(f"Error getting assessment {assessment_id} for {project_id}: {status_code}: {error_message}")
            raise GemApiClientException(status_code=status_code, reason=error_message)
        error_message, status_code, project = gem.get_project(project_id=str(project_id))
        if error_message:
            logging.error(f"Error getting project for {project_id}: {status_code}: {error_message}")
            raise GemApiClientException(status_code=status_code, reason=error_message)

        engine_input = _get_gem_calculation_engine_input(assessment=assessment, client=gem)
        valid, reason = _engine_input_validation(engine_input, assessment.parent.name, assessment.parent.id)
        if not valid:
            logging.error(f"Error getting live assessment for {project_id}: {status_code}: {error_message}")
            raise GemApiClientException(status_code=status_code, reason=error_message)
        return BaseAssessment(
            project_id=str(assessment.parent.id),
            project_name=project.name,
            technology=project.technology,
            phase=project.phase,
            country=project.parent.name,
            currency=assessment.results.currency,
            engine_input_json=engine_input,
        )


def get_base_gem_assessments(config: SensitivitySettings) -> BaseAssessments:
    gem_assessments = BaseAssessments(assessments=[])
    valid_technologies = {tech.value.lower() for tech in config.technologies}
    start_time = time.time()
    with _get_gem_api_client() as gem:
        for project, live_assessment in gem.get_projects_with_live_assessment(parent_id=config.folder, recursive=True):
            if project.technology.lower() not in valid_technologies:
                continue
            if project.phase == 0:
                logging.warning(f"Project {project.name} ({project.id}) is in phase 0. Ignoring")
                continue
            if not live_assessment:
                logging.warning(f"No live assessment for {project.name} ({project.id})")

                continue
            valid, reason = _basic_assessment_validation(live_assessment, project.name, project.id)
            if not valid:
                continue
            time_to_get_engine_input = time.time()
            engine_input = _get_gem_calculation_engine_input(assessment=live_assessment, client=gem)
            valid, reason = _engine_input_validation(engine_input, project.name, project.id)
            if not valid:
                continue
            gem_assessments.add(
                BaseAssessment(
                    project_id=str(project.id),
                    project_name=project.name,
                    currency=live_assessment.results.currency,
                    phase=project.phase,
                    country=project.parent.name,
                    technology=project.technology,
                    engine_input_json=engine_input,
                )
            )
            logging.info(
                f"Got engine input for {project.name} ({project.id}) in "
                f"{format_time_taken(time.time() - time_to_get_engine_input)}"
            )

    logging.info(
        f"Got {len(gem_assessments.assessments)} Live assessments in {format_time_taken(time.time() - start_time)}"
    )
    return gem_assessments


def _get_gem_calculation_engine_input(
    assessment: AssessmentModel,
    client: GemApiClient,
) -> dict:
    payload = {**assessment.data_dict, "results": None}

    resp = client._get_session().post(client._api_base_url + "/calculation/validate", json=payload)

    if resp.status_code != 200:
        raise GemApiClientException(
            status_code=resp.status_code, reason=f"Error getting calculation engine input: {resp.text}"
        )
    engine_input = resp.json()
    if engine_input.get("errors"):
        raise GemApiClientException(
            status_code=resp.status_code, reason=f"Error getting calculation engine input: {engine_input['errors']}"
        )
    if "calculationInput" not in engine_input:
        raise GemApiClientException(
            status_code=resp.status_code, reason=f"Error getting calculation engine input: {engine_input}"
        )
    logging.debug(f"Got engine input for {assessment.parent.name} ({assessment.parent.id}) ({assessment.id})")
    return engine_input["calculationInput"]


def _parse_gem_result(result: dict | None) -> GemResult | None:
    if result is None:
        return None
    try:
        dev_fee = float(result["solved_development_fee"])
    except KeyError:
        raise KeyError()
    except ValueError:
        raise ValueError()

    return GemResult(
        development_fee=dev_fee,
        total_capex=next(
            iter([x.get("total") for x in result.get("input_components", {}) if x.get("name") == "TOTAL_CAPEX"]), None
        ),
        total_merchant_revenue=next(
            iter([x.get("total") for x in result.get("input_components", {}) if x.get("name") == "MERCHANT_REVENUE"]),
            None,
        ),
        irr=result.get("development_fee_irr"),
        bep=result.get("bep"),
        discount_rate=result.get("target_project_discount_rate"),
        installed_capacity=result.get("rated_power_mw"),
        project_sale_date=result.get("project_sale_date"),
        total_opex=next(
            iter([x.get("total") for x in result.get("input_components", {}) if x.get("name") == "TOTAL_OPEX"]), None
        ),
        fid=result.get("financial_close"),
        cod=result.get("commercial_operation"),
        energy_yield=result.get("first_year_yield_mwh"),
        lifetime=result.get("operational_lifetime"),
    )


def _split_into_batches(
    data: list[IndividualSensitivityInput], batch_size: int
) -> Generator[list[IndividualSensitivityInput], None, None]:
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


def _get_log_text(
    start_time: float,
    batch_start_time: float,
    completed_assessments: int,
    total_assessments: int,
    batch_number: int,
    assessments_in_batch: int,
) -> str:
    now = time.time()
    elapsed_time = now - start_time
    batch_time = now - batch_start_time

    avg_total_assessment_time = elapsed_time / completed_assessments if completed_assessments > 0 else 0
    avg_batch_assessment_time = batch_time / assessments_in_batch if assessments_in_batch > 0 else 0
    remaining_time = (
        avg_total_assessment_time * (total_assessments - completed_assessments) if completed_assessments > 0 else 0
    )
    avg_batch_time = elapsed_time / batch_number if batch_number > 0 else 0

    return (
        "\n"
        f"Progress: {completed_assessments}/{total_assessments} assessments completed.\n"
        f"Batch Run Time: {format_time_taken(batch_time)} | "
        f"Average Assessment Time in Batch: {format_time_taken(avg_batch_assessment_time)}\n"
        f"Average Batch Run Time: {format_time_taken(avg_batch_time)} |"
        f"Average Overall Assessment Time: {format_time_taken(avg_total_assessment_time)}\n"
        f"Elapsed Time: {format_time_taken(elapsed_time)} | "
        f"Estimated Remaining Time: {format_time_taken(remaining_time)}\n"
        f"Forecasted Completion Time: {time.strftime('%H:%M:%S', time.localtime(now + remaining_time))}"
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=120, max=6000),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def async_calculate_gem_assessment(
    client: httpx.AsyncClient, assessment: IndividualSensitivityInput
) -> dict | None:
    engine_input = deepcopy(assessment.engine_input_json)
    if engine_input is None:
        return None
    response = await client.post(
        environment_variables.gem_calculation_function_url,
        json=engine_input,
        headers={"x-functions-key": environment_variables.gem_calculation_function_key},
        timeout=360,
    )
    response.raise_for_status()
    logging.debug(
        f"Calculated assessment for {assessment.project_name}"
        f"({assessment.project_id}) for combination [{assessment.combination}]"
    )
    return response.json()


async def run_async_batches(
    assessments: list[IndividualSensitivityInput], batch_size: int
) -> list[IndividualSensitivityResult]:
    start_time = time.time()
    scenario_results: list[IndividualSensitivityResult] = []

    batches = list(_split_into_batches(assessments, batch_size))
    total_batches = len(batches)
    total_assessments = len(assessments)
    completed_assessments = 0

    async with httpx.AsyncClient() as client:
        for batch_number, batch in enumerate(batches, start=1):
            batch_start_time = time.time()
            logging.info(f"Running batch {batch_number} of {total_batches}. Size: {len(batch)}")

            tasks = [async_calculate_gem_assessment(client, assessment) for assessment in batch]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                completed_assessments += 1
                if isinstance(result, dict) or result is None:
                    scenario_results.append(
                        IndividualSensitivityResult(
                            **batch[i].model_dump(exclude={"engine_input_json"}),
                            results=_parse_gem_result(result),
                        )
                    )
                else:
                    logging.error(
                        f"Error in calculation for {batch[i].project_name} ({batch[i].project_id})"
                        f"[{batch[i].combination}]: {result}"
                    )
                    os.makedirs("error_logs", exist_ok=True)
                    random_id = uuid.uuid4().hex
                    file_name = f"{batch[i].project_id}_{random_id}.json"
                    with open(f"error_logs/{file_name}", "w") as f:
                        f.write(batch[i].model_dump_json(indent=2))
                    scenario_results.append(
                        IndividualSensitivityResult(
                            **batch[i].model_dump(exclude={"engine_input_json", "reason_for_no_assessment"}),
                            results=None,
                            reason_for_no_assessment=ErrorReasons.CALCULATION_ERROR,
                        )
                    )

            logging.info(
                _get_log_text(
                    start_time,
                    batch_start_time,
                    completed_assessments,
                    total_assessments,
                    batch_number,
                    len(batch),
                )
            )
    logging.info(
        f"Completed GEM Sensitivity Analysis. "
        f"{total_assessments} assessments in {format_time_taken(time.time() - start_time)}"
    )
    return scenario_results


def run_gem_assessments_asyncio(assessments: list[IndividualSensitivityInput]) -> list[IndividualSensitivityResult]:
    return asyncio.run(run_async_batches(assessments, batch_size=environment_variables.gem_batch_size))
