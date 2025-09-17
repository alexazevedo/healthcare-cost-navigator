from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.provider import AskRequest, AskResponse, ProviderResponse
from app.services.openai_service import convert_question_to_sql
from app.utils.geo import get_zip_coordinates

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "healthcare-cost-navigator"}


@router.get("/providers", response_model=list[ProviderResponse])
async def get_providers(
    drg: str | None = Query(None, description="DRG definition to search for"),
    zip: str | None = Query(None, description="ZIP code to search from"),
    radius_km: float | None = Query(None, description="Radius in kilometers"),
    db: AsyncSession = Depends(get_db),
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
    # Build the base query with Haversine distance calculation
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
        r.rating,
        NULL AS distance_km
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
            # Get coordinates for the search ZIP from the database
            zip_query = "SELECT latitude, longitude FROM zip_codes WHERE zip_code = :zip_code"
            zip_result = await db.execute(text(zip_query), {"zip_code": zip})
            zip_row = zip_result.fetchone()
            
            if not zip_row:
                raise HTTPException(
                    status_code=400, 
                    detail=f"ZIP code {zip} not found in our database"
                )
            
            search_lat, search_lon = zip_row.latitude, zip_row.longitude
            
            # Update the query to include distance calculation and filtering
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
                r.rating,
                (
                    6371 * acos(
                        cos(radians(:search_lat)) * cos(radians(z.latitude)) * 
                        cos(radians(z.longitude) - radians(:search_lon)) + 
                        sin(radians(:search_lat)) * sin(radians(z.latitude))
                    )
                ) AS distance_km
            FROM providers p
            JOIN drg_prices d ON p.provider_id = d.provider_id
            JOIN ratings r ON p.provider_id = r.provider_id
            JOIN zip_codes z ON p.provider_zip_code = z.zip_code
            WHERE 1=1
            """
            
            # Add DRG filter if provided
            if drg:
                base_sql += " AND d.ms_drg_definition ILIKE :drg_pattern"
                params["drg_pattern"] = f"%{drg}%"
            
            # Add distance filter
            base_sql += """
            AND (
                6371 * acos(
                    cos(radians(:search_lat)) * cos(radians(z.latitude)) * 
                    cos(radians(z.longitude) - radians(:search_lon)) + 
                    sin(radians(:search_lat)) * sin(radians(z.latitude))
                )
            ) <= :radius_km
            """
            
            params["search_lat"] = search_lat
            params["search_lon"] = search_lon
            params["radius_km"] = radius_km

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error processing ZIP code: {str(e)}"
            ) from e

    # Sort by distance first (if available), then by average covered charges
    if zip and radius_km:
        base_sql += " ORDER BY distance_km ASC, d.average_covered_charges ASC"
    else:
        base_sql += " ORDER BY d.average_covered_charges ASC"

    # Execute query
    result = await db.execute(text(base_sql), params)
    rows = result.fetchall()

    # Convert to response format
    providers = []
    for row in rows:
        providers.append(
            ProviderResponse(
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
                rating=row.rating,
                distance_km=row.distance_km,
            )
        )

    return providers


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, db: AsyncSession = Depends(get_db)):
    """
    Answer natural language questions about healthcare providers.

    Args:
        request: Question request with natural language question
        db: Database session

    Returns:
        Answer with grounded results from the database
    """
    # Convert question to SQL using OpenAI
    result = await convert_question_to_sql(request.question)

    if result["sql"] is None:
        return AskResponse(answer=result["explanation"], results=None)

    try:
        # Execute the SQL query
        query_result = await db.execute(text(result["sql"]))
        rows = query_result.fetchall()

        # Convert rows to dictionaries
        results = []
        for row in rows:
            results.append(dict(row._mapping))

        # Format the answer
        if results:
            answer = f"Found {len(results)} results. {result['explanation']}"
        else:
            answer = f"No results found. {result['explanation']}"

        return AskResponse(answer=answer, results=results)

    except Exception as e:
        return AskResponse(answer=f"Error executing query: {str(e)}", results=None)
