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
