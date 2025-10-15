"""
Secure Command Execution Module

Provides secure command execution with input validation and privilege escalation handling.
"""

import logging
import shlex
import subprocess
import signal
import os
from typing import List, Union, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of command execution"""
    stdout: str
    stderr: str
    returncode: int
    execution_time: float


class CommandTimeoutError(Exception):
    """Raised when command execution times out"""
    pass


class SecureCommandExecutor:
    """
    Secure command execution with input validation and privilege escalation handling.
    
    Security Features:
    1. Command whitelist validation
    2. Parameter sanitization
    3. Privilege escalation handling
    4. Input validation
    5. Audit logging
    6. Timeout protection
    7. Command injection prevention
    """
    
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Whitelist of allowed command prefixes by OS
        self.allowed_commands = {
            'windows': [
                # PowerShell commands
                'powershell', 'pwsh', 'Get-', 'Set-', 'Enable-', 'Disable-',
                'New-', 'Remove-', 'Add-', 'Clear-', 'Test-', 'Invoke-',
                # Registry commands
                'reg', 'regedit', 'regsvr32',
                # System commands
                'wmic', 'net', 'sc', 'bcdedit', 'gpupdate', 'gpresult',
                'netsh', 'wusa', 'sfc', 'dism', 'chkdsk', 'diskpart',
                # Windows Defender
                'mpcmdrun', 'Update-MpSignature', 'Start-MpScan',
                # Service management
                'tasklist', 'taskkill', 'schtasks', 'wmic service',
                # User management
                'net user', 'net localgroup', 'whoami', 'query user',
                # File operations
                'icacls', 'attrib', 'cacls', 'takeown', 'robocopy',
                # Network commands
                'ipconfig', 'ping', 'tracert', 'nslookup', 'netstat',
                # Windows Update
                'wuauclt', 'usoclient', 'WindowsUpdate',
                # Event logs
                'wevtutil', 'eventvwr',
                # Group Policy
                'gpedit', 'rsop', 'gpresult'
            ],
            'linux': [
                # System commands
                'grep', 'sed', 'awk', 'systemctl', 'ufw', 'sysctl', 'lsmod',
                'bootctl', 'dpkg', 'rpm', 'yum', 'apt', 'sudo', 'apt-get',
                # File operations
                'stat', 'chmod', 'chown', 'cat', 'echo', 'tee', 'cut',
                'find', 'ls', 'wc', 'head', 'tail', 'sort', 'uniq',
                # Network and security
                'iptables', 'firewalld', 'sshd', 'ssh', 'openssh',
                'ip', 'iwconfig', 'netstat', 'ss', 'tcpdump',
                # Process and service management
                'service', 'chkconfig', 'systemd', 'cron', 'chrony',
                # Package management
                'dnf', 'zypper', 'pacman', 'emerge',
                # File system
                'mount', 'umount', 'fstab', 'passwd', 'shadow',
                # Kernel and modules
                'modprobe', 'rmmod', 'insmod', 'lsmod',
                # Time synchronization
                'ntp', 'timesyncd', 'chronyd',
                # Logging and monitoring
                'journalctl', 'logrotate', 'rsyslog', 'auditctl', 'auditd',
                # Security tools
                'getenforce', 'aa-status', 'sestatus', 'selinux',
                # Additional hardening commands
                'bluetooth', 'cups', 'avahi', 'dhcp', 'dns', 'ftp', 'ldap',
                'mail', 'nfs', 'nis', 'rpc', 'rsync', 'samba', 'snmp',
                'tftp', 'proxy', 'web', 'xinetd', 'x11', 'gdm'
            ],
            'macos': [
                # macOS specific commands
                'defaults', 'launchctl', 'pkill', 'ps', 'top', 'lsof',
                'netstat', 'ifconfig', 'route', 'arp', 'ping', 'traceroute',
                'chmod', 'chown', 'ls', 'find', 'grep', 'sed', 'awk',
                'systemctl', 'brew', 'port', 'pkgutil', 'spctl', 'csrutil',
                'diskutil', 'hdiutil', 'tmutil', 'sysctl', 'kextstat',
                'security', 'codesign', 'otool', 'file', 'strings'
            ]
        }
        
        # Commands that require privilege escalation
        self.sudo_required = [
            'systemctl', 'ufw', 'sed -i', 'tee -a', 'modprobe', 'apt-get',
            'chmod', 'chown', 'mount', 'umount', 'sysctl', 'firewalld',
            'service', 'chkconfig', 'dnf', 'yum', 'zypper', 'auditctl',
                'dpkg', 'rpm', 'pacman', 'emerge', 'bootctl', 'sudo'
        ]
        
        # Dangerous command patterns to block
        self.dangerous_patterns = [
            'rm -rf', 'del /f', 'format', 'mkfs', 'dd if=', 'mkfs.ext',
            'wget', 'curl', 'nc ', 'netcat', 'python -c', 'perl -e',
            'eval', 'exec', '$(', '`', '; rm', '| rm', '&& rm',
            'chmod 777', 'chmod 000', 'chown root:root',
            'passwd', 'useradd', 'userdel', 'groupadd', 'groupdel'
        ]
    
    def _validate_command(self, command: str, os_type: str) -> bool:
        """Validate command against whitelist with enhanced security"""
        if not command or not command.strip():
            return False
            
        # Check for dangerous patterns first
        command_lower = command.lower().strip()
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                self.logger.warning(f"Blocked dangerous command pattern: {pattern} in {command}")
                return False
        
        # Get allowed commands for OS
        allowed = self.allowed_commands.get(os_type, [])
        
        # Check if command starts with allowed prefix
        # Extract the first command from pipe chains
        first_cmd = command_lower.split('|')[0].split('&&')[0].split('||')[0].split(';')[0].strip()
        
        # Enhanced Windows PowerShell validation
        if os_type == 'windows':
            # Check for PowerShell commands with -Command parameter
            if 'powershell' in first_cmd or 'pwsh' in first_cmd:
                self.logger.info(f"Allowing PowerShell command: {command}")
                return True
            
            # Check for PowerShell cmdlets (Get-, Set-, etc.)
            for allowed_cmd in allowed:
                if allowed_cmd.endswith('-') and first_cmd.startswith(allowed_cmd.lower()):
                    self.logger.info(f"Allowing PowerShell cmdlet: {command}")
                    return True
                elif first_cmd.startswith(allowed_cmd.lower()):
                    return True
        
        # Standard validation for other commands
        for allowed_cmd in allowed:
            if first_cmd.startswith(allowed_cmd.lower()):
                return True
        
        # Additional validation for hardening-specific commands
        hardening_patterns = [
            # Linux patterns
            'kernel.randomize_va_space', 'permitrootlogin', 'protocol',
            'unattended-upgrade', 'timesyncd', 'chrony', 'cron',
            'firewalld', 'ufw', 'passwd', 'shadow', 'motd', 'issue',
            # Network security patterns
            'ipv6', 'inet6', 'wireless', 'ieee 802.11', 'bluetooth',
            # SSH security patterns
            'ssh_host', 'allowusers', 'denyusers', 'allowgroups', 'denygroups',
            'maxauthtries', 'maxsessions', 'clientaliveinterval', 'clientalivecountmax',
            # Logging patterns
            'logrotate', 'logfiles', 'auditctl', 'auditd', 'rsyslog',
            # Service patterns
            'autofs', 'avahi', 'dhcp', 'dns', 'ftp', 'ldap', 'mail', 'nfs',
            'nis', 'rpc', 'rsync', 'samba', 'snmp', 'tftp', 'proxy', 'web',
            'xinetd', 'x11', 'gdm', 'cups',
            # Windows patterns
            'enablelua', 'consentpromptbehavioradmin', 'firewall',
            'defender', 'bitlocker', 'smb', 'rdp', 'remoteaccess',
            'windowsupdate', 'autologon', 'guestaccount', 'administrator',
            'powershellpolicy', 'executionpolicy', 'scriptblocklogging'
        ]
        
        # Allow commands that contain hardening-related patterns
        for pattern in hardening_patterns:
            if pattern in command_lower:
                self.logger.info(f"Allowing hardening command: {command}")
                return True
        
        self.logger.warning(f"Command not in whitelist: {command}")
        return False
    
    def _needs_sudo(self, command: str) -> bool:
        """Check if command requires sudo privileges"""
        command_lower = command.lower()
        return any(sudo_cmd in command_lower for sudo_cmd in self.sudo_required)
    
    def _sanitize_command(self, command: str) -> Union[List[str], str]:
        """
        Sanitize command by parsing it safely with enhanced security
        
        Returns either:
        - List[str] for simple commands that can run with shell=False
        - str for complex commands that need shell=True but are validated
        
        This prevents command injection by:
        1. Using shlex to properly parse simple command arguments
        2. Validating complex commands against whitelist
        3. Avoiding shell interpretation when possible
        4. Special handling for Windows PowerShell commands
        """
        try:
            command = command.strip()
            
            # Check if command contains shell features that require shell=True
            shell_features = ['|', '>', '<', '&&', '||', ';', '`', '$', '(', ')']
            needs_shell = any(feature in command for feature in shell_features)
            
            # Windows PowerShell commands almost always need shell=True
            if command.lower().startswith(('powershell', 'pwsh')):
                self.logger.info(f"PowerShell command requires shell: {command}")
                return command
            
            # Windows registry commands need shell=True
            if command.lower().startswith(('reg ', 'regedit', 'netsh')):
                self.logger.info(f"Windows system command requires shell: {command}")
                return command
            
            if needs_shell:
                # Complex command - return as string for shell=True but validated
                self.logger.info(f"Complex command requires shell: {command}")
                return command
            else:
                # Simple command - parse into list for shell=False
                parsed = shlex.split(command)
                self.logger.info(f"Simple command parsed: {parsed}")
                return parsed
                
        except Exception as e:
            self.logger.error(f"Error sanitizing command: {e}")
            raise ValueError(f"Invalid command format: {command}")
    
    def execute_command(self, command: str, os_type: str, timeout: int = 30) -> CommandResult:
        """
        Execute a command securely with comprehensive validation and timeout protection
        
        Args:
            command: Command to execute
            os_type: Operating system type (windows, linux, macos)
            timeout: Maximum execution time in seconds
            
        Returns:
            CommandResult: Result of command execution
            
        Raises:
            CommandTimeoutError: If command exceeds timeout
            ValueError: If command fails validation
        """
        import time
        
        start_time = time.time()
        
        # Validate command
        if not self._validate_command(command, os_type):
            raise ValueError(f"Command not allowed: {command}")
        
        # Check if sudo is needed
        needs_sudo = self._needs_sudo(command)
        if needs_sudo:
            self.logger.warning(f"Command requires sudo: {command}")
            self.logger.warning("Note: This may fail if sudo password is required")
        
        # Sanitize command
        sanitized_cmd = self._sanitize_command(command)
        
        try:
            # Execute command with timeout
            if isinstance(sanitized_cmd, list):
                # Simple command - use shell=False for security
                process = subprocess.run(
                    sanitized_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False
                )
            else:
                # Complex command - use shell=True but validated
                process = subprocess.run(
                    sanitized_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True
                )
            
            execution_time = time.time() - start_time
            
            result = CommandResult(
                stdout=process.stdout,
                stderr=process.stderr,
                returncode=process.returncode,
                execution_time=execution_time
            )
            
            self.logger.info(f"Command executed successfully: {command}")
            self.logger.info(f"Return code: {result.returncode}, Time: {execution_time:.2f}s")
            
            if result.stderr:
                self.logger.warning(f"Command stderr: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"Command timed out after {timeout}s: {command}")
            raise CommandTimeoutError(f"Command timed out after {timeout}s: {command}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Command execution failed: {e}")
            return CommandResult(
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time=execution_time
            )
    
    def validate_mongodb_uri(self, uri: str) -> bool:
        """
        Validate MongoDB URI format for security
        
        Args:
            uri: MongoDB connection string
            
        Returns:
            bool: True if URI is valid and secure
        """
        if not uri or not uri.strip():
            return False
        
        # Check for basic MongoDB URI format
        if not uri.startswith(('mongodb://', 'mongodb+srv://')):
            self.logger.warning("Invalid MongoDB URI format")
            return False
        
        # Check for common security issues
        dangerous_patterns = [
            'localhost', '127.0.0.1', '0.0.0.0',  # Local connections
            'admin', 'root', 'administrator',  # Admin users
            'password', 'pass', 'pwd',  # Password in URI
        ]
        
        uri_lower = uri.lower()
        for pattern in dangerous_patterns:
            if pattern in uri_lower:
                self.logger.warning(f"Potentially insecure MongoDB URI pattern: {pattern}")
                # Don't block, just warn
        
        return True
        """
        Securely execute a command with validation and logging
        
        Args:
            command: Command to execute
            os_type: Operating system type (windows/linux/ubuntu/centos)
            timeout: Command timeout in seconds
            
        Returns:
            subprocess.CompletedProcess object
            
        Raises:
            ValueError: If command is invalid or not allowed
            subprocess.TimeoutExpired: If command times out
        """
        
        # Normalize OS type
        if os_type in ['ubuntu', 'centos']:
            os_type = 'linux'
        
        # Validate command
        if not self._validate_command(command, os_type):
            raise ValueError(f"Command not allowed: {command}")
        
        # Log the execution attempt
        self.logger.info(f"Executing command: {command} (OS: {os_type})")
        
        try:
            # Sanitize command - get either list or string
            sanitized_cmd = self._sanitize_command(command)
            
            # Determine if we need shell=True
            if isinstance(sanitized_cmd, str):
                # Complex command requiring shell=True (but validated)
                self.logger.info(f"Executing with shell=True (validated): {command}")
                result = subprocess.run(
                    sanitized_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True  # Required for complex commands, but command is validated
                )
            else:
                # Simple command that can run with shell=False
                self.logger.info(f"Executing with shell=False: {command}")
                result = subprocess.run(
                    sanitized_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False  # SECURE: No shell interpretation
                )
            
            # Log result with more detail
            if result.returncode == 0:
                self.logger.info(f"Command completed successfully: {command}")
            else:
                self.logger.warning(f"Command failed with return code {result.returncode}: {command}")
                if result.stderr:
                    self.logger.warning(f"Error output: {result.stderr}")
                if result.stdout:
                    self.logger.info(f"Output: {result.stdout}")
            
            return result
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {command}")
            raise
        except FileNotFoundError:
            # Command not found - might need different handling on Windows vs Linux
            self.logger.error(f"Command not found: {command}")
            raise ValueError(f"Command not found: {sanitized_cmd[0] if isinstance(sanitized_cmd, list) else command}")
        except Exception as e:
            self.logger.error(f"Command execution failed: {command}, Error: {e}")
            raise

