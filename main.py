import re
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from vanna_setup import get_agent
from fastapi.responses import RedirectResponse

# Initialize the Vanna Agent (which connects to SQLite and Gemini)
agent = get_agent()

# Initialize FastAPI App
app = FastAPI(
    title="Clinic NL2SQL API",
    description="An AI-powered Natural Language to SQL API built with Vanna 2.0",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
async def root():
    """Redirects users to the API documentation."""
    return RedirectResponse(url="/docs")

# --- API DATA MODELS ---
class ChatRequest(BaseModel):
    """The expected JSON payload from the client."""
    question: str

class ChatResponse(BaseModel):
    """The structured JSON response sent back to the client."""
    question: str
    generated_sql: str
    status: str
    results: list[dict] | None = None
    error: str | None = None


# --- SECURITY VALIDATION ---
def validate_sql(sql: str) -> str | None:
    """
    Validates SQL to ensure it is read-only and safe.
    Returns an error message string if invalid, or None if valid.
    """
    if not sql:
        return "Generated SQL is empty."
        
    sql_upper = sql.upper().strip()
    
    # 1. Must be a SELECT query (or a WITH clause preceding a SELECT)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        return "Security Violation: Only SELECT queries are allowed."
        
    # 2. Block dangerous keywords (Using regex to match whole words only)
    dangerous_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
        "EXEC", "XP_", "SP_", "GRANT", "REVOKE", "SHUTDOWN"
    ]
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', sql_upper):
            return f"Security Violation: Dangerous keyword '{keyword}' detected."
            
    # 3. Block system table access
    if "SQLITE_MASTER" in sql_upper:
        return "Security Violation: Queries to system tables are strictly prohibited."
        
    return None


# --- ENDPOINTS ---
@app.get("/health")
async def health_check():
    """
    Health check endpoint required by the technical assignment.
    Verifies API status and agent memory counts.
    """
    try:
        memory_items = agent.agent_memory.get_training_data()
        item_count = len(memory_items) if memory_items else 0
    except Exception:
        item_count = 0

    return {
        "status": "ok",
        "database": "connected",
        "agent_memory_items": item_count
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Main NL2SQL endpoint. Takes a natural language question, generates SQL,
    validates it for security, executes it, and returns the results.
    """
    try:
        # 1. Ask the AI to generate the SQL (but NOT execute it yet)
        generated_sql = agent.generate_sql(question=request.question)
        
        # 2. Intercept and Validate (The Security Gate)
        validation_error = validate_sql(generated_sql)
        if validation_error:
            # We return an HTTP 403 Forbidden if it violates our read-only policy
            raise HTTPException(status_code=403, detail=validation_error)
            
        # 3. Execute the validated SQL against the SQLite database
        df = agent.run_sql(generated_sql)
        
        # 4. Convert the Pandas DataFrame to a JSON-serializable dictionary
        results_json = df.to_dict(orient="records") if isinstance(df, pd.DataFrame) else []

        return ChatResponse(
            question=request.question,
            generated_sql=generated_sql,
            status="success",
            results=results_json
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")