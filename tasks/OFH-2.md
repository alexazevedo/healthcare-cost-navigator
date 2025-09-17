# Ticket OFH-2: Database Schema

## Description
Design and implement the database schema with async SQLAlchemy models and Alembic migrations for providers, DRG prices, and ratings.

## AI Prompt
You are an expert database designer.  
Using SQLAlchemy (async), create models and Alembic migrations for the following schema:

- providers:  
  provider_id (PK), provider_name, provider_city, provider_state, provider_zip_code  

- drg_prices:  
  id (PK), provider_id (FK -> providers.provider_id), ms_drg_definition,  
  total_discharges, average_covered_charges, average_total_payments, average_medicare_payments  

- ratings:  
  id (PK), provider_id (FK -> providers.provider_id), rating (int 1–10)  

Make sure provider_id matches the CSV column Rndrng_Prvdr_CCN (renamed to provider_id).  
Add indexes to support searching by zip_code and ms_drg_definition.  

## Acceptance Criteria
- [x] Models created for providers, drg_prices, and ratings  
- [x] Alembic migrations generated and applied  
- [x] Foreign keys and relationships set correctly  
- [x] Indexes created for performance  
- [x] provider_id aligned with CSV data  
