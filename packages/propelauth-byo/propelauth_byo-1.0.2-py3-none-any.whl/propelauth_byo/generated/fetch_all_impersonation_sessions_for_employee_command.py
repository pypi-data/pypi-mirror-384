"""Auto-generated from TypeScript type: FetchAllImpersonationSessionsForEmployeeCommand"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class FetchAllImpersonationSessionsForEmployeeCommand:
    employee_email: str

    def _to_request(self) -> Dict[str, Any]:
        """Convert dataclass to request format with camelCase field names."""
        data: Dict[str, Any] = {}
        data["employeeEmail"] = self.employee_email
        return data