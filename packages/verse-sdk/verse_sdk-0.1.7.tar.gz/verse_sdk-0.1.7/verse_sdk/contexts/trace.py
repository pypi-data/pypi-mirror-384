from __future__ import annotations

from typing import Any

from .base import BaseContext
from .types import ContextType, ObservationType


class TraceContext(BaseContext):
    """Context for trace-level spans (top-level operations)."""

    observation_type: ObservationType = "trace"
    type: ContextType = "trace"

    def input(self, input: Any) -> TraceContext:
        """Set the input for the trace."""
        self._span.set_attribute("input", str(input))
        return self

    def project(self, project_id: str) -> TraceContext:
        """Set the project ID for the trace."""
        self._span.set_attribute("project.id", project_id)
        return self

    def session(self, session_id: str) -> TraceContext:
        """Set the session ID for the trace."""
        self._span.set_attribute("session.id", session_id)
        return self

    def output(self, output: Any) -> TraceContext:
        """Set the output for the trace."""
        self._span.set_attribute("output", str(output))
        return self

    def scope(self, scope: str) -> TraceContext:
        """Set the scope for the trace."""
        self._span.set_attribute("session.scope", scope)
        return self

    def tags(self, tags: list[str]) -> TraceContext:
        """Add tags to the trace."""
        self._span.set_attribute("tags", tags)
        return self

    def update(self, **kwargs) -> TraceContext:
        """Update the trace with additional attributes."""
        self.set_attributes(**kwargs)
        return self

    def user(self, user_id: str) -> TraceContext:
        """Set the user ID for the trace."""
        self._span.set_attribute("user.id", user_id)
        return self
