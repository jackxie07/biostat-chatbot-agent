"""
Lightweight ADK wiring scaffold.

This module describes the agent graph and tool registrations and exposes a
client for routing messages through the ADK orchestrator. Replace the
NotImplementedError sections with your actual ADK SDK calls (e.g., session
creation, message streaming) in your environment.
"""

import os
from typing import Any, Dict, List, Optional

import httpx


def agent_graph_definition() -> Dict[str, Any]:
    """
    Declarative graph specification for ADK registration.

    Replace this with the ADK-native graph builder calls if available
    (e.g., adk.Graph(...).node(...).edge(...)).
    """
    return {
        "nodes": [
            {"id": "intent", "type": "llm", "desc": "Intent/analysis classifier"},
            {"id": "schema_loader", "type": "tool", "desc": "Loads analysis schema"},
            {"id": "param_collector", "type": "llm", "desc": "Conversational slot-filler"},
            {"id": "catalog", "type": "tool", "desc": "Dataset catalog options"},
            {"id": "validator", "type": "llm", "desc": "Enforces allowed values"},
            {"id": "confirm", "type": "llm", "desc": "Confirmation/update"},
            {"id": "sas_exec", "type": "tool", "desc": "Runs SAS macro and uploads output"},
            {"id": "audit", "type": "tool", "desc": "Persists history/metrics"},
        ],
        "edges": [
            ("intent", "schema_loader"),
            ("schema_loader", "param_collector"),
            ("param_collector", "catalog"),
            ("param_collector", "validator"),
            ("validator", "param_collector"),  # loop until valid
            ("param_collector", "confirm"),
            ("confirm", "sas_exec"),
            ("sas_exec", "audit"),
        ],
        "entry": "intent",
    }


def tool_registry() -> List[Dict[str, Any]]:
    """
    Tool/action registration list. Wire these into your ADK tool registry.
    """
    return [
        {"name": "load_standard_schema", "impl": "tools.schemas.load_standard_schema"},
        {"name": "load_analysis_schema", "impl": "tools.schemas.load_analysis_schema"},
        {"name": "list_options", "impl": "tools.catalog.list_options"},
        {"name": "validate_param", "impl": "tools.catalog.validate_param"},
        {"name": "run_sas", "impl": "tools.sas.run_sas"},
        {"name": "persist_session", "impl": "tools.audit.persist_session"},
        {"name": "render_markdown", "impl": "tools.render.render_markdown"},
    ]


def register_graph_and_tools(endpoint: str, api_key: str, graph_id: str = "biostat-orchestrator") -> None:
    """
    Convenience helper to register the graph and tools with the ADK runtime.
    Adjust endpoints/payloads to your ADK control-plane API.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    base = endpoint.rstrip("/")

    graph_payload = {"graph_id": graph_id, "definition": agent_graph_definition()}
    tools_payload = {"tools": tool_registry()}

    with httpx.Client(timeout=30.0) as client:
        graph_resp = client.post(f"{base}/graphs", headers=headers, json=graph_payload)
        graph_resp.raise_for_status()

        tools_resp = client.post(f"{base}/tools/register", headers=headers, json=tools_payload)
        tools_resp.raise_for_status()

class ADKOrchestratorClient:
    """
    Adapter to talk to the ADK orchestrator. Implement the private methods
    with your ADK SDK or HTTP calls.
    """

    def __init__(self) -> None:
        self.endpoint = os.getenv("ADK_ENDPOINT")
        self.api_key = os.getenv("ADK_API_KEY")
        self.graph_id = os.getenv("ADK_GRAPH_ID", "biostat-orchestrator")
        self._session_id: Optional[str] = None

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def ensure_session(self) -> str:
        if self._session_id is None:
            self._session_id = self._create_session()
        return self._session_id

    def send_message(self, user_input: str) -> str:
        """
        Route a message through the ADK graph and return the assistant response.
        Replace the NotImplementedError with your actual call.
        """
        session_id = self.ensure_session()
        return self._send_to_graph(session_id, user_input)

    def _create_session(self) -> str:
        """
        Create an ADK session for the configured graph.

        Expected REST shape (adjust to your ADK runtime):
            POST {ADK_ENDPOINT}/sessions
            headers: Authorization: Bearer {ADK_API_KEY}
            json: { "graph_id": self.graph_id }

        Response: { "session_id": "<id>" }
        """
        if not self.configured:
            raise RuntimeError("ADK endpoint/API key not configured")

        url = f"{self.endpoint.rstrip('/')}/sessions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"graph_id": self.graph_id}

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        session_id = data.get("session_id") or data.get("id")
        if not session_id:
            raise RuntimeError("ADK session creation failed: no session_id returned")
        return session_id

    def _send_to_graph(self, session_id: str, user_input: str) -> str:
        """
        Invoke the ADK graph with user input.

        Expected REST shape (adjust to your ADK runtime):
            POST {ADK_ENDPOINT}/graphs/{graph_id}/invoke
            headers: Authorization: Bearer {ADK_API_KEY}
            json: { "session_id": session_id, "input": user_input }

        Response: { "output": "<assistant text>" }
        """
        if not self.configured:
            raise RuntimeError("ADK endpoint/API key not configured")

        url = f"{self.endpoint.rstrip('/')}/graphs/{self.graph_id}/invoke"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"session_id": session_id, "input": user_input}

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        output = data.get("output") or data.get("message") or data.get("result")
        if output is None:
            raise RuntimeError("ADK graph invoke failed: no output returned")
        return output
