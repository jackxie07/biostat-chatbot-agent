"""
ADK agent definitions for the biostat chatbot, aligned with the agentic
architecture plan. Each agent is configured with a retry-enabled Gemini model
and an instruction tailored to its role. Tools are currently mapped to local
stubs under `tools/` and should be replaced or extended as richer tooling is
implemented.
"""

import os
from typing import Dict, List

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import FunctionTool
from google.genai import types as genai_types

import tools.audit
import tools.catalog
import tools.render
import tools.sas
import tools.schemas
import tools.state


def _retry_options() -> genai_types.HttpRetryOptions:
    return genai_types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )


def _model() -> Gemini:
    model_name = os.getenv("ADK_MODEL_NAME", "gemini-2.5-flash-lite")
    return Gemini(model=model_name, retry_options=_retry_options())


def orchestrator_agent() -> Agent:
    return Agent(
        name="orchestrator",
        model=_model(),
        description="Entry point; routes between agents and aggregates outputs.",
        instruction=(
            "You orchestrate the analysis workflow. Maintain session state "
            "(analysis_detail, ask_for, confirm_proceed, chat history). "
            "Delegate to intent classification, schema loading, slot filling, "
            "validation, confirmation, and SAS execution. Return concise, user-ready responses."
        ),
        tools=[
            FunctionTool(tools.schemas.load_standard_schema, name="load_standard_schema"),
            FunctionTool(tools.schemas.load_analysis_schema, name="load_analysis_schema"),
            FunctionTool(tools.catalog.list_options, name="list_options"),
            FunctionTool(tools.catalog.validate_param, name="validate_param"),
            FunctionTool(tools.sas.run_sas, name="run_sas"),
            FunctionTool(tools.audit.persist_session, name="persist_session"),
            FunctionTool(tools.render.render_markdown, name="render_markdown"),
        ],
    )


def intent_agent() -> Agent:
    return Agent(
        name="intent_classifier",
        model=_model(),
        description="Maps user asks to AnalysisMethod.",
        instruction=(
            "Classify the requested analysis using standard_analysis_schema.json. "
            "Return JSON with keys analysis_method and confidence. If unknown, set analysis_method to 0."
        ),
        tools=[FunctionTool(tools.schemas.load_standard_schema, name="load_standard_schema")],
        output_key="analysis_method",
    )


def schema_loader_agent() -> Agent:
    return Agent(
        name="schema_loader",
        model=_model(),
        description="Loads analysis schema and initializes parameter slots.",
        instruction=(
            "Load the schema for the selected AnalysisMethod. Initialize required and optional "
            "parameters and return a structured object with empty slots."
        ),
        tools=[FunctionTool(tools.schemas.load_analysis_schema, name="load_analysis_schema")],
        output_key="analysis_detail",
    )


def parameter_collector_agent() -> Agent:
    return Agent(
        name="parameter_collector",
        model=_model(),
        description="Conversational slot-filler for missing parameters.",
        instruction=(
            "Ask one question at a time. Summarize known parameters, request missing ones, "
            "and present options via the catalog tool. When ask_for is empty or confirmed, "
            "call exit_loop to end the loop. Maintain clarity and brevity."
        ),
        tools=[
            FunctionTool(tools.catalog.list_options, name="list_options"),
            FunctionTool(tools.render.render_markdown, name="render_markdown"),
            FunctionTool(tools.state.exit_loop, name="exit_loop"),
        ],
        output_key="ask_for",
    )


def dataset_catalog_agent() -> Agent:
    return Agent(
        name="dataset_catalog",
        model=_model(),
        description="Serves allowed values for dataset-driven parameters.",
        instruction="Return allowed options for Endpoint, Population, ResponseVariable, Covariate, CovarianceMatrix.",
        tools=[FunctionTool(tools.catalog.list_options, name="list_options")],
        output_key="options",
    )


def validation_agent() -> Agent:
    return Agent(
        name="validation_safety",
        model=_model(),
        description="Validates inputs against catalogs and enforces scope.",
        instruction=(
            "Validate that provided values are in the allowed lists. Reject out-of-scope inputs, "
            "remove PII/secrets, and request re-entry when invalid."
        ),
        tools=[FunctionTool(tools.catalog.validate_param, name="validate_param")],
    )


def confirmation_agent() -> Agent:
    return Agent(
        name="confirmation",
        model=_model(),
        description="Confirms final parameters or collects revisions.",
        instruction=(
            "Present the parameter summary and ask for explicit Yes/No to proceed. "
            "If No, collect the list of parameters to update."
        ),
        tools=[FunctionTool(tools.render.render_markdown, name="render_markdown")],
        output_key="confirmation",
    )


def sas_execution_agent() -> Agent:
    return Agent(
        name="sas_execution",
        model=_model(),
        description="Generates and runs SAS macro, returns output URL.",
        instruction="Call the SAS tool with collected parameters; return the output URL or error.",
        tools=[FunctionTool(tools.sas.run_sas, name="run_sas")],
        output_key="sas_output",
    )


def audit_agent() -> Agent:
    return Agent(
        name="audit_history",
        model=_model(),
        description="Persists conversation and job metadata.",
        instruction="Persist session state, chat, and job metadata for traceability.",
        tools=[FunctionTool(tools.audit.persist_session, name="persist_session")],
        output_key="audit_log",
    )


def all_agents() -> Dict[str, Agent]:
    """
    Returns all agent definitions keyed by role name.
    """
    return {
        "orchestrator": orchestrator_agent(),
        "intent": intent_agent(),
        "schema_loader": schema_loader_agent(),
        "parameter_collector": parameter_collector_agent(),
        "dataset_catalog": dataset_catalog_agent(),
        "validation": validation_agent(),
        "confirmation": confirmation_agent(),
        "sas_execution": sas_execution_agent(),
        "audit": audit_agent(),
    }
