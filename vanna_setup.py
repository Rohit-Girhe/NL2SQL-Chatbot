import os
import re
from dotenv import load_dotenv

from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

from vanna.tools import RunSqlTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()

# --- Identifies the user making requests ---
class DefaultUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="default_system_user")

# --- Adds a security layer before executing any SQL query ---
class SecureSqliteRunner(SqliteRunner):
    """
    A transparent security wrapper. It peeks at the arguments to validate the SQL,
    then passes all arguments exactly as they were received to the parent class.
    """
    def run_sql(self, *args, **kwargs):
        # 1. Peek at the SQL string (whether it is positional or a keyword)
        sql_query = None
        if args and isinstance(args[0], str):
            sql_query = args[0]
        elif kwargs.get("sql") and isinstance(kwargs.get("sql"), str):
            sql_query = kwargs.get("sql")
        elif kwargs.get("sql_query") and isinstance(kwargs.get("sql_query"), str):
            sql_query = kwargs.get("sql_query")

        # 2. Validate the SQL if we found it
        if sql_query:
            sql_upper = sql_query.upper().strip()
            
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

        # 3. Transparent Pass-Through!
        # We pass *args and **kwargs exactly as we received them,
        # ensuring Vanna's SqliteRunner gets its required 'context' argument.
        print(f"\n--- EXECUTING SQL ---\n{sql_query}\n---------------------\n")
        try:
            return super().run_sql(*args, **kwargs)
        except Exception as db_err:
            print(f"\n--- DATABASE ERROR ---\n{str(db_err)}\n----------------------\n")
            raise db_err


def get_agent() -> Agent:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Environment variable GOOGLE_API_KEY is not set.")
    
    llm_service = GeminiLlmService(api_key=api_key, model="gemini-2.5-flash")
    db_runner = SecureSqliteRunner(database_path="clinic.db")
    memory = DemoAgentMemory()
    registry = ToolRegistry()
    
    registry.register_local_tool(RunSqlTool(sql_runner=db_runner), access_groups=[])
    
    agent = Agent(
        config=AgentConfig(),
        llm_service=llm_service,
        tool_registry=registry,
        agent_memory=memory,
        user_resolver=DefaultUserResolver()
    )
    
    return agent