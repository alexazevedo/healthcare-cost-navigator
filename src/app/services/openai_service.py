"""OpenAI service for natural language to SQL conversion."""

import json
import re
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIService:
    """Service for converting natural language queries to SQL."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def convert_question_to_sql(self, question: str) -> Dict[str, str]:
        """
        Convert a natural language question to SQL query.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        # Check if question is out of scope
        if self._is_out_of_scope(question):
            return {
                "sql": None,
                "explanation": "I can only help with hospital pricing and quality information."
            }
        
        system_prompt = """
        You are a SQL expert for a healthcare cost database. Convert natural language questions to SQL queries.
        
        Database schema:
        - providers: provider_id, provider_name, provider_city, provider_state, provider_zip_code
        - drg_prices: provider_id, ms_drg_definition, total_discharges, average_covered_charges, average_total_payments, average_medicare_payments
        - ratings: provider_id, rating
        
        Common patterns:
        - "cheapest" or "lowest cost" = ORDER BY average_covered_charges ASC
        - "most expensive" or "highest cost" = ORDER BY average_covered_charges DESC
        - "within X miles" = use haversine distance calculation
        - "DRG 470" = WHERE ms_drg_definition ILIKE '%470%'
        - "near 10001" = filter by distance from ZIP code 10001
        
        Return only valid PostgreSQL queries. Use proper JOINs between tables.
        Always include provider information and costs in the result.
        """
        
        user_prompt = f"""
        Convert this question to SQL: "{question}"
        
        Return a JSON object with:
        - "sql": the SQL query
        - "explanation": brief explanation of what the query does
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            return {
                "sql": None,
                "explanation": f"Error processing question: {str(e)}"
            }
    
    def _is_out_of_scope(self, question: str) -> bool:
        """
        Check if the question is out of scope for healthcare pricing.
        
        Args:
            question: The user's question
            
        Returns:
            True if out of scope, False otherwise
        """
        out_of_scope_keywords = [
            "weather", "temperature", "rain", "snow", "forecast",
            "sports", "football", "basketball", "baseball",
            "politics", "election", "president", "congress",
            "cooking", "recipe", "food", "restaurant",
            "travel", "vacation", "hotel", "flight",
            "entertainment", "movie", "music", "book"
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in out_of_scope_keywords)
