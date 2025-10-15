#!/usr/bin/env python3
"""
Enhanced Security Configuration for OS Forge
Provides centralized security configuration management
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityPolicy:
    """Represents a security policy"""
    policy_id: str
    name: str
    description: str
    category: str
    severity: str
    enabled: bool
    rules: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    version: str

@dataclass
class SecurityBaseline:
    """Represents a security baseline"""
    baseline_id: str
    name: str
    description: str
    os_type: str  # linux, windows, macos
    policies: List[str]  # Policy IDs
    compliance_level: str  # strict, moderate, relaxed
    created_at: datetime
    updated_at: datetime

class SecurityConfigManager:
    """Enhanced security configuration manager"""
    
    def __init__(self, config_dir: str = "./security/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration files
        self.policies_file = self.config_dir / "policies.yaml"
        self.baselines_file = self.config_dir / "baselines.yaml"
        self.settings_file = self.config_dir / "settings.yaml"
        self.compliance_file = self.config_dir / "compliance.yaml"
        
        # Load configurations
        self.policies = self._load_policies()
        self.baselines = self._load_baselines()
        self.settings = self._load_settings()
        self.compliance_rules = self._load_compliance_rules()
        
        # Initialize default configurations if not present
        if not self.policies:
            self._initialize_default_policies()
        if not self.baselines:
            self._initialize_default_baselines()
        if not self.settings:
            self._initialize_default_settings()
    
    def _load_policies(self) -> Dict[str, SecurityPolicy]:
        """Load security policies"""
        if not self.policies_file.exists():
            return {}
        
        try:
            with open(self.policies_file, 'r') as f:
                data = yaml.safe_load(f)
            
            policies = {}
            for policy_id, policy_data in data.items():
                policy_data['created_at'] = datetime.fromisoformat(policy_data['created_at'])
                policy_data['updated_at'] = datetime.fromisoformat(policy_data['updated_at'])
                policies[policy_id] = SecurityPolicy(**policy_data)
            
            return policies
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
            return {}
    
    def _load_baselines(self) -> Dict[str, SecurityBaseline]:
        """Load security baselines"""
        if not self.baselines_file.exists():
            return {}
        
        try:
            with open(self.baselines_file, 'r') as f:
                data = yaml.safe_load(f)
            
            baselines = {}
            for baseline_id, baseline_data in data.items():
                baseline_data['created_at'] = datetime.fromisoformat(baseline_data['created_at'])
                baseline_data['updated_at'] = datetime.fromisoformat(baseline_data['updated_at'])
                baselines[baseline_id] = SecurityBaseline(**baseline_data)
            
            return baselines
        except Exception as e:
            logger.error(f"Failed to load baselines: {e}")
            return {}
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load security settings"""
        if not self.settings_file.exists():
            return {}
        
        try:
            with open(self.settings_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules"""
        if not self.compliance_file.exists():
            return {}
        
        try:
            with open(self.compliance_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load compliance rules: {e}")
            return {}
    
    def _save_policies(self):
        """Save policies to file"""
        try:
            data = {}
            for policy_id, policy in self.policies.items():
                policy_dict = asdict(policy)
                policy_dict['created_at'] = policy.created_at.isoformat()
                policy_dict['updated_at'] = policy.updated_at.isoformat()
                data[policy_id] = policy_dict
            
            with open(self.policies_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")
    
    def _save_baselines(self):
        """Save baselines to file"""
        try:
            data = {}
            for baseline_id, baseline in self.baselines.items():
                baseline_dict = asdict(baseline)
                baseline_dict['created_at'] = baseline.created_at.isoformat()
                baseline_dict['updated_at'] = baseline.updated_at.isoformat()
                data[baseline_id] = baseline_dict
            
            with open(self.baselines_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save baselines: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                yaml.dump(self.settings, f, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _initialize_default_policies(self):
        """Initialize default security policies"""
        default_policies = [
            SecurityPolicy(
                policy_id="password_policy",
                name="Password Security Policy",
                description="Enforces strong password requirements",
                category="authentication",
                severity="HIGH",
                enabled=True,
                rules=[
                    {
                        "rule_id": "min_length",
                        "description": "Minimum password length",
                        "value": 12,
                        "type": "integer"
                    },
                    {
                        "rule_id": "require_uppercase",
                        "description": "Require uppercase letters",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "require_lowercase",
                        "description": "Require lowercase letters",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "require_numbers",
                        "description": "Require numbers",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "require_special_chars",
                        "description": "Require special characters",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "password_history",
                        "description": "Password history length",
                        "value": 5,
                        "type": "integer"
                    },
                    {
                        "rule_id": "max_age_days",
                        "description": "Maximum password age in days",
                        "value": 90,
                        "type": "integer"
                    }
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0"
            ),
            SecurityPolicy(
                policy_id="network_security",
                name="Network Security Policy",
                description="Network security and firewall rules",
                category="network",
                severity="HIGH",
                enabled=True,
                rules=[
                    {
                        "rule_id": "firewall_enabled",
                        "description": "Firewall must be enabled",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "default_deny",
                        "description": "Default policy should be deny",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "ssh_port",
                        "description": "SSH port (0 to disable SSH)",
                        "value": 22,
                        "type": "integer"
                    },
                    {
                        "rule_id": "allow_http",
                        "description": "Allow HTTP traffic",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "allow_https",
                        "description": "Allow HTTPS traffic",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "block_telnet",
                        "description": "Block Telnet",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "block_ftp",
                        "description": "Block FTP",
                        "value": True,
                        "type": "boolean"
                    }
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0"
            ),
            SecurityPolicy(
                policy_id="system_hardening",
                name="System Hardening Policy",
                description="System hardening and security configurations",
                category="system",
                severity="HIGH",
                enabled=True,
                rules=[
                    {
                        "rule_id": "disable_root_login",
                        "description": "Disable root login",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "disable_guest_account",
                        "description": "Disable guest account",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "enable_audit_logging",
                        "description": "Enable audit logging",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "disable_unnecessary_services",
                        "description": "Disable unnecessary services",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "enable_aslr",
                        "description": "Enable Address Space Layout Randomization",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "disable_core_dumps",
                        "description": "Disable core dumps",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "secure_umask",
                        "description": "Secure umask value",
                        "value": "027",
                        "type": "string"
                    }
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0"
            ),
            SecurityPolicy(
                policy_id="data_protection",
                name="Data Protection Policy",
                description="Data encryption and protection requirements",
                category="data",
                severity="CRITICAL",
                enabled=True,
                rules=[
                    {
                        "rule_id": "encrypt_sensitive_data",
                        "description": "Encrypt sensitive data at rest",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "encrypt_data_in_transit",
                        "description": "Encrypt data in transit",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "backup_encryption",
                        "description": "Encrypt backups",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "secure_deletion",
                        "description": "Secure deletion of sensitive data",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "data_classification",
                        "description": "Implement data classification",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "access_logging",
                        "description": "Log data access",
                        "value": True,
                        "type": "boolean"
                    }
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0"
            ),
            SecurityPolicy(
                policy_id="application_security",
                name="Application Security Policy",
                description="Application security requirements",
                category="application",
                severity="HIGH",
                enabled=True,
                rules=[
                    {
                        "rule_id": "input_validation",
                        "description": "Implement input validation",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "output_encoding",
                        "description": "Implement output encoding",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "sql_injection_protection",
                        "description": "Protect against SQL injection",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "xss_protection",
                        "description": "Protect against XSS",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "csrf_protection",
                        "description": "Protect against CSRF",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "secure_headers",
                        "description": "Implement security headers",
                        "value": True,
                        "type": "boolean"
                    },
                    {
                        "rule_id": "session_security",
                        "description": "Secure session management",
                        "value": True,
                        "type": "boolean"
                    }
                ],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                version="1.0"
            )
        ]
        
        for policy in default_policies:
            self.policies[policy.policy_id] = policy
        
        self._save_policies()
        logger.info("Default security policies initialized")
    
    def _initialize_default_baselines(self):
        """Initialize default security baselines"""
        default_baselines = [
            SecurityBaseline(
                baseline_id="linux_server_strict",
                name="Linux Server - Strict",
                description="Strict security baseline for Linux servers",
                os_type="linux",
                policies=["password_policy", "network_security", "system_hardening", "data_protection", "application_security"],
                compliance_level="strict",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            SecurityBaseline(
                baseline_id="linux_server_moderate",
                name="Linux Server - Moderate",
                description="Moderate security baseline for Linux servers",
                os_type="linux",
                policies=["password_policy", "network_security", "system_hardening"],
                compliance_level="moderate",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            SecurityBaseline(
                baseline_id="windows_server_strict",
                name="Windows Server - Strict",
                description="Strict security baseline for Windows servers",
                os_type="windows",
                policies=["password_policy", "network_security", "system_hardening", "data_protection"],
                compliance_level="strict",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            SecurityBaseline(
                baseline_id="windows_workstation_moderate",
                name="Windows Workstation - Moderate",
                description="Moderate security baseline for Windows workstations",
                os_type="windows",
                policies=["password_policy", "system_hardening"],
                compliance_level="moderate",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            SecurityBaseline(
                baseline_id="docker_container",
                name="Docker Container",
                description="Security baseline for Docker containers",
                os_type="linux",
                policies=["system_hardening", "application_security"],
                compliance_level="strict",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        for baseline in default_baselines:
            self.baselines[baseline.baseline_id] = baseline
        
        self._save_baselines()
        logger.info("Default security baselines initialized")
    
    def _initialize_default_settings(self):
        """Initialize default security settings"""
        self.settings = {
            "global": {
                "enforce_policies": True,
                "auto_remediation": False,
                "notification_enabled": True,
                "compliance_reporting": True,
                "audit_logging": True
            },
            "scanning": {
                "scan_interval_minutes": 60,
                "deep_scan_interval_hours": 24,
                "scan_timeout_seconds": 300,
                "parallel_scans": 4,
                "exclude_patterns": [
                    "**/node_modules/**",
                    "**/.git/**",
                    "**/venv/**",
                    "**/__pycache__/**"
                ]
            },
            "reporting": {
                "report_format": "html",
                "include_remediation": True,
                "include_compliance_matrix": True,
                "email_reports": False,
                "retention_days": 90
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#security"
                }
            },
            "compliance": {
                "frameworks": ["NIST", "CIS", "ISO27001"],
                "auto_assessment": True,
                "remediation_suggestions": True,
                "compliance_threshold": 80
            }
        }
        
        self._save_settings()
        logger.info("Default security settings initialized")
    
    def get_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        """Get a security policy by ID"""
        return self.policies.get(policy_id)
    
    def get_policies_by_category(self, category: str) -> List[SecurityPolicy]:
        """Get policies by category"""
        return [policy for policy in self.policies.values() if policy.category == category]
    
    def get_enabled_policies(self) -> List[SecurityPolicy]:
        """Get all enabled policies"""
        return [policy for policy in self.policies.values() if policy.enabled]
    
    def create_policy(self, policy: SecurityPolicy) -> bool:
        """Create a new security policy"""
        try:
            if policy.policy_id in self.policies:
                logger.error(f"Policy {policy.policy_id} already exists")
                return False
            
            self.policies[policy.policy_id] = policy
            self._save_policies()
            logger.info(f"Policy {policy.policy_id} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            return False
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing policy"""
        try:
            if policy_id not in self.policies:
                logger.error(f"Policy {policy_id} not found")
                return False
            
            policy = self.policies[policy_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            
            policy.updated_at = datetime.now()
            self._save_policies()
            logger.info(f"Policy {policy_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update policy: {e}")
            return False
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy"""
        try:
            if policy_id not in self.policies:
                logger.error(f"Policy {policy_id} not found")
                return False
            
            del self.policies[policy_id]
            self._save_policies()
            logger.info(f"Policy {policy_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            return False
    
    def get_baseline(self, baseline_id: str) -> Optional[SecurityBaseline]:
        """Get a security baseline by ID"""
        return self.baselines.get(baseline_id)
    
    def get_baselines_by_os(self, os_type: str) -> List[SecurityBaseline]:
        """Get baselines by OS type"""
        return [baseline for baseline in self.baselines.values() if baseline.os_type == os_type]
    
    def create_baseline(self, baseline: SecurityBaseline) -> bool:
        """Create a new security baseline"""
        try:
            if baseline.baseline_id in self.baselines:
                logger.error(f"Baseline {baseline.baseline_id} already exists")
                return False
            
            # Validate that all referenced policies exist
            for policy_id in baseline.policies:
                if policy_id not in self.policies:
                    logger.error(f"Referenced policy {policy_id} not found")
                    return False
            
            self.baselines[baseline.baseline_id] = baseline
            self._save_baselines()
            logger.info(f"Baseline {baseline.baseline_id} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create baseline: {e}")
            return False
    
    def update_baseline(self, baseline_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing baseline"""
        try:
            if baseline_id not in self.baselines:
                logger.error(f"Baseline {baseline_id} not found")
                return False
            
            baseline = self.baselines[baseline_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(baseline, key):
                    setattr(baseline, key, value)
            
            baseline.updated_at = datetime.now()
            self._save_baselines()
            logger.info(f"Baseline {baseline_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update baseline: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a security setting"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a security setting"""
        try:
            keys = key.split('.')
            settings = self.settings
            
            # Navigate to the parent dictionary
            for k in keys[:-1]:
                if k not in settings:
                    settings[k] = {}
                settings = settings[k]
            
            # Set the value
            settings[keys[-1]] = value
            self._save_settings()
            logger.info(f"Setting {key} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set setting: {e}")
            return False
    
    def validate_compliance(self, baseline_id: str, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate system compliance against a baseline"""
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            return {"error": f"Baseline {baseline_id} not found"}
        
        compliance_results = {
            "baseline_id": baseline_id,
            "baseline_name": baseline.name,
            "compliance_level": baseline.compliance_level,
            "total_policies": len(baseline.policies),
            "compliant_policies": 0,
            "non_compliant_policies": 0,
            "compliance_percentage": 0.0,
            "policy_results": {},
            "overall_status": "UNKNOWN",
            "assessment_time": datetime.now().isoformat()
        }
        
        for policy_id in baseline.policies:
            policy = self.get_policy(policy_id)
            if not policy:
                continue
            
            policy_result = self._validate_policy_compliance(policy, system_state)
            compliance_results["policy_results"][policy_id] = policy_result
            
            if policy_result["compliant"]:
                compliance_results["compliant_policies"] += 1
            else:
                compliance_results["non_compliant_policies"] += 1
        
        # Calculate compliance percentage
        total_policies = compliance_results["total_policies"]
        if total_policies > 0:
            compliance_results["compliance_percentage"] = (
                compliance_results["compliant_policies"] / total_policies * 100
            )
        
        # Determine overall status
        compliance_percentage = compliance_results["compliance_percentage"]
        if compliance_percentage >= 95:
            compliance_results["overall_status"] = "EXCELLENT"
        elif compliance_percentage >= 80:
            compliance_results["overall_status"] = "GOOD"
        elif compliance_percentage >= 60:
            compliance_results["overall_status"] = "FAIR"
        else:
            compliance_results["overall_status"] = "POOR"
        
        return compliance_results
    
    def _validate_policy_compliance(self, policy: SecurityPolicy, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance for a single policy"""
        result = {
            "policy_id": policy.policy_id,
            "policy_name": policy.name,
            "compliant": True,
            "rule_results": {},
            "violations": [],
            "recommendations": []
        }
        
        for rule in policy.rules:
            rule_id = rule["rule_id"]
            rule_value = rule["value"]
            rule_type = rule["type"]
            
            # Check if rule is satisfied in system state
            system_value = system_state.get(rule_id)
            
            if system_value is None:
                result["violations"].append(f"Rule {rule_id} not found in system state")
                result["compliant"] = False
                continue
            
            # Validate based on rule type
            if rule_type == "boolean":
                if system_value != rule_value:
                    result["violations"].append(f"Rule {rule_id}: Expected {rule_value}, got {system_value}")
                    result["compliant"] = False
            elif rule_type == "integer":
                if isinstance(rule_value, str) and rule_value.startswith(">"):
                    threshold = int(rule_value[1:])
                    if system_value <= threshold:
                        result["violations"].append(f"Rule {rule_id}: Value {system_value} below threshold {threshold}")
                        result["compliant"] = False
                elif isinstance(rule_value, str) and rule_value.startswith("<"):
                    threshold = int(rule_value[1:])
                    if system_value >= threshold:
                        result["violations"].append(f"Rule {rule_id}: Value {system_value} above threshold {threshold}")
                        result["compliant"] = False
                else:
                    if system_value != rule_value:
                        result["violations"].append(f"Rule {rule_id}: Expected {rule_value}, got {system_value}")
                        result["compliant"] = False
            elif rule_type == "string":
                if system_value != rule_value:
                    result["violations"].append(f"Rule {rule_id}: Expected '{rule_value}', got '{system_value}'")
                    result["compliant"] = False
            
            result["rule_results"][rule_id] = {
                "expected": rule_value,
                "actual": system_value,
                "compliant": len(result["violations"]) == 0
            }
        
        # Generate recommendations for violations
        if result["violations"]:
            result["recommendations"].append(f"Review and fix {len(result['violations'])} violations in policy {policy.name}")
        
        return result
    
    def export_configuration(self, output_path: str, format: str = "yaml") -> bool:
        """Export security configuration"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "policies": {pid: asdict(policy) for pid, policy in self.policies.items()},
                "baselines": {bid: asdict(baseline) for bid, baseline in self.baselines.items()},
                "settings": self.settings,
                "compliance_rules": self.compliance_rules
            }
            
            if format.lower() == "yaml":
                with open(output_path, 'w') as f:
                    yaml.dump(export_data, f, default_flow_style=False, indent=2)
            elif format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Configuration exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_configuration(self, import_path: str) -> bool:
        """Import security configuration"""
        try:
            with open(import_path, 'r') as f:
                if import_path.endswith('.yaml') or import_path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Import policies
            if "policies" in data:
                for policy_id, policy_data in data["policies"].items():
                    policy_data['created_at'] = datetime.fromisoformat(policy_data['created_at'])
                    policy_data['updated_at'] = datetime.fromisoformat(policy_data['updated_at'])
                    policy = SecurityPolicy(**policy_data)
                    self.policies[policy_id] = policy
            
            # Import baselines
            if "baselines" in data:
                for baseline_id, baseline_data in data["baselines"].items():
                    baseline_data['created_at'] = datetime.fromisoformat(baseline_data['created_at'])
                    baseline_data['updated_at'] = datetime.fromisoformat(baseline_data['updated_at'])
                    baseline = SecurityBaseline(**baseline_data)
                    self.baselines[baseline_id] = baseline
            
            # Import settings
            if "settings" in data:
                self.settings.update(data["settings"])
            
            # Save all configurations
            self._save_policies()
            self._save_baselines()
            self._save_settings()
            
            logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False


def main():
    """CLI interface for security configuration manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OS Forge Security Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Policy commands
    policy_parser = subparsers.add_parser("policy", help="Policy management")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_action")
    
    policy_subparsers.add_parser("list", help="List all policies")
    policy_subparsers.add_parser("show", help="Show policy details").add_argument("policy_id")
    policy_subparsers.add_parser("create", help="Create new policy")
    policy_subparsers.add_parser("update", help="Update policy").add_argument("policy_id")
    policy_subparsers.add_parser("delete", help="Delete policy").add_argument("policy_id")
    
    # Baseline commands
    baseline_parser = subparsers.add_parser("baseline", help="Baseline management")
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_action")
    
    baseline_subparsers.add_parser("list", help="List all baselines")
    baseline_subparsers.add_parser("show", help="Show baseline details").add_argument("baseline_id")
    baseline_subparsers.add_parser("create", help="Create new baseline")
    baseline_subparsers.add_parser("update", help="Update baseline").add_argument("baseline_id")
    baseline_subparsers.add_parser("delete", help="Delete baseline").add_argument("baseline_id")
    
    # Settings commands
    settings_parser = subparsers.add_parser("settings", help="Settings management")
    settings_subparsers = settings_parser.add_subparsers(dest="settings_action")
    
    get_parser = settings_subparsers.add_parser("get", help="Get setting")
    get_parser.add_argument("key")
    set_parser = settings_subparsers.add_parser("set", help="Set setting")
    set_parser.add_argument("key")
    set_parser.add_argument("value")
    settings_subparsers.add_parser("list", help="List all settings")
    
    # Compliance commands
    compliance_parser = subparsers.add_parser("compliance", help="Compliance validation")
    compliance_parser.add_argument("baseline_id", help="Baseline ID to validate against")
    compliance_parser.add_argument("--system-state", help="System state file (JSON)")
    
    # Export/Import commands
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument("output_path", help="Output file path")
    export_parser.add_argument("--format", default="yaml", choices=["yaml", "json"], help="Export format")
    
    import_parser = subparsers.add_parser("import", help="Import configuration")
    import_parser.add_argument("import_path", help="Import file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = SecurityConfigManager()
    
    try:
        if args.command == "policy":
            if args.policy_action == "list":
                policies = list(manager.policies.values())
                if policies:
                    print(f"{'ID':<20} {'Name':<30} {'Category':<15} {'Severity':<10} {'Enabled':<8}")
                    print("-" * 83)
                    for policy in policies:
                        print(f"{policy.policy_id:<20} {policy.name:<30} {policy.category:<15} {policy.severity:<10} {policy.enabled:<8}")
                else:
                    print("No policies found")
                    
            elif args.policy_action == "show":
                policy = manager.get_policy(args.policy_id)
                if policy:
                    print(f"Policy ID: {policy.policy_id}")
                    print(f"Name: {policy.name}")
                    print(f"Description: {policy.description}")
                    print(f"Category: {policy.category}")
                    print(f"Severity: {policy.severity}")
                    print(f"Enabled: {policy.enabled}")
                    print(f"Version: {policy.version}")
                    print(f"Created: {policy.created_at}")
                    print(f"Updated: {policy.updated_at}")
                    print("\nRules:")
                    for rule in policy.rules:
                        print(f"  - {rule['rule_id']}: {rule['description']} = {rule['value']}")
                else:
                    print(f"Policy {args.policy_id} not found")
        
        elif args.command == "baseline":
            if args.baseline_action == "list":
                baselines = list(manager.baselines.values())
                if baselines:
                    print(f"{'ID':<25} {'Name':<30} {'OS Type':<10} {'Compliance':<10} {'Policies':<8}")
                    print("-" * 83)
                    for baseline in baselines:
                        print(f"{baseline.baseline_id:<25} {baseline.name:<30} {baseline.os_type:<10} {baseline.compliance_level:<10} {len(baseline.policies):<8}")
                else:
                    print("No baselines found")
                    
            elif args.baseline_action == "show":
                baseline = manager.get_baseline(args.baseline_id)
                if baseline:
                    print(f"Baseline ID: {baseline.baseline_id}")
                    print(f"Name: {baseline.name}")
                    print(f"Description: {baseline.description}")
                    print(f"OS Type: {baseline.os_type}")
                    print(f"Compliance Level: {baseline.compliance_level}")
                    print(f"Created: {baseline.created_at}")
                    print(f"Updated: {baseline.updated_at}")
                    print("\nPolicies:")
                    for policy_id in baseline.policies:
                        policy = manager.get_policy(policy_id)
                        if policy:
                            print(f"  - {policy_id}: {policy.name}")
                else:
                    print(f"Baseline {args.baseline_id} not found")
        
        elif args.command == "settings":
            if args.settings_action == "get":
                value = manager.get_setting(args.key)
                print(f"{args.key}: {value}")
                
            elif args.settings_action == "set":
                success = manager.set_setting(args.key, args.value)
                print("Setting updated successfully" if success else "Failed to update setting")
                
            elif args.settings_action == "list":
                def print_settings(settings, prefix=""):
                    for key, value in settings.items():
                        if isinstance(value, dict):
                            print(f"{prefix}{key}:")
                            print_settings(value, prefix + "  ")
                        else:
                            print(f"{prefix}{key}: {value}")
                
                print_settings(manager.settings)
        
        elif args.command == "compliance":
            # Load system state if provided
            system_state = {}
            if args.system_state and os.path.exists(args.system_state):
                with open(args.system_state, 'r') as f:
                    system_state = json.load(f)
            else:
                # Use default system state for demo
                system_state = {
                    "min_length": 12,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_numbers": True,
                    "require_special_chars": True,
                    "firewall_enabled": True,
                    "default_deny": True,
                    "ssh_port": 22,
                    "allow_http": True,
                    "allow_https": True,
                    "block_telnet": True,
                    "block_ftp": True,
                    "disable_root_login": True,
                    "disable_guest_account": True,
                    "enable_audit_logging": True,
                    "disable_unnecessary_services": True,
                    "enable_aslr": True,
                    "disable_core_dumps": True,
                    "secure_umask": "027"
                }
            
            results = manager.validate_compliance(args.baseline_id, system_state)
            
            print(f"=== Compliance Assessment ===")
            print(f"Baseline: {results['baseline_name']}")
            print(f"Compliance Level: {results['compliance_level']}")
            print(f"Overall Status: {results['overall_status']}")
            print(f"Compliance Percentage: {results['compliance_percentage']:.1f}%")
            print(f"Compliant Policies: {results['compliant_policies']}/{results['total_policies']}")
            print(f"Assessment Time: {results['assessment_time']}")
            
            print(f"\n=== Policy Results ===")
            for policy_id, policy_result in results['policy_results'].items():
                status = "✓" if policy_result['compliant'] else "✗"
                print(f"{status} {policy_id}: {policy_result['policy_name']}")
                
                if policy_result['violations']:
                    print(f"  Violations:")
                    for violation in policy_result['violations']:
                        print(f"    - {violation}")
                
                if policy_result['recommendations']:
                    print(f"  Recommendations:")
                    for rec in policy_result['recommendations']:
                        print(f"    - {rec}")
        
        elif args.command == "export":
            success = manager.export_configuration(args.output_path, args.format)
            print("Configuration exported successfully" if success else "Failed to export configuration")
            
        elif args.command == "import":
            success = manager.import_configuration(args.import_path)
            print("Configuration imported successfully" if success else "Failed to import configuration")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
