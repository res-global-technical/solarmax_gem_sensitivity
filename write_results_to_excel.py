import json
import logging
import os

from src.helpers.write_to_excel_template import write_results_to_template_excel_file
from src.models.gem_assessments import SensitivityResults

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)


def load_results(file_path: str) -> SensitivityResults:
    logging.info(f"Loading settings from {file_path}")
    with open(os.path.join(os.path.dirname(__file__), file_path), encoding="utf-8") as f:
        data = json.load(f)
        settings = SensitivityResults(**data)
        logging.info("Results loaded")
    return settings


ANALYSIS_NAME = "emea"
RESULTS_DIRECTORY = "results"

if __name__ == "__main__":
    file_path = os.path.join(RESULTS_DIRECTORY, f"{ANALYSIS_NAME}_results.json")
    results = load_results(file_path)
    write_results_to_template_excel_file(results, os.path.join(RESULTS_DIRECTORY, f"{ANALYSIS_NAME}.xlsx"))
