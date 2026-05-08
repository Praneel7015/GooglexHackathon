"""Tests for the agent orchestrator — sequential, parallel, and error handling."""

import pytest

from agents.base import AgentInput
from agents.orchestrator import Orchestrator
from agents.mock_agents import (
    MockUppercaseAgent,
    MockReverseAgent,
    MockCountAgent,
    MockErrorAgent,
)


@pytest.fixture
def orchestrator() -> Orchestrator:
    return Orchestrator()


@pytest.mark.asyncio
async def test_sequential_pipeline(orchestrator: Orchestrator) -> None:
    """uppercase -> reverse -> count on 'hello world'."""
    agents = [MockUppercaseAgent(), MockReverseAgent(), MockCountAgent()]
    inp = AgentInput(data={"text": "hello world"})

    results = await orchestrator.run_pipeline(agents, inp)

    assert len(results) == 3
    assert all(r.success for r in results)

    # Step 1: uppercase
    assert results[0].data["text"] == "HELLO WORLD"
    # Step 2: reverse
    assert results[1].data["text"] == "DLROW OLLEH"
    # Step 3: count
    assert results[2].data["char_count"] == 11
    assert results[2].data["text"] == "DLROW OLLEH"


@pytest.mark.asyncio
async def test_parallel_execution(orchestrator: Orchestrator) -> None:
    """All three agents run in parallel on the same input."""
    agents = [MockUppercaseAgent(), MockReverseAgent(), MockCountAgent()]
    inp = AgentInput(data={"text": "parallel"})

    results = await orchestrator.run_parallel(agents, inp)

    assert len(results) == 3
    assert all(r.success for r in results)

    names = {r.agent_name for r in results}
    assert names == {"UppercaseAgent", "ReverseAgent", "CountAgent"}


@pytest.mark.asyncio
async def test_pipeline_stops_on_error(orchestrator: Orchestrator) -> None:
    """Pipeline stops when an agent returns an error."""
    agents = [MockUppercaseAgent(), MockErrorAgent(), MockCountAgent()]
    inp = AgentInput(data={"text": "will fail"})

    results = await orchestrator.run_pipeline(agents, inp)

    # Only 2 results — pipeline stopped after ErrorAgent
    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False
    assert results[1].error == "Intentional test failure"


@pytest.mark.asyncio
async def test_latency_logged(orchestrator: Orchestrator) -> None:
    """Every agent output includes latency_ms > 0."""
    agents = [MockUppercaseAgent()]
    inp = AgentInput(data={"text": "timing"})

    results = await orchestrator.run_pipeline(agents, inp)

    assert results[0].latency_ms > 0
