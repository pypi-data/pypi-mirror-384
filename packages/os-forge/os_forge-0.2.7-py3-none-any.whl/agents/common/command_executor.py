"""
Command Execution Utilities for OS Forge Agents
Provides safe command execution with proper error handling and security measures
"""

import subprocess
import shlex
import logging
import time
from typing import Tuple, Optional, Dict, Any
from pathlib import Path


class CommandExecutor:
    """
    Safe command execution utility with security measures
    
    Provides secure command execution with:
    - Input sanitization
    - Timeout handling
    - Privilege escalation detection
    - Command logging
    - Error handling
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._dangerous_commands = {
            'rm', 'del', 'format', 'fdisk', 'mkfs', 'dd', 'shutdown', 'reboot',
            'halt', 'poweroff', 'init', 'kill', 'killall', 'pkill', 'xkill'
        }
        # Keep blocking risky shell features, but allow '&&' (we handle it by splitting)
        self._dangerous_patterns = [
            ';', '`', '$(', '${', '$'
        ]
    
    def is_command_safe(self, command: str) -> Tuple[bool, str]:
        """
        Check if a command is safe to execute
        
        Args:
            command: Command string to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for dangerous commands
        cmd_parts = shlex.split(command.lower())
        if cmd_parts:
            base_cmd = cmd_parts[0]
            if base_cmd in self._dangerous_commands:
                return False, f"Dangerous command detected: {base_cmd}"
        
        # Check for dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern in command:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check for path traversal
        if '..' in command or '../' in command:
            return False, "Path traversal detected"
        
        return True, "Command appears safe"
    
    def execute(
        self, 
        command: str, 
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        check_safety: bool = True
    ) -> Tuple[str, str, int]:
        """
        Execute a command safely
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            cwd: Working directory
            env: Environment variables
            check_safety: Whether to perform safety checks
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        # Handle '&&' chaining by executing each sub-command sequentially
        if '&&' in command:
            stdout_accum = []
            stderr_accum = []
            last_rc = 0
            for sub_cmd in [part.strip() for part in command.split('&&') if part.strip()]:
                if check_safety:
                    is_safe, reason = self.is_command_safe(sub_cmd)
                    if not is_safe:
                        self.logger.warning(f"Unsafe command blocked: {sub_cmd} - {reason}")
                        return "", f"Command blocked for safety: {reason}", 1
                out, err, rc = self._run_single(sub_cmd, timeout=timeout, cwd=cwd, env=env)
                stdout_accum.append(out)
                stderr_accum.append(err)
                last_rc = rc
                if rc != 0:
                    # Stop on first failure, similar to 'set -e'
                    break
            return "".join(stdout_accum), "".join(stderr_accum), last_rc

        # Non-chained single command path
        if check_safety:
            is_safe, reason = self.is_command_safe(command)
            if not is_safe:
                self.logger.warning(f"Unsafe command blocked: {command} - {reason}")
                return "", f"Command blocked for safety: {reason}", 1

        return self._run_single(command, timeout=timeout, cwd=cwd, env=env)

    def _run_single(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, str, int]:
        """
        Execute a single command (no '&&' chaining). If the command uses
        pipes or redirection, run via shell in a controlled way; otherwise
        run with shell=False using shlex splitting.
        """
        try:
            self.logger.debug(f"Executing command: {command}")

            # Detect simple shell features that require a shell
            shell_features = ['|', '>', '>>', '<']
            needs_shell = any(feature in command for feature in shell_features)

            start_time = time.time()
            if needs_shell:
                # Controlled shell execution; still blocked from dangerous patterns earlier
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd,
                    env=env,
                    check=False
                )
            else:
                cmd_parts = shlex.split(command)
                if not cmd_parts:
                    return "", "Empty command", 1
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=cwd,
                    env=env,
                    check=False
                )

            execution_time = time.time() - start_time
            self.logger.debug(
                f"Command completed in {execution_time:.2f}s: return_code={result.returncode}"
            )
            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {command}")
            return "", f"Command timed out after {timeout} seconds", 124
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with return code {e.returncode}: {command}")
            return e.stdout or "", e.stderr or "", e.returncode
        except Exception as e:
            self.logger.error(f"Unexpected error executing command: {command} - {str(e)}")
            return "", f"Execution error: {str(e)}", 1
    
    def execute_with_sudo(
        self, 
        command: str, 
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str, int]:
        """
        Execute a command with sudo privileges
        
        Args:
            command: Command to execute (without sudo prefix)
            timeout: Command timeout in seconds
            cwd: Working directory
            env: Environment variables
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        sudo_command = f"sudo {command}"
        return self.execute(sudo_command, timeout, cwd, env, check_safety=True)
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        try:
            return Path(file_path).exists()
        except Exception:
            return False
    
    def read_file(self, file_path: str, max_size: int = 1024 * 1024) -> Tuple[bool, str]:
        """
        Safely read a file
        
        Args:
            file_path: Path to file
            max_size: Maximum file size to read
            
        Returns:
            Tuple of (success, content)
        """
        try:
            if not self.check_file_exists(file_path):
                return False, "File does not exist"
            
            file_path_obj = Path(file_path)
            if file_path_obj.stat().st_size > max_size:
                return False, f"File too large (>{max_size} bytes)"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return True, content
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def write_file(
        self, 
        file_path: str, 
        content: str, 
        backup: bool = True
    ) -> Tuple[bool, str]:
        """
        Safely write to a file
        
        Args:
            file_path: Path to file
            content: Content to write
            backup: Whether to create backup
            
        Returns:
            Tuple of (success, message)
        """
        try:
            file_path_obj = Path(file_path)
            
            # Create backup if requested and file exists
            if backup and file_path_obj.exists():
                backup_path = f"{file_path}.backup.{int(time.time())}"
                file_path_obj.rename(backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Ensure directory exists
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, "File written successfully"
            
        except Exception as e:
            return False, f"Error writing file: {str(e)}"
    
    def get_file_permissions(self, file_path: str) -> Optional[str]:
        """Get file permissions in octal format"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return None
            
            stat_info = file_path_obj.stat()
            return oct(stat_info.st_mode)[-3:]
            
        except Exception:
            return None
    
    def set_file_permissions(self, file_path: str, permissions: str) -> bool:
        """Set file permissions"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False
            
            # Convert octal string to integer
            perm_int = int(permissions, 8)
            file_path_obj.chmod(perm_int)
            return True
            
        except Exception:
            return False
