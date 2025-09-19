#!/usr/bin/env python3
"""
Extract NY Data from CMS Source CSV

This script downloads the official CMS dataset, extracts only rows related to
New York state, and normalizes the columns to match the required schema.
"""

import sys
from pathlib import Path

import pandas as pd
import requests


def download_cms_data(url: str, output_path: str) -> bool:
    """
    Download the CMS dataset from the provided URL.

    Args:
        url: The URL to download the dataset from
        output_path: Local path to save the downloaded file

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        print(f"Downloading dataset from: {url}")

        # First, get the page to find the actual download link
        response = requests.get(url)
        response.raise_for_status()

        # Check if we got HTML instead of CSV
        if response.headers.get("content-type", "").startswith("text/html"):
            print("Received HTML page, looking for direct download link...")

            # Try to find the direct download link in the HTML
            import re

            html_content = response.text

            # Look for CSV download links
            csv_patterns = [
                r'href="([^"]*\.csv[^"]*)"',
                r'href="([^"]*download[^"]*\.csv[^"]*)"',
                r'data-download-url="([^"]*\.csv[^"]*)"',
            ]

            download_url = None
            for pattern in csv_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    download_url = matches[0]
                    if not download_url.startswith("http"):
                        # Make it absolute URL
                        from urllib.parse import urljoin

                        download_url = urljoin(url, download_url)
                    break

            if not download_url:
                print(
                    "Could not find direct CSV download link. Trying alternative approach..."
                )
                # Try the resource ID approach
                resource_id = "e51cf14c-615a-4efe-ba6b-3a3ef15dcfb0"
                download_url = f"https://data.cms.gov/api/views/{resource_id}/rows.csv?accessType=DOWNLOAD"
                print(f"Trying direct API URL: {download_url}")
            else:
                print(f"Found download URL: {download_url}")

            # Download the actual CSV file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

        # Save the file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Dataset downloaded successfully to: {output_path}")
        return True

    except requests.RequestException as e:
        print(f"Error downloading dataset: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during download: {e}")
        return False


def extract_ny_data(input_file: str, output_file: str) -> bool:
    """
    Extract NY data from the CMS dataset and normalize columns.

    Args:
        input_file: Path to the downloaded CMS dataset
        output_file: Path to save the processed NY data

    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        print(f"Reading dataset from: {input_file}")

        # Read the CSV file with proper encoding
        try:
            df = pd.read_csv(input_file, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding="latin-1")
            except UnicodeDecodeError:
                df = pd.read_csv(input_file, encoding="cp1252")
        print(f"Original dataset shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")

        # Filter for New York state only
        print("Filtering for New York state...")
        ny_df = df[df["Rndrng_Prvdr_State_Abrvtn"] == "NY"].copy()
        print(f"NY data shape: {ny_df.shape}")

        if ny_df.empty:
            print("No data found for New York state!")
            return False

        # Define column mapping based on actual CSV columns
        column_mapping = {
            "Rndrng_Prvdr_CCN": "provider_id",
            "Rndrng_Prvdr_Org_Name": "provider_name",
            "Rndrng_Prvdr_City": "provider_city",
            "Rndrng_Prvdr_State_Abrvtn": "provider_state",
            "Rndrng_Prvdr_Zip5": "provider_zip_code",
            "DRG_Cd": "drg_id",
            "DRG_Desc": "ms_drg_definition",  # Using DRG_Desc instead of DRG_Definition
            "Tot_Dschrgs": "total_discharges",
            "Avg_Submtd_Cvrd_Chrg": "average_covered_charges",  # Using Avg_Submtd_Cvrd_Chrg instead of Avg_Cvrd_Chrg
            "Avg_Tot_Pymt_Amt": "average_total_payments",
            "Avg_Mdcr_Pymt_Amt": "average_medicare_payments",
        }

        # Check if all required columns exist
        missing_columns = [
            col for col in column_mapping.keys() if col not in df.columns
        ]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print("Available columns:")
            for col in sorted(df.columns):
                print(f"  - {col}")
            return False

        # Rename columns according to schema
        print("Mapping columns to normalized schema...")
        ny_df = ny_df.rename(columns=column_mapping)

        # Select only the mapped columns
        mapped_columns = list(column_mapping.values())
        ny_df = ny_df[mapped_columns]

        # Clean the data
        print("Cleaning data...")

        # Remove rows with missing critical data
        ny_df = ny_df.dropna(
            subset=["provider_id", "provider_name", "ms_drg_definition"]
        )

        # Clean numeric columns
        numeric_columns = [
            "total_discharges",
            "average_covered_charges",
            "average_total_payments",
            "average_medicare_payments",
        ]

        for col in numeric_columns:
            if col in ny_df.columns:
                # Remove dollar signs and commas, convert to numeric
                ny_df[col] = (
                    ny_df[col].astype(str).str.replace("$", "").str.replace(",", "")
                )
                ny_df[col] = pd.to_numeric(ny_df[col], errors="coerce")

        # Remove rows where numeric values are invalid
        ny_df = ny_df.dropna(subset=numeric_columns)

        # Clean string columns
        string_columns = ["provider_name", "provider_city", "ms_drg_definition", "drg_id"]
        for col in string_columns:
            if col in ny_df.columns:
                ny_df[col] = ny_df[col].astype(str).str.strip()

        # Clean provider_id and zip_code
        if "provider_id" in ny_df.columns:
            ny_df["provider_id"] = ny_df["provider_id"].astype(str).str.strip()

        if "provider_zip_code" in ny_df.columns:
            ny_df["provider_zip_code"] = (
                ny_df["provider_zip_code"].astype(str).str.strip()
            )

        print(f"Final cleaned dataset shape: {ny_df.shape}")

        # Save the processed data
        print(f"Saving processed data to: {output_file}")
        ny_df.to_csv(output_file, index=False)

        # Display summary statistics
        print("\nData Summary:")
        print(f"Total records: {len(ny_df)}")
        print(f"Unique providers: {ny_df['provider_id'].nunique()}")
        print(f"Unique DRG definitions: {ny_df['ms_drg_definition'].nunique()}")
        print(f"Date range: {ny_df.index.min()} to {ny_df.index.max()}")

        print("\nSample of processed data:")
        print(ny_df.head())

        return True

    except Exception as e:
        print(f"Error processing data: {e}")
        return False


def main():
    """Main function to orchestrate the data extraction process."""

    # Configuration
    cms_url = "https://catalog.data.gov/dataset/medicare-inpatient-hospitals-by-provider-and-service-9af02/resource/e51cf14c-615a-4efe-ba6b-3a3ef15dcfb0"
    temp_file = "cms_data_temp.csv"
    output_file = "sample_prices_ny.csv"

    print("=" * 60)
    print("CMS Data Extraction for New York State")
    print("=" * 60)

    # Step 1: Download the dataset
    if not download_cms_data(cms_url, temp_file):
        print("Failed to download dataset. Exiting.")
        sys.exit(1)

    # Step 2: Process the data
    if not extract_ny_data(temp_file, output_file):
        print("Failed to process data. Exiting.")
        sys.exit(1)

    # Step 3: Clean up temporary file
    try:
        Path(temp_file).unlink()
        print(f"Cleaned up temporary file: {temp_file}")
    except Exception as e:
        print(f"Warning: Could not remove temporary file {temp_file}: {e}")

    print("\n" + "=" * 60)
    print("Data extraction completed successfully!")
    print(f"Output file: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
