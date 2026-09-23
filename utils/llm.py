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
- NEVER use GROUP_CONCAT without DISTINCT — always write GROUP_CONCAT(DISTINCT column) to avoid huge repeated text blobs
- If a question asks for a "summary", prefer COUNT, AVG, and simple aggregates over concatenating raw text columns

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

    MAX_CHARS = 1500
    if len(result_text) > MAX_CHARS:
        result_text = result_text[:MAX_CHARS] + "\n...(truncated, result too large to show in full)"

    prompt = f"""You are a data analyst reading a query result and explaining it to someone in plain English.

User's question: "{question}"

Actual query result:
{result_text}

Write a short, direct answer (1-2 sentences) using the REAL numbers and values from the result above.

CRITICAL RULES:
- Copy the actual numbers/values from the result into your answer — never write placeholder text like [total_entries] or [value] or brackets of any kind
- Every number or word in your answer must be something you can point to directly in the result above
- Do not say you don't have access to the data — it is provided above
- Do not mention SQL, queries, or tables
- Just state the finding directly, like: "There are 8807 entries, averaging around 2013 for release year."
"""

    response = ollama.chat(model=MODEL, messages=[
        {"role": "user", "content": prompt}
    ])
    answer = response['message']['content'].strip()

    refusal_phrases = ["i don't have", "i do not have", "i'm sorry", "i am sorry", "cannot answer", "unable to answer", "need more information"]
    placeholder_issue = "[" in answer and "]" in answer

    if any(phrase in answer.lower() for phrase in refusal_phrases) or placeholder_issue:
        answer = "Here's what I found — check the table below for the full result."

    return answer
