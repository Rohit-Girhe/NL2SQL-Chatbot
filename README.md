# 🏥 Clinic NL2SQL API
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00a393.svg)](https://fastapi.tiangolo.com)
[![Vanna](https://img.shields.io/badge/Vanna-2.0.x-orange.svg)](https://vanna.ai/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4.svg)](https://deepmind.google/technologies/gemini/)

A production-grade Natural Language to SQL (NL2SQL) backend built for a simulated Clinic Management System. This API allows users to query complex relational data using plain English, automatically translating intent into secure, executable SQLite queries.

This project strictly implements the **Vanna 2.0 Autonomous Agent Architecture** combined with a highly optimized FastAPI endpoint layer for seamless front-end integration.

---

## ✨ Key Technical Features

* **Advanced Component Parsing:** Implements an asynchronous FastAPI stream parser that hunts for and extracts raw SQL markdown and DataFrame objects natively from Vanna's `UiComponent` wrapper, scrubbing out LLM system noise for pristine JSON payloads.
* **Hardened Security Middleware:** Features a custom `SecureSqliteRunner` transparent proxy. This intercepts internal tool calls to validate that generated SQL is strictly `SELECT`-based and contains no destructive (`DROP`, `DELETE`) or system-level (`sqlite_master`) keywords before execution.
* **Few-Shot Memory Seeding:** Utilizes Vanna's local `DemoAgentMemory` system, pre-seeded with 15 highly complex Q&A pairs (handling multi-table JOINs, temporal grouping, and mathematical aggregations) to ensure high-accuracy zero-shot inference.
* **Legacy-Compatible Payloads:** Dynamically structures the Pandas DataFrame output into clean `columns`, `rows`, and `row_count` arrays to support standard enterprise charting libraries.

---

## 🏗️ Architecture Flow

```text
User Request (Plain English)
 └──> POST /chat (FastAPI)
       └──> Vanna 2.0 Agent (GeminiLlmService)
             ├──> Schema Context & DemoAgentMemory Retrieval
             ├──> SQL Generation (gemini-2.5-flash)
             └──> Tool Call: SecureSqliteRunner (Proxy Intercept)
                   ├──> Validation: Reject non-SELECT / malicious queries
                   └──> Execution: clinic.db (SQLite)
                         └──> Result DataFrame & Narrative Summary
                               └──> FastAPI Stream Parser (Regex Scrubbing)
                                     └──> Client (Pristine JSON Response)

🚀 Setup & Installation

1. Clone the Repository
git clone <your-repo-link>
cd NL2SQL-CHATBOT

2. Configure the Virtual Environment
It is highly recommended to isolate the project dependencies.

python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

3. Environment Configuration
Create a .env file in the root directory and add your Google AI Studio API key. The system uses gemini-2.5-flash via the free tier.

Code snippet
GOOGLE_API_KEY=your_google_api_key_here

4. Initialize the Database
Run the setup script to generate clinic.db. This will automatically seed the database with simulated transactional data (15 doctors, 200 patients, 500 appointments, treatments, and invoices).

python setup_database.py

5. Seed the Agent Memory
Populate the Vanna local vector store with baseline Q&A pairs to establish the LLM's behavioral boundaries and schema context. (Note: This creates a local hashed directory).

python seed_memory.py

6. Start the API Server
Launch the FastAPI application using Uvicorn.

uvicorn main:app --port 8000 --reload
The interactive Swagger UI will be available at: http://127.0.0.1:8000/docs

📖 API Documentation
POST /chat
Transforms a natural language string into a secure SQL query, executes it against the local database, and returns the structural results.

Request Payload:

JSON
{
  "question": "How many patients do we have?"
}
Success Response (200 OK):

JSON
{
  "message": "Result: 200",
  "sql_query": "SELECT COUNT(*) FROM patients",
  "columns": [
    "COUNT(*)"
  ],
  "rows": [
    [
      200
    ]
  ],
  "row_count": 1,
  "chart": null,
  "chart_type": null,
  "error": null
}
📂 Project Structure
Plaintext
NL2SQL-CHATBOT/
├── main.py                # FastAPI server, request models, and stream parser
├── vanna_setup.py         # Vanna 2.0 Agent config, Security Proxy, and Gemini setup
├── setup_database.py      # SQLite schema creation and dummy data population
├── seed_memory.py         # DemoAgentMemory initialization and training
├── clinic.db              # Generated SQLite database (created via setup script)
├── requirements.txt       # Core project dependencies
├── README.md              # Project documentation
└── RESULTS.md             # Test validation log for 20 benchmark queries