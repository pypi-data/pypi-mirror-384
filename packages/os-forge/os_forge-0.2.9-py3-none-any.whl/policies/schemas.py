"""
Pydantic Schemas for OS Forge

Data validation and serialization models.
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel


class SeverityLevel(str, Enum):
    """Security rule severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HardeningLevel(str, Enum):
    """System hardening levels"""
    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"


class RuleResult(BaseModel):
    """Result of executing a hardening rule"""
    rule_id: str
    description: str
    severity: SeverityLevel
    status: str  # pass, fail, error
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    error: Optional[str] = None


class RunRequest(BaseModel):
    """Request model for running hardening rules"""
    level: HardeningLevel = HardeningLevel.BASIC
    dry_run: bool = True
    os_filter: Optional[str] = None


class RuleSchema(BaseModel):
    """Schema for validating hardening rule definitions"""
    id: str
    description: str
    os: Union[str, List[str]]
    severity: SeverityLevel
    level: List[HardeningLevel]
    check: str
    remediate: str
    rollback: str
    expected: str
    
    class Config:
        # Validate assignment to prevent injection
        validate_assignment = True
        
    def validate_commands(self):
        """Additional validation for command safety"""
        dangerous_patterns = [
            'rm -rf', 'del /f', 'format', 'mkfs', 'dd if=', 
            'wget', 'curl', 'nc ', 'netcat', 'python -c',
            'eval', 'exec', '$(', '`'
        ]
        
        for cmd in [self.check, self.remediate, self.rollback]:
            cmd_lower = cmd.lower()
            for pattern in dangerous_patterns:
                if pattern in cmd_lower:
                    raise ValueError(f"Dangerous command pattern detected: {pattern} in {cmd}")
        
        return True

