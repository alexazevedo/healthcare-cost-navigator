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

## Acceptance Criteria
- [ ] GET /providers implemented  
- [ ] Supports DRG fuzzy search with ILIKE  
- [ ] Filters by radius from zip code  
- [ ] Returns providers sorted by cost  
- [ ] Includes ratings in response  
- [ ] POST /ask implemented with OpenAI integration  
- [ ] Converts NL queries into grounded SQL  
- [ ] Handles out-of-scope queries gracefully  
- [ ] All DB queries async  
