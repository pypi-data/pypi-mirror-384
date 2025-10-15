"""
Hardening Rules Definitions

Contains all the security hardening rules for different operating systems.
"""

import yaml
from typing import Dict, Any


def get_hardening_rules() -> Dict[str, Any]:
    """
    Load hardening rules from embedded YAML
    
    Returns:
        Dict containing all hardening rules organized by OS
    """
    rules_yaml = """
rules:
  # Windows Rules - Based on CIS Benchmarks
  - id: WIN-001
    description: "Check if Guest account is disabled"
    os: windows
    severity: high
    level: [basic, moderate, strict]
    check: 'powershell -Command "Get-LocalUser -Name Guest | Select-Object -ExpandProperty Enabled"'
    remediate: 'powershell -Command "Disable-LocalUser -Name Guest"'
    rollback: 'powershell -Command "Enable-LocalUser -Name Guest"'
    expected: "False"
  
  - id: WIN-002
    description: "Check Windows Firewall status"
    os: windows
    severity: critical
    level: [basic, moderate, strict]
    check: 'powershell -Command "Get-NetFirewallProfile -Profile Domain | Select-Object -ExpandProperty Enabled"'
    remediate: 'powershell -Command "Set-NetFirewallProfile -Profile Domain -Enabled True"'
    rollback: 'powershell -Command "Set-NetFirewallProfile -Profile Domain -Enabled False"'
    expected: "True"
  
  - id: WIN-003
    description: "Check if SMBv1 is disabled"
    os: windows
    severity: high
    level: [moderate, strict]
    check: 'powershell -Command "Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol | Select-Object -ExpandProperty State"'
    remediate: 'powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart"'
    rollback: 'powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart"'
    expected: "Disabled"
  
  - id: WIN-004
    description: "Check Windows Defender real-time protection"
    os: windows
    severity: critical
    level: [basic, moderate, strict]
    check: 'powershell -Command "Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring"'
    remediate: 'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $false"'
    rollback: 'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"'
    expected: "False"
  
  - id: WIN-005
    description: "Check UAC setting"
    os: windows
    severity: high
    level: [basic, moderate, strict]
    check: 'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD | findstr "0x1"'
    remediate: 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 1 /f'
    rollback: 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 0 /f'
    expected: "0x1"
  
  - id: WIN-006
    description: "Check automatic updates setting"
    os: windows
    severity: medium
    level: [moderate, strict]
    check: 'reg query "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate 2>nul | findstr "0x0" || echo "not_configured"'
    remediate: 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 0 /f'
    rollback: 'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /f'
    expected: "0x0"
  
  - id: WIN-007
    description: "Check RDP security settings"
    os: windows
    severity: high
    level: [strict]
    check: 'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v SecurityLayer | findstr "0x2"'
    remediate: 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v SecurityLayer /t REG_DWORD /d 2 /f'
    rollback: 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v SecurityLayer /t REG_DWORD /d 0 /f'
    expected: "0x2"
  
  # Linux Rules - Based on CIS Benchmarks
  - id: LIN-001
    description: "Check if SSH root login is disabled"
    os: [ubuntu, centos, linux]
    severity: high
    level: [basic, moderate, strict]
    check: 'grep "^PermitRootLogin" /etc/ssh/sshd_config || echo "PermitRootLogin yes"'
    remediate: 'sudo sed -i "s/^PermitRootLogin.*/PermitRootLogin no/" /etc/ssh/sshd_config && sudo systemctl reload ssh'
    rollback: 'sudo sed -i "s/^PermitRootLogin.*/PermitRootLogin yes/" /etc/ssh/sshd_config && sudo systemctl reload ssh'
    expected: "PermitRootLogin no"
  
  - id: LIN-002
    description: "Check if UFW firewall is enabled"
    os: [ubuntu, linux]
    severity: high
    level: [basic, moderate, strict]
    check: 'sudo ufw status | grep "Status:" | cut -d" " -f2'
    remediate: 'sudo ufw --force enable'
    rollback: 'sudo ufw --force disable'
    expected: "active"
  
  - id: LIN-003
    description: "Check password minimum length"
    os: [ubuntu, centos, linux]
    severity: medium
    level: [moderate, strict]
    check: 'grep "^minlen" /etc/security/pwquality.conf | cut -d"=" -f2 | tr -d " " || echo "8"'
    remediate: 'echo "minlen = 12" | sudo tee -a /etc/security/pwquality.conf'
    rollback: 'sudo sed -i "/^minlen = 12/d" /etc/security/pwquality.conf'
    expected: "12"
  
  - id: LIN-004
    description: "Check SSH Protocol version"
    os: [ubuntu, centos, linux]
    severity: high
    level: [basic, moderate, strict]
    check: 'grep "^Protocol" /etc/ssh/sshd_config | cut -d" " -f2 || echo "2"'
    remediate: 'echo "Protocol 2" | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh'
    rollback: 'sudo sed -i "/^Protocol 2/d" /etc/ssh/sshd_config && sudo systemctl reload ssh'
    expected: "2"
  
  - id: LIN-005
    description: "Check if password authentication is required for SSH"
    os: [ubuntu, centos, linux]
    severity: medium
    level: [moderate, strict]
    check: 'grep "^PasswordAuthentication" /etc/ssh/sshd_config | cut -d" " -f2 || echo "yes"'
    remediate: 'sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication no/" /etc/ssh/sshd_config && sudo systemctl reload ssh'
    rollback: 'sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config && sudo systemctl reload ssh'
    expected: "no"
  
  - id: LIN-006
    description: "Check if unused filesystems are disabled (cramfs)"
    os: [ubuntu, centos, linux]
    severity: low
    level: [strict]
    check: 'lsmod | grep cramfs || echo "not_loaded"'
    remediate: 'echo "install cramfs /bin/true" | sudo tee -a /etc/modprobe.d/cramfs.conf'
    rollback: 'sudo sed -i "/install cramfs/d" /etc/modprobe.d/cramfs.conf'
    expected: "not_loaded"
  
  - id: LIN-007
    description: "Check secure boot settings"
    os: [ubuntu, centos, linux]
    severity: medium
    level: [moderate, strict]
    check: 'bootctl status 2>/dev/null | grep "Secure Boot" | cut -d":" -f2 | tr -d " " || echo "disabled"'
    remediate: 'echo "Secure boot must be enabled in BIOS/UEFI"'
    rollback: 'echo "Secure boot configuration reverted"'
    expected: "enabled"
  
  - id: LIN-008
    description: "Check if automatic security updates are enabled"
    os: [ubuntu]
    severity: medium
    level: [basic, moderate, strict]
    check: 'grep "^APT::Periodic::Unattended-Upgrade" /etc/apt/apt.conf.d/20auto-upgrades | cut -d"\\"" -f2 || echo "0"'
    remediate: 'echo "APT::Periodic::Unattended-Upgrade \\"1\\";" | sudo tee -a /etc/apt/apt.conf.d/20auto-upgrades'
    rollback: 'sudo sed -i "/APT::Periodic::Unattended-Upgrade/d" /etc/apt/apt.conf.d/20auto-upgrades'
    expected: "1"
  
  - id: LIN-009
    description: "Check kernel parameter for ASLR"
    os: [ubuntu, centos, linux]
    severity: high
    level: [moderate, strict]
    check: 'sysctl kernel.randomize_va_space | cut -d"=" -f2 | tr -d " "'
    remediate: 'echo "kernel.randomize_va_space = 2" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
    rollback: 'sudo sed -i "/kernel.randomize_va_space = 2/d" /etc/sysctl.conf && sudo sysctl -p'
    expected: "2"
  
  - id: LIN-010
    description: "Check if core dumps are restricted"
    os: [ubuntu, centos, linux]
    severity: medium
    level: [strict]
    check: 'sysctl fs.suid_dumpable | cut -d"=" -f2 | tr -d " "'
    remediate: 'echo "fs.suid_dumpable = 0" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
    rollback: 'sudo sed -i "/fs.suid_dumpable = 0/d" /etc/sysctl.conf && sudo sysctl -p'
    expected: "0"
"""
    return yaml.safe_load(rules_yaml)

