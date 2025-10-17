"""Result type for handling success and error cases"""

from dataclasses import dataclass
from typing import Generic, TypeVar, Union
from typing_extensions import TypeIs

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Ok(Generic[T]):
    """Represents a successful result"""

    data: T


@dataclass
class Err(Generic[E]):
    """Represents an error result"""

    error: E


# Type alias for Result
Result = Union[Ok[T], Err[E]]


# Helper functions
def ok(data: T) -> Ok[T]:
    """Create a successful result"""
    return Ok(data=data)


def err(error: E) -> Err[E]:
    """Create an error result"""
    return Err(error=error)


def is_ok(result: Result[T, E]) -> TypeIs[Ok[T]]:
    """Check if a result is successful"""
    return isinstance(result, Ok)


def is_err(result: Result[T, E]) -> TypeIs[Err[E]]:
    """Check if a result is an error"""
    return isinstance(result, Err)
