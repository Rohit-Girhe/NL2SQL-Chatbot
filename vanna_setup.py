import os
from dotenv import load_dotenv

# Core Vanna imports
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

# Vanna Integrations & Tools
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

load_dotenv()

class DefaultUserResolver(UserResolver):
    """
    Resolves the user context for the Vanna Agent.
    Currently defaults to a single-tenant configuration.
    """
    def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="default_system_user")

def get_agent() -> Agent:
    """
    Configures and initializes the Vanna NL2SQL Agent.
    
    Returns:
        Agent: A fully configured Vanna Agent instance with the LLM provider, 
               SQLite execution engine, and local memory tools registered.
    """
    
    # 1. Configure LLM Provider
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Environment variable GOOGLE_API_KEY is not set.")
    
    # Instantiate Gemini service (Optimized for fast reasoning and context windows)
    llm_service = GeminiLlmService(api_key=api_key, model="gemini-2.5-flash")
    
    # 2. Configure Database Execution Engine
    db_runner = SqliteRunner(database_path="clinic.db")
    
    # 3. Initialize Agent Memory Engine
    memory = DemoAgentMemory()
    
    # 4. Register core execution and memory retrieval tools
    # Vanna 2.0 uses Contextual Dependency Injection. Tools are initialized empty 
    # and inherit the memory/db context from the Agent at runtime.
    registry = ToolRegistry()
    registry.register_local_tool(RunSqlTool(sql_runner=db_runner), access_groups=[])
    registry.register_local_tool(VisualizeDataTool(), access_groups=[])
    
    # Remove the constructor arguments here:
    registry.register_local_tool(SaveQuestionToolArgsTool(), access_groups=[])
    registry.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=[])
    
    # 5. Assemble and return the Agent
    agent = Agent(
        config=AgentConfig(),
        llm_service=llm_service,
        tool_registry=registry,
        agent_memory=memory,
        user_resolver=DefaultUserResolver()
    )
    
    return agent