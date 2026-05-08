"""
Orchestrator for NammaCity agent pipelines.
Supports sequential (chained) and parallel (gather) execution.
"""

import asyncio
import logging

from agents.base import AgentInput, AgentOutput, BaseAgent

logger = logging.getLogger("nammacity.orchestrator")


class Orchestrator:
    """Wire agents together in sequential or parallel pipelines."""

    async def run_pipeline(
        self,
        agents: list[BaseAgent],
        initial_input: AgentInput,
    ) -> list[AgentOutput]:
        """
        Run agents sequentially — each agent's output.data becomes
        the next agent's input.data. Stops on critical error.
        """
        results: list[AgentOutput] = []
        current_input = initial_input

        for agent in agents:
            output = await agent.execute(current_input)
            results.append(output)

            if not output.success:
                logger.error(
                    "Pipeline stopped: %s failed — %s",
                    agent.name,
                    output.error,
                )
                break

            current_input = AgentInput(data=output.data)

        return results

    async def run_parallel(
        self,
        agents: list[BaseAgent],
        agent_input: AgentInput,
    ) -> list[AgentOutput]:
        """
        Run agents in parallel with asyncio.gather.
        All agents receive the same input.
        """
        tasks = [agent.execute(agent_input) for agent in agents]
        results = await asyncio.gather(*tasks)
        return list(results)
