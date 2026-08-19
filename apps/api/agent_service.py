"""FastPath agent orchestration for the KappaLake data copilot."""
from fastpath.agent import Agent
from fastpath.memory import InMemoryMemory
from fastpath.orchestrator import Orchestrator

from agent_llm import OpenAICompatibleProvider
from agent_tools import (
    CreateGoldTableTool,
    DescribeTableTool,
    ExecuteQueryTool,
    ListTablesTool,
)


def build_orchestrator() -> Orchestrator:
    llm = OpenAICompatibleProvider()
    memory = InMemoryMemory(config={})
    tools = [
        ListTablesTool(),
        DescribeTableTool(),
        ExecuteQueryTool(),
        CreateGoldTableTool(),
    ]
    agent = Agent(
        name="DataEngineer",
        role=(
            "You are a KappaLake data engineer. You explore the lakehouse schema with tools "
            "(list_tables, describe_table, execute_query) and answer questions with real data, "
            "or create curated gold tables with create_gold_table."
        ),
        tools=tools,
        memory=memory,
        llm_provider=llm,
    )
    return Orchestrator(
        agents=[agent],
        mode="hierarchical",
        llm_provider=llm,
        enable_memory_reflection=False,
    )


async def run_agent_task(task: str) -> dict:
    """Run a task through the FastPath orchestrator and return a serializable result."""
    orchestrator = build_orchestrator()
    result = await orchestrator.run(task)
    return {
        "success": result.success,
        "output": result.output,
        "details": result.details,
        "reflection_rounds": result.reflection_rounds,
        "attempts": result.attempts,
    }
