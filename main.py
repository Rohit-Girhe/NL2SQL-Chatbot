import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from vanna.core.user import RequestContext, User
from vanna_setup import get_agent
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize the Vanna Agent
agent = get_agent()

app = FastAPI(
    title="Clinic NL2SQL API",
    description="An AI-powered Natural Language to SQL API built with Vanna 2.0",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    question: str
    status: str
    message: str | None = None
    sql_query: str | None = None
    results: list[dict] | None = None
    error: str | None = None

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    try:
        memory_items = agent.agent_memory.get_training_data()
        item_count = len(memory_items) if memory_items else 0
    except Exception:
        item_count = 0

    return {"status": "ok", "database": "connected", "agent_memory_items": item_count}


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Wraps the Vanna 2.0 send_message autonomous loop.
    Dynamically extracts SQL, narrative text, and Pandas dataframes from the component stream.
    """
    request_context = RequestContext(user=User(id="default_system_user"))
    
    response_data = {
        "question": request.question,
        "status": "success",
        "message": "",
        "sql_query": None,
        "results": []
    }
    
    try:
        # Listen to the Agent's autonomous thought process
        async for component in agent.send_message(request_context=request_context, message=request.question):
            
            # --- OUR DEBUG HOOK ---
            print(f"\n--- COMPONENT DEBUG ---")
            print(component)
            # ----------------------

            # Safely parse the complex Vanna 2.0 UiComponent objects
            comp_dict = component.__dict__ if hasattr(component, "__dict__") else {}
            
            # Extract the AI's natural language response and the raw SQL
            if "simple_component" in comp_dict and comp_dict["simple_component"]:
                sc = comp_dict["simple_component"]
                if hasattr(sc, "text") and sc.text:
                    response_data["message"] += sc.text + "\n"
                    # Capture the SQL string from the markdown block
                    if "```sql" in sc.text:
                        try:
                            response_data["sql_query"] = sc.text.split("```sql")[1].split("```")[0].strip()
                        except IndexError:
                            pass
                            
            # Extract the Database rows (DataFrame)
            if "rich_component" in comp_dict and comp_dict["rich_component"]:
                rc = comp_dict["rich_component"]
                if hasattr(rc, "dataframe") and rc.dataframe is not None:
                    response_data["results"] = rc.dataframe.to_dict(orient="records")

        return response_data

    except Exception as e:
        # If our SecureSqliteRunner blocked a DROP table command, it throws an error here!
        raise HTTPException(status_code=500, detail=f"Agent Execution Error: {str(e)}")