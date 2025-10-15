"""
macOS Agent Module for OS Forge

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

from .macos_agent import MacOSAgent
from .macos_agent_manager import MacOSAgentManager
from .macos_agent_cli import macos_cli
from .macos_rules import get_macos_hardening_rules, MacOSRuleCategory

__all__ = [
    'MacOSAgent',
    'MacOSAgentManager', 
    'macos_cli',
    'get_macos_hardening_rules',
    'MacOSRuleCategory'
]
