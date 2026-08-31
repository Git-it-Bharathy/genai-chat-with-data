## Day 1 — Aug 30, 2026
**Goal:** Pick project direction and get initial setup done

**What I did:**
- Decided on final project direction: chat-with-your-data (natural language to SQL/query tool)
- Sourced dataset: Superstore sales data (downloaded as .xlsx)
- Set up project folder structure (notebooks/, utils/, data/, app.py, venv)
- Loaded dataset into SQLite as "orders" table — columns: Date, Region, Product, Salesperson, Units_Sold, Unit_Price, Category, Revenue, Cost, Profit (2000 rows)
- Set up Jupyter notebook for prototyping
- Initial attempt at LLM integration using Anthropic API — got blocked on API key setup (dotenv path issues)

**What worked:**
- Dataset loaded cleanly into SQLite with no data issues at this stage
- Project structure set up cleanly, ready for development

**What broke / issues:**
- Struggled with .env file not loading correctly via python-dotenv (file initially wasn't created, then wasn't found from notebook's working directory)
- Accidentally pasted a live API key into chat — had to revoke and treat it as compromised

**Tomorrow:**
- Get LLM → SQL generation actually working
- Consider local LLM (Ollama) as alternative to avoid API key management


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
