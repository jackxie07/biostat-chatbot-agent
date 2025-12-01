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
from google.genai import types as genai_types

import tools.audit
import tools.catalog
import tools.render
import tools.sas
import tools.schemas


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
            tools.schemas.load_standard_schema,
            tools.schemas.load_analysis_schema,
            tools.catalog.list_options,
            tools.catalog.validate_param,
            tools.sas.run_sas,
            tools.audit.persist_session,
            tools.render.render_markdown,
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
        tools=[tools.schemas.load_standard_schema],
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
        tools=[tools.schemas.load_analysis_schema],
    )


def parameter_collector_agent() -> Agent:
    return Agent(
        name="parameter_collector",
        model=_model(),
        description="Conversational slot-filler for missing parameters.",
        instruction=(
            "Ask one question at a time. Summarize known parameters, request missing ones, "
            "and present options via the catalog tool. Maintain clarity and brevity."
        ),
        tools=[tools.catalog.list_options, tools.render.render_markdown],
    )


def dataset_catalog_agent() -> Agent:
    return Agent(
        name="dataset_catalog",
        model=_model(),
        description="Serves allowed values for dataset-driven parameters.",
        instruction="Return allowed options for Endpoint, Population, ResponseVariable, Covariate, CovarianceMatrix.",
        tools=[tools.catalog.list_options],
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
        tools=[tools.catalog.validate_param],
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
        tools=[tools.render.render_markdown],
    )


def sas_execution_agent() -> Agent:
    return Agent(
        name="sas_execution",
        model=_model(),
        description="Generates and runs SAS macro, returns output URL.",
        instruction="Call the SAS tool with collected parameters; return the output URL or error.",
        tools=[tools.sas.run_sas],
    )


def audit_agent() -> Agent:
    return Agent(
        name="audit_history",
        model=_model(),
        description="Persists conversation and job metadata.",
        instruction="Persist session state, chat, and job metadata for traceability.",
        tools=[tools.audit.persist_session],
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
