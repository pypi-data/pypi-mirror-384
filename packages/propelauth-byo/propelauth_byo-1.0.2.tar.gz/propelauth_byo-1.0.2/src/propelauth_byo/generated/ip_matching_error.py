"""Auto-generated from TypeScript type: IpMatchingError"""
from dataclasses import dataclass
from typing import Dict, Any, Literal, Union, List, Optional


@dataclass
class IpMatchingErrorIpOnBlocklist:
    ip: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["ip"] = self.ip
        return data



@dataclass
class IpMatchingErrorIpNotOnAllowlist:
    ip: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["ip"] = self.ip
        return data



@dataclass
class IpMatchingErrorIpAddressNotSpecified:
    pass

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        return data



@dataclass
class IpMatchingErrorCannotParseIpAddress:
    ip: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["ip"] = self.ip
        return data




IpMatchingError = Union[
    IpMatchingErrorIpOnBlocklist,
    IpMatchingErrorIpNotOnAllowlist,
    IpMatchingErrorIpAddressNotSpecified,
    IpMatchingErrorCannotParseIpAddress
]

# Export all types for client imports
__all__ = [
    'IpMatchingError',
    'IpMatchingErrorIpOnBlocklist',
    'IpMatchingErrorIpNotOnAllowlist',
    'IpMatchingErrorIpAddressNotSpecified',
    'IpMatchingErrorCannotParseIpAddress',
]

# Re-export UnexpectedErrorDetails if it was imported
