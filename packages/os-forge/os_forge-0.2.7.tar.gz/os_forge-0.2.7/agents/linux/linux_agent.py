"""
Linux Agent for OS Forge

Implements the BaseAgent interface for Linux systems.
Provides Linux-specific hardening capabilities including:
- SSH configuration management
- Firewall management (UFW, iptables, firewalld)
- System service management
- Kernel parameter tuning
- File system security
- User and permission management
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..common.base_agent import BaseAgent, AgentStatus, RuleStatus, RuleResult, AgentInfo
from ..common.command_executor import CommandExecutor
from ..common.os_detector import OSDetector


class LinuxAgent(BaseAgent):
    """
    Linux-specific agent for system hardening
    
    Implements all BaseAgent methods with Linux-specific logic
    """
    
    def __init__(self, agent_id: str = "linux-agent"):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        self.command_executor = CommandExecutor(self.logger)
        self.os_detector = OSDetector(self.logger)
        self._os_info = self.os_detector.detect_os()
        
        # Update initial status
        self.update_heartbeat()
    
    @property
    def os_type(self) -> str:
        """Return the operating system type"""
        return self._os_info['type']
    
    @property
    def os_version(self) -> str:
        """Return the operating system version"""
        return self._os_info['version']
    
    @property
    def architecture(self) -> str:
        """Return the system architecture"""
        return self._os_info['architecture']
    
    @property
    def capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        capabilities = ['file_management', 'service_management', 'user_management']
        
        # Add OS-specific capabilities
        os_caps = self._os_info['capabilities']
        if os_caps['sudo']:
            capabilities.append('privilege_escalation')
        if os_caps['systemctl']:
            capabilities.append('systemd_management')
        if os_caps['ufw']:
            capabilities.append('ufw_firewall')
        if os_caps['iptables']:
            capabilities.append('iptables_firewall')
        if os_caps['firewalld']:
            capabilities.append('firewalld_firewall')
        if os_caps['selinux']:
            capabilities.append('selinux_management')
        if os_caps['apparmor']:
            capabilities.append('apparmor_management')
        if os_caps['docker']:
            capabilities.append('docker_management')
        
        return capabilities
    
    def health_check(self) -> AgentStatus:
        """
        Perform agent health check
        
        Returns:
            AgentStatus: Current health status
        """
        try:
            # Check if we can execute basic commands
            stdout, stderr, return_code = self.command_executor.execute("echo 'health_check'", timeout=5)
            
            if return_code == 0:
                return AgentStatus.HEALTHY
            else:
                self.logger.warning(f"Health check failed: {stderr}")
                return AgentStatus.UNHEALTHY
                
        except Exception as e:
            self.logger.error(f"Health check error: {str(e)}")
            return AgentStatus.UNHEALTHY
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        Execute a system command safely
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        return self.command_executor.execute(command, timeout)
    
    def check_rule(self, rule: Dict[str, Any]) -> RuleResult:
        """
        Check if a hardening rule is currently satisfied
        
        Args:
            rule: Rule definition dictionary
            
        Returns:
            RuleResult: Result of the check
        """
        start_time = time.time()
        
        try:
            # Validate rule compatibility
            if not self.validate_rule(rule):
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.ERROR,
                    error="Rule not compatible with this agent",
                    execution_time=time.time() - start_time
                )
            
            # Execute check command
            stdout, stderr, return_code = self.command_executor.execute(
                rule['check'], 
                timeout=30
            )
            
            old_value = stdout.strip()
            expected = rule.get('expected', '')
            
            # Determine if rule is satisfied
            if old_value == expected:
                status = RuleStatus.PASS
            else:
                status = RuleStatus.FAIL
            
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=status,
                old_value=old_value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=RuleStatus.ERROR,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def remediate_rule(self, rule: Dict[str, Any], dry_run: bool = True) -> RuleResult:
        """
        Apply a hardening rule remediation
        
        Args:
            rule: Rule definition dictionary
            dry_run: If True, only simulate the action
            
        Returns:
            RuleResult: Result of the remediation
        """
        start_time = time.time()
        
        try:
            # Validate rule compatibility
            if not self.validate_rule(rule):
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.ERROR,
                    error="Rule not compatible with this agent",
                    execution_time=time.time() - start_time
                )
            
            # First check current state
            check_result = self.check_rule(rule)
            old_value = check_result.old_value
            
            if check_result.status == RuleStatus.PASS:
                # Rule is already satisfied
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.PASS,
                    old_value=old_value,
                    new_value=old_value,
                    execution_time=time.time() - start_time
                )
            
            if dry_run:
                # Simulate remediation
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.FAIL,
                    old_value=old_value,
                    new_value="[DRY RUN] Would apply remediation",
                    execution_time=time.time() - start_time
                )
            
            # Apply remediation
            stdout, stderr, return_code = self.command_executor.execute(
                rule['remediate'],
                timeout=60
            )
            
            if return_code == 0:
                # Verify the change
                verify_result = self.check_rule(rule)
                new_value = verify_result.old_value
                
                if verify_result.status == RuleStatus.PASS:
                    status = RuleStatus.PASS
                else:
                    status = RuleStatus.FAIL
                    new_value = f"Remediation applied but verification failed: {new_value}"
            else:
                status = RuleStatus.ERROR
                new_value = f"Remediation failed: {stderr}"
            
            # Prepare rollback data
            rollback_data = {
                'original_value': old_value,
                'rollback_command': rule.get('rollback', ''),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=status,
                old_value=old_value,
                new_value=new_value,
                rollback_data=rollback_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=RuleStatus.ERROR,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def rollback_rule(self, rule: Dict[str, Any], rollback_data: Dict[str, Any]) -> RuleResult:
        """
        Rollback a previously applied rule
        
        Args:
            rule: Rule definition dictionary
            rollback_data: Data needed for rollback
            
        Returns:
            RuleResult: Result of the rollback
        """
        start_time = time.time()
        
        try:
            rollback_command = rollback_data.get('rollback_command', '')
            if not rollback_command:
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.ERROR,
                    error="No rollback command available",
                    execution_time=time.time() - start_time
                )
            
            # Execute rollback command
            stdout, stderr, return_code = self.command_executor.execute(
                rollback_command,
                timeout=60
            )
            
            if return_code == 0:
                # Verify rollback
                verify_result = self.check_rule(rule)
                status = RuleStatus.PASS if verify_result.status == RuleStatus.PASS else RuleStatus.FAIL
                new_value = verify_result.old_value
            else:
                status = RuleStatus.ERROR
                new_value = f"Rollback failed: {stderr}"
            
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=status,
                old_value=rollback_data.get('original_value', ''),
                new_value=new_value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status=RuleStatus.ERROR,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        
        Returns:
            Dict containing system information
        """
        return {
            'agent_info': self.get_agent_info(),
            'os_info': self._os_info,
            'capabilities': self.capabilities,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_linux_specific_info(self) -> Dict[str, Any]:
        """
        Get Linux-specific system information
        
        Returns:
            Dict containing Linux-specific information
        """
        info = {
            'distribution': self._os_info['distribution'],
            'kernel': self._os_info['kernel'],
            'package_manager': self._os_info['package_manager'],
            'capabilities': self._os_info['capabilities']
        }
        
        # Get additional system info
        try:
            # Memory info
            stdout, _, _ = self.command_executor.execute("free -h")
            info['memory'] = stdout.strip()
            
            # Disk usage
            stdout, _, _ = self.command_executor.execute("df -h")
            info['disk_usage'] = stdout.strip()
            
            # Running services
            if self._os_info['capabilities']['systemctl']:
                stdout, _, _ = self.command_executor.execute("systemctl list-units --state=running --no-pager")
                info['running_services'] = stdout.strip()
            
        except Exception as e:
            self.logger.warning(f"Could not gather additional system info: {e}")
        
        return info
