# Copyright (c) 2023-2025, HaiyangLi <quantocean.li at gmail dot com>
# SPDX-License-Identifier: Apache-2.0

import copy as _copy
import logging
import types
import uuid
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, TypeVar, Union, get_args, get_origin

from .ln import (
    extract_json,
    fuzzy_json,
    get_bins,
    hash_dict,
    import_module,
    is_coro_func,
    is_import_installed,
    to_dict,
    to_list,
)
from .ln.types import (
    DataClass,
    Enum,
    KeysDict,
    MaybeSentinel,
    MaybeUndefined,
    MaybeUnset,
    Params,
    Undefined,
    UndefinedType,
    Unset,
    UnsetType,
)

R = TypeVar("R")
T = TypeVar("T")

logger = logging.getLogger(__name__)

UNDEFINED = Undefined

__all__ = (
    "UndefinedType",
    "KeysDict",
    "Params",
    "DataClass",
    "UNDEFINED",
    "copy",
    "is_same_dtype",
    "get_file_classes",
    "get_class_file_registry",
    "get_class_objects",
    "is_coro_func",
    "to_list",
    "create_path",
    "get_bins",
    "EventStatus",
    "logger",
    "Enum",
    "hash_dict",
    "is_union_type",
    "union_members",
    "Unset",
    "UnsetType",
    "Undefined",
    "MaybeSentinel",
    "MaybeUndefined",
    "MaybeUnset",
    "is_import_installed",
    "import_module",
    "to_dict",
)


def copy(obj: T, /, *, deep: bool = True, num: int = 1) -> T | list[T]:
    if num < 1:
        raise ValueError("Number of copies must be at least 1")

    copy_func = _copy.deepcopy if deep else _copy.copy
    return [copy_func(obj) for _ in range(num)] if num > 1 else copy_func(obj)


def is_same_dtype(
    input_: list[T] | dict[Any, T],
    dtype: type | None = None,
    return_dtype: bool = False,
) -> bool | tuple[bool, type | None]:
    if not input_:
        # If empty, trivially true. dtype is None since no elements exist.
        return (True, None) if return_dtype else True

    if isinstance(input_, Mapping):
        # For dictionaries, use values
        values_iter = iter(input_.values())
        first_val = next(values_iter, None)
        if dtype is None:
            dtype = type(first_val) if first_val is not None else None
        # Check the first element
        result = (dtype is None or isinstance(first_val, dtype)) and all(
            isinstance(v, dtype) for v in values_iter
        )
    else:
        # For lists (or list-like), directly access the first element
        first_val = input_[0]
        if dtype is None:
            dtype = type(first_val) if first_val is not None else None
        # Check all elements including the first
        result = all(isinstance(e, dtype) for e in input_)

    return (result, dtype) if return_dtype else result


def is_union_type(tp) -> bool:
    """True for typing.Union[...] and PEP 604 unions (A | B)."""
    origin = get_origin(tp)
    return origin is Union or origin is getattr(
        types, "UnionType", object()
    )  # Py3.10+


NoneType = type(None)
_UnionType = getattr(types, "UnionType", None)  # for A | B (PEP 604)


def _unwrap_annotated(tp):
    while get_origin(tp) is Annotated:
        tp = get_args(tp)[0]
    return tp


def union_members(
    tp, *, unwrap_annotated: bool = True, drop_none: bool = False
) -> tuple[type, ...]:
    """Return the member types of a Union (typing.Union or A|B). Empty tuple if not a Union."""
    tp = _unwrap_annotated(tp) if unwrap_annotated else tp
    origin = get_origin(tp)
    if origin is not Union and origin is not _UnionType:
        return ()
    members = get_args(tp)
    if unwrap_annotated:
        members = tuple(_unwrap_annotated(m) for m in members)
    if drop_none:
        members = tuple(m for m in members if m is not NoneType)
    return members


def create_path(
    directory: Path | str,
    filename: str,
    extension: str = None,
    timestamp: bool = False,
    dir_exist_ok: bool = True,
    file_exist_ok: bool = False,
    time_prefix: bool = False,
    timestamp_format: str | None = None,
    random_hash_digits: int = 0,
) -> Path:
    """
    Generate a new file path with optional timestamp and a random suffix.

    Args:
        directory: The directory where the file will be created.
        filename: The base name of the file to create.
        extension: The file extension, if not part of filename.
        timestamp: If True, add a timestamp to the filename.
        dir_exist_ok: If True, don't error if directory exists.
        file_exist_ok: If True, allow overwriting existing files.
        time_prefix: If True, timestamp is prefixed instead of suffixed.
        timestamp_format: Custom format for timestamp (default: "%Y%m%d%H%M%S").
        random_hash_digits: Number of hex digits for a random suffix.

    Returns:
        The full Path to the new or existing file.

    Raises:
        ValueError: If filename is invalid.
        FileExistsError: If file exists and file_exist_ok=False.
    """
    if "/" in filename:
        sub_dir, filename = filename.split("/")[:-1], filename.split("/")[-1]
        directory = Path(directory) / "/".join(sub_dir)

    if "\\" in filename:
        raise ValueError("Filename cannot contain directory separators.")

    directory = Path(directory)

    # Extract name and extension from filename if present
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
    else:
        name, ext = filename, extension

    # Ensure extension has a single leading dot
    ext = f".{ext.lstrip('.')}" if ext else ""

    # Add timestamp if requested
    if timestamp:
        ts_str = datetime.now().strftime(timestamp_format or "%Y%m%d%H%M%S")
        name = f"{ts_str}_{name}" if time_prefix else f"{name}_{ts_str}"

    # Add random suffix if requested
    if random_hash_digits > 0:
        # Use UUID4 and truncate its hex for random suffix
        random_suffix = uuid.uuid4().hex[:random_hash_digits]
        name = f"{name}-{random_suffix}"

    full_path = directory / f"{name}{ext}"

    # Check if file or directory existence
    full_path.parent.mkdir(parents=True, exist_ok=dir_exist_ok)
    if full_path.exists() and not file_exist_ok:
        raise FileExistsError(
            f"File {full_path} already exists and file_exist_ok is False."
        )

    return full_path


def get_bins(input_: list[str], upper: int) -> list[list[int]]:
    """Organizes indices of strings into bins based on a cumulative upper limit.

    Args:
        input_ (List[str]): The list of strings to be binned.
        upper (int): The cumulative length upper limit for each bin.

    Returns:
        List[List[int]]: A list of bins, each bin is a list of indices from the input list.
    """
    current = 0
    bins = []
    current_bin = []
    for idx, item in enumerate(input_):
        if current + len(item) < upper:
            current_bin.append(idx)
            current += len(item)
        else:
            bins.append(current_bin)
            current_bin = [idx]
            current = len(item)
    if current_bin:
        bins.append(current_bin)
    return bins
