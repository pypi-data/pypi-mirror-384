"""
Base Agent Interface for OS Forge
Defines the common interface that all OS-specific agents must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class AgentStatus(str, Enum):
    """Agent status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class RuleStatus(str, Enum):
    """Rule execution status"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class RuleResult:
    """Result of a rule execution"""
    rule_id: str
    description: str
    status: RuleStatus
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class AgentInfo:
    """Agent information and capabilities"""
    agent_id: str
    os_type: str
    os_version: str
    architecture: str
    capabilities: List[str]
    status: AgentStatus
    last_heartbeat: datetime
    version: str


class BaseAgent(ABC):
    """
    Abstract base class for all OS-specific agents
    
    This defines the common interface that all agents must implement
    to ensure consistency and interoperability across different operating systems.
    """
    
    def __init__(self, agent_id: str = "default"):
        self.agent_id = agent_id
        self._status = AgentStatus.UNKNOWN
        self._last_heartbeat = datetime.utcnow()
    
    @property
    @abstractmethod
    def os_type(self) -> str:
        """Return the operating system type (e.g., 'linux', 'windows')"""
        pass
    
    @property
    @abstractmethod
    def os_version(self) -> str:
        """Return the operating system version"""
        pass
    
    @property
    @abstractmethod
    def architecture(self) -> str:
        """Return the system architecture"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    @property
    def status(self) -> AgentStatus:
        """Return current agent status"""
        return self._status
    
    @property
    def last_heartbeat(self) -> datetime:
        """Return last heartbeat timestamp"""
        return self._last_heartbeat
    
    @abstractmethod
    def health_check(self) -> AgentStatus:
        """
        Perform agent health check
        
        Returns:
            AgentStatus: Current health status
        """
        pass
    
    @abstractmethod
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        Execute a system command safely
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        pass
    
    @abstractmethod
    def check_rule(self, rule: Dict[str, Any]) -> RuleResult:
        """
        Check if a hardening rule is currently satisfied
        
        Args:
            rule: Rule definition dictionary
            
        Returns:
            RuleResult: Result of the check
        """
        pass
    
    @abstractmethod
    def remediate_rule(self, rule: Dict[str, Any], dry_run: bool = True) -> RuleResult:
        """
        Apply a hardening rule remediation
        
        Args:
            rule: Rule definition dictionary
            dry_run: If True, only simulate the action
            
        Returns:
            RuleResult: Result of the remediation
        """
        pass
    
    @abstractmethod
    def rollback_rule(self, rule: Dict[str, Any], rollback_data: Dict[str, Any]) -> RuleResult:
        """
        Rollback a previously applied rule
        
        Args:
            rule: Rule definition dictionary
            rollback_data: Data needed for rollback
            
        Returns:
            RuleResult: Result of the rollback
        """
        pass
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dict containing system information
        """
        pass
    
    def update_heartbeat(self):
        """Update the last heartbeat timestamp"""
        self._last_heartbeat = datetime.utcnow()
        self._status = self.health_check()
    
    def get_agent_info(self) -> AgentInfo:
        """Get complete agent information"""
        return AgentInfo(
            agent_id=self.agent_id,
            os_type=self.os_type,
            os_version=self.os_version,
            architecture=self.architecture,
            capabilities=self.capabilities,
            status=self.status,
            last_heartbeat=self.last_heartbeat,
            version="1.0.0"
        )
    
    def validate_rule(self, rule: Dict[str, Any]) -> bool:
        """
        Validate that a rule is compatible with this agent
        
        Args:
            rule: Rule definition dictionary
            
        Returns:
            bool: True if rule is compatible
        """
        required_fields = ['id', 'description', 'os', 'severity', 'level']
        
        # Check required fields
        for field in required_fields:
            if field not in rule:
                return False
        
        # Check OS compatibility
        rule_os = rule.get('os', [])
        if isinstance(rule_os, str):
            rule_os = [rule_os]
        
        return self.os_type in rule_os or 'linux' in rule_os or 'windows' in rule_os
