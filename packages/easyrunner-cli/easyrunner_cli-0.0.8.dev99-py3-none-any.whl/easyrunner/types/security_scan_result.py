from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Literal, Optional

from ..types.dto_base import DTOBase


@dataclass
class SecurityCheckResult(DTOBase):
    """Result of a single security check."""
    
    check_name: str
    passed: bool
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    details: Optional[str] = None
    remediation: Optional[str] = None
    category: Optional[str] = None


@dataclass
class WebSecurityScanResult(DTOBase):
    """Complete result of a web security scan."""
    
    target_url: str
    timestamp: str
    checks: List[SecurityCheckResult]
    summary: Dict[str, int]  # counts by severity level
    total_checks: int
    passed_checks: int
    failed_checks: int
    
    @classmethod
    def create(
        cls,
        target_url: str,
        checks: List[SecurityCheckResult]
    ) -> "WebSecurityScanResult":
        """Create a WebSecurityScanResult with calculated summary statistics."""
        summary = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for check in checks:
            if not check.passed:
                summary[check.severity] += 1
        
        return cls(
            target_url=target_url,
            timestamp=datetime.now().isoformat(),
            checks=checks,
            summary=summary,
            total_checks=len(checks),
            passed_checks=sum(1 for check in checks if check.passed),
            failed_checks=sum(1 for check in checks if not check.passed)
        )
