"""
Memory manager.

Minimal in-memory conversation buffer:
- stores last N messages
- returns formatted conversation history for prompting

No database, no embeddings, no vector store.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "user" | "assistant" | "system"
    content: str


class MemoryManager:
    def __init__(self, max_messages: int = 10) -> None:
        self.max_messages = max_messages
        self._messages: list[ChatMessage] = []

    def add(self, role: str, content: str) -> None:
        content = (content or "").strip()
        if not content:
            return

        self._messages.append(ChatMessage(role=role, content=content))
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]

    def get_messages(self) -> list[ChatMessage]:
        return list(self._messages)

    def formatted_history(self) -> str:
        """
        Create a compact, readable history string.
        This is useful for debugging and for small-prompt models.
        """

        lines: list[str] = []
        for m in self._messages:
            prefix = "USER" if m.role == "user" else "ASSISTANT" if m.role == "assistant" else "SYSTEM"
            lines.append(f"{prefix}: {m.content}")
        return "\n".join(lines).strip()

