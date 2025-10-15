from __future__ import annotations

from typing import List, Callable
from langchain_core.tools import BaseTool


_strategies: list["ToolStrategyBase"] = []


class ToolStrategyBase:
    """Base class for tool strategies.

    Implement `make_tools()` to return a list of LangChain tools.
    Optionally implement `fallback(question: str)` for error fallback.
    """

    def make_tools(self) -> List[BaseTool]:  # pragma: no cover - abstract
        return []

    async def fallback(self, question: str) -> str:  # pragma: no cover - optional
        return ""

    @staticmethod
    def build_agent_for_tools(tools: List[BaseTool]) -> Callable:
        # Minimal agent builder using LangChain's built-in create_tool_calling_agent pattern
        # Kept generic; users can customize at service level.
        from langchain import hub
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_openai import ChatOpenAI
        import os

        # Use official OpenAI only
        llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        prompt = hub.pull("hwchase17/openai-functions-agent")
        agent = create_tool_calling_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=False)


def register_strategy(strategy: "ToolStrategyBase") -> None:
    _strategies.append(strategy)


def get_strategies() -> list["ToolStrategyBase"]:
    return list(_strategies)
