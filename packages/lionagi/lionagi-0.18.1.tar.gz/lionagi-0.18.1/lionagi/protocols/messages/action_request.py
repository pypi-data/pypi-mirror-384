# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import field_validator

from lionagi.utils import copy, to_dict

from .message import MessageContent, MessageRole, RoledMessage


@dataclass(slots=True)
class ActionRequestContent(MessageContent):
    """Content for action/function call requests.

    Fields:
        function: Function name to invoke
        arguments: Arguments for the function call
        action_response_id: Link to corresponding response (if any)
    """

    function: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    action_response_id: str | None = None

    @property
    def rendered(self) -> str:
        """Render action request as YAML."""
        from lionagi.libs.schema.minimal_yaml import minimal_yaml

        doc = {
            "Function": self.function,
            "Arguments": self.arguments,
        }
        return minimal_yaml(doc).strip()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionRequestContent":
        """Construct ActionRequestContent from dictionary."""
        # Handle nested structure from old format
        if "action_request" in data:
            req = data["action_request"]
            function = req.get("function", "")
            arguments = req.get("arguments", {})
        else:
            function = data.get("function", "")
            arguments = data.get("arguments", {})

        # Handle callable
        if isinstance(function, Callable):
            function = function.__name__
        if hasattr(function, "function"):
            function = function.function
        if not isinstance(function, str):
            raise ValueError("Function must be a string or callable")

        # Normalize arguments
        arguments = copy(arguments)
        if not isinstance(arguments, dict):
            try:
                arguments = to_dict(arguments, fuzzy_parse=True)
                if isinstance(arguments, list | tuple) and len(arguments) > 0:
                    arguments = arguments[0]
            except Exception:
                raise ValueError("Arguments must be a dictionary")

        action_response_id = data.get("action_response_id")
        if action_response_id:
            action_response_id = str(action_response_id)

        return cls(
            function=function,
            arguments=arguments,
            action_response_id=action_response_id,
        )


class ActionRequest(RoledMessage):
    """Message requesting an action or function execution."""

    role: MessageRole = MessageRole.ACTION
    content: ActionRequestContent

    @field_validator("content", mode="before")
    def _validate_content(cls, v):
        if v is None:
            return ActionRequestContent()
        if isinstance(v, dict):
            return ActionRequestContent.from_dict(v)
        if isinstance(v, ActionRequestContent):
            return v
        raise TypeError(
            "content must be dict or ActionRequestContent instance"
        )

    @property
    def function(self) -> str:
        """Access the function name."""
        return self.content.function

    @property
    def arguments(self) -> dict[str, Any]:
        """Access the function arguments."""
        return self.content.arguments

    def is_responded(self) -> bool:
        """Check if this request has been responded to."""
        return self.content.action_response_id is not None
