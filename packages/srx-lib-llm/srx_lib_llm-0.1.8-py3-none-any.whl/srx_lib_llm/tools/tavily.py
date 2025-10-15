import os
from typing import List
from tavily import TavilyClient
from langchain_core.tools import Tool

from .base import ToolStrategyBase


class TavilyToolStrategy(ToolStrategyBase):
    def make_tools(self) -> List[Tool]:
        api_key = os.getenv("TAVILY_API_KEY")
        client = TavilyClient(api_key=api_key) if api_key else TavilyClient()

        def search_tool(query: str) -> str:
            res = client.search(query, max_results=4)
            return "\n".join([item.get("url", "") for item in res.get("results", [])])

        return [
            Tool(
                name="tavily_search",
                description="Search the web using Tavily (returns URLs).",
                func=search_tool,
            )
        ]

