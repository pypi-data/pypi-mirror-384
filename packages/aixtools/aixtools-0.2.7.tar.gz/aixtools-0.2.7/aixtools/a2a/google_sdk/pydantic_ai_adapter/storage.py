"""Storage interface and in-memory implementation for Pydantic AI agent history."""

from abc import ABC, abstractmethod

from pydantic_ai.messages import ModelRequest, ModelResponse


class PydanticAiAgentHistoryStorage(ABC):
    @abstractmethod
    def get(self, task_id: str) -> list[ModelRequest | ModelResponse] | None:
        pass

    @abstractmethod
    def store(self, task_id: str, messages: list[ModelRequest | ModelResponse]) -> None:
        pass


class InMemoryHistoryStorage(PydanticAiAgentHistoryStorage):
    def __init__(self):
        self.storage: dict[str, list[ModelRequest | ModelResponse]] = {}

    def get(self, task_id: str) -> list[ModelRequest | ModelResponse] | None:
        return self.storage.get(task_id, None)

    def store(self, task_id: str, messages: list[ModelRequest | ModelResponse]) -> None:
        self.storage[task_id] = messages
