"""
Windows Agent for OS Forge

Implements the BaseAgent interface for Windows systems.
Provides Windows-specific hardening capabilities including:
- Group Policy management
- Registry security configuration
- Windows Defender configuration
- BitLocker management
- User Account Control (UAC)
- Windows Firewall management
- Service management
- Event log analysis
"""

import logging
import time
import platform
import subprocess
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Windows-specific imports (only available on Windows)
try:
    import winreg
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    winreg = None

from ..common.base_agent import BaseAgent, AgentStatus, RuleStatus, RuleResult, AgentInfo
from ..common.command_executor import CommandExecutor
from ..common.os_detector import OSDetector


class WindowsAgent(BaseAgent):
    """
    Windows-specific agent for system hardening
    
    Implements all BaseAgent methods with Windows-specific logic
    """
    
    def __init__(self, agent_id: str = "windows-agent"):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        self.command_executor = CommandExecutor(self.logger)
        self.os_detector = OSDetector(self.logger)
        self._os_info = self.os_detector.detect_os()
        
        # Check if we're actually on Windows
        self._is_windows = platform.system().lower() == "windows" and WINDOWS_AVAILABLE
        
        # Windows-specific capabilities
        self._windows_capabilities = self._detect_windows_capabilities()
        
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
        
        # Add Windows-specific capabilities
        for cap, enabled in self._windows_capabilities.items():
            if enabled:
                capabilities.append(cap)
        
        return capabilities
    
    def _detect_windows_capabilities(self) -> Dict[str, bool]:
        """Detect Windows-specific capabilities"""
        capabilities = {
            'group_policy': False,
            'registry_management': False,
            'windows_defender': False,
            'bitlocker': False,
            'uac_management': False,
            'windows_firewall': False,
            'powershell': False,
            'wmi': False,
            'event_logs': False,
            'active_directory': False,
            'wsus': False,
            'windows_update': False
        }
        
        # If not on Windows, return all False
        if not self._is_windows:
            self.logger.info("Not running on Windows - capabilities will be limited")
            return capabilities
        
        try:
            # Check for PowerShell
            result = subprocess.run(['powershell', '-Command', 'Get-Host'], 
                                  capture_output=True, timeout=5)
            capabilities['powershell'] = result.returncode == 0
            
            # Check for Group Policy
            try:
                if winreg:
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft")
                    capabilities['group_policy'] = True
            except:
                pass
            
            # Check for Windows Defender
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-MpComputerStatus'], 
                                      capture_output=True, timeout=5)
                capabilities['windows_defender'] = result.returncode == 0
            except:
                pass
            
            # Check for BitLocker
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-BitLockerVolume'], 
                                      capture_output=True, timeout=5)
                capabilities['bitlocker'] = result.returncode == 0
            except:
                pass
            
            # Check for Windows Firewall
            try:
                result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                                      capture_output=True, timeout=5)
                capabilities['windows_firewall'] = result.returncode == 0
            except:
                pass
            
            # Check for UAC
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLUA"'], 
                                      capture_output=True, timeout=5)
                capabilities['uac_management'] = result.returncode == 0
            except:
                pass
            
            # Check for WMI
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-WmiObject -Class Win32_OperatingSystem'], 
                                      capture_output=True, timeout=5)
                capabilities['wmi'] = result.returncode == 0
            except:
                pass
            
            # Check for Event Logs
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-EventLog -List'], 
                                      capture_output=True, timeout=5)
                capabilities['event_logs'] = result.returncode == 0
            except:
                pass
            
            # Check for Windows Update
            try:
                result = subprocess.run(['powershell', '-Command', 'Get-WindowsUpdate'], 
                                      capture_output=True, timeout=5)
                capabilities['windows_update'] = result.returncode == 0
            except:
                pass
            
            # Registry management is available on Windows
            capabilities['registry_management'] = self._is_windows
            
        except Exception as e:
            self.logger.warning(f"Error detecting Windows capabilities: {e}")
        
        return capabilities
    
    def health_check(self) -> AgentStatus:
        """
        Perform agent health check
        
        Returns:
            AgentStatus: Current health status
        """
        try:
            if not self._is_windows:
                # On non-Windows systems, just check if we can execute basic commands
                stdout, stderr, return_code = self.command_executor.execute(
                    'echo "Windows agent running on non-Windows system"', 
                    timeout=5
                )
                return AgentStatus.HEALTHY if return_code == 0 else AgentStatus.UNHEALTHY
            
            # Check if we can execute PowerShell commands
            stdout, stderr, return_code = self.command_executor.execute(
                'powershell -Command "Get-ComputerInfo | Select-Object WindowsProductName"', 
                timeout=10
            )
            
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
    
    def execute_powershell(self, script: str, timeout: int = 30) -> Tuple[str, str, int]:
        """
        Execute a PowerShell script safely
        
        Args:
            script: PowerShell script to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        command = f'powershell -Command "{script}"'
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
            if rule.get('check_type') == 'powershell':
                stdout, stderr, return_code = self.execute_powershell(
                    rule['check'], 
                    timeout=30
                )
            else:
                stdout, stderr, return_code = self.command_executor.execute(
                    rule['check'], 
                    timeout=30
                )
            
            old_value = stdout.strip()
            expected = rule.get('expected', '')
            
            # Determine if rule is satisfied
            if old_value == expected or (expected and expected in old_value):
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
            if rule.get('remediate_type') == 'powershell':
                stdout, stderr, return_code = self.execute_powershell(
                    rule['remediate'],
                    timeout=60
                )
            else:
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
                'rollback_type': rule.get('rollback_type', 'command'),
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
            rollback_type = rollback_data.get('rollback_type', 'command')
            
            if not rollback_command:
                return RuleResult(
                    rule_id=rule['id'],
                    description=rule['description'],
                    status=RuleStatus.ERROR,
                    error="No rollback command available",
                    execution_time=time.time() - start_time
                )
            
            # Execute rollback command
            if rollback_type == 'powershell':
                stdout, stderr, return_code = self.execute_powershell(
                    rollback_command,
                    timeout=60
                )
            else:
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
            'windows_capabilities': self._windows_capabilities,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_windows_specific_info(self) -> Dict[str, Any]:
        """
        Get Windows-specific system information
        
        Returns:
            Dict containing Windows-specific information
        """
        info = {
            'windows_version': platform.version(),
            'windows_release': platform.release(),
            'windows_edition': self._get_windows_edition(),
            'capabilities': self._windows_capabilities,
            'powershell_version': self._get_powershell_version(),
            'dotnet_version': self._get_dotnet_version()
        }
        
        # Get additional system info via PowerShell
        try:
            # Get computer info
            stdout, _, _ = self.execute_powershell("Get-ComputerInfo | Select-Object TotalPhysicalMemory, CsProcessors, WindowsProductName")
            info['computer_info'] = stdout.strip()
            
            # Get installed features
            stdout, _, _ = self.execute_powershell("Get-WindowsFeature | Where-Object InstallState -eq 'Installed' | Select-Object Name")
            info['installed_features'] = stdout.strip()
            
        except Exception as e:
            self.logger.warning(f"Could not gather additional Windows info: {e}")
        
        return info
    
    def _get_windows_edition(self) -> str:
        """Get Windows edition"""
        try:
            stdout, _, _ = self.execute_powershell("(Get-ComputerInfo).WindowsProductName")
            return stdout.strip()
        except:
            return "Unknown"
    
    def _get_powershell_version(self) -> str:
        """Get PowerShell version"""
        try:
            stdout, _, _ = self.execute_powershell("Get-Host | Select-Object Version")
            return stdout.strip()
        except:
            return "Unknown"
    
    def _get_dotnet_version(self) -> str:
        """Get .NET version"""
        try:
            stdout, _, _ = self.execute_powershell("Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full\\' -Name Release")
            return stdout.strip()
        except:
            return "Unknown"
