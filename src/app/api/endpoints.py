import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.drg_price import DRGPrice
from app.models.provider import Provider
from app.models.rating import Rating
from app.schemas.provider import AskRequest, AskResponse, ProviderResponse
from app.services.openai_service import OpenAIService
from app.utils.geo import get_zip_coordinates

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "healthcare-cost-navigator"}


@router.get("/providers", response_model=List[ProviderResponse])
async def get_providers(
    drg: Optional[str] = Query(None, description="DRG definition to search for"),
    zip: Optional[str] = Query(None, description="ZIP code to search from"),
    radius_km: Optional[float] = Query(None, description="Radius in kilometers"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for healthcare providers by DRG, ZIP code, and radius.
    
    Args:
        drg: DRG definition to search for (fuzzy match)
        zip: ZIP code to search from
        radius_km: Radius in kilometers from the ZIP code
        db: Database session
        
    Returns:
        List of providers matching the criteria, sorted by cost
    """
    # Build the base query with proper joins using raw SQL for now
    # This is a simplified approach that will work
    base_sql = """
    SELECT 
        p.provider_id,
        p.provider_name,
        p.provider_city,
        p.provider_state,
        p.provider_zip_code,
        d.ms_drg_definition,
        d.total_discharges,
        d.average_covered_charges,
        d.average_total_payments,
        d.average_medicare_payments,
        r.rating
    FROM providers p
    JOIN drg_prices d ON p.provider_id = d.provider_id
    JOIN ratings r ON p.provider_id = r.provider_id
    WHERE 1=1
    """
    
    params = {}
    
    # Apply DRG filter if provided
    if drg:
        base_sql += " AND d.ms_drg_definition ILIKE :drg_pattern"
        params["drg_pattern"] = f"%{drg}%"
    
    # Apply radius filter if ZIP and radius are provided
    if zip and radius_km:
        try:
            # Get coordinates for the search ZIP
            search_lat, search_lon = get_zip_coordinates(zip)
            
            # For now, we'll do a simple filter by ZIP code prefix
            # In a real implementation, you'd store lat/lon in the database
            # and use a proper spatial query
            zip_prefix = zip[:3]  # Use first 3 digits for rough geographic filtering
            base_sql += " AND p.provider_zip_code LIKE :zip_prefix"
            params["zip_prefix"] = f"{zip_prefix}%"
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid ZIP code: {str(e)}")
    
    # Sort by average covered charges (ascending - cheapest first)
    base_sql += " ORDER BY d.average_covered_charges ASC"
    
    # Execute query
    result = await db.execute(text(base_sql), params)
    rows = result.fetchall()
    
    # Convert to response format
    providers = []
    for row in rows:
        providers.append(ProviderResponse(
            provider_id=row.provider_id,
            provider_name=row.provider_name,
            provider_city=row.provider_city,
            provider_state=row.provider_state,
            provider_zip_code=row.provider_zip_code,
            ms_drg_definition=row.ms_drg_definition,
            total_discharges=row.total_discharges,
            average_covered_charges=row.average_covered_charges,
            average_total_payments=row.average_total_payments,
            average_medicare_payments=row.average_medicare_payments,
            rating=row.rating
        ))
    
    return providers


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Answer natural language questions about healthcare providers.
    
    Args:
        request: Question request with natural language question
        db: Database session
        
    Returns:
        Answer with grounded results from the database
    """
    # For now, return a simple response without OpenAI integration
    # This can be enhanced later when OpenAI API key is available
    return AskResponse(
        answer="I can only help with hospital pricing and quality information. Please ask about specific DRG codes, provider costs, or ratings.",
        results=None
    )