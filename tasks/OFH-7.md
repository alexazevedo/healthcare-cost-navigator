# Ticket OFH-7: Distance Filtering with Haversine in SQLAlchemy

## Description
Implement filtering of providers by geographic distance (radius from a given ZIP code) for the `/providers` endpoint.  
Since the dataset only contains ZIP codes, create or load a lookup table that maps ZIP codes to latitude/longitude.  
Use the Haversine formula directly in the SQL query via SQLAlchemy expressions so that filtering happens inside PostgreSQL.  

### Trade-offs considered:
- **In-code computation (Python)**: Simple but inefficient at scale, as it requires fetching all rows into application memory before filtering. Suitable only for very small datasets.  
- **Postgres function or PostGIS**: Most performant and production-ready (supports spatial indexes), but adds external dependencies and setup complexity. Considered out-of-scope for this 4h coding assessment.  
- **Raw SQL haversine in query (chosen approach)**: Efficient, keeps computation in Postgres, no extra dependencies, and aligns with the requested stack. Good trade-off between performance and simplicity.  

## AI Prompt
You are an expert FastAPI and SQLAlchemy backend engineer.  
Update the implementation with the following steps:

1. **Script to build ZIP → lat/lon data (`build_zip_latlon.py`)**  
   - Download a free ZIP → latitude/longitude dataset (e.g. CSV or ZIP file) that covers U.S. ZIP codes.  
   - Extract only the relevant columns (zip, latitude, longitude).  
   - Save the result into a new CSV (`zip_lat_lon.csv`).  
   - This script’s responsibility is **only downloading and saving** the cleaned CSV.  

2. **Database Migration**  
   - Create a new table `zip_codes` with the following schema:  
     - `zip_code` (PK, VARCHAR(10))  
     - `latitude` (FLOAT)  
     - `longitude` (FLOAT)  
   - Generate an Alembic migration for this new table.  

3. **Update ETL Script (`etl.py`)**  
   - Read the generated `zip_lat_lon.csv`.  
   - Validate, clean, and insert ZIP code + lat/lon into the `zip_codes` table.  
   - Ensure the ETL process can be run end-to-end (loading provider data + ZIP code data).  

4. **Update `/providers` endpoint**  
   - Accept `zip` and `radius_km` parameters.  
   - Look up the latitude/longitude of the input ZIP code from the `zip_codes` table.  
   - Join each provider with its corresponding latitude/longitude (via ZIP).  
   - Use the Haversine formula inside the SQLAlchemy query to compute distance in kilometers:  


```distance_km = 6371 * acos(
cos(radians(:lat)) * cos(radians(provider_lat)) *
cos(radians(provider_lon) - radians(:lon)) +
sin(radians(:lat)) * sin(radians(provider_lat))
)```


   - Filter results where `distance_km <= :radius_km`.  
   - Return providers sorted by `average_covered_charges` and include the computed `distance_km` in the JSON response.  

Ensure all queries are async and efficient.

## Acceptance Criteria
- [x] Script `build_zip_latlon.py` created, downloads and saves `zip_lat_lon.csv`  
- [x] Alembic migration created for `zip_codes` table  
- [x] ETL script (`etl.py`) updated to insert ZIP + lat/lon into the database  
- [x] `/providers` accepts `zip` and `radius_km` params  
- [x] Haversine formula implemented in SQLAlchemy query (executed in Postgres)  
- [x] Results filtered correctly by radius  
- [x] Providers sorted by `average_covered_charges`  
- [x] Response includes `distance_km` field for each provider  
- [x] Trade-offs documented in README (with note on PostGIS for production)

## Usage

The `/providers` endpoint now supports geographic distance filtering:

```bash
# Find providers within 10km of ZIP 10001 for ALCOHOL-related DRGs
curl "http://localhost:8000/providers?zip=10001&radius_km=10&drg=ALCOHOL"

# Find all providers within 5km of ZIP 10016
curl "http://localhost:8000/providers?zip=10016&radius_km=5"

# Find providers for specific DRG without distance filtering
curl "http://localhost:8000/providers?drg=ALCOHOL"
```

The response includes a `distance_km` field showing the calculated distance from the search ZIP code to each provider's ZIP code.

## Results

- ✅ ZIP code data successfully loaded (251 ZIP codes)
- ✅ Haversine distance calculation working correctly
- ✅ Distance filtering by radius working
- ✅ Results sorted by distance (when filtering) then by cost
- ✅ All acceptance criteria met  