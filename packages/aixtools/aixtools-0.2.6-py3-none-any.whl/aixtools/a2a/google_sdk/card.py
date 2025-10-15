import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

from aixtools.logging.logging_config import get_logger

logger = get_logger(__name__)


async def get_agent_card(httpx_client: httpx.AsyncClient, agent_url: str) -> AgentCard:
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=agent_url,
    )

    try:
        _public_card = await resolver.get_agent_card()  # Fetches from default public path
        logger.info("Successfully fetched public agent card:")
        logger.info(_public_card.model_dump_json(indent=2, exclude_none=True))
        final_agent_card_to_use = _public_card
    except Exception as e:
        logger.error(f"Critical error fetching public agent card: {e}", exc_info=True)
        raise RuntimeError("Failed to fetch the public agent card. Cannot continue.") from e

    # Set the URL which is accessible from the container
    final_agent_card_to_use.url = agent_url
    return final_agent_card_to_use
