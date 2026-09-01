import sqlite3
import pandas as pd

DB_PATH = "data/superstore.db"

SCHEMA = """
Table: orders
Columns:
- Date (datetime) — order date
- Region (text) — North/South/East/West
- Product (text) — product name e.g. Smartwatch, Monitor, Mobile, Headphones
- Salesperson (text) — name of salesperson
- Units_Sold (float)
- Unit_Price (float)
- Category (text) — Accessories/Office/Electronics
- Revenue (float)
- Cost (float)
- Profit (float)
"""

def run_query(sql: str) -> pd.DataFrame:
    sql = sql.strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError(f"Only SELECT queries are allowed. Got: {sql[:50]}")
    conn = sqlite3.connect(DB_PATH)
    result = pd.read_sql(sql, conn)
    conn.close()
    return result