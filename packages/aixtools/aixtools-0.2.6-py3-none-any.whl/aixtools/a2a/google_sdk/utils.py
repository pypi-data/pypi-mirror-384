import asyncio

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.server.agent_execution import RequestContext
from a2a.types import AgentCard
from a2a.utils import AGENT_CARD_WELL_KNOWN_PATH, PREV_AGENT_CARD_WELL_KNOWN_PATH

from aixtools.a2a.google_sdk.remote_agent_connection import RemoteAgentConnection
from aixtools.context import DEFAULT_SESSION_ID, DEFAULT_USER_ID, SessionIdTuple


class AgentCardLoadFailedError(Exception):
    pass


class _AgentCardResolver:
    def __init__(self, client: httpx.AsyncClient):
        self._httpx_client = client
        self._a2a_client_factory = ClientFactory(ClientConfig(httpx_client=self._httpx_client))
        self.clients: dict[str, RemoteAgentConnection] = {}

    def register_agent_card(self, card: AgentCard):
        remote_connection = RemoteAgentConnection(card, self._a2a_client_factory.create(card))
        self.clients[card.name] = remote_connection

    async def retrieve_card(self, address: str):
        for card_path in [AGENT_CARD_WELL_KNOWN_PATH, PREV_AGENT_CARD_WELL_KNOWN_PATH]:
            try:
                card_resolver = A2ACardResolver(self._httpx_client, address, card_path)
                card = await card_resolver.get_agent_card()
                card.url = address
                self.register_agent_card(card)
                return
            except Exception as e:
                print(f"Error retrieving agent card from {address} at path {card_path}: {e}")

        raise AgentCardLoadFailedError(f"Failed to load agent card from {address}")

    async def get_a2a_clients(self, agent_hosts: list[str]) -> dict[str, RemoteAgentConnection]:
        async with asyncio.TaskGroup() as task_group:
            for address in agent_hosts:
                task_group.create_task(self.retrieve_card(address))

        return self.clients


async def get_a2a_clients(ctx: SessionIdTuple, agent_hosts: list[str]) -> dict[str, RemoteAgentConnection]:
    headers = {
        "user-id": ctx[0],
        "session-id": ctx[1],
    }
    httpx_client = httpx.AsyncClient(headers=headers, timeout=60.0)
    return await _AgentCardResolver(httpx_client).get_a2a_clients(agent_hosts)


def get_session_id_tuple(context: RequestContext) -> SessionIdTuple:
    headers = context.call_context.state.get("headers", {})
    return headers.get("user-id", DEFAULT_USER_ID), headers.get("session-id", DEFAULT_SESSION_ID)
