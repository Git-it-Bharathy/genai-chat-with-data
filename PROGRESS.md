## Day 2 — Aug 31, 2026
**Goal:** Get NL → SQL → result pipeline working end-to-end

**What I did:**
- Tried running local LLM via Ollama (llama3.1:8b) — crashed with RemoteProtocolError, likely RAM constraints
- Tried smaller local model (qwen2.5-coder:1.5b) — worked but generated dialect errors (Postgres syntax instead of SQLite) and unreliable SQL on complex questions
- Switched to Gemini Flash API instead of local models
- Fixed Jupyter kernel mismatch issue (notebook was using system Python instead of venv — had to register venv as a Jupyter kernel)
- Debugged a network issue where IPv6 was broken on my machine, causing API calls to hang indefinitely — fixed by disabling IPv6 via sysctl
- Handled model deprecation: gemini-2.5-flash was retired, switched to gemini-3.6-flash
- Built generate_sql() with schema-aware prompting, few-shot examples for SQLite syntax, and a retry-on-error loop that feeds the error back to the LLM
- Built run_query() with SELECT-only safety check
- Built ask() wrapper combining generation + execution + retry

**What worked:**
- Full pipeline works: user question → Gemini generates SQL → SQL executes against SQLite → real result returned
- Retry loop successfully self-corrected a failed query (DATE_PART error → fixed to use strftime)

**What broke / issues:**
- Local LLMs (Ollama) too unreliable/resource-heavy for this task on my hardware — abandoned this approach
- Discovered a data quality issue in the dataset itself: "Region" column has a typo ("Easst" instead of "East") — will need a data cleaning step

**Tomorrow:**
- Add plain-English explanation of query results (not just raw table)
- Start wrapping pipeline in Streamlit UI


## Day 3 — Sep 1, 2026
**Goal:** Add plain-English result explanations, build the Streamlit UI, and add auto-charting

**What I did:**
- Built `explain_result()` — takes the SQL result and generates a natural-language answer to the user's original question instead of just showing a raw table
- Combined query generation, execution, and explanation into a single `ask_and_explain()` pipeline
- Stress-tested the pipeline across 6+ varied question types: top-N rankings, category aggregations, region filters, time-trend analysis — all handled correctly
- Refactored notebook prototype code into clean modules: `utils/db.py` (SQLite connection + schema) and `utils/llm.py` (Gemini prompt logic)
- Built the Streamlit chat interface in `app.py` — chat input, message history, expandable SQL/raw-data view per response
- Added automatic chart rendering — detects when a query result has a label column + numeric column and renders a bar chart alongside the text answer (skips charting for single-value results)

**What worked:**
- Full end-to-end flow confirmed in the actual UI: natural language question → SQL generation → execution → plain-English answer → auto-generated chart, all in one interface
- Time-trend question ("how did revenue trend across 2024") produced both an accurate written summary and a matching bar chart with no manual chart-type selection needed

**What broke / issues:**
- None major today — mostly integration and polish work building on yesterday's working pipeline

**Tomorrow:**
- Consider adding a data-cleaning step for known dataset issues (e.g. "Easst" typo in Region column)
- Explore adding conversation memory / follow-up question handling
- Start drafting report sections using this progress log
