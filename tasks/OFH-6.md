# Ticket OFH-6: Extract NY Data from CMS Source CSV

## Description
Download the official CMS dataset from the provided link, extract only rows related to New York state, and normalize the columns to match the required schema. Save the resulting file as `sample_prices_ny.csv` for use in the ETL step.

## AI Prompt
You are an expert in data engineering.  
Write a Python script (`extract_ny_data.py`) that:  
- Downloads the dataset from the link: 
  https://data.cms.gov/sites/default/files/2024-05/7d1f4bcd-7dd9-4fd1-aa7f-91cd69e452d3/MUP_INP_RY24_P03_V10_DY22_PrvSvc.CSV
- Extracts only rows where the provider state = "NY".  
- Maps the original CSV columns into the following normalized schema:  
    provider_id -> Rndrng_Prvdr_CCN
    provider_name -> Rndrng_Prvdr_Org_Name
    provider_city -> Rndrng_Prvdr_City
    provider_state -> Rndrng_Prvdr_State_Abrvtn
    provider_zip_code -> Rndrng_Prvdr_Zip5
    ms_drg_definition -> DRG_Definition
    total_discharges -> Tot_Dschrgs
    average_covered_charges -> Avg_Cvrd_Chrg
    average_total_payments -> Avg_Tot_Pymt_Amt
    average_medicare_payments -> Avg_Mdcr_Pymt_Amt
- Writes the cleaned and normalized result into a new file: `sample_prices_ny.csv`.

## Usage

```bash
# Download and extract NY healthcare data
make download-sample-ny-data

# Or run directly
pipenv run python scripts/extract_ny_data.py
```

## Acceptance Criteria
- [x] Script `extract_ny_data.py` implemented  
- [x] Dataset downloaded from the provided CMS link  
- [x] Only rows for New York (NY) are kept  
- [x] Columns renamed and mapped exactly as per schema  
- [x] Output file `sample_prices_ny.csv` generated successfully  
- [x] File ready for use by ETL pipeline  