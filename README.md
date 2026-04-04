# Clinic NL2SQL API (Vanna 2.0 + FastAPI)

This project is an AI-powered Natural Language to SQL (NL2SQL) backend built for a simulated clinic management system. It allows users to ask questions in plain English and returns executed database results alongside the generated SQL.

This project strictly implements the **Vanna 2.0 Agent architecture** using `FastAPI` and a local `SQLite` database.

## 🧠 LLM Choice
This project uses **Google Gemini (`gemini-2.5-flash`)** via the Google AI Studio free tier. It is integrated using the official `vanna[gemini]` module.

## 🏗️ Architecture Overview
1. **User Request:** A natural language string is sent via `POST /chat`.
2. **Vanna 2.0 Agent:** The `GeminiLlmService` interprets the schema and generates the SQL.
3. **Security Middleware:** A custom `SecureSqliteRunner` (transparent proxy) intercepts the tool call to validate that the SQL is `SELECT` only and contains no dangerous keywords before execution.
4. **Data Extraction:** An asynchronous FastAPI endpoint parses Vanna's `Component` stream, aggressively scrubbing system noise to return a clean JSON payload formatted for standard charting (columns and rows).
5. **Memory:** The `DemoAgentMemory` system is pre-seeded with high-quality Q&A pairs for few-shot learning accuracy.

## 🚀 Setup Instructions

**1. Clone the repository and navigate to the directory:**
```bash
git clone <your-repo-link>
cd NL2SQL-CHATBOT
2. Create a virtual environment and install dependencies:

Bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
3. Configure Environment Variables:
Create a .env file in the root directory and add your Gemini API key:

Code snippet
GOOGLE_API_KEY=your_google_api_key_here
4. Generate the Database:
Run the setup script to create clinic.db and insert dummy data (15 doctors, 200 patients, 500 appointments, etc.):

Bash
python setup_database.py
5. Seed the Vanna Agent Memory:
Note: Due to Vanna 2.0's architecture, memory is seeded locally in a generated folder.

Bash
python seed_memory.py
6. Start the API Server:

Bash
uvicorn main:app --port 8000 --reload