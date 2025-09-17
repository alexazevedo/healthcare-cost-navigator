"""OpenAI service for natural language to SQL conversion."""

import json

from openai import AsyncOpenAI

from app.core.config import settings


async def convert_question_to_sql(question: str) -> dict[str, str]:
    """
    Convert a natural language question to SQL query using OpenAI.

    Args:
        question: Natural language question

    Returns:
        Dictionary with 'sql' and 'explanation' keys
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = """
    You are a SQL expert for a healthcare cost database. You can ONLY help with questions about:
    - Hospital and healthcare provider information
    - Medical procedure costs (DRG codes and pricing)
    - Provider ratings and quality metrics
    - Geographic searches for healthcare providers
    - Cost comparisons between providers
    - Healthcare quality and performance data

    You CANNOT help with:
    - Weather, sports, politics, entertainment, cooking, travel, or any non-healthcare topics
    - Personal medical advice or diagnoses
    - Insurance coverage questions
    - General technology or software questions

    If asked about anything outside healthcare costs and provider information, respond with:
    {"sql": null, "explanation": "I can only help with hospital pricing and quality information."}

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
    - "sql": the SQL query (or null if out of scope)
    - "explanation": brief explanation of what the query does
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        return {
            "sql": None,
            "explanation": (f"Error processing question: {str(e)}",),
        }
