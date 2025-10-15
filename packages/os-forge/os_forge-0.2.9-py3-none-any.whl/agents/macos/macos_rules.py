"""
macOS Hardening Rules for OS Forge

Comprehensive set of macOS-specific hardening rules covering:
- System Preferences Security
- FileVault Encryption
- Firewall Configuration
- Gatekeeper Settings
- Privacy Controls
- Network Security
- User Account Security
- System Integrity Protection
"""

from enum import Enum
from typing import List, Dict, Any


class MacOSRuleCategory(Enum):
    """macOS-specific rule categories"""
    SYSTEM_PREFERENCES = "system_preferences"
    FILEVAULT = "filevault"
    FIREWALL = "firewall"
    GATEKEEPER = "gatekeeper"
    PRIVACY = "privacy"
    NETWORK_SECURITY = "network_security"
    USER_SECURITY = "user_security"
    SIP = "system_integrity_protection"
    LOGGING = "logging"
    REMOTE_ACCESS = "remote_access"


def get_macos_hardening_rules() -> List[Dict[str, Any]]:
    """
    Get comprehensive macOS hardening rules
    
    Returns:
        List of macOS hardening rule dictionaries
    """
    return [
        # System Preferences Security
        {
            "id": "MAC-SYS-001",
            "description": "Enable automatic software updates",
            "category": MacOSRuleCategory.SYSTEM_PREFERENCES.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled",
                "expected": "1"
            },
            "remediate": {
                "command": "sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled -bool false"
            }
        },
        {
            "id": "MAC-SYS-002",
            "description": "Enable automatic security updates",
            "category": MacOSRuleCategory.SYSTEM_PREFERENCES.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticSecurityUpdatesEnabled",
                "expected": "1"
            },
            "remediate": {
                "command": "sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticSecurityUpdatesEnabled -bool true"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticSecurityUpdatesEnabled -bool false"
            }
        },
        {
            "id": "MAC-SYS-003",
            "description": "Disable automatic app downloads",
            "category": MacOSRuleCategory.SYSTEM_PREFERENCES.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.SoftwareUpdate AutomaticDownload",
                "expected": "0"
            },
            "remediate": {
                "command": "defaults write com.apple.SoftwareUpdate AutomaticDownload -bool false"
            },
            "rollback": {
                "command": "defaults write com.apple.SoftwareUpdate AutomaticDownload -bool true"
            }
        },

        # FileVault Encryption
        {
            "id": "MAC-FV-001",
            "description": "Enable FileVault disk encryption",
            "category": MacOSRuleCategory.FILEVAULT.value,
            "severity": "critical",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "fdesetup status",
                "expected": "FileVault is On"
            },
            "remediate": {
                "command": "sudo fdesetup enable -user $(whoami)"
            },
            "rollback": {
                "command": "sudo fdesetup disable -user $(whoami)"
            }
        },
        {
            "id": "MAC-FV-002",
            "description": "Set FileVault recovery key",
            "category": MacOSRuleCategory.FILEVAULT.value,
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": {
                "command": "fdesetup hasrecoverykey",
                "expected": "true"
            },
            "remediate": {
                "command": "sudo fdesetup changerecovery -personal"
            },
            "rollback": {
                "command": "sudo fdesetup removerecovery -personal"
            }
        },

        # Firewall Configuration
        {
            "id": "MAC-FW-001",
            "description": "Enable macOS firewall",
            "category": MacOSRuleCategory.FIREWALL.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.alf globalstate",
                "expected": "1"
            },
            "remediate": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 1"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf globalstate -int 0"
            }
        },
        {
            "id": "MAC-FW-002",
            "description": "Enable stealth mode firewall",
            "category": MacOSRuleCategory.FIREWALL.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.alf stealthenabled",
                "expected": "1"
            },
            "remediate": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf stealthenabled -int 1"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf stealthenabled -int 0"
            }
        },
        {
            "id": "MAC-FW-003",
            "description": "Block all incoming connections",
            "category": MacOSRuleCategory.FIREWALL.value,
            "severity": "high",
            "level": ["strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.alf allowsignedenabled",
                "expected": "0"
            },
            "remediate": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf allowsignedenabled -int 0"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.alf allowsignedenabled -int 1"
            }
        },

        # Gatekeeper Settings
        {
            "id": "MAC-GK-001",
            "description": "Enable Gatekeeper",
            "category": MacOSRuleCategory.GATEKEEPER.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "spctl --status",
                "expected": "assessments enabled"
            },
            "remediate": {
                "command": "sudo spctl --master-enable"
            },
            "rollback": {
                "command": "sudo spctl --master-disable"
            }
        },
        {
            "id": "MAC-GK-002",
            "description": "Set Gatekeeper to App Store and identified developers",
            "category": MacOSRuleCategory.GATEKEEPER.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "spctl --status",
                "expected": "assessments enabled"
            },
            "remediate": {
                "command": "sudo spctl --enable --label \"Mac App Store and identified developers\""
            },
            "rollback": {
                "command": "sudo spctl --disable"
            }
        },

        # Privacy Controls
        {
            "id": "MAC-PRIV-001",
            "description": "Disable location services",
            "category": MacOSRuleCategory.PRIVACY.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read /var/db/locationd/Library/Preferences/ByHost/com.apple.locationd LocationServicesEnabled",
                "expected": "0"
            },
            "remediate": {
                "command": "sudo defaults write /var/db/locationd/Library/Preferences/ByHost/com.apple.locationd LocationServicesEnabled -bool false"
            },
            "rollback": {
                "command": "sudo defaults write /var/db/locationd/Library/Preferences/ByHost/com.apple.locationd LocationServicesEnabled -bool true"
            }
        },
        {
            "id": "MAC-PRIV-002",
            "description": "Disable analytics and diagnostics",
            "category": MacOSRuleCategory.PRIVACY.value,
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.analyticsd Disabled",
                "expected": "1"
            },
            "remediate": {
                "command": "sudo defaults write com.apple.analyticsd Disabled -bool true"
            },
            "rollback": {
                "command": "sudo defaults write com.apple.analyticsd Disabled -bool false"
            }
        },
        {
            "id": "MAC-PRIV-003",
            "description": "Disable Siri",
            "category": MacOSRuleCategory.PRIVACY.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.assistant.support 'Assistant Enabled'",
                "expected": "0"
            },
            "remediate": {
                "command": "defaults write com.apple.assistant.support 'Assistant Enabled' -bool false"
            },
            "rollback": {
                "command": "defaults write com.apple.assistant.support 'Assistant Enabled' -bool true"
            }
        },

        # Network Security
        {
            "id": "MAC-NET-001",
            "description": "Disable IPv6",
            "category": MacOSRuleCategory.NETWORK_SECURITY.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "networksetup -getinfo \"Wi-Fi\" | grep \"IPv6: Off\"",
                "expected": "IPv6: Off"
            },
            "remediate": {
                "command": "sudo networksetup -setv6off \"Wi-Fi\""
            },
            "rollback": {
                "command": "sudo networksetup -setv6automatic \"Wi-Fi\""
            }
        },
        {
            "id": "MAC-NET-002",
            "description": "Disable AirDrop",
            "category": MacOSRuleCategory.NETWORK_SECURITY.value,
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.NetworkBrowser DisableAirDrop",
                "expected": "1"
            },
            "remediate": {
                "command": "defaults write com.apple.NetworkBrowser DisableAirDrop -bool true"
            },
            "rollback": {
                "command": "defaults write com.apple.NetworkBrowser DisableAirDrop -bool false"
            }
        },
        {
            "id": "MAC-NET-003",
            "description": "Disable Bluetooth when not in use",
            "category": MacOSRuleCategory.NETWORK_SECURITY.value,
            "severity": "low",
            "level": ["strict"],
            "check": {
                "command": "defaults read com.apple.Bluetooth ControllerPowerState",
                "expected": "0"
            },
            "remediate": {
                "command": "sudo pkill bluetoothd"
            },
            "rollback": {
                "command": "sudo launchctl load /System/Library/LaunchDaemons/com.apple.bluetoothd.plist"
            }
        },

        # User Security
        {
            "id": "MAC-USER-001",
            "description": "Require password immediately after sleep",
            "category": MacOSRuleCategory.USER_SECURITY.value,
            "severity": "medium",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.screensaver askForPassword",
                "expected": "1"
            },
            "remediate": {
                "command": "defaults write com.apple.screensaver askForPassword -bool true"
            },
            "rollback": {
                "command": "defaults write com.apple.screensaver askForPassword -bool false"
            }
        },
        {
            "id": "MAC-USER-002",
            "description": "Set screensaver timeout to 5 minutes",
            "category": MacOSRuleCategory.USER_SECURITY.value,
            "severity": "medium",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read com.apple.screensaver idleTime",
                "expected": "300"
            },
            "remediate": {
                "command": "defaults write com.apple.screensaver idleTime -int 300"
            },
            "rollback": {
                "command": "defaults write com.apple.screensaver idleTime -int 0"
            }
        },
        {
            "id": "MAC-USER-003",
            "description": "Disable automatic login",
            "category": MacOSRuleCategory.USER_SECURITY.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "defaults read /Library/Preferences/com.apple.loginwindow autoLoginUser",
                "expected": ""
            },
            "remediate": {
                "command": "sudo defaults delete /Library/Preferences/com.apple.loginwindow autoLoginUser"
            },
            "rollback": {
                "command": "sudo defaults write /Library/Preferences/com.apple.loginwindow autoLoginUser -string \"\""
            }
        },

        # System Integrity Protection
        {
            "id": "MAC-SIP-001",
            "description": "Enable System Integrity Protection",
            "category": MacOSRuleCategory.SIP.value,
            "severity": "critical",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "csrutil status",
                "expected": "System Integrity Protection status: enabled"
            },
            "remediate": {
                "command": "echo 'SIP must be enabled from Recovery Mode'"
            },
            "rollback": {
                "command": "echo 'SIP must be disabled from Recovery Mode'"
            }
        },

        # Logging
        {
            "id": "MAC-LOG-001",
            "description": "Enable audit logging",
            "category": MacOSRuleCategory.LOGGING.value,
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": {
                "command": "launchctl list | grep auditd",
                "expected": "com.apple.auditd"
            },
            "remediate": {
                "command": "sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.auditd.plist"
            },
            "rollback": {
                "command": "sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.auditd.plist"
            }
        },

        # Remote Access
        {
            "id": "MAC-RDP-001",
            "description": "Disable Remote Management",
            "category": MacOSRuleCategory.REMOTE_ACCESS.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "sudo launchctl list | grep -i remote",
                "expected": ""
            },
            "remediate": {
                "command": "sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off"
            },
            "rollback": {
                "command": "sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -activate -configure -access -on"
            }
        },
        {
            "id": "MAC-RDP-002",
            "description": "Disable Screen Sharing",
            "category": MacOSRuleCategory.REMOTE_ACCESS.value,
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": {
                "command": "sudo launchctl list | grep -i screensharing",
                "expected": ""
            },
            "remediate": {
                "command": "sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.screensharing.plist"
            },
            "rollback": {
                "command": "sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.screensharing.plist"
            }
        }
    ]
