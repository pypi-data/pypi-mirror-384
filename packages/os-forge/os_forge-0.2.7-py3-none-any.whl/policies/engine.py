"""
Policy Engine for OS Forge

Core policy execution engine that orchestrates rule validation and execution.
"""

import platform
import logging
import subprocess
from typing import Dict, List, Optional, Any

from .schemas import HardeningLevel, RuleResult, SeverityLevel
from .rules import get_hardening_rules
from security.executor import SecureCommandExecutor


class PolicyEngine:
    """
    Core policy engine for executing security hardening rules
    
    This class handles:
    - OS detection
    - Rule loading and filtering
    - Secure command execution
    - Result aggregation
    """
    
    def __init__(self):
        self.rules = get_hardening_rules()
        self.current_os = self._detect_os()
        self.secure_executor = SecureCommandExecutor()
        self.logger = logging.getLogger(__name__)
    
    def _detect_os(self) -> str:
        """
        Detect current operating system
        
        Returns:
            str: OS type (windows, ubuntu, centos, linux, macos, unknown)
        """
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            # Try to detect specific Linux distribution
            try:
                with open("/etc/os-release") as f:
                    content = f.read().lower()
                    if "ubuntu" in content:
                        return "ubuntu"
                    elif "centos" in content or "rhel" in content:
                        return "centos"
                    elif "debian" in content:
                        return "debian"
                    elif "fedora" in content:
                        return "fedora"
            except FileNotFoundError:
                self.logger.warning("Could not detect Linux distribution: /etc/os-release not found")
            except PermissionError:
                self.logger.warning("Could not detect Linux distribution: Permission denied reading /etc/os-release")
            except Exception as e:
                self.logger.warning(f"Could not detect Linux distribution: {e}")
            return "linux"
        return "unknown"
    
    def get_applicable_rules(self, level: HardeningLevel, os_filter: Optional[str] = None) -> List[Dict]:
        """
        Get rules applicable for current OS and hardening level
        
        Args:
            level: Hardening level (basic, moderate, strict)
            os_filter: Optional OS filter to override detected OS
            
        Returns:
            List of applicable rule dictionaries
        """
        target_os = os_filter or self.current_os
        applicable = []
        
        for rule in self.rules["rules"]:
            # Check OS compatibility
            rule_os = rule["os"]
            if isinstance(rule_os, str):
                rule_os = [rule_os]
            
            # Check if current OS matches any of the rule's target OSes
            if target_os not in rule_os:
                continue
            
            # Check level compatibility
            if level not in rule["level"]:
                continue
            
            applicable.append(rule)
        
        return applicable
    
    def execute_rule(self, rule: Dict, dry_run: bool = True) -> RuleResult:
        """
        Execute a single hardening rule with secure command execution
        
        Args:
            rule: Rule dictionary containing commands and metadata
            dry_run: If True, only check current state without applying changes
            
        Returns:
            RuleResult object with execution results
        """
        rule_id = rule["id"]
        description = rule["description"]
        severity = rule["severity"]
        
        try:
            # Execute check command securely
            check_result = self.secure_executor.execute_command(
                command=rule["check"],
                os_type=self.current_os,
                timeout=30
            )
            
            old_value = check_result.stdout.strip()
            expected = rule.get("expected", "")
            
            # Determine if remediation is needed
            needs_remediation = old_value != expected
            status = "fail" if needs_remediation else "pass"
            new_value = old_value
            
            # Apply remediation if not dry run and needed
            if not dry_run and needs_remediation:
                remediate_result = self.secure_executor.execute_command(
                    command=rule["remediate"],
                    os_type=self.current_os,
                    timeout=30
                )
                
                if remediate_result.returncode == 0:
                    # Verify the change
                    verify_result = self.secure_executor.execute_command(
                        command=rule["check"],
                        os_type=self.current_os,
                        timeout=30
                    )
                    new_value = verify_result.stdout.strip()
                    status = "pass" if new_value == expected else "fail"
                else:
                    status = "error"
                    new_value = f"Remediation failed: {remediate_result.stderr}"
            
            return RuleResult(
                rule_id=rule_id,
                description=description,
                severity=severity,
                status=status,
                old_value=old_value,
                new_value=new_value
            )
            
        except subprocess.TimeoutExpired:
            return RuleResult(
                rule_id=rule_id,
                description=description,
                severity=severity,
                status="error",
                error="Command timeout"
            )
        except ValueError as e:
            # Security validation failed
            return RuleResult(
                rule_id=rule_id,
                description=description,
                severity=severity,
                status="error",
                error=f"Security validation failed: {str(e)}"
            )
        except Exception as e:
            return RuleResult(
                rule_id=rule_id,
                description=description,
                severity=severity,
                status="error",
                error=str(e)
            )
    
    def execute_rollback(self, rule_id: str) -> Dict[str, Any]:
        """
        Execute rollback for a specific rule
        
        Args:
            rule_id: ID of the rule to rollback
            
        Returns:
            Dict with rollback execution results
        """
        # Find the rule definition
        applicable_rules = self.get_applicable_rules(HardeningLevel.STRICT)  # Get all rules
        rule_def = None
        for rule in applicable_rules:
            if rule["id"] == rule_id:
                rule_def = rule
                break
        
        if not rule_def:
            raise ValueError(f"Rule definition not found for {rule_id}")
        
        try:
            # Execute rollback command securely
            rollback_result = self.secure_executor.execute_command(
                command=rule_def["rollback"],
                os_type=self.current_os,
                timeout=30
            )
            
            if rollback_result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"Successfully rolled back rule {rule_id}",
                    "rule_id": rule_id,
                    "rollback_output": rollback_result.stdout
                }
            else:
                return {
                    "status": "error",
                    "message": f"Rollback failed for rule {rule_id}",
                    "error": rollback_result.stderr
                }
                
        except subprocess.TimeoutExpired:
            raise Exception("Rollback command timed out")
        except Exception as e:
            raise Exception(f"Rollback failed: {str(e)}")
    
    def get_rule_count_by_level(self) -> Dict[str, int]:
        """
        Get count of rules available for each hardening level
        
        Returns:
            Dict mapping level names to rule counts
        """
        counts = {}
        for level in HardeningLevel:
            counts[level.value] = len(self.get_applicable_rules(level))
        return counts

