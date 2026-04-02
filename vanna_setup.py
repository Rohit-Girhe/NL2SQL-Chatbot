import os
from dotenv import load_dotenv

# Vanna 2.0 Core Imports
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

# Vanna 2.0 Tools & Integrations
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService

# Load environment variables from .env
load_dotenv()

class DefaultUserResolver(UserResolver):
    """A simple resolver that assigns all requests to a default user."""
    def resolve_user(self, request_context: RequestContext) -> User:
        return User(user_id="default_user")

def get_agent() -> Agent:
    """Initializes and returns the fully configured Vanna 2.0 Agent."""
    
    # 1. Initialize the LLM Service (The Brain)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing from the .env file.")
    
    # We use gemini-2.5-flash as specified in the assignment guidebook
    llm = GeminiLlmService(api_key=api_key, model="gemini-2.5-flash")
    
    # 2. Initialize the Database Runner
    # This automatically connects to the clinic.db you generated in Step 1
    db_runner = SqliteRunner(db_file="clinic.db")
    
    # 3. Initialize Agent Memory (Replaces ChromaDB)
    memory = DemoAgentMemory()
    
    # 4. Register Tools (The Hands)
    registry = ToolRegistry()
    registry.register_tool(RunSqlTool(db_runner=db_runner))
    registry.register_tool(VisualizeDataTool())
    
    # These tools allow the agent to read and write to its memory
    registry.register_tool(SaveQuestionToolArgsTool(agent_memory=memory))
    registry.register_tool(SearchSavedCorrectToolUsesTool(agent_memory=memory))
    
    # 5. Assemble the Agent
    agent = Agent(
        config=AgentConfig(),
        llm_service=llm,
        tool_registry=registry,
        agent_memory=memory,
        user_resolver=DefaultUserResolver()
    )
    
    return agent