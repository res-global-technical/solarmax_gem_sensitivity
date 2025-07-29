from enum import Enum


class ScenarioComponents(Enum):
    DISCOUNT_RATE = "discount_rate"
    POWER_PRICES = "power_prices"
    ALL_CAPEX = "all_capex"
    ALL_OPEX = "all_opex"
    ENERGY_YIELD = "energy_yield"
    GBP_FX_RATES = "gbp_fx_rates"
    INFLATION = "inflation"
    OPERATIONAL_LIFETIME = "operational_life_time"
    SALE_DATE = "sale_date"
    FINANCIAL_CLOSE_DATE = "financial_close_date"


class SensitivityTypes(Enum):
    PERCENTAGE_ADJUSTMENT = "percentage_adjustment"
    GENERIC_ADDER = "generic_adder"
    CAPEX_ADDER_PER_MW = "capex_adder_per_mw"
    OVERRIDE_VALUE = "override_value"
