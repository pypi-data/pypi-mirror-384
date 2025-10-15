"""
macOS Agent for OS Forge

Implements the BaseAgent interface for macOS systems.
Provides macOS-specific hardening capabilities including:
- System Preferences management
- FileVault encryption
- Firewall configuration
- Gatekeeper settings
- Privacy controls
- Network security
- User account security
- System Integrity Protection
"""

import logging
import time
import platform
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from ..common.base_agent import BaseAgent, AgentStatus, RuleStatus, RuleResult, AgentInfo
from ..common.command_executor import CommandExecutor
from ..common.os_detector import OSDetector


class MacOSAgent(BaseAgent):
    """
    macOS-specific agent for system hardening
    
    Implements all BaseAgent methods with macOS-specific logic
    """
    
    def __init__(self, agent_id: str = "macos-agent"):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        self.command_executor = CommandExecutor(self.logger)
        self.os_detector = OSDetector(self.logger)
        self._os_info = self.os_detector.detect_os()
        
        # Check if we're actually on macOS
        self._is_macos = platform.system().lower() == "darwin"
        
        # macOS-specific capabilities
        self._macos_capabilities = self._detect_macos_capabilities()
        
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
        capabilities = ['file_management', 'user_management', 'system_preferences']
        
        # Add macOS-specific capabilities
        for cap, enabled in self._macos_capabilities.items():
            if enabled:
                capabilities.append(cap)
        
        return capabilities
    
    def _detect_macos_capabilities(self) -> Dict[str, bool]:
        """Detect macOS-specific capabilities"""
        capabilities = {
            'filevault': False,
            'gatekeeper': False,
            'firewall': False,
            'sip': False,
            'launchctl': False,
            'defaults': False,
            'networksetup': False,
            'spctl': False,
            'fdesetup': False
        }
        
        if not self._is_macos:
            return capabilities
        
        # Check for FileVault
        try:
            stdout, stderr, return_code = self.command_executor.execute("which fdesetup")
            capabilities['filevault'] = return_code == 0
        except Exception:
            pass
        
        # Check for Gatekeeper
        try:
            stdout, stderr, return_code = self.command_executor.execute("which spctl")
            capabilities['gatekeeper'] = return_code == 0
        except Exception:
            pass
        
        # Check for Firewall (Application Layer Firewall)
        try:
            stdout, stderr, return_code = self.command_executor.execute("which pfctl")
            capabilities['firewall'] = return_code == 0
        except Exception:
            pass
        
        # Check for SIP
        try:
            stdout, stderr, return_code = self.command_executor.execute("which csrutil")
            capabilities['sip'] = return_code == 0
        except Exception:
            pass
        
        # Check for launchctl
        try:
            stdout, stderr, return_code = self.command_executor.execute("which launchctl")
            capabilities['launchctl'] = return_code == 0
        except Exception:
            pass
        
        # Check for defaults
        try:
            stdout, stderr, return_code = self.command_executor.execute("which defaults")
            capabilities['defaults'] = return_code == 0
        except Exception:
            pass
        
        # Check for networksetup
        try:
            stdout, stderr, return_code = self.command_executor.execute("which networksetup")
            capabilities['networksetup'] = return_code == 0
        except Exception:
            pass
        
        return capabilities
    
    def health_check(self) -> AgentStatus:
        """
        Perform macOS agent health check
        
        Returns:
            AgentStatus: Current health status
        """
        try:
            # Check if we're on macOS
            if not self._is_macos:
                self._status = AgentStatus.ERROR
                return self._status
            
            # Check basic macOS commands
            stdout, stderr, return_code = self.command_executor.execute("uname -s")
            if return_code != 0 or "Darwin" not in stdout:
                self._status = AgentStatus.ERROR
                return self._status
            
            # Check if we can execute basic commands
            stdout, stderr, return_code = self.command_executor.execute("sw_vers -productName")
            if return_code != 0:
                self._status = AgentStatus.ERROR
                return self._status
            
            self._status = AgentStatus.HEALTHY
            self.update_heartbeat()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self._status = AgentStatus.ERROR
        
        return self._status
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        Execute a macOS command safely
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        return self.command_executor.execute(command, timeout)
    
    def check_rule(self, rule: Dict[str, Any]) -> RuleResult:
        """
        Check if a macOS hardening rule is compliant
        
        Args:
            rule: Rule dictionary containing check information
            
        Returns:
            RuleResult: Result of the rule check
        """
        try:
            if not self._is_macos:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="Not on macOS",
                    new_value="N/A",
                    error="Rule not compatible with this agent"
                )
            
            check_info = rule.get("check", {})
            if not check_info:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No check information provided"
                )
            
            command = check_info.get("command")
            expected = check_info.get("expected")
            
            if not command:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No check command provided"
                )
            
            # Execute the check command
            stdout, stderr, return_code = self.execute_command(command)
            
            if return_code != 0:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value=stderr.strip(),
                    new_value="N/A",
                    error=f"Command failed with return code {return_code}"
                )
            
            current_value = stdout.strip()
            
            # Check if the result matches expected value
            if expected is not None:
                if current_value == expected:
                    status = RuleStatus.PASS
                else:
                    status = RuleStatus.FAIL
            else:
                # If no expected value, assume non-empty output means pass
                status = RuleStatus.PASS if current_value else RuleStatus.FAIL
            
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=status,
                old_value=current_value,
                new_value=expected or "N/A",
                error=None
            )
            
        except Exception as e:
            self.logger.error(f"Error checking rule {rule['id']}: {e}")
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.ERROR,
                old_value="N/A",
                new_value="N/A",
                error=str(e)
            )
    
    def remediate_rule(self, rule: Dict[str, Any], dry_run: bool = True) -> RuleResult:
        """
        Remediate a macOS hardening rule
        
        Args:
            rule: Rule dictionary containing remediation information
            dry_run: If True, only simulate the remediation
            
        Returns:
            RuleResult: Result of the remediation
        """
        try:
            if not self._is_macos:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="Not on macOS",
                    new_value="N/A",
                    error="Rule not compatible with this agent"
                )
            
            remediate_info = rule.get("remediate", {})
            if not remediate_info:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No remediation information provided"
                )
            
            command = remediate_info.get("command")
            if not command:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No remediation command provided"
                )
            
            if dry_run:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.PASS,
                    old_value="Dry run - no changes made",
                    new_value="Would execute remediation",
                    error=None
                )
            
            # Execute the remediation command
            stdout, stderr, return_code = self.execute_command(command)
            
            if return_code != 0:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error=f"Remediation failed with return code {return_code}: {stderr}"
                )
            
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.PASS,
                old_value="Remediation executed",
                new_value=stdout.strip() or "Success",
                error=None
            )
            
        except Exception as e:
            self.logger.error(f"Error remediating rule {rule['id']}: {e}")
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.ERROR,
                old_value="N/A",
                new_value="N/A",
                error=str(e)
            )
    
    def rollback_rule(self, rule: Dict[str, Any], rollback_data: Optional[Dict[str, Any]] = None) -> RuleResult:
        """
        Rollback a macOS hardening rule
        
        Args:
            rule: Rule dictionary containing rollback information
            
        Returns:
            RuleResult: Result of the rollback
        """
        try:
            if not self._is_macos:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="Not on macOS",
                    new_value="N/A",
                    error="Rule not compatible with this agent"
                )
            
            rollback_info = rule.get("rollback", {})
            if not rollback_info:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No rollback information provided"
                )
            
            command = rollback_info.get("command")
            if not command:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error="No rollback command provided"
                )
            
            # Execute the rollback command
            stdout, stderr, return_code = self.execute_command(command)
            
            if return_code != 0:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error=f"Rollback failed with return code {return_code}: {stderr}"
                )
            
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.PASS,
                old_value="Rollback executed",
                new_value=stdout.strip() or "Success",
                error=None
            )
            
        except Exception as e:
            self.logger.error(f"Error rolling back rule {rule['id']}: {e}")
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.ERROR,
                old_value="N/A",
                new_value="N/A",
                error=str(e)
            )
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive macOS system information
        
        Returns:
            Dict containing system information
        """
        try:
            system_info = {
                "os_type": self.os_type,
                "os_version": self.os_version,
                "architecture": self.architecture,
                "capabilities": self.capabilities,
                "macos_capabilities": self._macos_capabilities,
                "is_macos": self._is_macos
            }
            
            # Get additional macOS-specific info
            if self._is_macos:
                try:
                    # Get macOS version details
                    stdout, stderr, return_code = self.execute_command("sw_vers")
                    if return_code == 0:
                        for line in stdout.split('\n'):
                            if 'ProductName:' in line:
                                system_info['product_name'] = line.split(':', 1)[1].strip()
                            elif 'ProductVersion:' in line:
                                system_info['product_version'] = line.split(':', 1)[1].strip()
                            elif 'BuildVersion:' in line:
                                system_info['build_version'] = line.split(':', 1)[1].strip()
                    
                    # Get hardware info
                    stdout, stderr, return_code = self.execute_command("system_profiler SPHardwareDataType")
                    if return_code == 0:
                        system_info['hardware_info'] = stdout
                    
                    # Get security status
                    stdout, stderr, return_code = self.execute_command("fdesetup status")
                    if return_code == 0:
                        system_info['filevault_status'] = stdout.strip()
                    
                    # Get SIP status
                    stdout, stderr, return_code = self.execute_command("csrutil status")
                    if return_code == 0:
                        system_info['sip_status'] = stdout.strip()
                        
                except Exception as e:
                    self.logger.warning(f"Could not get additional macOS info: {e}")
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {
                "os_type": self.os_type,
                "os_version": "unknown",
                "architecture": "unknown",
                "capabilities": [],
                "error": str(e)
            }
    
    def get_agent_info(self) -> AgentInfo:
        """
        Get comprehensive agent information
        
        Returns:
            AgentInfo: Detailed agent information
        """
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
    
    def update_heartbeat(self):
        """Update the last heartbeat timestamp"""
        self._last_heartbeat = datetime.utcnow()
