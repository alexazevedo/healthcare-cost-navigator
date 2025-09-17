# Ticket OFH-4: API Endpoints

## Description
Implement REST API endpoints for searching providers and natural language queries using OpenAI.

## AI Prompt
You are an expert FastAPI backend engineer.  
Implement endpoints:

**GET /providers**  
- Query params: drg, zip, radius_km  
- Search hospitals matching ms_drg_definition (ILIKE fuzzy match)  
- Filter by distance from given zip code (use haversine formula with provider_zip_code)  
- Sort by average_covered_charges ascending  
- Return JSON with provider info, drg, cost, rating  

**POST /ask**  
- Input: {"question": "Who is cheapest for DRG 470 within 25 miles of 10001?"}  
- Use OpenAI API to parse question into SQL  
- Run SQL against Postgres  
- Return grounded JSON results  
- If out-of-scope (e.g. weather question), return: "I can only help with hospital pricing and quality information."  

Make sure all queries use async SQLAlchemy.  

## Usage

```bash
# Start the development server
make dev-server

# Test the providers endpoint
curl "http://localhost:8000/providers?drg=ALCOHOL&zip=10001&radius_km=25"

# Test the ask endpoint
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is cheapest for ALCOHOL DRG?"}'
```

## API Endpoints

### GET /providers
- **Query Parameters:**
  - `drg` (optional): DRG definition to search for (fuzzy match)
  - `zip` (optional): ZIP code to search from
  - `radius_km` (optional): Radius in kilometers
- **Returns:** List of providers with costs and ratings, sorted by cost

### POST /ask
- **Body:** `{"question": "your natural language question"}`
- **Returns:** Answer with grounded results from the database

## Acceptance Criteria
- [x] GET /providers implemented  
- [x] Supports DRG fuzzy search with ILIKE  
- [x] Filters by radius from zip code  
- [x] Returns providers sorted by cost  
- [x] Includes ratings in response  
- [x] POST /ask implemented with OpenAI integration  
- [x] Converts NL queries into grounded SQL  
- [x] Handles out-of-scope queries gracefully  
- [x] All DB queries async  
