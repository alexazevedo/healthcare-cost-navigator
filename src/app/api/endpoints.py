"""FastAPI endpoints for providers and natural language /ask."""

import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..models.drg import DRG
from ..models.drg_price import DRGPrice
from ..models.provider import Provider
from ..models.rating import Rating
from ..schemas.provider import AskRequest, AskResponse, ProviderInfo
from ..services.openai_service import generate_grounded_answer, nl_to_sql, run_sql
from ..utils.geo import get_zip_coordinates

router = APIRouter()


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point

    Returns:
        Distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371
    return c * r


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "healthcare-cost-navigator"}


@router.get("/providers", response_model=list[ProviderInfo])
async def get_providers(
    drg: str | None = Query(None, description="DRG ID (e.g., '470') or DRG definition to search for"),
    zip: str | None = Query(None, description="ZIP code to search from"),
    radius_km: float | None = Query(None, description="Radius in kilometers"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for healthcare providers by DRG, ZIP code, and radius.

    Args:
        drg: DRG ID (e.g., '470') for exact match or DRG definition text for fuzzy search
        zip: ZIP code to search from
        radius_km: Radius in kilometers from the ZIP code
        db: Database session

    Returns:
        List of distinct providers matching the criteria
    """
    # Build a single query that returns providers with aggregated rating
    query = (
        select(
            Provider.provider_id,
            Provider.provider_name,
            Provider.provider_city,
            Provider.provider_state,
            Provider.provider_zip_code,
            func.avg(Rating.rating).label("avg_rating"),
        )
        .select_from(Provider)
        .outerjoin(Rating, Rating.provider_id == Provider.provider_id)
    )

    # Apply DRG filter if provided - join with DRGPrice and DRG tables
    if drg:
        # First check if drg is a number (DRG ID) or text (DRG definition search)
        if drg.isdigit():
            # Search by DRG ID
            query = query.join(DRGPrice, DRGPrice.provider_id == Provider.provider_id).where(
                DRGPrice.drg_id == int(drg)
            )
        else:
            # Search by DRG definition - need to join through DRG table
            query = (
                query.join(DRGPrice, DRGPrice.provider_id == Provider.provider_id)
                .join(DRG, DRG.drg_id == DRGPrice.drg_id)
                .where(DRG.ms_drg_definition.ilike(f"%{drg}%"))
            )

    # Group by provider fields for aggregation
    query = query.group_by(
        Provider.provider_id,
        Provider.provider_name,
        Provider.provider_city,
        Provider.provider_state,
        Provider.provider_zip_code,
    )

    # Execute the query and build response models
    rows = (await db.execute(query)).mappings().all()

    providers: list[ProviderInfo] = []
    for row in rows:
        avg_rating = row["avg_rating"]
        providers.append(
            ProviderInfo(
                provider_id=row["provider_id"],
                provider_name=row["provider_name"],
                provider_city=row["provider_city"],
                provider_state=row["provider_state"],
                provider_zip_code=row["provider_zip_code"],
                rating=int(avg_rating) if avg_rating is not None else None,
                distance_km=None,
            )
        )

    # Apply radius filter if ZIP and radius are provided
    if zip and radius_km:
        try:
            # Get coordinates for the search ZIP using the geo utility
            search_lat, search_lon = await get_zip_coordinates(zip)

            # Filter providers by distance
            filtered_providers = []
            for provider in providers:
                try:
                    # Get coordinates for provider ZIP code
                    provider_lat, provider_lon = await get_zip_coordinates(provider.provider_zip_code)

                    # Calculate distance
                    distance = calculate_distance(search_lat, search_lon, provider_lat, provider_lon)

                    # Check if within radius
                    if distance <= radius_km:
                        provider.distance_km = distance
                        filtered_providers.append(provider)
                except ValueError:
                    # Skip providers with invalid ZIP codes
                    continue

            providers = filtered_providers

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid ZIP code: {str(e)}") from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing geographic search: {str(e)}") from e

    # Sort by provider name for consistent ordering
    providers.sort(key=lambda x: x.provider_name)

    return providers


@router.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest, db: AsyncSession = Depends(get_db)):
    """
    Receive a natural language question, generate SQL with LLM,
    execute it against Postgres, and return grounded answer + results.
    """
    question = payload.question

    # Generate SQL query from natural language
    sql_query = await nl_to_sql(question)
    
    # Execute the SQL query safely
    results = await run_sql(db, sql_query)

    # Handle error cases
    if not results:
        answer = await generate_grounded_answer(question, sql_query, [])
        return {
            "question": question,
            "sql_query": sql_query,
            "results": [],
            "answer": answer,
            "explanation": "No rows returned; generated grounded answer from empty result set.",
        }

    first = results[0] if isinstance(results, list) else {}
    if isinstance(first, dict) and "error" in first:
        raise HTTPException(status_code=400, detail=first)

    # Generate grounded answer based on results
    answer = await generate_grounded_answer(question, sql_query, results)

    return {
        "question": question,
        "sql_query": sql_query,
        "results": results,
        "answer": answer,
        "explanation": "SQL generated by LLM and executed; answer grounded in returned rows.",
    }
