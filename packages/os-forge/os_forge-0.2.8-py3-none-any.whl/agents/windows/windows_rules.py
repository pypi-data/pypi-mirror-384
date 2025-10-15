"""
Windows-specific hardening rules for OS Forge

Contains comprehensive Windows hardening rules based on:
- CIS Benchmarks for Windows
- NIST Guidelines
- Microsoft Security Baselines
- Common Windows vulnerabilities
"""

from typing import Dict, List, Any
from enum import Enum


class WindowsRuleCategory(str, Enum):
    """Categories for Windows hardening rules based on NTRO SIH25237 Annexure A"""
    # NTRO Annexure A Categories
    ACCOUNT_POLICIES = "account_policies"
    LOCAL_POLICIES = "local_policies"
    SYSTEM_SERVICES = "system_services"
    WINDOWS_FIREWALL = "windows_firewall"
    ADVANCED_AUDIT_POLICY = "advanced_audit_policy"
    MICROSOFT_DEFENDER_GUARD = "microsoft_defender_guard"
    AUTOPLAY_POLICIES = "autoplay_policies"
    
    # Additional Security Categories (existing)
    USER_ACCOUNT_CONTROL = "user_account_control"
    WINDOWS_DEFENDER = "windows_defender"
    GROUP_POLICY = "group_policy"
    REGISTRY_SECURITY = "registry_security"
    SERVICE_MANAGEMENT = "service_management"
    NETWORK_SECURITY = "network_security"
    BITLOCKER = "bitlocker"
    AUDIT_LOGGING = "audit_logging"
    WINDOWS_UPDATE = "windows_update"
    REMOTE_ACCESS = "remote_access"
    SYSTEM_CONFIGURATION = "system_configuration"


def get_windows_hardening_rules() -> List[Dict[str, Any]]:
    """
    Get comprehensive list of Windows hardening rules
    
    Returns:
        List of rule dictionaries
    """
    return [
        # User Account Control Rules
        {
            "id": "WIN-UAC-001",
            "description": "Enable User Account Control (UAC)",
            "category": WindowsRuleCategory.USER_ACCOUNT_CONTROL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLUA" | Select-Object -ExpandProperty EnableLUA',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLUA" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLUA" -Value 0',
            "expected": "1",
            "rationale": "UAC prevents unauthorized system changes and malware execution"
        },
        
        {
            "id": "WIN-UAC-002",
            "description": "Set UAC to always notify",
            "category": WindowsRuleCategory.USER_ACCOUNT_CONTROL,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "ConsentPromptBehaviorAdmin" | Select-Object -ExpandProperty ConsentPromptBehaviorAdmin',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "ConsentPromptBehaviorAdmin" -Value 2',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "ConsentPromptBehaviorAdmin" -Value 5',
            "expected": "2",
            "rationale": "Maximum UAC protection requires admin consent for all elevation requests"
        },
        
        # Windows Firewall Rules
        {
            "id": "WIN-FW-001",
            "description": "Enable Windows Firewall for all profiles",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "command",
            "check": 'netsh advfirewall show allprofiles | findstr "State"',
            "remediate_type": "command",
            "remediate": 'netsh advfirewall set allprofiles state on',
            "rollback_type": "command",
            "rollback": 'netsh advfirewall set allprofiles state off',
            "expected": "ON",
            "rationale": "Windows Firewall provides essential network security"
        },
        
        {
            "id": "WIN-FW-002",
            "description": "Block inbound connections by default",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "command",
            "check": 'netsh advfirewall show allprofiles | findstr "Inbound"',
            "remediate_type": "command",
            "remediate": 'netsh advfirewall set allprofiles firewallpolicy blockinbound,allowoutbound',
            "rollback_type": "command",
            "rollback": 'netsh advfirewall set allprofiles firewallpolicy allowinbound,allowoutbound',
            "expected": "BlockInbound",
            "rationale": "Blocking inbound connections by default reduces attack surface"
        },
        
        # Windows Defender Rules
        {
            "id": "WIN-DEF-001",
            "description": "Enable Windows Defender real-time protection",
            "category": WindowsRuleCategory.WINDOWS_DEFENDER,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring',
            "remediate_type": "powershell",
            "remediate": 'Set-MpPreference -DisableRealtimeMonitoring 0',
            "rollback_type": "powershell",
            "rollback": 'Set-MpPreference -DisableRealtimeMonitoring 1',
            "expected": "False",
            "rationale": "Real-time protection prevents malware execution"
        },
        
        {
            "id": "WIN-DEF-002",
            "description": "Enable Windows Defender cloud protection",
            "category": WindowsRuleCategory.WINDOWS_DEFENDER,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-MpPreference | Select-Object -ExpandProperty MAPSReporting',
            "remediate_type": "powershell",
            "remediate": 'Set-MpPreference -MAPSReporting 2',
            "rollback_type": "powershell",
            "rollback": 'Set-MpPreference -MAPSReporting 0',
            "expected": "2",
            "rationale": "Cloud protection provides enhanced threat detection"
        },
        
        {
            "id": "WIN-DEF-003",
            "description": "Enable Windows Defender automatic sample submission",
            "category": WindowsRuleCategory.WINDOWS_DEFENDER,
            "os": ["windows"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-MpPreference | Select-Object -ExpandProperty SubmitSamplesConsent',
            "remediate_type": "powershell",
            "remediate": 'Set-MpPreference -SubmitSamplesConsent 2',
            "rollback_type": "powershell",
            "rollback": 'Set-MpPreference -SubmitSamplesConsent 0',
            "expected": "2",
            "rationale": "Sample submission helps improve threat detection"
        },
        
        # Group Policy Rules
        {
            "id": "WIN-GP-001",
            "description": "Disable guest account",
            "category": WindowsRuleCategory.GROUP_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-LocalUser -Name "Guest" | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'Disable-LocalUser -Name "Guest"',
            "rollback_type": "powershell",
            "rollback": 'Enable-LocalUser -Name "Guest"',
            "expected": "False",
            "rationale": "Guest account provides unauthorized access to the system"
        },
        
        {
            "id": "WIN-GP-002",
            "description": "Disable SMBv1 protocol",
            "category": WindowsRuleCategory.GROUP_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol | Select-Object -ExpandProperty State',
            "remediate_type": "powershell",
            "remediate": 'Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart',
            "rollback_type": "powershell",
            "rollback": 'Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart',
            "expected": "Disabled",
            "rationale": "SMBv1 has known security vulnerabilities"
        },
        
        {
            "id": "WIN-GP-003",
            "description": "Disable SMBv2 client",
            "category": WindowsRuleCategory.GROUP_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "RequireSecuritySignature" | Select-Object -ExpandProperty RequireSecuritySignature',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "RequireSecuritySignature" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "RequireSecuritySignature" -Value 0',
            "expected": "1",
            "rationale": "Requiring security signatures prevents man-in-the-middle attacks"
        },
        
        # Registry Security Rules
        {
            "id": "WIN-REG-001",
            "description": "Disable Windows Script Host",
            "category": WindowsRuleCategory.REGISTRY_SECURITY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Script Host\\Settings" -Name "Enabled" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'New-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Script Host\\Settings" -Force; Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Script Host\\Settings" -Name "Enabled" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Remove-Item -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Script Host\\Settings" -Recurse -Force',
            "expected": "0",
            "rationale": "Disabling WSH prevents malicious script execution"
        },
        
        {
            "id": "WIN-REG-002",
            "description": "Disable AutoRun for all drives",
            "category": WindowsRuleCategory.REGISTRY_SECURITY,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun" | Select-Object -ExpandProperty NoDriveTypeAutoRun',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun" -Value 255',
            "rollback_type": "powershell",
            "rollback": 'Remove-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun"',
            "expected": "255",
            "rationale": "Disabling AutoRun prevents malware from executing from removable drives"
        },
        
        # Service Management Rules
        {
            "id": "WIN-SVC-001",
            "description": "Disable Telnet service",
            "category": WindowsRuleCategory.SERVICE_MANAGEMENT,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "Telnet" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Stop-Service -Name "Telnet" -ErrorAction SilentlyContinue; Set-Service -Name "Telnet" -StartupType Disabled -ErrorAction SilentlyContinue',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "Telnet" -StartupType Manual -ErrorAction SilentlyContinue',
            "expected": "Stopped",
            "rationale": "Telnet transmits credentials in plain text"
        },
        
        {
            "id": "WIN-SVC-002",
            "description": "Disable Remote Registry service",
            "category": WindowsRuleCategory.SERVICE_MANAGEMENT,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "RemoteRegistry" | Select-Object -ExpandProperty StartType',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "RemoteRegistry" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "RemoteRegistry" -StartupType Manual',
            "expected": "Disabled",
            "rationale": "Remote Registry allows unauthorized access to registry"
        },
        
        # Network Security Rules
        {
            "id": "WIN-NET-001",
            "description": "Disable NetBIOS over TCP/IP",
            "category": WindowsRuleCategory.NETWORK_SECURITY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetAdapterBinding -ComponentID ms_tcpip6 | Where-Object Name -like "*NetBIOS*" | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'Disable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6',
            "rollback_type": "powershell",
            "rollback": 'Enable-NetAdapterBinding -Name "*" -ComponentID ms_tcpip6',
            "expected": "False",
            "rationale": "NetBIOS over TCP/IP can leak system information"
        },
        
        {
            "id": "WIN-NET-002",
            "description": "Disable LLMNR (Link-Local Multicast Name Resolution)",
            "category": WindowsRuleCategory.NETWORK_SECURITY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" -Name "EnableMulticast" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty EnableMulticast',
            "remediate_type": "powershell",
            "remediate": 'New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" -Force; Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" -Name "EnableMulticast" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Remove-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" -Recurse -Force',
            "expected": "0",
            "rationale": "LLMNR can be used for DNS poisoning attacks"
        },
        
        # BitLocker Rules
        {
            "id": "WIN-BIT-001",
            "description": "Enable BitLocker for system drive",
            "category": WindowsRuleCategory.BITLOCKER,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-BitLockerVolume -MountPoint "C:" | Select-Object -ExpandProperty VolumeStatus',
            "remediate_type": "powershell",
            "remediate": 'Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -UsedSpaceOnly',
            "rollback_type": "powershell",
            "rollback": 'Disable-BitLocker -MountPoint "C:"',
            "expected": "FullyEncrypted",
            "rationale": "BitLocker protects data in case of physical theft"
        },
        
        {
            "id": "WIN-BIT-002",
            "description": "Configure BitLocker to use TPM + PIN",
            "category": WindowsRuleCategory.BITLOCKER,
            "os": ["windows"],
            "severity": "medium",
            "level": ["strict"],
            "check_type": "powershell",
            "check": 'Get-BitLockerVolume -MountPoint "C:" | Select-Object -ExpandProperty KeyProtector',
            "remediate_type": "powershell",
            "remediate": 'Add-BitLockerKeyProtector -MountPoint "C:" -TpmAndPinProtector',
            "rollback_type": "powershell",
            "rollback": 'Remove-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId (Get-BitLockerVolume -MountPoint "C:").KeyProtector[0].KeyProtectorId',
            "expected": "TpmAndPin",
            "rationale": "TPM + PIN provides stronger authentication than TPM alone"
        },
        
        # Audit Logging Rules
        {
            "id": "WIN-AUDIT-001",
            "description": "Enable audit logon events",
            "category": WindowsRuleCategory.AUDIT_LOGGING,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Logon/Logoff" | findstr "Logon"',
            "remediate_type": "command",
            "remediate": 'auditpol /set /category:"Logon/Logoff" /success:enable /failure:enable',
            "rollback_type": "command",
            "rollback": 'auditpol /set /category:"Logon/Logoff" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audit logging helps track security events"
        },
        
        {
            "id": "WIN-AUDIT-002",
            "description": "Enable audit object access",
            "category": WindowsRuleCategory.AUDIT_LOGGING,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Object Access" | findstr "Object Access"',
            "remediate_type": "command",
            "remediate": 'auditpol /set /category:"Object Access" /success:enable /failure:enable',
            "rollback_type": "command",
            "rollback": 'auditpol /set /category:"Object Access" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Object access auditing tracks file and registry access"
        },
        
        # Windows Update Rules
        {
            "id": "WIN-UPD-001",
            "description": "Enable automatic Windows updates",
            "category": WindowsRuleCategory.WINDOWS_UPDATE,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "NoAutoUpdate" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty NoAutoUpdate',
            "remediate_type": "powershell",
            "remediate": 'New-Item -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Force; Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "NoAutoUpdate" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "NoAutoUpdate" -Value 1',
            "expected": "0",
            "rationale": "Automatic updates keep system patched with security fixes"
        },
        
        {
            "id": "WIN-UPD-002",
            "description": "Configure Windows Update to install updates automatically",
            "category": WindowsRuleCategory.WINDOWS_UPDATE,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "AUOptions" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty AUOptions',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "AUOptions" -Value 4',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" -Name "AUOptions" -Value 2',
            "expected": "4",
            "rationale": "Automatic installation ensures critical updates are applied promptly"
        },
        
        # Remote Access Rules
        {
            "id": "WIN-RDP-001",
            "description": "Enable Network Level Authentication for RDP",
            "category": WindowsRuleCategory.REMOTE_ACCESS,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "UserAuthentication" | Select-Object -ExpandProperty UserAuthentication',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "UserAuthentication" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "UserAuthentication" -Value 0',
            "expected": "1",
            "rationale": "NLA prevents RDP brute force attacks"
        },
        
        {
            "id": "WIN-RDP-002",
            "description": "Set RDP encryption level to High",
            "category": WindowsRuleCategory.REMOTE_ACCESS,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "MinEncryptionLevel" | Select-Object -ExpandProperty MinEncryptionLevel',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "MinEncryptionLevel" -Value 3',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" -Name "MinEncryptionLevel" -Value 1',
            "expected": "3",
            "rationale": "High encryption level protects RDP sessions from eavesdropping"
        },
        
        # System Configuration Rules
        {
            "id": "WIN-SYS-001",
            "description": "Disable Windows Error Reporting",
            "category": WindowsRuleCategory.SYSTEM_CONFIGURATION,
            "os": ["windows"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" -Name "Disabled" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Disabled',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" -Name "Disabled" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" -Name "Disabled" -Value 0',
            "expected": "1",
            "rationale": "Disabling error reporting prevents potential information leakage"
        },
        
        {
            "id": "WIN-SYS-002",
            "description": "Disable Windows Search indexing",
            "category": WindowsRuleCategory.SYSTEM_CONFIGURATION,
            "os": ["windows"],
            "severity": "low",
            "level": ["strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "WSearch" | Select-Object -ExpandProperty StartType',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "WSearch" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "WSearch" -StartupType Automatic',
            "expected": "Disabled",
            "rationale": "Disabling search indexing reduces system resource usage and attack surface"
        },

        # ===== NTRO SIH25237 ANNEXURE A RULES =====
        
        # Account Policies - Password Policy
        {
            "id": "WIN-ACC-001",
            "description": "Ensure 'Enforce password history' is set to '24 or more password(s)'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "PasswordHistory" | Select-Object -ExpandProperty PasswordHistory',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "PasswordHistory" -Value 24',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "PasswordHistory" -Value 0',
            "expected": "24",
            "rationale": "Prevents reuse of recent passwords"
        },
        {
            "id": "WIN-ACC-002",
            "description": "Ensure 'Maximum password age' is set to '90 days, but not 0'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MaximumPasswordAge" | Select-Object -ExpandProperty MaximumPasswordAge',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MaximumPasswordAge" -Value 90',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MaximumPasswordAge" -Value 0',
            "expected": "90",
            "rationale": "Ensures passwords are changed regularly"
        },
        {
            "id": "WIN-ACC-003",
            "description": "Ensure 'Minimum password age' is set to '1 day'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordAge" | Select-Object -ExpandProperty MinimumPasswordAge',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordAge" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordAge" -Value 0',
            "expected": "1",
            "rationale": "Prevents immediate password changes"
        },
        {
            "id": "WIN-ACC-004",
            "description": "Ensure 'Minimum password length' is set to '12 or more character(s)'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordLength" | Select-Object -ExpandProperty MinimumPasswordLength',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordLength" -Value 12',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "MinimumPasswordLength" -Value 0',
            "expected": "12",
            "rationale": "Ensures passwords are sufficiently long"
        },
        {
            "id": "WIN-ACC-005",
            "description": "Ensure 'Password must meet complexity requirements' is set to 'Enabled'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "PasswordComplexity" | Select-Object -ExpandProperty PasswordComplexity',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "PasswordComplexity" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "PasswordComplexity" -Value 0',
            "expected": "1",
            "rationale": "Ensures passwords meet complexity requirements"
        },
        {
            "id": "WIN-ACC-006",
            "description": "Ensure 'Store passwords using reversible encryption' is set to 'Disabled'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "StoreCleartextPassword" | Select-Object -ExpandProperty StoreCleartextPassword',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "StoreCleartextPassword" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "StoreCleartextPassword" -Value 1',
            "expected": "0",
            "rationale": "Prevents storage of passwords in reversible encryption"
        },

        # Account Policies - Account Lockout Policy
        {
            "id": "WIN-ACC-007",
            "description": "Ensure 'Account lockout duration' is set to '15 or more minute(s)'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutDuration" | Select-Object -ExpandProperty LockoutDuration',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutDuration" -Value 15',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutDuration" -Value 0',
            "expected": "15",
            "rationale": "Prevents brute force attacks"
        },
        {
            "id": "WIN-ACC-008",
            "description": "Ensure 'Account lockout threshold' is set to '5 or fewer invalid logon attempt(s), but not 0'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutThreshold" | Select-Object -ExpandProperty LockoutThreshold',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutThreshold" -Value 5',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutThreshold" -Value 0',
            "expected": "5",
            "rationale": "Limits failed login attempts"
        },
        {
            "id": "WIN-ACC-009",
            "description": "Ensure 'Allow Administrator account lockout' is set to 'Enabled'",
            "category": WindowsRuleCategory.ACCOUNT_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutBadCount" | Select-Object -ExpandProperty LockoutBadCount',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutBadCount" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Netlogon\\Parameters" -Name "LockoutBadCount" -Value 0',
            "expected": "1",
            "rationale": "Applies lockout policy to administrator account"
        },

        # Local Policies - User Rights Assignment
        {
            "id": "WIN-LOC-001",
            "description": "Ensure 'Access Credential Manager as a trusted caller' is set to 'No One'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeTrustedCredManAccessPrivilege" | Select-Object -ExpandProperty SeTrustedCredManAccessPrivilege',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeTrustedCredManAccessPrivilege" -Value ""',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeTrustedCredManAccessPrivilege" -Value "S-1-5-32-544"',
            "expected": "",
            "rationale": "Restricts access to credential manager"
        },
        {
            "id": "WIN-LOC-002",
            "description": "Ensure 'Access this computer from the network' is set to 'Administrators, Remote Desktop Users'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeNetworkLogonRight" | Select-Object -ExpandProperty SeNetworkLogonRight',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeNetworkLogonRight" -Value "S-1-5-32-544,S-1-5-32-555"',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeNetworkLogonRight" -Value "S-1-5-32-544,S-1-5-32-555,S-1-1-0"',
            "expected": "S-1-5-32-544,S-1-5-32-555",
            "rationale": "Restricts network access to authorized users"
        },
        {
            "id": "WIN-LOC-003",
            "description": "Ensure 'Adjust memory quotas for a process' is set to 'Administrators, LOCAL SERVICE, NETWORK SERVICE'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeIncreaseQuotaPrivilege" | Select-Object -ExpandProperty SeIncreaseQuotaPrivilege',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeIncreaseQuotaPrivilege" -Value "S-1-5-32-544,S-1-5-19,S-1-5-20"',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeIncreaseQuotaPrivilege" -Value "S-1-5-32-544,S-1-5-19,S-1-5-20,S-1-1-0"',
            "expected": "S-1-5-32-544,S-1-5-19,S-1-5-20",
            "rationale": "Restricts memory quota adjustment privileges"
        },
        {
            "id": "WIN-LOC-004",
            "description": "Ensure 'Allow log on locally' is set to 'Administrators, Users'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeInteractiveLogonRight" | Select-Object -ExpandProperty SeInteractiveLogonRight',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeInteractiveLogonRight" -Value "S-1-5-32-544,S-1-5-32-545"',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeInteractiveLogonRight" -Value "S-1-5-32-544,S-1-5-32-545,S-1-1-0"',
            "expected": "S-1-5-32-544,S-1-5-32-545",
            "rationale": "Restricts local logon to authorized users"
        },
        {
            "id": "WIN-LOC-005",
            "description": "Ensure 'Back up files and directories' is set to 'Administrators'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeBackupPrivilege" | Select-Object -ExpandProperty SeBackupPrivilege',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeBackupPrivilege" -Value "S-1-5-32-544"',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "SeBackupPrivilege" -Value "S-1-5-32-544,S-1-1-0"',
            "expected": "S-1-5-32-544",
            "rationale": "Restricts backup privileges to administrators"
        },

        # Local Policies - Security Options - Accounts
        {
            "id": "WIN-LOC-006",
            "description": "Ensure 'Accounts: Block Microsoft accounts' is set to 'Users can't add or log on with Microsoft accounts'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "NoConnectedUser" | Select-Object -ExpandProperty NoConnectedUser',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "NoConnectedUser" -Value 3',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "NoConnectedUser" -Value 0',
            "expected": "3",
            "rationale": "Prevents Microsoft account usage"
        },
        {
            "id": "WIN-LOC-007",
            "description": "Ensure 'Accounts: Guest account status' is set to 'Disabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-LocalUser -Name "Guest" | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'Disable-LocalUser -Name "Guest"',
            "rollback_type": "powershell",
            "rollback": 'Enable-LocalUser -Name "Guest"',
            "expected": "False",
            "rationale": "Disables guest account access"
        },
        {
            "id": "WIN-LOC-008",
            "description": "Ensure 'Accounts: Limit local account use of blank passwords to console logon only' is set to 'Enabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "LimitBlankPasswordUse" | Select-Object -ExpandProperty LimitBlankPasswordUse',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "LimitBlankPasswordUse" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "LimitBlankPasswordUse" -Value 0',
            "expected": "1",
            "rationale": "Restricts blank password usage to console only"
        },

        # Local Policies - Security Options - Interactive logon
        {
            "id": "WIN-LOC-009",
            "description": "Ensure 'Interactive logon: Do not require CTRL+ALT+DEL' is set to 'Disabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableCAD" | Select-Object -ExpandProperty DisableCAD',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableCAD" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DisableCAD" -Value 1',
            "expected": "0",
            "rationale": "Requires CTRL+ALT+DEL for secure logon"
        },
        {
            "id": "WIN-LOC-010",
            "description": "Ensure 'Interactive logon: Don't display last signed in' is set to 'Enabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DontDisplayLastUserName" | Select-Object -ExpandProperty DontDisplayLastUserName',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DontDisplayLastUserName" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "DontDisplayLastUserName" -Value 0',
            "expected": "1",
            "rationale": "Prevents username disclosure"
        },
        {
            "id": "WIN-LOC-011",
            "description": "Ensure 'Interactive logon: Machine inactivity limit' is set to '900 or fewer second(s), but not 0'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "InactivityTimeoutSecs" | Select-Object -ExpandProperty InactivityTimeoutSecs',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "InactivityTimeoutSecs" -Value 900',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "InactivityTimeoutSecs" -Value 0',
            "expected": "900",
            "rationale": "Automatically locks inactive sessions"
        },

        # Local Policies - Security Options - Microsoft network server
        {
            "id": "WIN-LOC-012",
            "description": "Ensure 'Microsoft network server: Amount of idle time required before suspending session' is set to '15 or fewer minute(s)'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "Autodisconnect" | Select-Object -ExpandProperty Autodisconnect',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "Autodisconnect" -Value 15',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "Autodisconnect" -Value 0',
            "expected": "15",
            "rationale": "Automatically disconnects idle sessions"
        },
        {
            "id": "WIN-LOC-013",
            "description": "Ensure 'Microsoft network server: Disconnect clients when logon hours expire' is set to 'Enabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "EnableForcedLogoff" | Select-Object -ExpandProperty EnableForcedLogoff',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "EnableForcedLogoff" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" -Name "EnableForcedLogoff" -Value 0',
            "expected": "1",
            "rationale": "Enforces logon hour restrictions"
        },
        {
            "id": "WIN-LOC-014",
            "description": "Ensure 'Network access: Allow anonymous SID/Name translation' is set to 'Disabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymous" | Select-Object -ExpandProperty RestrictAnonymous',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymous" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymous" -Value 0',
            "expected": "1",
            "rationale": "Prevents anonymous SID/Name translation"
        },
        {
            "id": "WIN-LOC-015",
            "description": "Ensure 'Network access: Do not allow anonymous enumeration of SAM accounts' is set to 'Enabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymousSAM" | Select-Object -ExpandProperty RestrictAnonymousSAM',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymousSAM" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "RestrictAnonymousSAM" -Value 0',
            "expected": "1",
            "rationale": "Prevents anonymous SAM enumeration"
        },

        # Local Policies - Security Options - Network security
        {
            "id": "WIN-LOC-016",
            "description": "Ensure 'Network security: Do not store LAN Manager hash value on next password change' is set to 'Enabled'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "NoLMHash" | Select-Object -ExpandProperty NoLMHash',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "NoLMHash" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa" -Name "NoLMHash" -Value 0',
            "expected": "1",
            "rationale": "Prevents weak LAN Manager hash storage"
        },
        {
            "id": "WIN-LOC-017",
            "description": "Ensure 'Network security: LDAP client signing requirements' is set to 'Negotiate signing' or higher",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LDAP" -Name "LDAPClientIntegrity" | Select-Object -ExpandProperty LDAPClientIntegrity',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LDAP" -Name "LDAPClientIntegrity" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LDAP" -Name "LDAPClientIntegrity" -Value 0',
            "expected": "1",
            "rationale": "Requires LDAP client signing"
        },
        {
            "id": "WIN-LOC-018",
            "description": "Ensure 'Network security: Minimum session security for NTLM SSP based clients' is set to 'Require NTLMv2 session security, Require 128-bit encryption'",
            "category": WindowsRuleCategory.LOCAL_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa\\MSV1_0" -Name "NTLMMinClientSec" | Select-Object -ExpandProperty NTLMMinClientSec',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa\\MSV1_0" -Name "NTLMMinClientSec" -Value 537395200',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa\\MSV1_0" -Name "NTLMMinClientSec" -Value 0',
            "expected": "537395200",
            "rationale": "Requires strong NTLM client security"
        },

        # System Services - Disable unnecessary services
        {
            "id": "WIN-SVC-003",
            "description": "Ensure 'Bluetooth Audio Gateway Service (BTAGService)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "BTAGService" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "BTAGService" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "BTAGService" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables unnecessary Bluetooth service"
        },
        {
            "id": "WIN-SVC-004",
            "description": "Ensure 'Bluetooth Support Service (bthserv)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "bthserv" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "bthserv" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "bthserv" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables Bluetooth support service"
        },
        {
            "id": "WIN-SVC-005",
            "description": "Ensure 'Computer Browser (Browser)' is set to 'Disabled' or 'Not Installed'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "Browser" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "Browser" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "Browser" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables computer browser service"
        },
        {
            "id": "WIN-SVC-006",
            "description": "Ensure 'Geolocation Service (lfsvc)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "lfsvc" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "lfsvc" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "lfsvc" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables geolocation service"
        },
        {
            "id": "WIN-SVC-007",
            "description": "Ensure 'Internet Connection Sharing (ICS) (SharedAccess)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "SharedAccess" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "SharedAccess" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "SharedAccess" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables internet connection sharing"
        },
        {
            "id": "WIN-SVC-008",
            "description": "Ensure 'Remote Desktop Configuration (SessionEnv)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "SessionEnv" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "SessionEnv" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "SessionEnv" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables remote desktop configuration"
        },
        {
            "id": "WIN-SVC-009",
            "description": "Ensure 'Remote Desktop Services (TermService)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "TermService" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "TermService" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "TermService" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables remote desktop services"
        },
        {
            "id": "WIN-SVC-010",
            "description": "Ensure 'Remote Registry (RemoteRegistry)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "RemoteRegistry" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "RemoteRegistry" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "RemoteRegistry" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables remote registry access"
        },
        {
            "id": "WIN-SVC-011",
            "description": "Ensure 'SNMP Service (SNMP)' is set to 'Disabled' or 'Not Installed'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "SNMP" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "SNMP" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "SNMP" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables SNMP service"
        },
        {
            "id": "WIN-SVC-012",
            "description": "Ensure 'UPnP Device Host (upnphost)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "upnphost" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "upnphost" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "upnphost" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables UPnP device host"
        },
        {
            "id": "WIN-SVC-013",
            "description": "Ensure 'Windows Error Reporting Service (WerSvc)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "WerSvc" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "WerSvc" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "WerSvc" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables Windows error reporting"
        },
        {
            "id": "WIN-SVC-014",
            "description": "Ensure 'Windows Remote Management (WS Management) (WinRM)' is set to 'Disabled'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "WinRM" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "WinRM" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "WinRM" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables Windows remote management"
        },
        {
            "id": "WIN-SVC-015",
            "description": "Ensure 'World Wide Web Publishing Service (W3SVC)' is set to 'Disabled' or 'Not Installed'",
            "category": WindowsRuleCategory.SYSTEM_SERVICES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-Service -Name "W3SVC" | Select-Object -ExpandProperty Status',
            "remediate_type": "powershell",
            "remediate": 'Set-Service -Name "W3SVC" -StartupType Disabled',
            "rollback_type": "powershell",
            "rollback": 'Set-Service -Name "W3SVC" -StartupType Automatic',
            "expected": "Stopped",
            "rationale": "Disables web publishing service"
        },

        # Windows Firewall - Private Profile
        {
            "id": "WIN-FW-003",
            "description": "Ensure 'Windows Firewall: Private: Firewall state' is set to 'On (recommended)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Private | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Private -Enabled True',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Private -Enabled False',
            "expected": "True",
            "rationale": "Enables Windows Firewall for private networks"
        },
        {
            "id": "WIN-FW-004",
            "description": "Ensure 'Windows Firewall: Private: Inbound connections' is set to 'Block (default)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Private | Select-Object -ExpandProperty DefaultInboundAction',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Private -DefaultInboundAction Block',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Private -DefaultInboundAction Allow',
            "expected": "Block",
            "rationale": "Blocks inbound connections by default"
        },
        {
            "id": "WIN-FW-005",
            "description": "Ensure 'Windows Firewall: Private: Outbound connections' is set to 'Allow (default)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Private | Select-Object -ExpandProperty DefaultOutboundAction',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Private -DefaultOutboundAction Allow',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Private -DefaultOutboundAction Block',
            "expected": "Allow",
            "rationale": "Allows outbound connections by default"
        },
        {
            "id": "WIN-FW-006",
            "description": "Ensure 'Windows Firewall: Private: Settings: Display a notification' is set to 'No'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Private | Select-Object -ExpandProperty NotifyOnListen',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Private -NotifyOnListen False',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Private -NotifyOnListen True',
            "expected": "False",
            "rationale": "Disables firewall notifications"
        },

        # Windows Firewall - Public Profile
        {
            "id": "WIN-FW-007",
            "description": "Ensure 'Windows Firewall: Public: Firewall state' is set to 'On (recommended)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Public | Select-Object -ExpandProperty Enabled',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Public -Enabled True',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Public -Enabled False',
            "expected": "True",
            "rationale": "Enables Windows Firewall for public networks"
        },
        {
            "id": "WIN-FW-008",
            "description": "Ensure 'Windows Firewall: Public: Inbound connections' is set to 'Block (default)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Public | Select-Object -ExpandProperty DefaultInboundAction',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Public -DefaultInboundAction Block',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Public -DefaultInboundAction Allow',
            "expected": "Block",
            "rationale": "Blocks inbound connections by default"
        },
        {
            "id": "WIN-FW-009",
            "description": "Ensure 'Windows Firewall: Public: Outbound connections' is set to 'Allow (default)'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Public | Select-Object -ExpandProperty DefaultOutboundAction',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Public -DefaultOutboundAction Allow',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Public -DefaultOutboundAction Block',
            "expected": "Allow",
            "rationale": "Allows outbound connections by default"
        },
        {
            "id": "WIN-FW-010",
            "description": "Ensure 'Windows Firewall: Public: Settings: Display a notification' is set to 'No'",
            "category": WindowsRuleCategory.WINDOWS_FIREWALL,
            "os": ["windows"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-NetFirewallProfile -Profile Public | Select-Object -ExpandProperty NotifyOnListen',
            "remediate_type": "powershell",
            "remediate": 'Set-NetFirewallProfile -Profile Public -NotifyOnListen False',
            "rollback_type": "powershell",
            "rollback": 'Set-NetFirewallProfile -Profile Public -NotifyOnListen True',
            "expected": "False",
            "rationale": "Disables firewall notifications"
        },

        # Advanced Audit Policy Configuration
        {
            "id": "WIN-AUDIT-003",
            "description": "Ensure 'Audit Credential Validation' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Account Logon" | Select-String "Credential Validation"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Credential Validation" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits credential validation attempts"
        },
        {
            "id": "WIN-AUDIT-004",
            "description": "Ensure 'Audit Application Group Management' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Account Management" | Select-String "Application Group Management"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Application Group Management" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Application Group Management" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits application group management"
        },
        {
            "id": "WIN-AUDIT-005",
            "description": "Ensure 'Audit Security Group Management' is set to include 'Success'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Account Management" | Select-String "Security Group Management"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Security Group Management" /success:enable /failure:disable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Security Group Management" /success:disable /failure:disable',
            "expected": "Success",
            "rationale": "Audits security group management"
        },
        {
            "id": "WIN-AUDIT-006",
            "description": "Ensure 'Audit User Account Management' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Account Management" | Select-String "User Account Management"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"User Account Management" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits user account management"
        },
        {
            "id": "WIN-AUDIT-007",
            "description": "Ensure 'Audit Process Creation' is set to include 'Success'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Detailed Tracking" | Select-String "Process Creation"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Process Creation" /success:enable /failure:disable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Process Creation" /success:disable /failure:disable',
            "expected": "Success",
            "rationale": "Audits process creation"
        },
        {
            "id": "WIN-AUDIT-008",
            "description": "Ensure 'Audit Account Lockout' is set to include 'Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Account Logon" | Select-String "Account Lockout"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Account Lockout" /success:disable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Account Lockout" /success:disable /failure:disable',
            "expected": "Failure",
            "rationale": "Audits account lockout events"
        },
        {
            "id": "WIN-AUDIT-009",
            "description": "Ensure 'Audit Other Logon/Logoff Events' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Logon/Logoff" | Select-String "Other Logon/Logoff Events"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Other Logon/Logoff Events" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits other logon/logoff events"
        },
        {
            "id": "WIN-AUDIT-010",
            "description": "Ensure 'Audit File Share' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Object Access" | Select-String "File Share"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"File Share" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"File Share" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits file share access"
        },
        {
            "id": "WIN-AUDIT-011",
            "description": "Ensure 'Audit Removable Storage' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Object Access" | Select-String "Removable Storage"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Removable Storage" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Removable Storage" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits removable storage access"
        },
        {
            "id": "WIN-AUDIT-012",
            "description": "Ensure 'Audit Audit Policy Change' is set to include 'Success'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Policy Change" | Select-String "Audit Policy Change"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Audit Policy Change" /success:enable /failure:disable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Audit Policy Change" /success:disable /failure:disable',
            "expected": "Success",
            "rationale": "Audits audit policy changes"
        },
        {
            "id": "WIN-AUDIT-013",
            "description": "Ensure 'Audit Sensitive Privilege Use' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"Privilege Use" | Select-String "Sensitive Privilege Use"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"Sensitive Privilege Use" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits sensitive privilege use"
        },
        {
            "id": "WIN-AUDIT-014",
            "description": "Ensure 'Audit System Integrity' is set to 'Success and Failure'",
            "category": WindowsRuleCategory.ADVANCED_AUDIT_POLICY,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'auditpol /get /category:"System" | Select-String "System Integrity"',
            "remediate_type": "powershell",
            "remediate": 'auditpol /set /subcategory:"System Integrity" /success:enable /failure:enable',
            "rollback_type": "powershell",
            "rollback": 'auditpol /set /subcategory:"System Integrity" /success:disable /failure:disable',
            "expected": "Success and Failure",
            "rationale": "Audits system integrity events"
        },

        # Microsoft Defender Application Guard
        {
            "id": "WIN-DEF-004",
            "description": "Ensure 'Allow auditing events in Microsoft Defender Application Guard' is set to 'Enabled'",
            "category": WindowsRuleCategory.MICROSOFT_DEFENDER_GUARD,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowAuditEventsInWDAG" | Select-Object -ExpandProperty AllowAuditEventsInWDAG',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowAuditEventsInWDAG" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowAuditEventsInWDAG" -Value 0',
            "expected": "1",
            "rationale": "Enables auditing in Application Guard"
        },
        {
            "id": "WIN-DEF-005",
            "description": "Ensure 'Allow camera and microphone access in Microsoft Defender Application Guard' is set to 'Disabled'",
            "category": WindowsRuleCategory.MICROSOFT_DEFENDER_GUARD,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowCameraAndMicrophoneInWDAG" | Select-Object -ExpandProperty AllowCameraAndMicrophoneInWDAG',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowCameraAndMicrophoneInWDAG" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowCameraAndMicrophoneInWDAG" -Value 1',
            "expected": "0",
            "rationale": "Disables camera and microphone access in Application Guard"
        },
        {
            "id": "WIN-DEF-006",
            "description": "Ensure 'Allow data persistence for Microsoft Defender Application Guard' is set to 'Disabled'",
            "category": WindowsRuleCategory.MICROSOFT_DEFENDER_GUARD,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowDataPersistenceInWDAG" | Select-Object -ExpandProperty AllowDataPersistenceInWDAG',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowDataPersistenceInWDAG" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowDataPersistenceInWDAG" -Value 1',
            "expected": "0",
            "rationale": "Disables data persistence in Application Guard"
        },
        {
            "id": "WIN-DEF-007",
            "description": "Ensure 'Allow files to download and save to the host operating system from Microsoft Defender Application Guard' is set to 'Disabled'",
            "category": WindowsRuleCategory.MICROSOFT_DEFENDER_GUARD,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowFileDownloadInWDAG" | Select-Object -ExpandProperty AllowFileDownloadInWDAG',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowFileDownloadInWDAG" -Value 0',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "AllowFileDownloadInWDAG" -Value 1',
            "expected": "0",
            "rationale": "Disables file downloads from Application Guard"
        },

        # AutoPlay Policies
        {
            "id": "WIN-AUTO-001",
            "description": "Ensure 'Disallow Autoplay for non-volume devices' is set to 'Enabled'",
            "category": WindowsRuleCategory.AUTOPLAY_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutoplayfornonVolume" | Select-Object -ExpandProperty NoAutoplayfornonVolume',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutoplayfornonVolume" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutoplayfornonVolume" -Value 0',
            "expected": "1",
            "rationale": "Disables autoplay for non-volume devices"
        },
        {
            "id": "WIN-AUTO-002",
            "description": "Ensure 'Set the default behaviour for AutoRun' is set to 'Enabled: Do not execute any autorun commands'",
            "category": WindowsRuleCategory.AUTOPLAY_POLICIES,
            "os": ["windows"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutorun" | Select-Object -ExpandProperty NoAutorun',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutorun" -Value 1',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoAutorun" -Value 0',
            "expected": "1",
            "rationale": "Disables autorun commands"
        },
        {
            "id": "WIN-AUTO-003",
            "description": "Ensure 'Turn off Autoplay' is set to 'Enabled: All drives'",
            "category": WindowsRuleCategory.AUTOPLAY_POLICIES,
            "os": ["windows"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check_type": "powershell",
            "check": 'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun" | Select-Object -ExpandProperty NoDriveTypeAutoRun',
            "remediate_type": "powershell",
            "remediate": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun" -Value 255',
            "rollback_type": "powershell",
            "rollback": 'Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" -Name "NoDriveTypeAutoRun" -Value 0',
            "expected": "255",
            "rationale": "Disables autoplay for all drives"
        }
    ]


def get_rules_by_category(category: WindowsRuleCategory) -> List[Dict[str, Any]]:
    """
    Get rules filtered by category
    
    Args:
        category: Rule category to filter by
        
    Returns:
        List of rules in the specified category
    """
    all_rules = get_windows_hardening_rules()
    return [rule for rule in all_rules if rule.get('category') == category]


def get_rules_by_severity(severity: str) -> List[Dict[str, Any]]:
    """
    Get rules filtered by severity
    
    Args:
        severity: Severity level to filter by
        
    Returns:
        List of rules with the specified severity
    """
    all_rules = get_windows_hardening_rules()
    return [rule for rule in all_rules if rule.get('severity') == severity]


def get_rules_by_level(level: str) -> List[Dict[str, Any]]:
    """
    Get rules filtered by hardening level
    
    Args:
        level: Hardening level to filter by
        
    Returns:
        List of rules for the specified level
    """
    all_rules = get_windows_hardening_rules()
    return [rule for rule in all_rules if level in rule.get('level', [])]
