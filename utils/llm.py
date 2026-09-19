import ollama
import re

MODEL = "qwen2.5-coder:7b"

def generate_sql(schema: str, question: str, error_context: str = None) -> str:
    error_note = f"\n\nYour previous attempt failed with this error: {error_context}\nFix the query." if error_context else ""
    
    prompt = f"""You are a SQLite expert. Given this table schema:

{schema}

IMPORTANT: This is SQLite, not PostgreSQL or MySQL. Use SQLite syntax only.
- For dates, use strftime('%Y', Date), strftime('%m', Date), or strftime('%Y-%m', Date)
- Keep queries as simple as possible — avoid unnecessary subqueries or aliases when a single query works

Write a single valid SQLite SELECT query to answer this question:
"{question}"

Rules:
- Only output the raw SQL query, nothing else — no markdown, no explanation, no backticks
- Only use SELECT statements — never DROP, DELETE, UPDATE, INSERT, or ALTER
- Use the exact column and table names given above{error_note}
"""
    response = ollama.chat(model=MODEL, messages=[
        {"role": "user", "content": prompt}
    ])
    raw = response['message']['content'].strip()
    raw = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return raw


def explain_result(question: str, sql: str, result) -> str:
    result_text = result.to_string(index=False)
    
    prompt = f"""A user asked this question about their data:
"{question}"

This SQL query was run to answer it:
{sql}

Here is the result:
{result_text}

Write a short, clear, plain-English answer to the user's original question based on this result.
Be direct and conversational — 1-2 sentences. Don't mention SQL or the query.
"""
    response = ollama.chat(model=MODEL, messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content'].strip()


