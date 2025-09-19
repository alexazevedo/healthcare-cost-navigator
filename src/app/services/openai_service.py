"""OpenAI service for NL → SQL generation and grounded answers using SQLDatabaseChain."""

import asyncio
import re
from typing import Any

from fastapi import HTTPException
from langchain.prompts import PromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_sync_engine

ALLOWED_TABLES = {
    "providers": {"provider_id", "provider_name", "provider_city", "provider_state", "provider_zip_code"},
    "drgs": {"drg_id", "ms_drg_definition"},  # drg_id is INTEGER
    "drg_prices": {
        "id",
        "provider_id",
        "drg_id",  # INTEGER FK to drgs.drg_id
        "total_discharges",
        "average_covered_charges",
        "average_total_payments",
        "average_medicare_payments",
    },
    "ratings": {"id", "provider_id", "rating"},
    "zip_codes": {"zip_code", "latitude", "longitude"},
}

FORBIDDEN_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]


# Initialize LLM
llm = ChatOpenAI(model=settings.OPENAI_MODEL or "gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)

# Create sync engine and custom SQLDatabase
sync_engine = get_sync_engine()


# Custom SQLDatabase that cleans SQL before execution
class SafeSQLDatabase(SQLDatabase):
    def run(self, command: str, fetch: str = "all", include_columns: bool = False):
        """Override to clean SQL before execution."""
        # Clean markdown formatting from the command
        clean_command = re.sub(r"^```sql\s*", "", command, flags=re.IGNORECASE)
        clean_command = re.sub(r"\s*```$", "", clean_command, flags=re.IGNORECASE)
        clean_command = clean_command.strip()

        # Call the parent method with cleaned command
        return super().run(clean_command, fetch, include_columns)


db = SafeSQLDatabase(sync_engine)

# Custom prompt template that avoids markdown formatting and provides explicit schema
CUSTOM_SQL_PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "dialect"],
    template="""Given an input question, create a syntactically correct {dialect} query to run and return the answer.

Use this exact format with NO markdown, NO code blocks, NO backticks:

Question: Question here
SQLQuery: SELECT statement here
SQLResult: Result of the SQLQuery
Answer: Final answer here

EXACT SCHEMA (use these exact column names):
- providers: provider_id, provider_name, provider_city, provider_state, provider_zip_code
- drgs: drg_id (INTEGER), ms_drg_definition (VARCHAR) -- NOTE: ms_drg_definition not msr_drg_definition
- drg_prices: id, provider_id, drg_id (INTEGER FK), total_discharges, average_covered_charges, average_total_payments, average_medicare_payments
- ratings: id, provider_id, rating
- zip_codes: zip_code, latitude, longitude

CRITICAL: 
- Use exact column names: ms_drg_definition (NOT msr_drg_definition)
- drg_id is INTEGER type
- Write SQL queries as plain text without any formatting

Question: {input}""",
)

# Create SQLDatabaseChain with custom database and prompt
sql_db_chain = SQLDatabaseChain.from_llm(
    llm=llm,
    db=db,
    prompt=CUSTOM_SQL_PROMPT,
    verbose=True,
    use_query_checker=True,
    return_intermediate_steps=True,
)


def validate_sql(sql: str) -> bool:
    """Allow only read-only queries (SELECT / WITH)."""
    if not sql:
        return False
    normalized = sql.strip().lstrip("(").strip()
    normalized_lower = re.sub(r"\s+", " ", normalized).lower()
    return normalized_lower.startswith("select") or normalized_lower.startswith("with")


async def ask_langchain(question: str) -> dict[str, Any]:
    """Use SQLDatabaseChain to convert NL → SQL → results with custom prompt."""
    try:
        # Run the chain in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(sql_db_chain.invoke, {"query": question})

        # Extract SQL from intermediate steps
        sql_query = None
        if isinstance(result, dict):
            steps = result.get("intermediate_steps") or []
            if steps and isinstance(steps, list):
                for step in steps:
                    if isinstance(step, dict) and "sql_cmd" in step:
                        sql_query = step["sql_cmd"]
                        break

        # If no SQL from steps, try to extract from result string
        if not sql_query:
            result_str = str(result)
            # Look for "SQLQuery:" followed by the query
            query_match = re.search(
                r"SQLQuery:\s*([^\\n]*(?:\\n[^\\n]*)*?)(?=\\nSQLResult:|\\nAnswer:|$)", result_str, re.IGNORECASE
            )
            if query_match:
                sql_query = query_match.group(1).strip()
            else:
                # Fallback: look for SELECT statements
                select_match = re.search(
                    r"SELECT[\s\S]+?(?=\\n\\n|\\nSQLResult:|\\nAnswer:|$)", result_str, re.IGNORECASE
                )
                if select_match:
                    sql_query = select_match.group(0).strip()

        # Clean up any remaining markdown formatting
        if sql_query:
            sql_query = re.sub(r"^```sql\s*", "", sql_query, flags=re.IGNORECASE)
            sql_query = re.sub(r"\s*```$", "", sql_query, flags=re.IGNORECASE)
            sql_query = sql_query.strip()

        if not sql_query:
            raise HTTPException(status_code=500, detail="Failed to extract SQL query from response.")

        # Validate safety boundaries (read-only, allowed tables)
        if not validate_sql(sql_query):
            raise HTTPException(status_code=400, detail="Only read-only SELECT queries are allowed.")

        return {
            "success": True,
            "sql_query": sql_query,
            "answer": result.get("result") if isinstance(result, dict) else str(result),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLDatabaseChain error: {str(e)}") from e


# Backward-compatible helpers used by endpoints
async def nl_to_sql(question: str) -> str:
    result = await ask_langchain(question)
    return result.get("sql_query", "")


async def run_sql(db: AsyncSession, sql_query: str) -> list[dict[str, Any]]:
    try:
        if not validate_sql(sql_query):
            return [{"error": "Only read-only SELECT queries are allowed.", "sql_query": sql_query}]

        result = await db.execute(text(sql_query))
        rows = result.mappings().all()
        return [dict(row) for row in rows]
    except Exception as e:
        return [{"error": str(e), "sql_query": sql_query}]


async def generate_grounded_answer(
    question: str,
    sql_query: str,
    results: list[dict[str, Any]],
) -> str:
    prompt = (
        "Answer the user's question based strictly on the SQL results.\n"
        f"Question: {question}\n"
        f"SQL: {sql_query}\n"
        f"Results: {results}\n"
    )
    try:
        ai_msg = await llm.ainvoke(prompt)
        return getattr(ai_msg, "content", str(ai_msg))
    except Exception as e:
        return f"Unable to generate grounded answer: {e}"
