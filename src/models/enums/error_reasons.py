from enum import Enum


class ErrorReasons(Enum):
    EXCEL_IMPORT = "Excel import"
    SALE_DATE_IN_PAST = "Sale date in past"
    NO_LIVE_ASSESSMENT = "No live assessment"
    CALCULATION_ERROR = "Calculation error"
    NO_ELECTRICITY_PRICES = "No electricity prices"
    FINANCIAL_CLOSE_DATE_BEFORE_SALE_DATE = "Financial close date before sale date"
