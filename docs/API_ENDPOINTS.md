# API Endpoints Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. All endpoints are publicly accessible.

## Endpoints

### 1. Health Check

**GET** `/health`

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "healthcare-cost-navigator"
}
```

---

### 2. Provider Search

**GET** `/providers`

Search for healthcare providers with optional filtering by DRG, geographic location, and radius.

**Query Parameters:**
- `drg` (optional, string): DRG definition to search for (fuzzy match)
- `zip` (optional, string): ZIP code to search from
- `radius_km` (optional, float): Radius in kilometers from the ZIP code

**Examples:**
```bash
# Get all providers
GET /providers

# Search by DRG
GET /providers?drg=ALCOHOL

# Search within 10km of ZIP 10001
GET /providers?zip=10001&radius_km=10

# Combined search
GET /providers?zip=10016&radius_km=5&drg=ALCOHOL
```

**Response:**
```json
[
  {
    "provider_id": "330169",
    "provider_name": "Mount Sinai Beth Israel",
    "provider_city": "New York",
    "provider_state": "NY",
    "provider_zip_code": "10003",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC",
    "total_discharges": 35,
    "average_covered_charges": 50464.89,
    "average_total_payments": 10421.63,
    "average_medicare_payments": 7797.74,
    "rating": 5,
    "distance_km": 0.0
  }
]
```

**Response Fields:**
- `provider_id`: Unique identifier for the provider
- `provider_name`: Name of the healthcare provider
- `provider_city`: City where the provider is located
- `provider_state`: State where the provider is located
- `provider_zip_code`: ZIP code of the provider
- `ms_drg_definition`: Medicare Severity Diagnosis Related Group definition
- `total_discharges`: Number of total discharges for this DRG
- `average_covered_charges`: Average covered charges (what the provider billed)
- `average_total_payments`: Average total payments (what was actually paid)
- `average_medicare_payments`: Average Medicare payments
- `rating`: Provider rating (1-10, mock data)
- `distance_km`: Distance from search ZIP code (only when filtering by location)

---

### 3. Natural Language Query

**POST** `/ask`

Ask natural language questions about healthcare providers and get AI-powered answers.

**Request Body:**
```json
{
  "question": "What are the cheapest hospitals for alcohol treatment in New York?"
}
```

**Response:**
```json
{
  "answer": "Found 15 results. Here are the cheapest hospitals for alcohol treatment in New York, sorted by average covered charges:",
  "results": [
    {
      "provider_name": "Bellevue Hospital Center",
      "provider_city": "New York",
      "average_covered_charges": 44648.0,
      "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC"
    }
  ]
}
```

**Response Fields:**
- `answer`: Natural language explanation of the results
- `results`: Array of matching providers (null if no results or error)

## Error Responses

### 400 Bad Request
```json
{
  "detail": "ZIP code 99999 not found in our database"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

## CORS

The API is configured to allow requests from any origin (`*`). In production, configure CORS to only allow requests from your frontend domain.

## Data Sources

- **Provider Data**: CMS (Centers for Medicare & Medicaid Services) Inpatient Prospective Payment System
- **Geographic Data**: ZIP code to latitude/longitude mapping
- **Quality Ratings**: Mock data (1-10 scale)

## Geographic Filtering

The geographic filtering uses the Haversine formula to calculate distances between ZIP codes:

```sql
6371 * acos(
  cos(radians(lat1)) * cos(radians(lat2)) * 
  cos(radians(lon2) - radians(lon1)) + 
  sin(radians(lat1)) * sin(radians(lat2))
)
```

Where:
- `6371` is the Earth's radius in kilometers
- `lat1, lon1` are the coordinates of the search ZIP code
- `lat2, lon2` are the coordinates of the provider's ZIP code

## Performance Notes

- Geographic queries are optimized with database indexes
- Results are sorted by distance (when filtering) then by cost
- Large result sets are not paginated (consider implementing pagination for production)
- Database connections are pooled for better performance
