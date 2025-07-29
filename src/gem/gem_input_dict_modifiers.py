import logging
from collections.abc import Callable
from copy import deepcopy
from datetime import date
from functools import partial
from typing import Any, Literal

from dateutil import relativedelta

from src.models.enums.sensitivities import ScenarioComponents, SensitivityTypes
from src.models.settings import SensitivitySettings

logger = logging.getLogger(__name__)


def apply_discount_rate_sensitivity(
    engine_input_json: dict,
    discount_rate_adjustment: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, discount_rate_adjustment: float) -> dict:
        input_json["discount_rate"] += discount_rate_adjustment
        return input_json

    def _override(input_json: dict, discount_rate_adjustment: float) -> dict:
        input_json["discount_rate"] = discount_rate_adjustment
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, discount_rate_adjustment)
    elif sensitivity_type is SensitivityTypes.OVERRIDE_VALUE:
        return _override(input_json, discount_rate_adjustment)
    else:
        raise ValueError("Discount rate adjustment must be a percentage adjustment")


def override_land_area(
    engine_input_json: dict,
    land_area: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _override(input_json: dict, land_area: float) -> dict:
        input_json["project_land_area"] = land_area
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.OVERRIDE_VALUE:
        return _override(input_json, land_area)
    else:
        raise ValueError("Land area must be overridden")


def override_solar_installed_dc_capacity(
    engine_input_json: dict,
    installed_dc_capacity: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _override(input_json: dict, installed_dc_capacity: float) -> dict:
        input_json["total_module_rated_power_mw"] = installed_dc_capacity
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.OVERRIDE_VALUE:
        return _override(input_json, installed_dc_capacity)
    else:
        raise ValueError("Installed DC capacity must be overridden")


def override_solar_installed_ac_capacity(
    engine_input_json: dict,
    installed_ac_capacity: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _override(input_json: dict, installed_ac_capacity: float) -> dict:
        input_json["installed_ac_capacity"] = installed_ac_capacity
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.OVERRIDE_VALUE:
        return _override(input_json, installed_ac_capacity)
    else:
        raise ValueError("Installed AC capacity must be overridden")


def apply_energy_yield_sensitivity(
    engine_input_json: dict,
    energy_yield_adjustment: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, energy_yield_adjustment: float) -> dict:
        energy_yield_information = input_json["energy_yield_information"]
        if energy_yield_information.get("energy_loss_calculators") is None:
            energy_yield_information["energy_loss_calculators"] = []
        energy_yield_information["energy_loss_calculators"].append(
            {
                "name": "GRID_LINE_LOSSES",
                "calculator": "LINE LOSS",
                "items": [
                    {
                        "cost": 1 + energy_yield_adjustment,
                        "cost_type": "PERCENTAGE",
                        "start_year": 1,
                    }
                ],
            }
        )

        return input_json

    def _override(input_json: dict, energy_yield_adjustment: float) -> dict:
        input_json["energy_yield_information"].pop("monthly_profile")
        input_json["energy_yield_information"]["energy_yield_per_year_MWh"] = energy_yield_adjustment
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, energy_yield_adjustment)
    elif sensitivity_type is SensitivityTypes.OVERRIDE_VALUE:
        return _override(input_json, energy_yield_adjustment)
    else:
        raise ValueError("Energy yield adjustment must be a percentage adjustment or override value")


def apply_fx_rates_sensitivity(
    sensitivity_currency: str,
    engine_input_json: dict,
    fx_rates_adjustment: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, fx_rates_adjustment: float, sensitivity_currency: str) -> dict:
        sensitivity_factor = 1 + fx_rates_adjustment
        base_currency = input_json["currency"]
        currencies = input_json["currencies"]
        if sensitivity_currency in currencies:
            for year, rate in currencies[sensitivity_currency].items():
                currencies[sensitivity_currency][year] *= sensitivity_factor

        if base_currency != sensitivity_currency:
            for year, rate in currencies[sensitivity_currency].items():
                base_to_sensitivity_rate = 1 / rate
                currencies.setdefault(base_currency, {})[year] = base_to_sensitivity_rate

        for currency, rates in currencies.items():
            if currency != sensitivity_currency and currency != base_currency:
                for year, base_to_other_rate in rates.items():
                    if sensitivity_currency in currencies:
                        sensitivity_to_other_rate = currencies[sensitivity_currency][year] * base_to_other_rate
                        currencies[currency][year] = sensitivity_to_other_rate

        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, fx_rates_adjustment, sensitivity_currency)
    else:
        raise ValueError("FX rates adjustment must be a percentage adjustment")


def apply_capex_sensitivity(
    engine_input_json: dict, capex_adjustment: float, sensitivity_type: SensitivityTypes, config: SensitivitySettings
) -> dict:
    def _adjustment(input_json: dict, capex_adjustment: float) -> dict:
        components = [
            "ADDITIONAL_CIVIL_WORKS",
            "AUGMENTATION_CAPEX",
            "BOP_CAPEX",
            "CABLES",
            "COMPENSATION_CAPEX",
            "CONSTRUCTION_COMPOUND",
            "CONSTRUCTION_INSURANCE_CAPEX",
            "CONSTRUCTION_MANAGEMENT",
            "CONSTRUCTION_INSURANCE",
            "EXTERNAL_CONSULTANCY",
            "HARDSTANDINGS",
            "INTERCONNECTION",
            "INTERNAL",
            "INVERTERS_EQUIPMENT",
            "INVERTERS",
            "LAND_CAPEX",
            "LOCAL_TAX_CAPEX",
            "MODULE_CAPEX",
            "GRID_CAPEX",
            "OTHER_CAPEX",
            "PCS_CAPEX",
            "PROJECT_SPECIFIC_CAPEX",
            "SUBSTATION",
            "CONTINGENCY",
            "ROADS",
            "SITE_COMMUNICATIONS",
            "SOLAR_FOUNDATIONS",
            "STORAGE_LAND_CAPEX",
            "BATTERY_CAPEX",
            "TRACKS",
            "SITE_CLEARANCE",
            "TURBINE_CAPEX",
            "WIDER_NETWORK_UPGRADE",
            "TURBINE_FOUNDATIONS",
        ]
        for component in components:
            input_json["calculators"].append(
                {
                    "name": "INVESTOR_CONTINGENCY",
                    "calculator": "GENERIC_CAPEX",
                    "cost": capex_adjustment,
                    "cost_type": "PERCENTAGE_OF_COMPONENT",
                    "component_to_apply_percentage": component,
                    "is_contingency": True,
                }
            )
        return input_json

    def _cost_adder(
        input_json: dict,
        capex_adjustment: float,
        type: Literal[SensitivityTypes.GENERIC_ADDER] | Literal[SensitivityTypes.CAPEX_ADDER_PER_MW],
    ) -> dict:
        input_json["calculators"].append(
            {
                "name": "BOP_CAPEX",
                "calculator": "GENERIC_CAPEX",
                "cost": capex_adjustment,
                "cost_type": "LUMP_SUM" if type is SensitivityTypes.GENERIC_ADDER else "PER_MW",
            }
        )
        return input_json

    input_json = deepcopy(engine_input_json)

    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, capex_adjustment)
    if sensitivity_type is SensitivityTypes.GENERIC_ADDER or sensitivity_type is SensitivityTypes.CAPEX_ADDER_PER_MW:
        return _cost_adder(input_json, capex_adjustment, sensitivity_type)

    else:
        raise ValueError(
            f"Capex adjustment must be one of {SensitivityTypes.GENERIC_ADDER.name}, "
            f"{SensitivityTypes.CAPEX_ADDER_PER_MW.name}, "
            f"{SensitivityTypes.PERCENTAGE_ADJUSTMENT.name}"
        )


def apply_opex_adjustment(
    engine_input_json: dict, opex_adjustment: float, sensitivity_type: SensitivityTypes, config: SensitivitySettings
) -> dict:
    def _adjustment(input_dict: dict, opex_adjustment: float) -> dict:
        opex_calculators = {"GENERIC_OPEX", "LAND_OPEX"}
        calculators = input_dict.get("calculators", [])
        if not isinstance(calculators, list):
            raise ValueError("Expected calculations to a list in the engine input json")

        for calculator in calculators:
            if calculator.get("calculator") in opex_calculators:
                items = calculator.get("items", [])
                if not isinstance(items, list):
                    continue
                for item in items:
                    item["risk_factor"] = 1 + opex_adjustment

        turbine_groups = input_dict.get("turbine_groups")
        if not turbine_groups:
            return input_dict

        for turbine in turbine_groups:
            o_and_m = turbine.get("turbine_o_and_m", {})
            if not isinstance(o_and_m, dict):
                continue

            per_turbine_cost = o_and_m.get("o_and_m_cost_per_turbine", {})
            if isinstance(per_turbine_cost, dict):
                for year, cost in per_turbine_cost.items():
                    per_turbine_cost[year] = cost * (1 + opex_adjustment)
            per_mwh_cost = o_and_m.get("o_and_m_cost_per_mwh", {})
            if isinstance(per_mwh_cost, dict):
                for year, cost in per_mwh_cost.items():
                    per_mwh_cost[year] = cost * (1 + opex_adjustment)

        return input_dict

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, opex_adjustment)
    else:
        raise ValueError("Opex adjustment must be a percentage adjustment")


def apply_power_prices_adjustment(
    engine_input_json: dict,
    power_prices_adjustment: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, power_prices_adjustment: float) -> dict:
        input_json["electricity_price"]["risk_factor"] = 1 + power_prices_adjustment
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, power_prices_adjustment)
    else:
        raise ValueError("Power prices adjustment must be a percentage adjustment")


def apply_inflation_sensitivity(
    engine_input_json: dict,
    inflation_adjustment: float,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, inflation_adjustment: float) -> dict:
        inflation_rate = input_json["inflation_rate"]
        for inflation in inflation_rate:
            inflation["rate"] += inflation_adjustment
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.PERCENTAGE_ADJUSTMENT:
        return _adjustment(input_json, inflation_adjustment)
    else:
        raise ValueError("Inflation adjustment must be a percentage adjustment")


def apply_lifetime_sensitivity(
    engine_input_json: dict, lifetime_adjustment: int, sensitivity_type: SensitivityTypes, config: SensitivitySettings
) -> dict:
    def _adjustment(input_json: dict, lifetime_adjustment: int) -> dict:
        input_json["operational_lifetime_years"] = int(input_json["operational_lifetime_years"] + lifetime_adjustment)
        for calculator in input_json["calculators"]:
            if "operational_lifetime_years" in calculator:
                calculator["operational_lifetime_years"] = int(
                    calculator["operational_lifetime_years"] + lifetime_adjustment
                )
        energy_loss_calculators = input_json["energy_yield_information"].get("energy_loss_calculators", [])
        for calculator in energy_loss_calculators:
            if "operational_lifetime_years" in calculator:
                calculator["operational_lifetime_years"] = int(
                    calculator["operational_lifetime_years"] + lifetime_adjustment
                )
        return input_json

    input_json = deepcopy(engine_input_json)

    if sensitivity_type is SensitivityTypes.GENERIC_ADDER:
        return _adjustment(input_json, lifetime_adjustment)
    else:
        raise ValueError("Lifetime adjustment must be a generic adder")


def apply_financial_close_date_sensitivity(
    engine_input_json: dict,
    financial_close_date_adjustment: int,
    sensitivity_type: SensitivityTypes,
    config: SensitivitySettings,
) -> dict:
    def _adjustment(input_json: dict, financial_close_date_adjustment: int) -> dict:
        financial_close_year = input_json["date_of_financial_close"]["year"]
        financial_close_month = input_json["date_of_financial_close"]["month"]
        fid = date(financial_close_year, financial_close_month, 1)
        fid += relativedelta.relativedelta(months=financial_close_date_adjustment)
        input_json["date_of_financial_close"]["year"] = fid.year
        input_json["date_of_financial_close"]["month"] = fid.month
        return input_json

    input_json = deepcopy(engine_input_json)
    if sensitivity_type is SensitivityTypes.GENERIC_ADDER:
        return _adjustment(input_json, financial_close_date_adjustment)
    else:
        raise ValueError("Financial close date adjustment must be a generic adder")


ADJUSTMENT_FUNCS: dict[ScenarioComponents, Callable[[dict, Any, SensitivityTypes, SensitivitySettings], dict]] = {
    ScenarioComponents.DISCOUNT_RATE: apply_discount_rate_sensitivity,
    ScenarioComponents.ALL_CAPEX: apply_capex_sensitivity,
    ScenarioComponents.ALL_OPEX: apply_opex_adjustment,
    ScenarioComponents.POWER_PRICES: apply_power_prices_adjustment,
    ScenarioComponents.ENERGY_YIELD: apply_energy_yield_sensitivity,
    ScenarioComponents.INFLATION: apply_inflation_sensitivity,
    ScenarioComponents.GBP_FX_RATES: partial(apply_fx_rates_sensitivity, "GBP"),
    ScenarioComponents.OPERATIONAL_LIFETIME: apply_lifetime_sensitivity,
    ScenarioComponents.FINANCIAL_CLOSE_DATE: apply_financial_close_date_sensitivity,
}

logger.debug(f"Adjustment functions loaded: {ADJUSTMENT_FUNCS}")
