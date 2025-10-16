# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

import contextlib
from collections.abc import Callable
from typing import Any
from uuid import UUID

from pydantic import (
    Field,
    JsonValue,
    PrivateAttr,
    field_serializer,
    model_validator,
)
from typing_extensions import Self

from lionagi.protocols.types import (
    ID,
    MESSAGE_FIELDS,
    Graph,
    Node,
    Pile,
    Progression,
    Relational,
    RoledMessage,
    SenderRecipient,
    System,
)

from .._errors import ItemNotFoundError
from ..ln import lcall
from ..service.imodel import iModel
from .branch import ActionManager, Branch, OperationManager, Tool


class Session(Node, Relational):
    """
    Manages multiple conversation branches in a session.

    Attributes:
        branches (Pile | None): Collection of conversation branches.
        default_branch (Branch | None): The default conversation branch.
    """

    branches: Pile[Branch] = Field(
        default_factory=lambda: Pile(item_type={Branch}, strict_type=False)
    )
    default_branch: Any = Field(default=None, exclude=True)
    name: str = Field(default="Session")
    user: SenderRecipient | None = None
    _operation_manager: OperationManager = PrivateAttr(
        default_factory=OperationManager
    )

    @field_serializer("user")
    def _serialize_user(self, value: SenderRecipient | None) -> JsonValue:
        if value is None:
            return None
        return str(value)

    async def ainclude_branches(self, branches: ID[Branch].ItemSeq):
        async with self.branches:
            self.include_branches(branches)

    def include_branches(self, branches: ID[Branch].ItemSeq):
        def _take_in_branch(branch: Branch):
            if branch not in self.branches:
                self.branches.include(branch)

            branch.user = self.id
            branch._operation_manager = self._operation_manager
            if self.default_branch is None:
                self.default_branch = branch

        branches = [branches] if isinstance(branches, Branch) else branches

        for i in branches:
            _take_in_branch(i)

    def register_operation(
        self, operation: str, func: Callable, *, update: bool = False
    ):
        self._operation_manager.register(operation, func, update=update)

    def operation(self, name: str = None, *, update: bool = False):
        """
        Decorator to automatically register functions as operations.

        Args:
            name: Operation name. If None, uses the function's __name__.
            update: Whether to update if operation already exists.

        Usage:
            @session.operation()
            async def read_issue():
                ...

            @session.operation("custom_name")
            async def some_function():
                ...
        """

        def decorator(func: Callable) -> Callable:
            operation_name = name if name is not None else func.__name__
            self.register_operation(operation_name, func, update=update)
            return func

        return decorator

    @model_validator(mode="after")
    def _initialize_branches(self) -> Self:
        if self.default_branch is None:
            self.default_branch = Branch()
        if self.default_branch not in self.branches:
            self.branches.include(self.default_branch)
        if self.branches:
            self.include_branches(self.branches)
        return self

    def _lookup_branch_by_name(self, name: str) -> Branch | None:
        for branch in self.branches:
            if branch.name == name:
                return branch
        return None

    def get_branch(
        self, branch: ID.Ref | str, default: Any = ..., /
    ) -> Branch:
        """Get a branch by its ID or name."""

        with contextlib.suppress(ItemNotFoundError, ValueError):
            id = ID.get_id(branch)
            return self.branches[id]

        if isinstance(branch, str):
            if b := self._lookup_branch_by_name(branch):
                return b

        if default is ...:
            raise ItemNotFoundError(f"Branch '{branch}' not found.")
        return default

    def new_branch(
        self,
        system: System | JsonValue = None,
        system_sender: SenderRecipient = None,
        system_datetime: bool | str = None,
        user: SenderRecipient = None,
        name: str | None = None,
        imodel: iModel | None = None,
        messages: Pile[RoledMessage] = None,
        progress: Progression = None,
        tool_manager: ActionManager = None,
        tools: Tool | Callable | list = None,
        as_default_branch: bool = False,
        **kwargs,
    ) -> Branch:
        """Create and include a new branch in the session."""
        params = {
            k: v
            for k, v in locals().items()
            if k not in ("self", "as_default_branch", "kwargs")
            and v is not None
        }
        branch = Branch(**params, **kwargs)  # type: ignore
        self.include_branches(branch)
        if as_default_branch:
            self.default_branch = branch
        return branch

    def remove_branch(
        self,
        branch: ID.Ref,
        delete: bool = False,
    ):
        branch = ID.get_id(branch)

        if branch not in self.branches:
            _s = (
                str(branch)
                if len(str(branch)) < 10
                else str(branch)[:10] + "..."
            )
            raise ItemNotFoundError(f"Branch {_s}.. does not exist.")
        branch: Branch = self.branches[branch]

        self.branches.exclude(branch)

        if self.default_branch.id == branch.id:
            if not self.branches:
                self.default_branch = None
            else:
                self.default_branch = self.branches[0]

        if delete:
            del branch

    async def asplit(self, branch: ID.Ref) -> Branch:
        """
        Split a branch, creating a new branch with the same messages and tools.

        Args:
            branch: The branch to split or its identifier.

        Returns:
            The newly created branch.
        """
        async with self.branches:
            return self.split(branch)

    def split(self, branch: ID.Ref) -> Branch:
        """
        Split a branch, creating a new branch with the same messages and tools.

        Args:
            branch: The branch to split or its identifier.

        Returns:
            The newly created branch.
        """
        branch: Branch = self.branches[branch]
        branch_clone = branch.clone(sender=self.id)
        self.include_branches(branch_clone)
        return branch_clone

    def change_default_branch(self, branch: ID.Ref):
        """
        Change the default branch of the session.

        Args:
            branch: The branch to set as default or its identifier.
        """
        branch = self.branches[branch]
        if not isinstance(branch, Branch):
            raise ValueError("Input value for branch is not a valid branch.")
        self.default_branch = branch

    def to_df(
        self,
        branches: ID.RefSeq = None,
        exclude_clone: bool = False,
        exlcude_load: bool = False,
    ):
        out = self.concat_messages(
            branches=branches,
            exclude_clone=exclude_clone,
            exclude_load=exlcude_load,
        )
        return out.to_df(columns=MESSAGE_FIELDS)

    def concat_messages(
        self,
        branches: ID.RefSeq = None,
        exclude_clone: bool = False,
        exclude_load: bool = False,
    ) -> Pile[RoledMessage]:
        if not branches:
            branches = self.branches

        if any(i not in self.branches for i in branches):
            raise ValueError("Branch does not exist.")

        # Note: exclude_clone and exclude_load parameters are deprecated
        # and currently have no effect. They are kept for API compatibility.

        messages = lcall(
            branches,
            lambda x: list(self.branches[x].messages),
            input_unique=True,
            input_flatten=True,
            input_dropna=True,
            output_flatten=True,
            output_unique=True,
        )
        return Pile(
            collections=messages, item_type={RoledMessage}, strict_type=False
        )

    async def flow(
        self,
        graph: Graph,
        *,
        context: dict[str, Any] | None = None,
        parallel: bool = True,
        max_concurrent: int = 5,
        verbose: bool = False,
        default_branch: Branch | ID.Ref | None = None,
        alcall_params: Any = None,
    ) -> dict[str, Any]:
        """
        Execute a graph-based workflow using multi-branch orchestration.

        This is a Session-native operation that coordinates execution across
        multiple branches for parallel processing.

        Args:
            graph: The workflow graph containing Operation nodes
            context: Initial context for the workflow
            parallel: Whether to execute independent operations in parallel
            max_concurrent: Maximum concurrent operations (branches)
            verbose: Enable verbose logging
            default_branch: Branch to use as default (defaults to self.default_branch)
            alcall_params: Parameters for async parallel call execution

        Returns:
            Execution results with completed operations and final context
        """
        from lionagi.operations.flow import flow

        # Use specified branch or session's default
        branch = default_branch or self.default_branch
        if isinstance(branch, (str, UUID)):
            branch = self.branches[branch]

        return await flow(
            session=self,
            graph=graph,
            branch=branch,
            context=context,
            parallel=parallel,
            max_concurrent=max_concurrent,
            verbose=verbose,
            alcall_params=alcall_params,
        )


__all__ = ("Session",)
