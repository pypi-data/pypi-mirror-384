"""Auto-generated from TypeScript type: JwkKey"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class JwkKey:
    kty: str
    kid: str
    use: str
    alg: str
    n: str
    e: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["kty"] = self.kty
        data["kid"] = self.kid
        data["use"] = self.use
        data["alg"] = self.alg
        data["n"] = self.n
        data["e"] = self.e
        return data