#!/usr/bin/env python3
"""
ETL Pipeline for Healthcare Cost Navigator

This script loads CMS CSV data into PostgreSQL, normalizing columns and generating mock ratings.
"""

import asyncio
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.database import AsyncSessionLocal
from app.models.provider import Provider
from app.models.drg_price import DRGPrice
from app.models.rating import Rating
from app.models.zip_code import ZipCode


class ETLPipeline:
    """ETL Pipeline for loading healthcare data into PostgreSQL."""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.processed_providers = set()
        self.provider_data = {}
        self.drg_data = []
        self.ratings_data = []
    
    async def run(self) -> None:
        """Run the complete ETL pipeline."""
        print("=" * 60)
        print("Healthcare Cost Navigator - ETL Pipeline")
        print("=" * 60)
        
        try:
            # Step 1: Read and validate CSV
            print("Step 1: Reading CSV data...")
            await self._read_csv()
            
            # Step 2: Normalize and prepare data
            print("Step 2: Normalizing and preparing data...")
            await self._normalize_data()
            
            # Step 3: Load providers
            print("Step 3: Loading providers...")
            await self._load_providers()
            
            # Step 4: Load DRG prices
            print("Step 4: Loading DRG prices...")
            await self._load_drg_prices()
            
            # Step 5: Generate and load ratings
            print("Step 5: Generating and loading ratings...")
            await self._generate_and_load_ratings()
            await self._load_zip_codes()
            
            print("\n" + "=" * 60)
            print("ETL Pipeline completed successfully!")
            print(f"Processed {len(self.processed_providers)} providers")
            print(f"Loaded {len(self.drg_data)} DRG price records")
            print(f"Generated {len(self.ratings_data)} ratings")
            print("=" * 60)
            
        except Exception as e:
            print(f"ETL Pipeline failed: {e}")
            raise
    
    async def _read_csv(self) -> None:
        """Read and validate the CSV file."""
        if not Path(self.csv_file_path).exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
        
        # Read CSV with proper encoding
        try:
            self.df = pd.read_csv(self.csv_file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                self.df = pd.read_csv(self.csv_file_path, encoding='latin-1')
            except UnicodeDecodeError:
                self.df = pd.read_csv(self.csv_file_path, encoding='cp1252')
        
        print(f"CSV loaded: {len(self.df)} records, {len(self.df.columns)} columns")
        print(f"Columns: {list(self.df.columns)}")
        
        # Validate required columns
        required_columns = [
            'provider_id', 'provider_name', 'provider_city', 'provider_state', 
            'provider_zip_code', 'ms_drg_definition', 'total_discharges',
            'average_covered_charges', 'average_total_payments', 'average_medicare_payments'
        ]
        
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    async def _normalize_data(self) -> None:
        """Normalize and prepare data for loading."""
        # Clean and validate data
        self.df = self.df.dropna(subset=['provider_id', 'provider_name', 'ms_drg_definition'])
        
        # Ensure numeric columns are properly formatted
        numeric_columns = [
            'total_discharges', 'average_covered_charges', 
            'average_total_payments', 'average_medicare_payments'
        ]
        
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Remove rows with invalid numeric data
        self.df = self.df.dropna(subset=numeric_columns)
        
        # Clean string columns
        string_columns = ['provider_name', 'provider_city', 'ms_drg_definition']
        for col in string_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
        
        # Clean provider_id and zip_code
        self.df['provider_id'] = self.df['provider_id'].astype(str).str.strip()
        self.df['provider_zip_code'] = self.df['provider_zip_code'].astype(str).str.strip()
        
        print(f"Data normalized: {len(self.df)} valid records")
    
    async def _load_providers(self) -> None:
        """Load unique providers into the database."""
        async with AsyncSessionLocal() as session:
            # Get unique providers
            unique_providers = self.df.groupby('provider_id').first().reset_index()
            
            for _, row in unique_providers.iterrows():
                provider_id = row['provider_id']
                
                # Check if provider already exists
                result = await session.execute(
                    select(Provider).where(Provider.provider_id == provider_id)
                )
                existing_provider = result.scalar_one_or_none()
                
                if not existing_provider:
                    provider = Provider(
                        provider_id=provider_id,
                        provider_name=row['provider_name'],
                        provider_city=row['provider_city'],
                        provider_state=row['provider_state'],
                        provider_zip_code=row['provider_zip_code']
                    )
                    session.add(provider)
                    self.processed_providers.add(provider_id)
                    self.provider_data[provider_id] = provider
                else:
                    self.processed_providers.add(provider_id)
                    self.provider_data[provider_id] = existing_provider
            
            await session.commit()
            print(f"Loaded {len(self.processed_providers)} providers")
    
    async def _load_drg_prices(self) -> None:
        """Load DRG prices into the database."""
        async with AsyncSessionLocal() as session:
            for _, row in self.df.iterrows():
                provider_id = row['provider_id']
                
                # Get the provider from our loaded data
                if provider_id not in self.provider_data:
                    continue
                
                drg_price = DRGPrice(
                    provider_id=provider_id,
                    ms_drg_definition=row['ms_drg_definition'],
                    total_discharges=int(row['total_discharges']),
                    average_covered_charges=float(row['average_covered_charges']),
                    average_total_payments=float(row['average_total_payments']),
                    average_medicare_payments=float(row['average_medicare_payments'])
                )
                session.add(drg_price)
                self.drg_data.append(drg_price)
            
            await session.commit()
            print(f"Loaded {len(self.drg_data)} DRG price records")
    
    async def _generate_and_load_ratings(self) -> None:
        """Generate mock ratings for all providers and load into database."""
        async with AsyncSessionLocal() as session:
            for provider_id in self.processed_providers:
                # Generate random rating between 1 and 10
                rating_value = random.randint(1, 10)
                
                rating = Rating(
                    provider_id=provider_id,
                    rating=rating_value
                )
                session.add(rating)
                self.ratings_data.append(rating)
            
            await session.commit()
            print(f"Generated {len(self.ratings_data)} ratings")

    async def _load_zip_codes(self) -> None:
        """Load ZIP code data from CSV into database."""
        zip_csv_path = "zip_lat_lon.csv"
        
        if not Path(zip_csv_path).exists():
            print(f"ZIP code CSV file not found: {zip_csv_path}")
            print("Please run 'python scripts/build_zip_latlon.py' first")
            return

        print(f"Loading ZIP code data from: {zip_csv_path}")
        
        try:
            # Read ZIP code data
            df = pd.read_csv(zip_csv_path)
            print(f"Found {len(df)} ZIP codes")
            
            async with AsyncSessionLocal() as session:
                # Clear existing ZIP code data
                await session.execute(text("DELETE FROM zip_codes"))
                
                # Load new ZIP code data
                for _, row in df.iterrows():
                    # Convert ZIP code to integer first to remove decimal point, then back to string
                    zip_code_str = str(int(float(row['zip_code'])))
                    zip_code = ZipCode(
                        zip_code=zip_code_str,
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude'])
                    )
                    session.add(zip_code)
                
                await session.commit()
                print(f"Loaded {len(df)} ZIP codes into database")
                
        except Exception as e:
            print(f"Error loading ZIP code data: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded data."""
        async with AsyncSessionLocal() as session:
            # Count providers
            provider_count = await session.execute(select(Provider))
            provider_count = len(provider_count.scalars().all())
            
            # Count DRG prices
            drg_count = await session.execute(select(DRGPrice))
            drg_count = len(drg_count.scalars().all())
            
            # Count ratings
            rating_count = await session.execute(select(Rating))
            rating_count = len(rating_count.scalars().all())
            
            return {
                'providers': provider_count,
                'drg_prices': drg_count,
                'ratings': rating_count
            }


async def main():
    """Main function to run the ETL pipeline."""
    csv_file = "sample_prices_ny.csv"
    
    if not Path(csv_file).exists():
        print(f"Error: {csv_file} not found. Please run 'make download-sample-ny-data' first.")
        return
    
    etl = ETLPipeline(csv_file)
    await etl.run()
    
    # Display final statistics
    stats = await etl.get_statistics()
    print(f"\nFinal Statistics:")
    print(f"  Providers: {stats['providers']}")
    print(f"  DRG Prices: {stats['drg_prices']}")
    print(f"  Ratings: {stats['ratings']}")


if __name__ == "__main__":
    asyncio.run(main())
