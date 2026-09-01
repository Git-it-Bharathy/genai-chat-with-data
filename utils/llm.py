from google import genai
from dotenv import load_dotenv
import os
import re

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.6-flash"

def generate_sql(schema: str, question: str, error_context: str = None) -> str:
    error_note = f"\n\nYour previous attempt failed with this error: {error_context}\nFix the query." if error_context else ""
    prompt = f"""You are a SQLite expert. Given this table schema:

{schema}

IMPORTANT: This is SQLite, not PostgreSQL or MySQL. Use SQLite syntax only.
- For dates, use strftime('%Y', Date), strftime('%m', Date), or strftime('%Y-%m', Date)

Write a single valid SQLite SELECT query to answer this question:
"{question}"

Rules:
- Only output the raw SQL query, nothing else — no markdown, no explanation, no backticks
- Only use SELECT statements — never DROP, DELETE, UPDATE, INSERT, or ALTER
- Use the exact column and table names given above{error_note}
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return raw

def explain_result(question: str, sql: str, result) -> str:
    result_text = result.to_string(index=False)
    prompt = f"""A user asked this question about sales data:
"{question}"

This SQL query was run to answer it:
{sql}

Here is the result:
{result_text}

Write a short, clear, plain-English answer to the user's original question based on this result.
Be direct and conversational — 1-2 sentences. Don't mention SQL or the query.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()