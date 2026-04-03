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

# --- OUR SECURITY MIDDLEWARE ---
class SecureSqliteRunner(SqliteRunner):
    def run_sql(self, sql: str, **kwargs):
        if not sql:
            raise ValueError("Security Violation: Generated SQL is empty.")
            
        sql_upper = sql.upper().strip()
        
        # 1. Must be a SELECT query
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            raise ValueError("Security Violation: Only SELECT queries are allowed.")
            
        # 2. Block dangerous keywords
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
            "EXEC", "XP_", "SP_", "GRANT", "REVOKE", "SHUTDOWN"
        ]
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                raise ValueError(f"Security Violation: Dangerous keyword '{keyword}' detected.")
                
        # 3. Block system table access
        if "SQLITE_MASTER" in sql_upper:
            raise ValueError("Security Violation: Queries to system tables are strictly prohibited.")
            
        # If validation passes, execute using the parent class, passing along the hidden args
        return super().run_sql(sql=sql, **kwargs)


def get_agent() -> Agent:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Environment variable GOOGLE_API_KEY is not set.")
    
    llm_service = GeminiLlmService(api_key=api_key, model="gemini-2.5-flash")
    
    # Inject our Secure Runner instead of the default one!
    db_runner = SecureSqliteRunner(database_path="clinic.db")
    
    memory = DemoAgentMemory()
    registry = ToolRegistry()
    
    # The agent will now use our secure database connection
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