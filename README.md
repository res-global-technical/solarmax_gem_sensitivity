# Prototype GEM Sensitivity

Scripts to perform a Technoeconomic Sensitivity Assessment from SolarMAX projects

Utilises [GEM Engine Function App](https://portal.azure.com/#@reshive.onmicrosoft.com/resource/subscriptions/0b17f9dd-4b32-445d-a304-45bff0dd4e0b/resourceGroups/gem-calculation-engine-rg/providers/Microsoft.Web/sites/gem-calculation-engine/appServices)


# Getting Started

This project allows you to run sensitivity analyses across multiple SolarMAX assessments. Below is a step-by-step guide to set up and execute the tool locally.


## Prerequisites

Ensure the following are installed on your machine:
- [Python 3.11](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)


## Setting Up the Environment

### 1. Create and Configure Virtual Environment
(Optional) Configure Poetry to create a virtual environment in the project root:
```bash
poetry config virtualenvs.in-project true
```

Install dependencies:
```bash
poetry install
```

Activate the virtual environment (see [Python's venv documentation](https://docs.python.org/3/library/venv.html) if needed).

## Configuration

### 1. Create `.env` File
Create a `.env` file in the root directory with the following content:
```plaintext
GEM_CALCULATION_FUNCTION_KEY=""
GEM_CALCULATION_FUNCTION_URL=""
GEM_CHUNK_SIZE=1000
GEM_API_BASE_URL="https://www.res-gem.com/api"
GEM_CLIENT_ID=""
GEM_CLIENT_SECRET=""
```
- **GEM_CHUNK_SIZE**: Maximum recommended value is `1000` due to concurrency limits on Engine Function App.

For Client ID and Secret please contact [Ross Donnelly](Ross.Donnelly@res-group.com)

### 2. Define Sensitivity JSON
Add a JSON file (e.g., `my_sensitivity.json`) to the `examples/` folder.

The `examples/Sesntivity Set Up.xlsx` file and `src/helpers/excel_to_sensitivity_json.py` script can be used to generate this. See instructions in `examples/Sesntivity Set Up.xlsx` 
```

**Note:** Currently supported components and their available sensitivity types can be found in the below table:

| Component | `percentage_adjustment` | `generic_adder` | `capex_adder_per_mw` | `override_value` |
|-----------|:-----------------------:|:---------------:|:--------------------:|:----------------:|
| `discount_rate` | ✓ |  |  | ✓ |
| `all_capex` | ✓ | ✓ | ✓ |  |
| `all_opex` | ✓ |  |  |  |
| `energy_yield` | ✓ |  |  |  |
| `gbp_fx_rates` | ✓ |  |  |  |
| `inflation` | ✓ |  |  |  |
| `operational_life_time` |  | ✓ |  |  |
| `financial_close_date` |  | ✓ |  |  |

### 3. Define Solarmax Designs
Add a JSON file (e.g. `my_designs.json` to the `designs/` folder, see example `designs/design_options.json`

You can download solarmax CSV

## Running Locally

### 1. Update `main.py`
Set the `ANALSYSIS_NAME` variable in `main.py` to point to your sensitivity JSON file (e.g., `examples/my_sensitivity.json`).

### 2. Run the Script
To execute the analysis:
```bash
python main.py
```

or as a background process
```bash
python main.py &
```

Follow the log for status updates and estimated completion time e.g.:
```bash
Get-Content .\application.log -Wait -Tail 1000
```


## How It Works
The script creates an element-wise parameter sweep of all specified parameter sweeps and their values. For example, if two sweeps with values `[A1, A2, A3]` and `[B1, B2, B3]` are defined, the script generates:
```plaintext
(A1, B1), (A1, B2), (A1, B3),
(A2, B1), (A2, B2), (A2, B3),
(A3, B1), (A3, B2), (A3, B3)
```

## Additional Notes

- Ensure all required environment variables are set in the `.env` file before running the script.
- The `GEM_CHUNK_SIZE` parameter controls concurrency. The default value of `1000` is recommended for optimal performance.
- The logs provide detailed status updates, including estimated completion times.
