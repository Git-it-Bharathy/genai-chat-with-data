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

    prompt = f"""You are a data analyst. You have already run a query and have the exact result below — you have full access to this data, it is provided to you directly.

User's question: "{question}"

Query result (this IS the answer, read it directly):
{result_text}

Task: Write a short, direct, plain-English answer to the user's question using ONLY the numbers/values in the result above.

Rules:
- You DO have the data — it's right above. Never say you don't have access, can't answer, or need more information.
- Just state the answer directly, like reading a number off the table and explaining what it means.
- 1-2 sentences, conversational tone. No SQL mentions.
"""
    response = ollama.chat(model=MODEL, messages=[
        {"role": "user", "content": prompt}
    ])
    answer = response['message']['content'].strip()

    # Safety net: if the model still refuses despite having the data, fall back to a simple direct statement
    refusal_phrases = ["i don't have", "i do not have", "i'm sorry", "i am sorry", "cannot answer", "unable to answer", "need more information"]
    if any(phrase in answer.lower() for phrase in refusal_phrases):
        answer = f"Based on the data: {result_text}"

    return answer
