"""Auto-generated from TypeScript type: CreateStatelessTokenError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class CreateStatelessTokenErrorTokenCreationFailed:
    details: str
    type: Literal["TokenCreationFailed"] = "TokenCreationFailed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class CreateStatelessTokenErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




CreateStatelessTokenError = Union[
    CreateStatelessTokenErrorTokenCreationFailed,
    CreateStatelessTokenErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'CreateStatelessTokenError',
    'CreateStatelessTokenErrorTokenCreationFailed',
    'CreateStatelessTokenErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
