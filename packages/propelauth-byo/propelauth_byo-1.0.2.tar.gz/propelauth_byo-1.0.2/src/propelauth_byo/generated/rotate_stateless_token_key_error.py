"""Auto-generated from TypeScript type: RotateStatelessTokenKeyError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional
from .unexpected_error_details import UnexpectedErrorDetails


@dataclass
class RotateStatelessTokenKeyErrorRotationFailed:
    details: str
    type: Literal["RotationFailed"] = "RotationFailed"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class RotateStatelessTokenKeyErrorInvalidParameters:
    details: str
    type: Literal["InvalidParameters"] = "InvalidParameters"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data



@dataclass
class RotateStatelessTokenKeyErrorUnexpectedError:
    details: UnexpectedErrorDetails
    type: Literal["UnexpectedError"] = "UnexpectedError"

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["details"] = self.details
        data["type"] = self.type
        return data




RotateStatelessTokenKeyError = Union[
    RotateStatelessTokenKeyErrorRotationFailed,
    RotateStatelessTokenKeyErrorInvalidParameters,
    RotateStatelessTokenKeyErrorUnexpectedError
]

# Export all types for client imports
__all__ = [
    'RotateStatelessTokenKeyError',
    'RotateStatelessTokenKeyErrorRotationFailed',
    'RotateStatelessTokenKeyErrorInvalidParameters',
    'RotateStatelessTokenKeyErrorUnexpectedError',
]

# Re-export UnexpectedErrorDetails if it was imported
__all__.append('UnexpectedErrorDetails')
