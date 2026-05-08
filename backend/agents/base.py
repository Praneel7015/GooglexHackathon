"""
Base agent class for NammaCity.
Follows Google ADK conventions — agents have a name, description,
and async run method with structured input/output.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("nammacity.agents")


class AgentInput(BaseModel):
    """Standard input passed between agents in a pipeline."""
    data: dict[str, Any] = {}


class AgentOutput(BaseModel):
    """Standard output from every agent."""
    agent_name: str
    success: bool = True
    data: dict[str, Any] = {}
    error: str | None = None
    latency_ms: float = 0.0


class BaseAgent(ABC):
    """
    Abstract base for all NammaCity agents.
    Wraps run logic with logging, timing, and error handling.
    Agents never raise — they return structured errors in AgentOutput.
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Run the agent with logging and error handling.
        Subclasses implement `run` — this wrapper handles the rest.
        """
        start = time.perf_counter()
        logger.info(json.dumps({
            "event": "agent_start",
            "agent": self.name,
            "input": agent_input.data,
        }))

        try:
            output = await self.run(agent_input)
            output.latency_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            output = AgentOutput(
                agent_name=self.name,
                success=False,
                error=str(e),
                latency_ms=(time.perf_counter() - start) * 1000,
            )

        logger.info(json.dumps({
            "event": "agent_done",
            "agent": self.name,
            "success": output.success,
            "latency_ms": round(output.latency_ms, 2),
            "output": output.data if output.success else {"error": output.error},
        }))

        return output

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Implement agent logic here. Return AgentOutput, never raise."""
        ...
