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

## Acceptance Criteria
- [ ] ETL script implemented as etl.py  
- [ ] Reads CSV successfully  
- [ ] Normalizes and maps columns correctly  
- [ ] Data loaded into providers and drg_prices  
- [ ] Ratings generated for all providers  
- [ ] Async SQLAlchemy used for inserts  
