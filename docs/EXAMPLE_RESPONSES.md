# Example API Responses

## Provider Search Examples

### 1. Basic Provider Search

**Request:**
```bash
curl "http://localhost:8000/providers"
```

**Response:**
```json
[
  {
    "provider_id": "330057",
    "provider_name": "St Peter's Hospital",
    "provider_city": "Albany",
    "provider_state": "NY",
    "provider_zip_code": "12208",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE, LEFT AMA",
    "total_discharges": 14,
    "average_covered_charges": 6480.14,
    "average_total_payments": 4358.0,
    "average_medicare_payments": 2528.57,
    "rating": 6,
    "distance_km": null
  },
  {
    "provider_id": "330057",
    "provider_name": "St Peter's Hospital",
    "provider_city": "Albany",
    "provider_state": "NY",
    "provider_zip_code": "12208",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC",
    "total_discharges": 25,
    "average_covered_charges": 12500.50,
    "average_total_payments": 8500.25,
    "average_medicare_payments": 6500.75,
    "rating": 6,
    "distance_km": null
  }
]
```

### 2. DRG-Specific Search

**Request:**
```bash
curl "http://localhost:8000/providers?drg=ALCOHOL"
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
    "distance_km": null
  },
  {
    "provider_id": "330169",
    "provider_name": "Mount Sinai Beth Israel",
    "provider_city": "New York",
    "provider_state": "NY",
    "provider_zip_code": "10003",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE, LEFT AMA",
    "total_discharges": 12,
    "average_covered_charges": 45200.00,
    "average_total_payments": 9500.00,
    "average_medicare_payments": 7200.00,
    "rating": 2,
    "distance_km": null
  }
]
```

### 3. Geographic Search with Distance

**Request:**
```bash
curl "http://localhost:8000/providers?zip=10001&radius_km=10&drg=ALCOHOL"
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
    "distance_km": 0.6893849802787918
  },
  {
    "provider_id": "330169",
    "provider_name": "Mount Sinai Beth Israel",
    "provider_city": "New York",
    "provider_state": "NY",
    "provider_zip_code": "10003",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE, LEFT AMA",
    "total_discharges": 12,
    "average_covered_charges": 45200.00,
    "average_total_payments": 9500.00,
    "average_medicare_payments": 7200.00,
    "rating": 2,
    "distance_km": 0.6893849802787918
  }
]
```

### 4. Large Radius Search

**Request:**
```bash
curl "http://localhost:8000/providers?zip=10001&radius_km=20"
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
    "ms_drg_definition": "TRAUMA TO THE SKIN, SUBCUTANEOUS TISSUE AND BREAST WITHOUT MCC",
    "total_discharges": 45,
    "average_covered_charges": 25000.00,
    "average_total_payments": 12000.00,
    "average_medicare_payments": 9500.00,
    "rating": 7,
    "distance_km": 0.6893849802787918
  },
  {
    "provider_id": "330057",
    "provider_name": "St Peter's Hospital",
    "provider_city": "Albany",
    "provider_state": "NY",
    "provider_zip_code": "12208",
    "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC",
    "total_discharges": 25,
    "average_covered_charges": 12500.50,
    "average_total_payments": 8500.25,
    "average_medicare_payments": 6500.75,
    "rating": 6,
    "distance_km": 15.234567890123456
  }
]
```

## Natural Language Query Examples

### 1. Cost Comparison Query

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the cheapest hospitals for alcohol treatment in New York?"}'
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
      "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC",
      "total_discharges": 28,
      "rating": 8
    },
    {
      "provider_name": "Mount Sinai Beth Israel",
      "provider_city": "New York",
      "average_covered_charges": 50464.89,
      "ms_drg_definition": "ALCOHOL, DRUG ABUSE OR DEPENDENCE WITHOUT REHABILITATION THERAPY WITHOUT MCC",
      "total_discharges": 35,
      "rating": 5
    }
  ]
}
```

### 2. Geographic Distribution Query

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many hospitals are there in each borough of New York?"}'
```

**Response:**
```json
{
  "answer": "Found 5 results. Here's the distribution of hospitals by borough:",
  "results": [
    {
      "provider_state": "NY",
      "provider_city": "New York",
      "hospital_count": 3
    },
    {
      "provider_state": "NY",
      "provider_city": "Brooklyn",
      "hospital_count": 1
    },
    {
      "provider_state": "NY",
      "provider_city": "Queens",
      "hospital_count": 1
    }
  ]
}
```

### 3. Rating Analysis Query

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Which hospitals have the highest ratings for trauma care?"}'
```

**Response:**
```json
{
  "answer": "Found 8 results. Here are the hospitals with the highest ratings for trauma care:",
  "results": [
    {
      "provider_name": "Bellevue Hospital Center",
      "provider_city": "New York",
      "rating": 9,
      "ms_drg_definition": "TRAUMA TO THE SKIN, SUBCUTANEOUS TISSUE AND BREAST WITHOUT MCC",
      "average_covered_charges": 25000.00
    },
    {
      "provider_name": "Mount Sinai Beth Israel",
      "provider_city": "New York",
      "rating": 8,
      "ms_drg_definition": "TRAUMA TO THE SKIN, SUBCUTANEOUS TISSUE AND BREAST WITHOUT MCC",
      "average_covered_charges": 28000.00
    }
  ]
}
```

### 4. Specific DRG Query

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all providers for DRG 470 in Brooklyn"}'
```

**Response:**
```json
{
  "answer": "Found 2 results. Here are all providers for DRG 470 in Brooklyn:",
  "results": [
    {
      "provider_name": "Brooklyn Hospital Center",
      "provider_city": "Brooklyn",
      "provider_state": "NY",
      "ms_drg_definition": "MAJOR JOINT REPLACEMENT OR REATTACHMENT OF LOWER EXTREMITY",
      "total_discharges": 15,
      "average_covered_charges": 45000.00,
      "average_total_payments": 18000.00,
      "rating": 7
    }
  ]
}
```

### 5. Average Cost Analysis Query

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the average cost of heart surgery in Manhattan?"}'
```

**Response:**
```json
{
  "answer": "Found 3 results. Here's the average cost analysis for heart surgery in Manhattan:",
  "results": [
    {
      "provider_name": "Mount Sinai Beth Israel",
      "provider_city": "New York",
      "ms_drg_definition": "PERCUTANEOUS CARDIOVASCULAR PROCEDURES WITH DRUG-ELUTING STENT WITHOUT MCC",
      "average_covered_charges": 75000.00,
      "average_total_payments": 25000.00,
      "total_discharges": 20,
      "rating": 8
    },
    {
      "provider_name": "Bellevue Hospital Center",
      "provider_city": "New York",
      "ms_drg_definition": "PERCUTANEOUS CARDIOVASCULAR PROCEDURES WITH DRUG-ELUTING STENT WITHOUT MCC",
      "average_covered_charges": 68000.00,
      "average_total_payments": 22000.00,
      "total_discharges": 18,
      "rating": 9
    }
  ]
}
```

## Error Response Examples

### 1. Invalid ZIP Code

**Request:**
```bash
curl "http://localhost:8000/providers?zip=99999&radius_km=10"
```

**Response:**
```json
{
  "detail": "ZIP code 99999 not found in our database"
}
```

### 2. Missing Required Field

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
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

### 3. Out of Scope Question

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather like today?"}'
```

**Response:**
```json
{
  "answer": "I can only help with questions about hospital pricing and quality information. Please ask about healthcare providers, DRG prices, or ratings.",
  "results": null
}
```

### 4. No Results Found

**Request:**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me hospitals in California"}'
```

**Response:**
```json
{
  "answer": "No results found. The database only contains healthcare providers in New York state.",
  "results": null
}
```
