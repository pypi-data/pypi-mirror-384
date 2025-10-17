"""Auto-generated from TypeScript type: CreateDeviceChallengeResponse"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CreateDeviceChallengeResponse:
    device_challenge: str
    expires_at: int

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["deviceChallenge"] = self.device_challenge
        data["expiresAt"] = self.expires_at
        return data