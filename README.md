# InsightForge AI: Conversational Analytics on Your CSV

Upload a CSV, ask a question in plain English, and get the SQL, an interactive dashboard and a written insight back.
Everything runs **locally**: the LLM runs through Ollama, and your data never leaves your machine.

<!-- Add screenshots to a docs/ folder and uncomment these lines
![Dashboard](docs/dashboard.png)
![SQL and logs](docs/sql-logs.png)
-->

## Features

- **Text-to-SQL** with a local model (`qwen2.5-coder` via Ollama), no API keys or cloud calls
- **Schema RAG**: the table schema and a per-column profile (real values, ranges, missing counts) are indexed in ChromaDB and retrieved for each question, so the model writes exact filters
- **Self-correcting SQL loop**: failed queries are sent back to the model with the error, up to 3 attempts
- **Result validation**: queries that run but look wrong (identical columns, the same value for every group, empty groups in a ranking, one group per row) are flagged and retried
- **Automatic repairs**: invented column names (`internet_service` instead of `InternetService`) are mapped to the real ones, and a misplaced `WHERE` is moved before `GROUP BY`
- **Dashboard**: KPI cards, auto-selected charts (bar, donut, trend, grouped bar, heatmap, scatter), plain-English chart explanations, a themed data table and CSV download
- **Verified takeaway**: the LLM writes the summary from the real result rows; if it skips a number or refuses, a deterministic summary is used instead

## How it works

```
CSV upload -> in-memory SQLite -> schema + column profile -> ChromaDB retrieval
          -> LLM writes SQL -> column repair -> execute -> validate result
          -> (retry with feedback, max 3) -> KPIs, charts, explanations, takeaway
```

## Getting started

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.com), and about 6 GB of free RAM for the 7B model (use the 3B model on smaller machines).

```bash
# 1. Pull a model
ollama pull qwen2.5-coder:7b      # or qwen2.5-coder:3b for low-memory machines

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate            # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

To switch models, change the model name in `load_llm()` inside `app.py`.

## Example questions

Try these on a customer churn or Titanic dataset:

- What is the churn rate by contract type?
- What is the churn rate for each combination of contract and internet service?
- What is the average fare of survivors compared with non-survivors?
- Which embarkation port has the highest survival rate?

## Project structure

```
app.py                  Streamlit app (UI, RAG, SQL generation, validation, charts)
main.py                 Minimal command-line version of the pipeline
requirements.txt
.streamlit/config.toml  Dark theme
```

## Limitations

- A small local model can still write wrong SQL for complex questions. The app catches common failure patterns and retries, but it cannot catch every plausible-looking wrong answer, so spot-check important numbers.
- Results depend on question wording; naming the column in the question helps.
- Each retry adds several seconds on CPU-only machines.

## Tech stack

Streamlit, Plotly, Pandas, SQLAlchemy, SQLite, LangChain, ChromaDB, FastEmbed, Ollama
