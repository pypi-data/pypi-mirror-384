"""Shared type definitions for the PropelAuth client library"""

from typing import Optional, Dict, Any, Awaitable, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .result import Result


# Protocol for the request function used by all clients  
class RequestFunc(Protocol):
    async def __call__(
        self, 
        command: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        ...