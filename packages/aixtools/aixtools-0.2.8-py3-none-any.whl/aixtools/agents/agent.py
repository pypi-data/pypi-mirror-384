"""
Core agent implementation providing model selection and configuration for AI agents.
"""

from types import NoneType
from typing import Any

from fastmcp import Context
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from aixtools.logging.log_objects import ObjectLogger
from aixtools.logging.logging_config import get_logger
from aixtools.logging.model_patch_logging import model_patch_logging
from aixtools.utils.config import (
    AWS_PROFILE,
    AWS_REGION,
    AZURE_MODEL_NAME,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_ENDPOINT,
    BEDROCK_MODEL_NAME,
    MODEL_FAMILY,
    MODEL_TIMEOUT,
    OLLAMA_MODEL_NAME,
    OLLAMA_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    OPENROUTER_MODEL_NAME,
)

logger = get_logger(__name__)


def _get_model_bedrock(model_name=BEDROCK_MODEL_NAME, aws_region=AWS_REGION):
    assert model_name, "BEDROCK_MODEL_NAME is not set"
    assert aws_region, "AWS_REGION is not set"

    if AWS_PROFILE is not None:
        return BedrockConverseModel(model_name=model_name)

    provider = BedrockProvider(region_name=aws_region)
    return BedrockConverseModel(model_name=model_name, provider=provider)


def _get_model_ollama(model_name=OLLAMA_MODEL_NAME, ollama_url=OLLAMA_URL):
    assert ollama_url, "OLLAMA_URL is not set"
    assert model_name, "Model name is not set"
    provider = OpenAIProvider(base_url=ollama_url)
    return OpenAIChatModel(model_name=model_name, provider=provider)


def _get_model_openai(model_name=OPENAI_MODEL_NAME, openai_api_key=OPENAI_API_KEY):
    assert openai_api_key, "OPENAI_API_KEY is not set"
    assert model_name, "Model name is not set"
    provider = OpenAIProvider(api_key=openai_api_key)
    return OpenAIChatModel(model_name=model_name, provider=provider)


def _get_model_openai_azure(
    model_name=AZURE_MODEL_NAME,
    azure_openai_api_key=AZURE_OPENAI_API_KEY,
    azure_openai_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_openai_api_version=AZURE_OPENAI_API_VERSION,
):
    assert azure_openai_endpoint, "AZURE_OPENAI_ENDPOINT is not set"
    assert azure_openai_api_key, "AZURE_OPENAI_API_KEY is not set"
    assert azure_openai_api_version, "AZURE_OPENAI_API_VERSION is not set"
    assert model_name, "Model name is not set"
    client = AsyncAzureOpenAI(
        azure_endpoint=azure_openai_endpoint, api_version=azure_openai_api_version, api_key=azure_openai_api_key
    )
    return OpenAIChatModel(model_name=model_name, provider=OpenAIProvider(openai_client=client))


def _get_model_open_router(
    model_name=OPENROUTER_MODEL_NAME, openrouter_api_url=OPENROUTER_API_URL, openrouter_api_key=OPENROUTER_API_KEY
):
    assert openrouter_api_url, "OPENROUTER_API_URL is not set"
    assert openrouter_api_key, "OPENROUTER_API_KEY is not set"
    assert model_name, "Model name is not set, missing 'OPENROUTER_MODEL_NAME' environment variable?"
    provider = OpenAIProvider(base_url=openrouter_api_url, api_key=openrouter_api_key)
    return OpenAIChatModel(model_name, provider=provider)


def get_model(model_family=MODEL_FAMILY, model_name=None, **kwargs):
    """Create and return appropriate model instance based on specified family and name."""
    assert model_family is not None and model_family != "", f"Model family '{model_family}' is not set"
    match model_family:
        case "azure":
            return _get_model_openai_azure(model_name=model_name or AZURE_MODEL_NAME, **kwargs)
        case "bedrock":
            return _get_model_bedrock(model_name=model_name or BEDROCK_MODEL_NAME, **kwargs)
        case "ollama":
            return _get_model_ollama(model_name=model_name or OLLAMA_MODEL_NAME, **kwargs)
        case "openai":
            return _get_model_openai(model_name=model_name or OPENAI_MODEL_NAME, **kwargs)
        case "openrouter":
            return _get_model_open_router(model_name=model_name or OPENROUTER_MODEL_NAME, **kwargs)
        case _:
            raise ValueError(f"Model family '{model_family}' not supported")


def get_agent(  # noqa: PLR0913, pylint: disable=too-many-arguments,too-many-positional-arguments
    model=None,
    *,
    instructions=None,
    system_prompt=(),
    tools=(),
    toolsets=(),
    model_settings=None,
    output_type: Any = str,
    deps_type=NoneType,
) -> Agent:
    """Get a PydanticAI agent"""
    if model_settings is None:
        model_settings = ModelSettings(timeout=MODEL_TIMEOUT)
    if model is None:
        model = get_model()
    agent = Agent(
        model=model,
        output_type=output_type,
        instructions=instructions,
        system_prompt=system_prompt,
        deps_type=deps_type,
        model_settings=model_settings,
        tools=tools,
        toolsets=toolsets,
        instrument=True,
    )
    return agent


async def run_agent(  # noqa: PLR0913, pylint: disable=too-many-arguments,too-many-positional-arguments
    agent: Agent,
    prompt: str | list[str],
    usage_limits: UsageLimits | None = None,
    verbose: bool = False,
    debug: bool = False,
    log_model_requests: bool = False,
    parent_logger: ObjectLogger | None = None,
    ctx: Context | None = None,
):
    """
    Run the agent with the given prompt and log the execution details.
    Args:
        agent (Agent): The PydanticAI agent to run.
        prompt (str | list[str]): The input prompt(s) for the agent.
        usage_limits (UsageLimits | None): Optional usage limits for the agent.
        verbose (bool): If True, enables verbose logging.
        debug (bool): If True, enables debug logging.
        log_model_requests (bool): If True, logs model requests and responses.
        parent_logger (ObjectLogger | None): Optional parent logger for hierarchical logging.
        ctx (Context | None): Optional FastMCP context for logging messages to the MCP client.
    Returns:
        tuple[final_output, nodes]: A tuple containing the agent's final output and a list of all logged nodes.
    """
    # Results
    nodes, result = [], None
    async with agent.iter(prompt, usage_limits=usage_limits) as agent_run:
        # Create a new log file for each run
        with ObjectLogger(parent_logger=parent_logger, verbose=verbose, debug=debug) as agent_logger:
            # Patch the model with the logger
            if log_model_requests:
                agent.model = model_patch_logging(agent.model, agent_logger)
            # Run the agent
            async for node in agent_run:
                await agent_logger.log(node)  # Log each node
                if ctx:
                    # If we are executing in an MCP server, send info messages to the client for better debugging
                    server_name = ctx.fastmcp.name
                    await ctx.info(f"MCP server {server_name}: {node}")
                nodes.append(node)
            result = agent_run.result
    return result.output if result else None, nodes
