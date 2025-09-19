"""Provider schemas for API responses."""

from pydantic import BaseModel


class ProviderInfo(BaseModel):
    """Provider information schema (without DRG pricing data)."""

    provider_id: str
    provider_name: str
    provider_city: str
    provider_state: str
    provider_zip_code: str
    rating: int | None = None
    distance_km: float | None = None


class ProviderResponse(BaseModel):
    """Provider response schema with DRG pricing data."""

    provider_id: str
    provider_name: str
    provider_city: str
    provider_state: str
    provider_zip_code: str
    drg_id: int | None = None  # Now integer
    ms_drg_definition: str | None = None  # From joined DRG table
    total_discharges: int
    average_covered_charges: float
    average_total_payments: float
    average_medicare_payments: float
    rating: int | None = None
    distance_km: float | None = None


class AskRequest(BaseModel):
    """Ask request schema."""

    question: str


class AskResponse(BaseModel):
    """Ask response schema."""

    question: str
    answer: str
    sql_query: str | None = None
    explanation: str
    results: list[dict] | None = None
