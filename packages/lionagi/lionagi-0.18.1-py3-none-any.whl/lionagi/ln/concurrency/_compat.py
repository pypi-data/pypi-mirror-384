"""Compatibility layer for Python 3.10+ support.

Provides ExceptionGroup backport and other compatibility utilities.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence

# ExceptionGroup compatibility for Python 3.10
if sys.version_info >= (3, 11):
    # Python 3.11+ has built-in ExceptionGroup
    from builtins import ExceptionGroup as _ExceptionGroup

    BaseExceptionGroup = _ExceptionGroup
    ExceptionGroup = _ExceptionGroup

else:
    # Python 3.10: Use exceptiongroup backport
    try:
        from exceptiongroup import BaseExceptionGroup, ExceptionGroup
    except ImportError:
        # Fallback implementation for environments without exceptiongroup
        class BaseExceptionGroup(BaseException):  # type: ignore
            """Minimal BaseExceptionGroup implementation for Python 3.10 without exceptiongroup."""

            def __init__(
                self, message: str, exceptions: Sequence[BaseException]
            ) -> None:
                super().__init__(message)
                self.message = message
                self.exceptions = tuple(exceptions)

            def __str__(self) -> str:
                return (
                    f"{self.message} ({len(self.exceptions)} sub-exceptions)"
                )

        class ExceptionGroup(BaseExceptionGroup, Exception):  # type: ignore
            """Minimal ExceptionGroup implementation for Python 3.10 without exceptiongroup."""

            pass


def is_exception_group(exc: BaseException) -> bool:
    """Check if exception is an ExceptionGroup (compatible across Python versions)."""
    return isinstance(exc, BaseExceptionGroup)


def get_exception_group_exceptions(
    exc: BaseException,
) -> Sequence[BaseException]:
    """Get exceptions from ExceptionGroup, or return single exception in list."""
    if is_exception_group(exc):
        return getattr(exc, "exceptions", (exc,))
    return (exc,)


__all__ = [
    "BaseExceptionGroup",
    "ExceptionGroup",
    "is_exception_group",
    "get_exception_group_exceptions",
]
