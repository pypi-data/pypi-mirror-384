"""
This module provides functionality to convert a Pydantic AI Agent into a FastA2A application
"""

import json
from functools import partial
from typing import assert_never

from fasta2a.applications import FastA2A
from fasta2a.broker import InMemoryBroker
from fasta2a.schema import Part, TaskSendParams
from fasta2a.storage import InMemoryStorage
from pydantic_ai import Agent
from pydantic_ai._a2a import AgentWorker, worker_lifespan
from pydantic_ai.messages import (
    AudioUrl,
    BinaryContent,
    DocumentUrl,
    ImageUrl,
    ModelRequestPart,
    UserPromptPart,
    VideoUrl,
)
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from aixtools.context import session_id_var, user_id_var


class AgentWorkerWithMetadataParser(AgentWorker):
    """Custom AgentWorker class that extracts the session metadata from message metadata."""

    async def run_task(self, params: TaskSendParams) -> None:
        """
        Extract session metadata from message and store them in context variables,
        then call the parent class's run_task method.
        """
        # Load the task to extract metadata
        task = await self.storage.load_task(params["id"])
        if task:
            # Extract headers from message metadata if available
            if message := (task.get("history") or [None])[-1]:
                metadata = message.get("metadata", {})
                # Store in context variables
                user_id_var.set(metadata.get("user_id", ""))
                session_id_var.set(metadata.get("session_id", ""))
        # Call the parent class's run_task method
        return await super().run_task(params)


class AgentWorkerWithDataPartSupport(AgentWorkerWithMetadataParser):
    """Custom agent worker that adds support for data parts in messages."""

    def _request_parts_from_a2a(self, parts: list[Part]) -> list[ModelRequestPart]:
        """
        Clones underlying method with additional support for data parts.
        TODO: remove once pydantic-ai supports data parts natively.
        """
        model_parts: list[ModelRequestPart] = []
        for part in parts:
            if part["kind"] == "text":
                model_parts.append(UserPromptPart(content=part["text"]))
            elif part["kind"] == "file":
                file_content = part["file"]
                if "bytes" in file_content:
                    data = file_content["bytes"].encode("utf-8")
                    mime_type = file_content.get("mime_type", "application/octet-stream")
                    content = BinaryContent(data=data, media_type=mime_type)
                    model_parts.append(UserPromptPart(content=[content]))
                else:
                    url = file_content["uri"]
                    for url_cls in (DocumentUrl, AudioUrl, ImageUrl, VideoUrl):
                        content = url_cls(url=url)
                        try:
                            content.media_type
                        except ValueError:  # pragma: no cover
                            continue
                        else:
                            break
                    else:
                        raise ValueError(f"Unsupported file type: {url}")  # pragma: no cover
                    model_parts.append(UserPromptPart(content=[content]))
            elif part["kind"] == "data":
                content = json.dumps(part["data"])
                model_parts.append(UserPromptPart(content=[content]))
            else:
                assert_never(part)
        return model_parts


def agent_to_a2a(
    agent: Agent, name: str, description: str, skills: list[dict], worker_class=AgentWorkerWithMetadataParser
) -> FastA2A:
    """Convert the agent to an A2A application taking care of session metadata extraction."""
    storage = InMemoryStorage()
    broker = InMemoryBroker()
    worker = worker_class(broker=broker, storage=storage, agent=agent)
    return FastA2A(
        storage=storage,
        broker=broker,
        name=name,
        description=description,
        skills=skills,
        url="",
        lifespan=partial(worker_lifespan, worker=worker, agent=agent),
    )


def fix_a2a_docs_pages(app: Starlette) -> None:
    """
    Fix the FastA2A documentation to point to the correct path.
    This is a workaround for the issue with the FastA2A docs not being served correctly
    when mounted as a sub-path.
    """

    async def redirect_to_sub_agent(request: Request):
        """Redirect to proper sub-app using the Referer header to determine the path prefix."""
        referer = request.headers.get("referer", "")
        if referer.endswith("/docs"):
            return RedirectResponse(url=f"{referer.rsplit('/', 1)[0]}{request.url.path}")
        raise HTTPException(status_code=404)

    app.router.add_route("/.well-known/agent.json", redirect_to_sub_agent, methods=["GET"])
    app.router.add_route("/", redirect_to_sub_agent, methods=["POST"])
