# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from lionagi.ln import AlcallParams
from lionagi.protocols.messages import ActionRequest, ActionResponse

from ..fields import ActionResponseModel
from ..types import ActionParam

if TYPE_CHECKING:
    from lionagi.session.branch import Branch

_DEFAULT_ALCALL_PARAMS = None


async def _act(
    branch: "Branch",
    action_request: BaseModel | dict | ActionRequest,
    suppress_errors: bool = False,
    verbose_action: bool = False,
):

    _request = action_request
    if isinstance(action_request, ActionRequest):
        _request = {
            "function": action_request.function,
            "arguments": action_request.arguments,
        }
    elif isinstance(action_request, BaseModel) and set(
        action_request.__class__.model_fields.keys()
    ) >= {"function", "arguments"}:
        _request = {
            "function": action_request.function,
            "arguments": action_request.arguments,
        }
    if not isinstance(_request, dict) or not {"function", "arguments"} <= set(
        _request.keys()
    ):
        raise ValueError(
            "action_request must be an ActionRequest, BaseModel with 'function'"
            " and 'arguments', or dict with 'function' and 'arguments'."
        )

    try:
        if verbose_action:
            args_ = str(_request["arguments"])
            args_ = args_[:50] + "..." if len(args_) > 50 else args_
            print(f"Invoking action {_request['function']} with {args_}.")

        func_call = await branch._action_manager.invoke(_request)
        if verbose_action:
            print(
                f"Action {_request['function']} invoked, status: {func_call.status}."
            )

    except Exception as e:
        content = {
            "error": str(e),
            "function": _request.get("function"),
            "arguments": _request.get("arguments"),
            "branch": str(branch.id),
        }
        branch._log_manager.log(content)
        if verbose_action:
            print(f"Action {_request['function']} failed, error: {str(e)}.")
        if suppress_errors:
            error_msg = f"Error invoking action '{_request['function']}': {e}"
            logging.error(error_msg)

            # Return error as action response so model knows it failed
            return ActionResponseModel(
                function=_request.get("function", "unknown"),
                arguments=_request.get("arguments", {}),
                output={"error": str(e), "message": error_msg},
            )
        raise e

    branch._log_manager.log(func_call)

    if not isinstance(action_request, ActionRequest):
        action_request = ActionRequest(
            content=_request,
            sender=branch.id,
            recipient=func_call.func_tool.id,
        )

    # Add the action request/response to the message manager, if not present
    if action_request not in branch.messages:
        branch.msgs.add_message(action_request=action_request)

    branch.msgs.add_message(
        action_request=action_request,
        action_output=func_call.response,
    )

    return ActionResponseModel(
        function=action_request.function,
        arguments=action_request.arguments,
        output=func_call.response,
    )


def prepare_act_kw(
    branch: "Branch",
    action_request: list | ActionRequest | BaseModel | dict,
    *,
    strategy: Literal["concurrent", "sequential"] = "concurrent",
    verbose_action: bool = False,
    suppress_errors: bool = True,
    call_params: AlcallParams = None,
):

    action_param = ActionParam(
        action_call_params=call_params or _get_default_call_params(),
        tools=None,  # Not used in this context
        strategy=strategy,
        suppress_errors=suppress_errors,
        verbose_action=verbose_action,
    )
    return {
        "action_request": action_request,
        "action_param": action_param,
    }


async def act(
    branch: "Branch",
    action_request: list | ActionRequest | BaseModel | dict,
    action_param: ActionParam,
) -> list[ActionResponse]:
    """Execute action requests with ActionParam."""

    match action_param.strategy:
        case "concurrent":
            return await _concurrent_act(
                branch,
                action_request,
                action_param.action_call_params,
                suppress_errors=action_param.suppress_errors,
                verbose_action=action_param.verbose_action,
            )
        case "sequential":
            return await _sequential_act(
                branch,
                action_request,
                suppress_errors=action_param.suppress_errors,
                verbose_action=action_param.verbose_action,
            )
        case _:
            raise ValueError(
                "Invalid strategy. Choose 'concurrent' or 'sequential'."
            )


async def _concurrent_act(
    branch: "Branch",
    action_request: list | ActionRequest | BaseModel | dict,
    call_params: AlcallParams,
    suppress_errors: bool = True,
    verbose_action: bool = False,
) -> list:
    """Execute actions concurrently using AlcallParams."""

    async def _wrapper(req):
        return await _act(branch, req, suppress_errors, verbose_action)

    # AlcallParams expects a list as first argument
    action_request_list = (
        action_request
        if isinstance(action_request, list)
        else [action_request]
    )

    return await call_params(action_request_list, _wrapper)


async def _sequential_act(
    branch: "Branch",
    action_request: list | ActionRequest | BaseModel | dict,
    suppress_errors: bool = True,
    verbose_action: bool = False,
) -> list:
    """Execute actions sequentially."""
    action_request = (
        action_request
        if isinstance(action_request, list)
        else [action_request]
    )
    results = []
    for req in action_request:
        result = await _act(branch, req, suppress_errors, verbose_action)
        results.append(result)
    return results


def _get_default_call_params() -> AlcallParams:
    """Get or create default AlcallParams."""
    global _DEFAULT_ALCALL_PARAMS
    if _DEFAULT_ALCALL_PARAMS is None:
        _DEFAULT_ALCALL_PARAMS = AlcallParams(output_dropna=True)
    return _DEFAULT_ALCALL_PARAMS
