# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from lionagi.models import FieldModel, ModelParams

from ..fields import get_default_field
from .operative import Operative


class Step:
    """Utility class providing methods to create and manage Operative instances for steps."""

    @staticmethod
    def request_operative(
        *,
        operative: Operative = None,
        operative_name: str | None = None,
        reason: bool = False,
        actions: bool = False,
        request_params: ModelParams | None = None,
        parameter_fields: dict[str, FieldInfo] | None = None,
        base_type: type[BaseModel] | None = None,
        field_models: list[FieldModel] | None = None,
        exclude_fields: list[str] | None = None,
        new_model_name: str | None = None,
        field_descriptions: dict[str, str] | None = None,
        inherit_base: bool = True,
        config_dict: dict | None = None,
        doc: str | None = None,
        frozen: bool = False,
        max_retries: int = None,
        auto_retry_parse: bool = True,
        parse_kwargs: dict | None = None,
    ) -> Operative:
        """Creates an Operative instance configured for request handling.

        Args:
            operative_name (str, optional): Name of the operative.
            reason (bool, optional): Whether to include reason field.
            actions (bool, optional): Whether to include action fields.
            request_params (ModelParams, optional): Parameters for the new model.
            parameter_fields (dict[str, FieldInfo], optional): Parameter fields for the model.
            base_type (type[BaseModel], optional): Base type for the model.
            field_models (list[FieldModel], optional): List of field models.
            exclude_fields (list[str], optional): List of fields to exclude.
            new_model_name (str | None, optional): Name of the new model.
            field_descriptions (dict[str, str], optional): Descriptions for the fields.
            inherit_base (bool, optional): Whether to inherit base.
            config_dict (dict | None, optional): Configuration dictionary.
            doc (str | None, optional): Documentation string.
            frozen (bool, optional): Whether the model is frozen.
            max_retries (int, optional): Maximum number of retries.

        Returns:
            Operative: The configured operative instance.
        """

        params = {}
        if operative:
            params = operative.model_dump()
            request_params = operative.request_params.model_dump()
            field_models = request_params.field_models

        field_models = field_models or []
        exclude_fields = exclude_fields or []
        field_descriptions = field_descriptions or {}
        if reason and (fm := get_default_field("reason")) not in field_models:
            field_models.append(fm)
        if (
            actions
            and (fm := get_default_field("action_requests"))
            not in field_models
        ):
            fm2 = get_default_field("action_required")
            field_models.extend([fm, fm2])
        if isinstance(request_params, ModelParams):
            request_params = request_params.to_dict()

        request_params = request_params or {}
        request_params_fields = {
            "parameter_fields": parameter_fields,
            "field_models": field_models,
            "exclude_fields": exclude_fields,
            "field_descriptions": field_descriptions,
            "inherit_base": inherit_base,
            "config_dict": config_dict,
            "doc": doc,
            "frozen": frozen,
            "base_type": base_type,
            "name": new_model_name,
        }
        request_params.update(
            {k: v for k, v in request_params_fields.items() if v is not None}
        )
        request_params = ModelParams(**request_params)
        if max_retries:
            params["max_retries"] = max_retries
        if operative_name:
            params["name"] = operative_name
        if isinstance(auto_retry_parse, bool):
            params["auto_retry_parse"] = auto_retry_parse
        if parse_kwargs:
            params["parse_kwargs"] = parse_kwargs
        params["request_params"] = request_params
        return Operative(**params)

    @staticmethod
    def respond_operative(
        *,
        operative: Operative,
        additional_data: dict | None = None,
        response_params: ModelParams | None = None,
        field_models: list[FieldModel] | None = None,
        frozen_response: bool = False,
        response_config_dict: dict | None = None,
        response_doc: str | None = None,
        exclude_fields: list[str] | None = None,
    ) -> Operative:
        """Updates the operative with response parameters and data.

        Args:
            operative (Operative): The operative instance to update.
            additional_data (dict | None, optional): Additional data to include in the response.
            response_params (ModelParams | None, optional): Parameters for the response model.
            field_models (list[FieldModel] | None, optional): List of field models.
            frozen_response (bool, optional): Whether the response model is frozen.
            response_config_dict (dict | None, optional): Configuration dictionary for the response.
            response_doc (str | None, optional): Documentation string for the response.
            exclude_fields (list[str] | None, optional): List of fields to exclude.

        Returns:
            Operative: The updated operative instance.
        """

        additional_data = additional_data or {}
        field_models = field_models or []
        if hasattr(operative.response_model, "action_required"):
            for i in {
                "action_requests",
                "action_required",
                "action_responses",
            }:
                fm = get_default_field(i)
                if fm not in field_models:
                    field_models.append(fm)

        if "reason" in type(operative.response_model).model_fields:
            field_models.append(get_default_field("reason"))

        operative = Step._create_response_type(
            operative=operative,
            response_params=response_params,
            field_models=field_models,
            frozen_response=frozen_response,
            response_config_dict=response_config_dict,
            response_doc=response_doc,
            exclude_fields=exclude_fields,
        )

        data = operative.response_model.model_dump()
        data.update(additional_data or {})
        operative.response_model = operative.response_type.model_validate(data)
        return operative

    @staticmethod
    def _create_response_type(
        operative: Operative,
        response_params: ModelParams | None = None,
        response_validators: dict | None = None,
        frozen_response: bool = False,
        response_config_dict: dict | None = None,
        response_doc: str | None = None,
        field_models: list[FieldModel] | None = None,
        exclude_fields: list[str] | None = None,
    ) -> Operative:
        """Internal method to create a response type for the operative.

        Args:
            operative (Operative): The operative instance.
            response_params (ModelParams | None, optional): Parameters for the response model.
            response_validators (dict | None, optional): Validators for the response model.
            frozen_response (bool, optional): Whether the response model is frozen.
            response_config_dict (dict | None, optional): Configuration dictionary for the response.
            response_doc (str | None, optional): Documentation string for the response.
            field_models (list[FieldModel] | None, optional): List of field models.
            exclude_fields (list[str] | None, optional): List of fields to exclude.

        Returns:
            Operative: The operative instance with updated response type.
        """

        field_models = field_models or []

        if (
            hasattr(operative.request_type, "action_required")
            and operative.response_model.action_required
        ):
            for i in {
                "action_requests",
                "action_required",
                "action_responses",
            }:
                fm = get_default_field(i)
                if fm not in field_models:
                    field_models.append(fm)

        if hasattr(operative.request_type, "reason"):
            field_models.append(get_default_field("reason"))

        operative.create_response_type(
            response_params=response_params,
            field_models=field_models,
            exclude_fields=exclude_fields or [],
            doc=response_doc,
            config_dict=response_config_dict,
            frozen=frozen_response,
            validators=response_validators,
        )
        return operative
