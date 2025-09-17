# Ticket OFH-3: ETL Script

## Description
Build ETL pipeline to load CMS CSV data into PostgreSQL, normalizing columns and generating mock ratings.

## AI Prompt
You are an expert in data engineering.  
Write etl.py that:  
- Reads sample_prices_ny.csv  
- Normalizes column names to match the schema:  
  provider_id, provider_name, provider_city, provider_state, provider_zip_code,  
  ms_drg_definition, total_discharges, average_covered_charges,  
  average_total_payments, average_medicare_payments  
- Loads data into providers and drg_prices tables  
- Generates mock ratings (random int 1–10) for each provider_id  
- Uses async SQLAlchemy for inserts  

## Usage

```bash
# Run the ETL pipeline
pipenv run python scripts/etl.py

# Or using make command (if added to Makefile)
make run-etl
```

## Results

The ETL pipeline successfully processed:
- **131 providers** loaded into the `providers` table
- **8,499 DRG price records** loaded into the `drg_prices` table  
- **131 ratings** generated and loaded into the `ratings` table

## Acceptance Criteria
- [x] ETL script implemented as etl.py  
- [x] Reads CSV successfully  
- [x] Normalizes and maps columns correctly  
- [x] Data loaded into providers and drg_prices  
- [x] Ratings generated for all providers  
- [x] Async SQLAlchemy used for inserts  
