from datetime import date

from pydantic import BaseModel


class GemResult(BaseModel):
    development_fee: float
    total_capex: None | float
    total_merchant_revenue: None | float
    irr: None | float
    bep: None | float
    discount_rate: None | float
    installed_capacity: None | float
    project_sale_date: None | date
    total_opex: None | float
    fid: None | date
    cod: None | date
    energy_yield: None | float
    lifetime: None | int
