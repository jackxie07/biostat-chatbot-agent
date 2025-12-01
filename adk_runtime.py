"""
ADK agent wiring using Sequential and Loop agents patterned on the ADK samples.

The root workflow: Intent → Schema Loader → (loop) Parameter Collector + Validation →
Confirmation → SAS Execution → Audit. The loop runs until required slots are filled.
"""

from typing import Optional

from google.adk.agents import Agent, LoopAgent, SequentialAgent
from google.adk.runners import InMemoryRunner

import agents


def create_parameter_loop(max_iterations: int = 4) -> LoopAgent:
    """
    Loop over parameter collection and validation until slots are complete.
    """
    return LoopAgent(
        name="parameter_loop",
        sub_agents=[
            agents.parameter_collector_agent(),
            agents.validation_agent(),
        ],
        max_iterations=max_iterations,
    )


def create_root_agent() -> Agent:
    """
    Root workflow agent assembled as a SequentialAgent:
    Intent → Schema → Parameter Loop → Confirmation → SAS Execution → Audit.
    """
    return SequentialAgent(
        name="biostat_workflow",
        sub_agents=[
            agents.intent_agent(),
            agents.schema_loader_agent(),
            create_parameter_loop(),
            agents.confirmation_agent(),
            agents.sas_execution_agent(),
            agents.audit_agent(),
        ],
    )


def create_inmemory_runner(agent: Optional[Agent] = None) -> InMemoryRunner:
    """
    Local runner for development and debugging.
    """
    agent = agent or create_root_agent()
    return InMemoryRunner(agent=agent)


class ADKOrchestratorClient:
    """
    Adapter to execute the ADK agent locally via InMemoryRunner.
    Replace with remote graph execution when available.
    """

    def __init__(self) -> None:
        self._runner: Optional[InMemoryRunner] = None

    @property
    def configured(self) -> bool:
        # Local runner does not require remote endpoint
        return True

    def ensure_runner(self) -> InMemoryRunner:
        if self._runner is None:
            self._runner = create_inmemory_runner()
        return self._runner

    async def send_message(self, user_input: str) -> str:
        """
        Run the root agent against user input using run_debug for traceability.
        """
        runner = self.ensure_runner()
        result = await runner.run_debug(user_input)
        return result.text if hasattr(result, "text") else str(result)
