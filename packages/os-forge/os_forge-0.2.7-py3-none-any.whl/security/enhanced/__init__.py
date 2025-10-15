"""
Enhanced Security Module for OS Forge
Provides comprehensive security scanning, monitoring, and configuration management
"""

from .vulnerability_scanner import VulnerabilityScanner, Vulnerability, ScanResult
from .secrets_manager import SecretsManager, SecretMetadata, SecretAccessLog
from .security_monitor import SecurityMonitor, SecurityEvent, AlertRule, ThreatIndicator
from .security_config import SecurityConfigManager, SecurityPolicy, SecurityBaseline

__version__ = "1.0.0"
__author__ = "OS Forge Team"

__all__ = [
    "VulnerabilityScanner",
    "Vulnerability", 
    "ScanResult",
    "SecretsManager",
    "SecretMetadata",
    "SecretAccessLog",
    "SecurityMonitor",
    "SecurityEvent",
    "AlertRule",
    "ThreatIndicator",
    "SecurityConfigManager",
    "SecurityPolicy",
    "SecurityBaseline"
]
