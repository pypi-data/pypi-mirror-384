from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Artifact,
    FilePart,
    FileWithUri,
    Message,
    Part,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import get_file_parts, get_message_text, new_agent_text_message, new_task
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent

from aixtools.a2a.google_sdk.pydantic_ai_adapter.storage import InMemoryHistoryStorage
from aixtools.a2a.google_sdk.remote_agent_connection import is_in_terminal_state
from aixtools.a2a.google_sdk.utils import get_session_id_tuple
from aixtools.agents import get_agent
from aixtools.agents.prompt import build_user_input
from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger
from aixtools.mcp.client import get_configured_mcp_servers

logger = get_logger(__name__)


class AgentParameters(BaseModel):
    system_prompt: str
    mcp_servers: list[str]


class RunOutput(BaseModel):
    is_task_failed: bool
    is_task_in_progress: bool
    is_input_required: bool
    output: str
    created_artifacts_paths: list[str]


def _task_failed_event(text: str, context_id: str | None, task_id: str | None) -> TaskStatusUpdateEvent:
    """Creates a TaskStatusUpdateEvent indicating task failure."""
    return TaskStatusUpdateEvent(
        status=TaskStatus(
            state=TaskState.failed, message=new_agent_text_message(text=text, context_id=context_id, task_id=task_id)
        ),
        final=True,
        context_id=context_id,
        task_id=task_id,
    )


class PydanticAgentExecutor(AgentExecutor):
    def __init__(self, agent_parameters: AgentParameters):
        self._agent_parameters = agent_parameters
        self.history_storage = InMemoryHistoryStorage()

    def _convert_message_to_pydantic_parts(
        self,
        session_tuple: SessionIdTuple,
        message: Message,
    ) -> str | list[str | BinaryContent]:
        """Convert A2A Message to a Pydantic AI agent input format"""
        text_prompt = get_message_text(message)
        file_parts = get_file_parts(message.parts)
        if not file_parts:
            return text_prompt
        file_paths = [Path(part.uri) for part in file_parts if isinstance(part, FileWithUri)]

        return build_user_input(session_tuple, text_prompt, file_paths)

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """
        Execute the agent run.
        Wraps pydantic ai agent execution with a2a protocol events
        Args:
            context (RequestContext): The request context containing the message and task information.
            event_queue (EventQueue): The event queue to enqueue events.
        """
        session_tuple = get_session_id_tuple(context)
        agent = self._build_agent(session_tuple)
        if context.message is None:
            raise ValueError("No message provided")

        task = context.current_task
        message = context.message
        if not task:
            task = new_task(message)
            await event_queue.enqueue_event(task)

        if is_in_terminal_state(task):
            raise RuntimeError("Can not perform a task as it is in a terminal state: %s", task.status.state)

        prompt = self._convert_message_to_pydantic_parts(session_tuple, message)
        history_message = self.history_storage.get(task.id)

        try:
            result = await agent.run(
                user_prompt=prompt,
                message_history=history_message,
            )
        except Exception as e:
            await event_queue.enqueue_event(
                _task_failed_event(
                    text=f"Agent execution error: {e}",
                    context_id=context.context_id,
                    task_id=task.id,
                )
            )
            return

        self.history_storage.store(task.id, result.all_messages())

        run_output: RunOutput = result.output
        if run_output.is_task_failed:
            await event_queue.enqueue_event(
                _task_failed_event(
                    text=f"Task failed: {run_output.output}",
                    context_id=context.context_id,
                    task_id=task.id,
                )
            )
            return

        if run_output.is_input_required:
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    status=TaskStatus(
                        state=TaskState.input_required,
                        message=new_agent_text_message(
                            text=run_output.output, context_id=context.context_id, task_id=task.id
                        ),
                    ),
                    final=False,
                    context_id=context.context_id,
                    task_id=task.id,
                )
            )
            return

        if run_output.is_task_in_progress:
            logger.error("Task hasn't been completed: %s", run_output.output)
            await event_queue.enqueue_event(
                _task_failed_event(
                    text=f"Agent didn't manage complete the task: {run_output.output}",
                    context_id=context.context_id,
                    task_id=task.id,
                )
            )
            return

        for idx, artifact in enumerate(run_output.created_artifacts_paths):
            image_file = FileWithUri(uri=str(artifact), name=f"image_{idx}")
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    append=False,
                    context_id=task.context_id,
                    task_id=task.id,
                    last_chunk=True,
                    artifact=Artifact(
                        artifact_id=f"image_{idx}",
                        parts=[Part(root=FilePart(file=image_file))],
                    ),
                )
            )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(
                    state=TaskState.completed,
                    message=new_agent_text_message(
                        text=run_output.output, context_id=context.context_id, task_id=task.id
                    ),
                ),
                final=True,
                context_id=context.context_id,
                task_id=task.id,
            )
        )

    async def cancel(self, ctx: RequestContext, event_queue: EventQueue) -> None:
        """Cancel"""
        raise Exception("cancel not supported")

    def _build_agent(self, session_tuple: SessionIdTuple) -> Agent:
        params = self._agent_parameters
        mcp_servers = get_configured_mcp_servers(session_tuple, params.mcp_servers)
        return get_agent(
            system_prompt=params.system_prompt,
            toolsets=mcp_servers,
            output_type=RunOutput,
        )
