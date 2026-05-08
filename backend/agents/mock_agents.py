"""
Mock agents for testing the orchestrator pipeline.
"""

from agents.base import AgentInput, AgentOutput, BaseAgent


class MockUppercaseAgent(BaseAgent):
    """Uppercases the 'text' field in input data."""

    def __init__(self) -> None:
        super().__init__(name="UppercaseAgent", description="Uppercases text")

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        text = agent_input.data.get("text", "")
        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={"text": text.upper()},
        )


class MockReverseAgent(BaseAgent):
    """Reverses the 'text' field in input data."""

    def __init__(self) -> None:
        super().__init__(name="ReverseAgent", description="Reverses text")

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        text = agent_input.data.get("text", "")
        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={"text": text[::-1]},
        )


class MockCountAgent(BaseAgent):
    """Counts characters in the 'text' field."""

    def __init__(self) -> None:
        super().__init__(name="CountAgent", description="Counts characters")

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        text = agent_input.data.get("text", "")
        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={"text": text, "char_count": len(text)},
        )


class MockErrorAgent(BaseAgent):
    """Always returns an error — for testing pipeline error handling."""

    def __init__(self) -> None:
        super().__init__(name="ErrorAgent", description="Always fails")

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            success=False,
            error="Intentional test failure",
        )
