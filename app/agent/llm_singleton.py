import os
from agno.agent import Agent
from agno.models.openrouter import OpenRouter

_llm_agent = None

def get_llm_agent():
    global _llm_agent
    if _llm_agent is None:
        _llm_agent = Agent(
            model=OpenRouter(
                id="qwen/qwen2.5-vl-32b-instruct:free",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        )
    return _llm_agent
