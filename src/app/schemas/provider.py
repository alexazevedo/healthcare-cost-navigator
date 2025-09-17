"""Provider schemas for API responses."""

from typing import Optional

from pydantic import BaseModel


class ProviderResponse(BaseModel):
    """Provider response schema."""
    
    provider_id: str
    provider_name: str
    provider_city: str
    provider_state: str
    provider_zip_code: str
    ms_drg_definition: str
    total_discharges: int
    average_covered_charges: float
    average_total_payments: float
    average_medicare_payments: float
    rating: Optional[int] = None


class AskRequest(BaseModel):
    """Ask request schema."""
    
    question: str


class AskResponse(BaseModel):
    """Ask response schema."""
    
    answer: str
    results: Optional[list[dict]] = None
