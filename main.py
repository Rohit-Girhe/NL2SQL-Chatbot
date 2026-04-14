import re
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from vanna.core.user import RequestContext, User
from vanna_setup import get_agent
import logging

logging.basicConfig(level=logging.DEBUG)

agent = get_agent()

app = FastAPI(
    title="Clinic NL2SQL API",
    description="An AI-powered Natural Language to SQL API",
    version="1.0.0"
)

# --- Ensure the reuqest body contains a question filed (string) ---
class ChatRequest(BaseModel):
    question: str

# --- Defines the response structure returned to clients ---
class ChatResponse(BaseModel):
    message: str | None = None
    sql_query: str | None = None
    columns: list[str] | None = None
    rows: list[list] | None = None
    row_count: int | None = 0
    chart: str | None = None
    chart_type: str | None = None
    error: str | None = None

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# --- Creates a Vanna context for user identification ---
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    request_context = RequestContext(user=User(id="default_system_user"))
    
    final_text = ""
    generated_sql = None
    df_results = None
    
# --- Iterates through streaming responses from the Vanna agent ---
    try:
        async for component_wrapper in agent.send_message(request_context=request_context, message=request.question):
            
            # 1. Simple Component Extraction
            sc = getattr(component_wrapper, "simple_component", None)
            if sc and hasattr(sc, "text") and sc.text:
                if "```sql" in sc.text:
                    try:
                        generated_sql = sc.text.split("```sql")[1].split("```")[0].strip()
                    except IndexError:
                        pass
                final_text = sc.text
                
            # 2. Rich Component Extraction (Catching DataFrames)
            rc = getattr(component_wrapper, "rich_component", None)
            if rc:
                comp_type = getattr(rc, "type", None)
                type_value = comp_type.value if comp_type else ""

                if type_value == "sql":
                    generated_sql = getattr(rc, "content", getattr(rc, "sql", generated_sql))
                elif type_value == "code" and getattr(rc, "language", "") == "sql":
                    generated_sql = getattr(rc, "content", generated_sql)
                elif type_value == "dataframe":
                    if hasattr(rc, "dataframe") and rc.dataframe is not None:
                        df_results = rc.dataframe
                    elif hasattr(rc, "rows") and rc.rows:
                        df_results = pd.DataFrame(rc.rows)

        # --- SCRUB SYSTEM NOISE ---
        if final_text:
            final_text = re.sub(r"Query executed successfully.*?affected\.", "", final_text, flags=re.IGNORECASE)
            final_text = re.sub(r"Results saved to file:.*?\.csv", "", final_text, flags=re.IGNORECASE)
            final_text = re.sub(r"\*?\*?\s*IMPORTANT: FOR VISUALIZE_DATA.*?\*?\*?", "", final_text, flags=re.IGNORECASE)
            if generated_sql and f"```sql" in final_text:
                final_text = re.sub(r"```sql.*?```", "", final_text, flags=re.IGNORECASE|re.DOTALL)
            final_text = final_text.strip()
            
        # --- FORMAT THE RESULT ---
        columns = []
        rows = []
        row_count = 0
        
        # Convert the DataFrame into isolated lists
        if df_results is not None and not df_results.empty:
            columns = df_results.columns.tolist()
            rows = df_results.values.tolist()
            row_count = len(rows)
            
        # Match the "Result: 200" message 
        if not final_text and row_count > 0:
            final_text = f"Result: {rows[0][0]}"

        return ChatResponse(
            message=final_text,
            sql_query=generated_sql,
            columns=columns,
            rows=rows,
            row_count=row_count,
            chart=None,
            chart_type=None,
            error=None
        )

    except Exception as e:
        return ChatResponse(
            message="An error occurred while processing the request.",
            sql_query=None,
            columns=None,
            rows=None,
            row_count=0,
            chart=None,
            chart_type=None,
            error=str(e)
        )