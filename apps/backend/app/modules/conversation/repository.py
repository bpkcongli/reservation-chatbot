"""Repository boundary and process-local implementation for conversation sessions."""

from copy import deepcopy
from threading import RLock
from typing import Protocol

from app.modules.conversation.domain import ConversationContext


class ConversationRepository(Protocol):
    """Storage operations needed by CONV-01 through CONV-03."""

    def create(self, context: ConversationContext) -> None:
        """Store a new conversation."""

    def get(self, conversation_id: str) -> ConversationContext | None:
        """Return a detached snapshot when the conversation exists."""

    def save(self, context: ConversationContext) -> None:
        """Replace an existing conversation snapshot."""


class InMemoryConversationRepository:
    """Thread-safe store used until database persistence is implemented in CONV-08."""

    def __init__(self) -> None:
        self._contexts: dict[str, ConversationContext] = {}
        self._lock = RLock()

    def create(self, context: ConversationContext) -> None:
        with self._lock:
            if context.conversation_id in self._contexts:
                raise ValueError("Conversation ID already exists.")
            self._contexts[context.conversation_id] = deepcopy(context)

    def get(self, conversation_id: str) -> ConversationContext | None:
        with self._lock:
            context = self._contexts.get(conversation_id)
            return deepcopy(context) if context is not None else None

    def save(self, context: ConversationContext) -> None:
        with self._lock:
            if context.conversation_id not in self._contexts:
                raise KeyError(context.conversation_id)
            self._contexts[context.conversation_id] = deepcopy(context)
