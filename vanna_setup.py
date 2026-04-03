import os
import re
from dotenv import load_dotenv

from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()

class DefaultUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="default_system_user")

# --- OUR BULLETPROOF SECURITY MIDDLEWARE ---
class SecureSqliteRunner(SqliteRunner):
    """
    Intercepts SQL, dynamically extracts it regardless of how Vanna's Tool Engine
    injects telemetry, validates it, and cleanly passes it to SQLite.
    """
    def run_sql(self, *args, **kwargs):
        sql_query = None
        
        # 1. Look for an explicit keyword argument
        sql_query = kwargs.get("sql")
        
        # 2. Look inside positional arguments to find the string
        if not sql_query:
            for arg in args:
                # Is it a raw string?
                if isinstance(arg, str):
                    sql_query = arg
                    break
                # Is it a Pydantic model with a .sql attribute?
                elif hasattr(arg, 'sql') and isinstance(arg.sql, str):
                    sql_query = arg.sql
                    break
                # Is it a dictionary?
                elif isinstance(arg, dict) and "sql" in arg:
                    sql_query = arg["sql"]
                    break
        
        if not sql_query or not isinstance(sql_query, str):
            # If extraction fails, we print to terminal to see exactly what Vanna sent
            print(f"\n--- FATAL EXTRACTION ERROR ---\nARGS: {args}\nKWARGS: {kwargs}\n")
            raise ValueError("Security Violation: Generated SQL is empty or could not be extracted.")
            
        sql_upper = sql_query.upper().strip()
        
        # --- Validation Rules ---
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            raise ValueError("Security Violation: Only SELECT queries are allowed.")
            
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
            "EXEC", "XP_", "SP_", "GRANT", "REVOKE", "SHUTDOWN"
        ]
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                raise ValueError(f"Security Violation: Dangerous keyword '{keyword}' detected.")
                
        if "SQLITE_MASTER" in sql_upper:
            raise ValueError("Security Violation: Queries to system tables are strictly prohibited.")
            
        # --- THE FIX: STRIP TELEMETRY ---
        # The parent SQLite connection ONLY wants the raw SQL string.
        # We drop *args and **kwargs and pass the exact string explicitly.
        return super().run_sql(sql=sql_query)


def get_agent() -> Agent:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Environment variable GOOGLE_API_KEY is not set.")
    
    llm_service = GeminiLlmService(api_key=api_key, model="gemini-2.5-flash")
    
    db_runner = SecureSqliteRunner(database_path="clinic.db")
    memory = DemoAgentMemory()
    registry = ToolRegistry()
    
    registry.register_local_tool(RunSqlTool(sql_runner=db_runner), access_groups=[])
    registry.register_local_tool(VisualizeDataTool(), access_groups=[])
    registry.register_local_tool(SaveQuestionToolArgsTool(), access_groups=[])
    registry.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=[])
    
    agent = Agent(
        config=AgentConfig(),
        llm_service=llm_service,
        tool_registry=registry,
        agent_memory=memory,
        user_resolver=DefaultUserResolver()
    )
    
    return agent