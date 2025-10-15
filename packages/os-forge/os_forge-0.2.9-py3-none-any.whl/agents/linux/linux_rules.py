"""
Linux-specific hardening rules for OS Forge

Contains comprehensive Linux hardening rules based on:
- CIS Benchmarks
- NIST Guidelines
- Security best practices
- Common vulnerabilities
"""

from typing import Dict, List, Any
from enum import Enum


class LinuxRuleCategory(str, Enum):
    """Categories for Linux hardening rules based on NTRO SIH25237"""
    # NTRO Annexure B Categories
    FILESYSTEM = "filesystem"
    PACKAGE_MANAGEMENT = "package_management"
    SERVICES = "services"
    NETWORK = "network"
    HOST_FIREWALL = "host_firewall"
    ACCESS_CONTROL = "access_control"
    USER_ACCOUNTS = "user_accounts"
    LOGGING_AUDITING = "logging_auditing"
    SYSTEM_MAINTENANCE = "system_maintenance"
    
    # Additional Security Categories
    SSH_SECURITY = "ssh_security"
    USER_MANAGEMENT = "user_management"
    FILE_PERMISSIONS = "file_permissions"
    KERNEL_SECURITY = "kernel_security"
    SERVICE_MANAGEMENT = "service_management"
    NETWORK_SECURITY = "network_security"
    LOGGING = "logging"
    SYSTEM_CONFIGURATION = "system_configuration"
    CONTAINER_SECURITY = "container_security"
    RHEL_SPECIFIC = "rhel_specific"
    APPARMOR_SELINUX = "apparmor_selinux"


def get_linux_hardening_rules() -> List[Dict[str, Any]]:
    """
    Get comprehensive list of Linux hardening rules
    
    Returns:
        List of rule dictionaries
    """
    return [
        # ========================================
        # 1. FILESYSTEM RULES (NTRO Section 1)
        # ========================================
        
        # Filesystem Kernel Modules
        {
            "id": "LIN-FS-001",
            "description": "Ensure cramfs kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep cramfs || echo 'cramfs not loaded'",
            "remediate": "echo 'install cramfs /bin/true' | sudo tee -a /etc/modprobe.d/cramfs.conf",
            "rollback": "sudo sed -i '/install cramfs/d' /etc/modprobe.d/cramfs.conf"
        },
        {
            "id": "LIN-FS-002", 
            "description": "Ensure freevxfs kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep freevxfs || echo 'freevxfs not loaded'",
            "remediate": "echo 'install freevxfs /bin/true' | sudo tee -a /etc/modprobe.d/freevxfs.conf",
            "rollback": "sudo sed -i '/install freevxfs/d' /etc/modprobe.d/freevxfs.conf"
        },
        {
            "id": "LIN-FS-003",
            "description": "Ensure hfs kernel module is not available", 
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep hfs || echo 'hfs not loaded'",
            "remediate": "echo 'install hfs /bin/true' | sudo tee -a /etc/modprobe.d/hfs.conf",
            "rollback": "sudo sed -i '/install hfs/d' /etc/modprobe.d/hfs.conf"
        },
        {
            "id": "LIN-FS-004",
            "description": "Ensure hfsplus kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium", 
            "level": ["moderate", "strict"],
            "check": "lsmod | grep hfsplus || echo 'hfsplus not loaded'",
            "remediate": "echo 'install hfsplus /bin/true' | sudo tee -a /etc/modprobe.d/hfsplus.conf",
            "rollback": "sudo sed -i '/install hfsplus/d' /etc/modprobe.d/hfsplus.conf"
        },
        {
            "id": "LIN-FS-005",
            "description": "Ensure jffs2 kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep jffs2 || echo 'jffs2 not loaded'",
            "remediate": "echo 'install jffs2 /bin/true' | sudo tee -a /etc/modprobe.d/jffs2.conf",
            "rollback": "sudo sed -i '/install jffs2/d' /etc/modprobe.d/jffs2.conf"
        },
        {
            "id": "LIN-FS-006",
            "description": "Ensure overlayfs kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep overlay || echo 'overlay not loaded'",
            "remediate": "echo 'install overlay /bin/true' | sudo tee -a /etc/modprobe.d/overlay.conf",
            "rollback": "sudo sed -i '/install overlay/d' /etc/modprobe.d/overlay.conf"
        },
        {
            "id": "LIN-FS-007",
            "description": "Ensure squashfs kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep squashfs || echo 'squashfs not loaded'",
            "remediate": "echo 'install squashfs /bin/true' | sudo tee -a /etc/modprobe.d/squashfs.conf",
            "rollback": "sudo sed -i '/install squashfs/d' /etc/modprobe.d/squashfs.conf"
        },
        {
            "id": "LIN-FS-008",
            "description": "Ensure udf kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep udf || echo 'udf not loaded'",
            "remediate": "echo 'install udf /bin/true' | sudo tee -a /etc/modprobe.d/udf.conf",
            "rollback": "sudo sed -i '/install udf/d' /etc/modprobe.d/udf.conf"
        },
        {
            "id": "LIN-FS-009",
            "description": "Ensure usb-storage kernel module is not available",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep usb_storage || echo 'usb_storage not loaded'",
            "remediate": "echo 'install usb-storage /bin/true' | sudo tee -a /etc/modprobe.d/usb-storage.conf",
            "rollback": "sudo sed -i '/install usb-storage/d' /etc/modprobe.d/usb-storage.conf"
        },
        
        # Filesystem Partitions - /tmp
        {
            "id": "LIN-FS-010",
            "description": "Ensure /tmp is a separate partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /tmp ' | grep -v 'tmpfs' || echo '/tmp not separate partition'",
            "remediate": "echo 'Manual: Create separate /tmp partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-011",
            "description": "Ensure nodev option set on /tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /tmp ' | grep nodev || echo 'nodev not set on /tmp'",
            "remediate": "sudo mount -o remount,nodev /tmp",
            "rollback": "sudo mount -o remount,dev /tmp"
        },
        {
            "id": "LIN-FS-012",
            "description": "Ensure nosuid option set on /tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /tmp ' | grep nosuid || echo 'nosuid not set on /tmp'",
            "remediate": "sudo mount -o remount,nosuid /tmp",
            "rollback": "sudo mount -o remount,suid /tmp"
        },
        {
            "id": "LIN-FS-013",
            "description": "Ensure noexec option set on /tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /tmp ' | grep noexec || echo 'noexec not set on /tmp'",
            "remediate": "sudo mount -o remount,noexec /tmp",
            "rollback": "sudo mount -o remount,exec /tmp"
        },
        
        # Filesystem Partitions - /dev/shm
        {
            "id": "LIN-FS-014",
            "description": "Ensure /dev/shm is a separate partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /dev/shm ' | grep tmpfs || echo '/dev/shm not tmpfs'",
            "remediate": "echo 'tmpfs /dev/shm tmpfs defaults,nodev,nosuid,noexec 0 0' | sudo tee -a /etc/fstab",
            "rollback": "sudo sed -i '/tmpfs.*\\/dev\\/shm/d' /etc/fstab"
        },
        {
            "id": "LIN-FS-015",
            "description": "Ensure nodev option set on /dev/shm partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /dev/shm ' | grep nodev || echo 'nodev not set on /dev/shm'",
            "remediate": "sudo mount -o remount,nodev /dev/shm",
            "rollback": "sudo mount -o remount,dev /dev/shm"
        },
        {
            "id": "LIN-FS-016",
            "description": "Ensure nosuid option set on /dev/shm partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /dev/shm ' | grep nosuid || echo 'nosuid not set on /dev/shm'",
            "remediate": "sudo mount -o remount,nosuid /dev/shm",
            "rollback": "sudo mount -o remount,suid /dev/shm"
        },
        {
            "id": "LIN-FS-017",
            "description": "Ensure noexec option set on /dev/shm partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /dev/shm ' | grep noexec || echo 'noexec not set on /dev/shm'",
            "remediate": "sudo mount -o remount,noexec /dev/shm",
            "rollback": "sudo mount -o remount,exec /dev/shm"
        },
        
        # Filesystem Partitions - /home
        {
            "id": "LIN-FS-018",
            "description": "Ensure separate partition exists for /home",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /home ' | grep -v 'tmpfs' || echo '/home not separate partition'",
            "remediate": "echo 'Manual: Create separate /home partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-019",
            "description": "Ensure nodev option set on /home partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /home ' | grep nodev || echo 'nodev not set on /home'",
            "remediate": "sudo mount -o remount,nodev /home",
            "rollback": "sudo mount -o remount,dev /home"
        },
        {
            "id": "LIN-FS-020",
            "description": "Ensure nosuid option set on /home partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /home ' | grep nosuid || echo 'nosuid not set on /home'",
            "remediate": "sudo mount -o remount,nosuid /home",
            "rollback": "sudo mount -o remount,suid /home"
        },
        
        # Filesystem Partitions - /var
        {
            "id": "LIN-FS-021",
            "description": "Ensure separate partition exists for /var",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var ' | grep -v 'tmpfs' || echo '/var not separate partition'",
            "remediate": "echo 'Manual: Create separate /var partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-022",
            "description": "Ensure nodev option set on /var partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var ' | grep nodev || echo 'nodev not set on /var'",
            "remediate": "sudo mount -o remount,nodev /var",
            "rollback": "sudo mount -o remount,dev /var"
        },
        {
            "id": "LIN-FS-023",
            "description": "Ensure nosuid option set on /var partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var ' | grep nosuid || echo 'nosuid not set on /var'",
            "remediate": "sudo mount -o remount,nosuid /var",
            "rollback": "sudo mount -o remount,suid /var"
        },
        
        # Filesystem Partitions - /var/tmp
        {
            "id": "LIN-FS-024",
            "description": "Ensure separate partition exists for /var/tmp",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/tmp ' | grep -v 'tmpfs' || echo '/var/tmp not separate partition'",
            "remediate": "echo 'Manual: Create separate /var/tmp partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-025",
            "description": "Ensure nodev option set on /var/tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/tmp ' | grep nodev || echo 'nodev not set on /var/tmp'",
            "remediate": "sudo mount -o remount,nodev /var/tmp",
            "rollback": "sudo mount -o remount,dev /var/tmp"
        },
        {
            "id": "LIN-FS-026",
            "description": "Ensure nosuid option set on /var/tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/tmp ' | grep nosuid || echo 'nosuid not set on /var/tmp'",
            "remediate": "sudo mount -o remount,nosuid /var/tmp",
            "rollback": "sudo mount -o remount,suid /var/tmp"
        },
        {
            "id": "LIN-FS-027",
            "description": "Ensure noexec option set on /var/tmp partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/tmp ' | grep noexec || echo 'noexec not set on /var/tmp'",
            "remediate": "sudo mount -o remount,noexec /var/tmp",
            "rollback": "sudo mount -o remount,exec /var/tmp"
        },
        
        # Filesystem Partitions - /var/log
        {
            "id": "LIN-FS-028",
            "description": "Ensure separate partition exists for /var/log",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log ' | grep -v 'tmpfs' || echo '/var/log not separate partition'",
            "remediate": "echo 'Manual: Create separate /var/log partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-029",
            "description": "Ensure nodev option set on /var/log partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log ' | grep nodev || echo 'nodev not set on /var/log'",
            "remediate": "sudo mount -o remount,nodev /var/log",
            "rollback": "sudo mount -o remount,dev /var/log"
        },
        {
            "id": "LIN-FS-030",
            "description": "Ensure nosuid option set on /var/log partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log ' | grep nosuid || echo 'nosuid not set on /var/log'",
            "remediate": "sudo mount -o remount,nosuid /var/log",
            "rollback": "sudo mount -o remount,suid /var/log"
        },
        {
            "id": "LIN-FS-031",
            "description": "Ensure noexec option set on /var/log partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log ' | grep noexec || echo 'noexec not set on /var/log'",
            "remediate": "sudo mount -o remount,noexec /var/log",
            "rollback": "sudo mount -o remount,exec /var/log"
        },
        
        # Filesystem Partitions - /var/log/audit
        {
            "id": "LIN-FS-032",
            "description": "Ensure separate partition exists for /var/log/audit",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log/audit ' | grep -v 'tmpfs' || echo '/var/log/audit not separate partition'",
            "remediate": "echo 'Manual: Create separate /var/log/audit partition during installation'",
            "rollback": "echo 'Manual: Revert to single partition layout'"
        },
        {
            "id": "LIN-FS-033",
            "description": "Ensure nodev option set on /var/log/audit partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log/audit ' | grep nodev || echo 'nodev not set on /var/log/audit'",
            "remediate": "sudo mount -o remount,nodev /var/log/audit",
            "rollback": "sudo mount -o remount,dev /var/log/audit"
        },
        {
            "id": "LIN-FS-034",
            "description": "Ensure nosuid option set on /var/log/audit partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log/audit ' | grep nosuid || echo 'nosuid not set on /var/log/audit'",
            "remediate": "sudo mount -o remount,nosuid /var/log/audit",
            "rollback": "sudo mount -o remount,suid /var/log/audit"
        },
        {
            "id": "LIN-FS-035",
            "description": "Ensure noexec option set on /var/log/audit partition",
            "category": LinuxRuleCategory.FILESYSTEM,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "mount | grep ' /var/log/audit ' | grep noexec || echo 'noexec not set on /var/log/audit'",
            "remediate": "sudo mount -o remount,noexec /var/log/audit",
            "rollback": "sudo mount -o remount,exec /var/log/audit"
        },

        # ========================================
        # 2. PACKAGE MANAGEMENT RULES (NTRO Section 2)
        # ========================================
        
        # Bootloader Configuration
        {
            "id": "LIN-PKG-001",
            "description": "Ensure bootloader password is set",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep -E '^password|^GRUB2_PASSWORD' /boot/grub/grub.cfg || echo 'No bootloader password'",
            "remediate": "echo 'Manual: Set GRUB2 password using grub2-mkpasswd-pbkdf2'",
            "rollback": "echo 'Manual: Remove password from GRUB2 configuration'"
        },
        {
            "id": "LIN-PKG-002",
            "description": "Ensure access to bootloader config is configured",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /boot/grub/grub.cfg | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure permissions'",
            "remediate": "sudo chmod 600 /boot/grub/grub.cfg",
            "rollback": "sudo chmod 644 /boot/grub/grub.cfg"
        },
        
        # Process Hardening
        {
            "id": "LIN-PKG-003",
            "description": "Ensure address space layout randomization is enabled",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["basic", "moderate", "strict"],
            "check": "sysctl kernel.randomize_va_space",
            "remediate": "echo 'kernel.randomize_va_space = 2' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/kernel.randomize_va_space/d' /etc/sysctl.conf && sudo sysctl -p",
            "expected": "kernel.randomize_va_space = 2"
        },
        {
            "id": "LIN-PKG-004",
            "description": "Ensure ptrace_scope is restricted",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl kernel.yama.ptrace_scope | grep 'kernel.yama.ptrace_scope = 1' || echo 'ptrace_scope not restricted'",
            "remediate": "echo 'kernel.yama.ptrace_scope = 1' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/kernel.yama.ptrace_scope/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-PKG-005",
            "description": "Ensure core dumps are restricted",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl fs.suid_dumpable | grep 'fs.suid_dumpable = 0' || echo 'Core dumps not restricted'",
            "remediate": "echo 'fs.suid_dumpable = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/fs.suid_dumpable/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-PKG-006",
            "description": "Ensure prelink is not installed",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep prelink || echo 'prelink not installed'",
            "remediate": "sudo apt-get remove --purge prelink",
            "rollback": "sudo apt-get install prelink"
        },
        {
            "id": "LIN-PKG-007",
            "description": "Ensure Automatic Error Reporting is not enabled",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "systemctl is-enabled apport || echo 'apport not enabled'",
            "remediate": "sudo systemctl disable apport",
            "rollback": "sudo systemctl enable apport"
        },
        
        # Command Line Warning Banners
        {
            "id": "LIN-PKG-008",
            "description": "Ensure local login warning banner is configured properly",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["basic", "moderate", "strict"],
            "check": "cat /etc/issue 2>/dev/null | grep -E 'WARNING|AUTHORIZED' || echo 'No warning banner'",
            "remediate": "echo 'WARNING: This system is for authorized users only. All activities are logged and monitored.' | sudo tee /etc/issue",
            "rollback": "sudo rm /etc/issue",
            "expected": "WARNING: This system is for authorized users only. All activities are logged and monitored."
        },
        {
            "id": "LIN-PKG-009",
            "description": "Ensure remote login warning banner is configured properly",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["basic", "moderate", "strict"],
            "check": "cat /etc/issue.net 2>/dev/null | grep -E 'WARNING|AUTHORIZED' || echo 'No remote warning banner'",
            "remediate": "echo 'WARNING: This system is for authorized users only. All activities are logged and monitored.' | sudo tee /etc/issue.net",
            "rollback": "sudo rm /etc/issue.net",
            "expected": "WARNING: This system is for authorized users only. All activities are logged and monitored."
        },
        {
            "id": "LIN-PKG-010",
            "description": "Ensure access to /etc/motd is configured",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["basic", "moderate", "strict"],
            "check": "if [ -f /etc/motd ]; then stat -c '%a' /etc/motd; else echo 'File does not exist'; fi",
            "remediate": "if [ ! -f /etc/motd ]; then sudo touch /etc/motd; fi && sudo chmod 644 /etc/motd",
            "rollback": "sudo chmod 666 /etc/motd",
            "expected": "644"
        },
        {
            "id": "LIN-PKG-011",
            "description": "Ensure access to /etc/issue is configured",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["basic", "moderate", "strict"],
            "check": "stat -c '%a' /etc/issue | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure issue permissions'",
            "remediate": "sudo chmod 644 /etc/issue",
            "rollback": "sudo chmod 666 /etc/issue",
            "expected": "644"
        },
        {
            "id": "LIN-PKG-012",
            "description": "Ensure access to /etc/issue.net is configured",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["basic", "moderate", "strict"],
            "check": "stat -c '%a' /etc/issue.net | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure issue.net permissions'",
            "remediate": "sudo chmod 644 /etc/issue.net",
            "rollback": "sudo chmod 666 /etc/issue.net",
            "expected": "644"
        },

        # ========================================
        # 4. NETWORK SECURITY RULES (NTRO Section 4)
        # ========================================
        
        # Network Devices
        {
            "id": "LIN-NET-005",
            "description": "Ensure IPv6 status is identified",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "ip -6 addr show | grep -q inet6 || echo 'IPv6 not configured'",
            "remediate": "echo 'Manual: Configure IPv6 if needed'",
            "rollback": "echo 'Manual: Disable IPv6 if not needed'"
        },
        {
            "id": "LIN-NET-006",
            "description": "Ensure wireless interfaces are disabled",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "iwconfig 2>/dev/null | grep -q 'IEEE 802.11' || echo 'No wireless interfaces'",
            "remediate": "sudo rfkill block wifi",
            "rollback": "sudo rfkill unblock wifi"
        },
        {
            "id": "LIN-NET-007",
            "description": "Ensure bluetooth services are not in use",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active bluetooth || echo 'bluetooth not active'",
            "remediate": "sudo systemctl stop bluetooth && sudo systemctl disable bluetooth",
            "rollback": "sudo systemctl enable bluetooth && sudo systemctl start bluetooth"
        },
        
        # Network Kernel Modules
        {
            "id": "LIN-NET-008",
            "description": "Ensure dccp kernel module is not available",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep dccp || echo 'dccp not loaded'",
            "remediate": "echo 'install dccp /bin/true' | sudo tee -a /etc/modprobe.d/dccp.conf",
            "rollback": "sudo sed -i '/install dccp/d' /etc/modprobe.d/dccp.conf"
        },
        {
            "id": "LIN-NET-009",
            "description": "Ensure tipc kernel module is not available",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep tipc || echo 'tipc not loaded'",
            "remediate": "echo 'install tipc /bin/true' | sudo tee -a /etc/modprobe.d/tipc.conf",
            "rollback": "sudo sed -i '/install tipc/d' /etc/modprobe.d/tipc.conf"
        },
        {
            "id": "LIN-NET-010",
            "description": "Ensure rds kernel module is not available",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep rds || echo 'rds not loaded'",
            "remediate": "echo 'install rds /bin/true' | sudo tee -a /etc/modprobe.d/rds.conf",
            "rollback": "sudo sed -i '/install rds/d' /etc/modprobe.d/rds.conf"
        },
        {
            "id": "LIN-NET-011",
            "description": "Ensure sctp kernel module is not available",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "lsmod | grep sctp || echo 'sctp not loaded'",
            "remediate": "echo 'install sctp /bin/true' | sudo tee -a /etc/modprobe.d/sctp.conf",
            "rollback": "sudo sed -i '/install sctp/d' /etc/modprobe.d/sctp.conf"
        },
        
        # Network Kernel Parameters
        {
            "id": "LIN-NET-012",
            "description": "Ensure packet redirect sending is disabled",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.conf.all.send_redirects | grep 'net.ipv4.conf.all.send_redirects = 0' || echo 'Packet redirects enabled'",
            "remediate": "echo 'net.ipv4.conf.all.send_redirects = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.conf.all.send_redirects = 0/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-013",
            "description": "Ensure bogus icmp responses are ignored",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.icmp_ignore_bogus_error_responses | grep 'net.ipv4.icmp_ignore_bogus_error_responses = 1' || echo 'Bogus ICMP responses not ignored'",
            "remediate": "echo 'net.ipv4.icmp_ignore_bogus_error_responses = 1' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.icmp_ignore_bogus_error_responses = 1/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-014",
            "description": "Ensure broadcast icmp requests are ignored",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.icmp_echo_ignore_broadcasts | grep 'net.ipv4.icmp_echo_ignore_broadcasts = 1' || echo 'Broadcast ICMP requests not ignored'",
            "remediate": "echo 'net.ipv4.icmp_echo_ignore_broadcasts = 1' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.icmp_echo_ignore_broadcasts = 1/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-015",
            "description": "Ensure secure icmp redirects are not accepted",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.conf.all.secure_redirects | grep 'net.ipv4.conf.all.secure_redirects = 0' || echo 'Secure ICMP redirects accepted'",
            "remediate": "echo 'net.ipv4.conf.all.secure_redirects = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.conf.all.secure_redirects = 0/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-016",
            "description": "Ensure source routed packets are not accepted",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.conf.all.accept_source_route | grep 'net.ipv4.conf.all.accept_source_route = 0' || echo 'Source routed packets accepted'",
            "remediate": "echo 'net.ipv4.conf.all.accept_source_route = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.conf.all.accept_source_route = 0/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-017",
            "description": "Ensure suspicious packets are logged",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv4.conf.all.log_martians | grep 'net.ipv4.conf.all.log_martians = 1' || echo 'Suspicious packets not logged'",
            "remediate": "echo 'net.ipv4.conf.all.log_martians = 1' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv4.conf.all.log_martians = 1/d' /etc/sysctl.conf && sudo sysctl -p"
        },
        {
            "id": "LIN-NET-018",
            "description": "Ensure ipv6 router advertisements are not accepted",
            "category": LinuxRuleCategory.NETWORK,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sysctl net.ipv6.conf.all.accept_ra | grep 'net.ipv6.conf.all.accept_ra = 0' || echo 'IPv6 router advertisements accepted'",
            "remediate": "echo 'net.ipv6.conf.all.accept_ra = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "rollback": "sudo sed -i '/net.ipv6.conf.all.accept_ra = 0/d' /etc/sysctl.conf && sudo sysctl -p"
        },

        # ========================================
        # 5. HOST BASED FIREWALL RULES (NTRO Section 5)
        # ========================================
        
        {
            "id": "LIN-FW-003",
            "description": "Ensure ufw is installed",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*ufw' | awk '{print $1, $2}' || echo 'ufw not installed'",
            "remediate": "sudo apt-get install ufw",
            "expected": "ii ufw"
        },
        {
            "id": "LIN-FW-004",
            "description": "Ensure iptables-persistent is not installed with ufw",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep iptables-persistent || echo 'iptables-persistent not installed'",
            "remediate": "sudo apt-get remove iptables-persistent",
            "rollback": "sudo apt-get install iptables-persistent"
        },
        {
            "id": "LIN-FW-005",
            "description": "Ensure ufw loopback traffic is configured",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sudo ufw status | grep 'Anywhere on lo' || echo 'Loopback traffic not configured'",
            "remediate": "sudo ufw allow in on lo && sudo ufw allow out on lo",
            "rollback": "sudo ufw delete allow in on lo && sudo ufw delete allow out on lo"
        },
        {
            "id": "LIN-FW-006",
            "description": "Ensure ufw outbound connections are configured",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sudo ufw status | grep 'Anywhere' | grep -q 'ALLOW OUT' || echo 'Outbound connections not configured'",
            "remediate": "sudo ufw default allow out",
            "rollback": "sudo ufw default deny out"
        },
        {
            "id": "LIN-FW-007",
            "description": "Ensure ufw firewall rules exist for all open ports",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "sudo ufw status numbered | grep -q '22/tcp' || echo 'SSH port not configured'",
            "remediate": "sudo ufw allow 22/tcp",
            "rollback": "sudo ufw delete allow 22/tcp"
        },
        {
            "id": "LIN-FW-008",
            "description": "Ensure ufw default deny firewall policy",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "sudo ufw status | grep 'Default:' | grep -q 'deny (incoming)' || echo 'Default deny policy not set'",
            "remediate": "sudo ufw default deny incoming",
            "rollback": "sudo ufw default allow incoming"
        },
        {
            "id": "LIN-FW-009",
            "description": "Ensure ufw is not in use with iptables",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "sudo iptables -L | grep -q 'ufw' || echo 'iptables rules not managed by ufw'",
            "remediate": "sudo ufw --force reset && sudo ufw --force enable",
            "rollback": "sudo ufw disable"
        },

        # ========================================
        # 6. ACCESS CONTROL RULES (NTRO Section 6)
        # ========================================
        
        # SSH Server Configuration
        {
            "id": "LIN-SSH-005",
            "description": "Ensure permissions on /etc/ssh/sshd_config are configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/ssh/sshd_config | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure SSH config permissions'",
            "remediate": "sudo chmod 600 /etc/ssh/sshd_config",
            "rollback": "sudo chmod 644 /etc/ssh/sshd_config"
        },
        {
            "id": "LIN-SSH-006",
            "description": "Ensure permissions on SSH private host key files are configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "find /etc/ssh -name 'ssh_host_*_key' -exec stat -c '%a %n' {} \\; | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure SSH private key permissions'",
            "remediate": "sudo chmod 600 /etc/ssh/ssh_host_*_key",
            "rollback": "sudo chmod 644 /etc/ssh/ssh_host_*_key"
        },
        {
            "id": "LIN-SSH-007",
            "description": "Ensure permissions on SSH public host key files are configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "find /etc/ssh -name 'ssh_host_*_key.pub' -exec stat -c '%a %n' {} \\; | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure SSH public key permissions'",
            "remediate": "sudo chmod 644 /etc/ssh/ssh_host_*_key.pub",
            "rollback": "sudo chmod 666 /etc/ssh/ssh_host_*_key.pub"
        },
        {
            "id": "LIN-SSH-008",
            "description": "Ensure sshd access is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^AllowUsers' /etc/ssh/sshd_config || echo 'No user access restrictions'",
            "remediate": "echo 'AllowUsers root' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^AllowUsers/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-009",
            "description": "Ensure sshd Banner is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "grep '^Banner' /etc/ssh/sshd_config || echo 'No SSH banner'",
            "remediate": "echo 'Banner /etc/issue.net' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^Banner/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-010",
            "description": "Ensure sshd Ciphers are configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^Ciphers' /etc/ssh/sshd_config || echo 'No cipher restrictions'",
            "remediate": "echo 'Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^Ciphers/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-011",
            "description": "Ensure sshd ClientAliveCountMax is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^ClientAliveCountMax' /etc/ssh/sshd_config || echo 'No ClientAliveCountMax'",
            "remediate": "echo 'ClientAliveCountMax 2' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^ClientAliveCountMax/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-012",
            "description": "Ensure sshd DisableForwarding is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^DisableForwarding' /etc/ssh/sshd_config || echo 'Forwarding not disabled'",
            "remediate": "echo 'DisableForwarding yes' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^DisableForwarding/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-013",
            "description": "Ensure sshd GSSAPIAuthentication is disabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^GSSAPIAuthentication' /etc/ssh/sshd_config | grep -q 'no' || echo 'GSSAPI authentication enabled'",
            "remediate": "echo 'GSSAPIAuthentication no' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^GSSAPIAuthentication/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-014",
            "description": "Ensure sshd HostbasedAuthentication is disabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^HostbasedAuthentication' /etc/ssh/sshd_config | grep -q 'no' || echo 'Host-based authentication enabled'",
            "remediate": "echo 'HostbasedAuthentication no' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^HostbasedAuthentication/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-015",
            "description": "Ensure sshd IgnoreRhosts is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^IgnoreRhosts' /etc/ssh/sshd_config | grep -q 'yes' || echo 'Rhosts not ignored'",
            "remediate": "echo 'IgnoreRhosts yes' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^IgnoreRhosts/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-016",
            "description": "Ensure sshd KexAlgorithms is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^KexAlgorithms' /etc/ssh/sshd_config || echo 'No KEX algorithm restrictions'",
            "remediate": "echo 'KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^KexAlgorithms/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-017",
            "description": "Ensure sshd LoginGraceTime is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^LoginGraceTime' /etc/ssh/sshd_config || echo 'No login grace time'",
            "remediate": "echo 'LoginGraceTime 60' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^LoginGraceTime/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-018",
            "description": "Ensure sshd LogLevel is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "grep '^LogLevel' /etc/ssh/sshd_config || echo 'No log level'",
            "remediate": "echo 'LogLevel VERBOSE' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^LogLevel/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-019",
            "description": "Ensure sshd MACs are configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^MACs' /etc/ssh/sshd_config || echo 'No MAC restrictions'",
            "remediate": "echo 'MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^MACs/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-020",
            "description": "Ensure sshd MaxAuthTries is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^MaxAuthTries' /etc/ssh/sshd_config || echo 'No max auth tries'",
            "remediate": "echo 'MaxAuthTries 3' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^MaxAuthTries/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-021",
            "description": "Ensure sshd MaxSessions is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^MaxSessions' /etc/ssh/sshd_config || echo 'No max sessions'",
            "remediate": "echo 'MaxSessions 10' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^MaxSessions/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-022",
            "description": "Ensure sshd MaxStartups is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^MaxStartups' /etc/ssh/sshd_config || echo 'No max startups'",
            "remediate": "echo 'MaxStartups 10:30:60' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^MaxStartups/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-023",
            "description": "Ensure sshd PermitEmptyPasswords is disabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^PermitEmptyPasswords' /etc/ssh/sshd_config | grep -q 'no' || echo 'Empty passwords allowed'",
            "remediate": "echo 'PermitEmptyPasswords no' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^PermitEmptyPasswords/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-024",
            "description": "Ensure sshd PermitUserEnvironment is disabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^PermitUserEnvironment' /etc/ssh/sshd_config | grep -q 'no' || echo 'User environment allowed'",
            "remediate": "echo 'PermitUserEnvironment no' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^PermitUserEnvironment/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        {
            "id": "LIN-SSH-025",
            "description": "Ensure sshd UsePAM is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^UsePAM' /etc/ssh/sshd_config | grep -q 'yes' || echo 'PAM not enabled'",
            "remediate": "echo 'UsePAM yes' | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh",
            "rollback": "sudo sed -i '/^UsePAM/d' /etc/ssh/sshd_config && sudo systemctl reload ssh"
        },
        
        # Privilege Escalation
        {
            "id": "LIN-SUDO-001",
            "description": "Ensure sudo is installed",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*sudo' | awk '{print $1, $2}' || echo 'sudo not installed'",
            "remediate": "sudo apt-get install sudo",
            "expected": "ii sudo"
        },
        {
            "id": "LIN-SUDO-002",
            "description": "Ensure sudo commands use pty",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^Defaults use_pty' /etc/sudoers || echo 'PTY not required'",
            "remediate": "echo 'Defaults use_pty' | sudo tee -a /etc/sudoers",
            "rollback": "sudo sed -i '/^Defaults use_pty/d' /etc/sudoers"
        },
        {
            "id": "LIN-SUDO-003",
            "description": "Ensure sudo log file exists",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^Defaults logfile' /etc/sudoers || echo 'No sudo log file'",
            "remediate": "echo 'Defaults logfile=/var/log/sudo.log' | sudo tee -a /etc/sudoers",
            "rollback": "sudo sed -i '/^Defaults logfile/d' /etc/sudoers"
        },
        {
            "id": "LIN-SUDO-004",
            "description": "Ensure users must provide password for privilege escalation",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^Defaults.*NOPASSWD' /etc/sudoers || echo 'Password required'",
            "remediate": "echo 'Defaults requiretty' | sudo tee -a /etc/sudoers",
            "rollback": "sudo sed -i '/^Defaults requiretty/d' /etc/sudoers"
        },
        {
            "id": "LIN-SUDO-005",
            "description": "Ensure re-authentication for privilege escalation is not disabled globally",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^Defaults.*timestamp_timeout=-1' /etc/sudoers || echo 'Re-authentication enabled'",
            "remediate": "echo 'Defaults timestamp_timeout=15' | sudo tee -a /etc/sudoers",
            "rollback": "sudo sed -i '/^Defaults timestamp_timeout/d' /etc/sudoers"
        },
        {
            "id": "LIN-SUDO-006",
            "description": "Ensure sudo authentication timeout is configured correctly",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^Defaults timestamp_timeout' /etc/sudoers | grep -E '^[0-9]+$' || echo 'No timeout configured'",
            "remediate": "echo 'Defaults timestamp_timeout=15' | sudo tee -a /etc/sudoers",
            "rollback": "sudo sed -i '/^Defaults timestamp_timeout/d' /etc/sudoers"
        },
        {
            "id": "LIN-SUDO-007",
            "description": "Ensure access to the su command is restricted",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^auth.*required.*pam_wheel.so' /etc/pam.d/su || echo 'su access not restricted'",
            "remediate": "echo 'auth required pam_wheel.so use_uid' | sudo tee -a /etc/pam.d/su",
            "rollback": "sudo sed -i '/auth required pam_wheel.so use_uid/d' /etc/pam.d/su"
        },

        # ========================================
        # 7. PAM AUTHENTICATION MODULES (NTRO Section 6c)
        # ========================================
        
        # PAM Software Packages
        {
            "id": "LIN-PAM-001",
            "description": "Ensure latest version of pam is installed",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*libpam0g' || echo 'PAM not installed'",
            "remediate": "sudo apt-get install libpam0g",
            "rollback": "sudo apt-get remove libpam0g"
        },
        {
            "id": "LIN-PAM-002",
            "description": "Ensure libpam-modules is installed",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*libpam-modules' || echo 'PAM modules not installed'",
            "remediate": "sudo apt-get install libpam-modules",
            "rollback": "sudo apt-get remove libpam-modules"
        },
        {
            "id": "LIN-PAM-003",
            "description": "Ensure libpam-pwquality is installed",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*libpam-pwquality' || echo 'PAM pwquality not installed'",
            "remediate": "sudo apt-get install libpam-pwquality",
            "rollback": "sudo apt-get remove libpam-pwquality"
        },
        
        # PAM Auth Update Profiles
        {
            "id": "LIN-PAM-004",
            "description": "Ensure pam_unix module is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^@include common-auth' /etc/pam.d/login || echo 'pam_unix not enabled'",
            "remediate": "echo 'Manual: Ensure @include common-auth is in PAM configs'",
            "rollback": "echo 'Manual: Remove @include common-auth from PAM configs'"
        },
        {
            "id": "LIN-PAM-005",
            "description": "Ensure pam_faillock module is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'pam_faillock.so' /etc/pam.d/common-auth || echo 'pam_faillock not enabled'",
            "remediate": "echo 'auth required pam_faillock.so preauth' | sudo tee -a /etc/pam.d/common-auth",
            "rollback": "sudo sed -i '/pam_faillock.so/d' /etc/pam.d/common-auth"
        },
        {
            "id": "LIN-PAM-006",
            "description": "Ensure pam_pwquality module is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'pam_pwquality.so' /etc/pam.d/common-password || echo 'pam_pwquality not enabled'",
            "remediate": "echo 'password requisite pam_pwquality.so retry=3' | sudo tee -a /etc/pam.d/common-password",
            "rollback": "sudo sed -i '/pam_pwquality.so/d' /etc/pam.d/common-password"
        },
        {
            "id": "LIN-PAM-007",
            "description": "Ensure pam_pwhistory module is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'pam_pwhistory.so' /etc/pam.d/common-password || echo 'pam_pwhistory not enabled'",
            "remediate": "echo 'password required pam_pwhistory.so remember=5' | sudo tee -a /etc/pam.d/common-password",
            "rollback": "sudo sed -i '/pam_pwhistory.so/d' /etc/pam.d/common-password"
        },
        
        # PAM Faillock Module
        {
            "id": "LIN-PAM-008",
            "description": "Ensure password failed attempts lockout is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'deny=' /etc/security/faillock.conf || echo 'No lockout threshold'",
            "remediate": "echo 'deny = 5' | sudo tee -a /etc/security/faillock.conf",
            "rollback": "sudo sed -i '/deny = 5/d' /etc/security/faillock.conf"
        },
        {
            "id": "LIN-PAM-009",
            "description": "Ensure password unlock time is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'unlock_time=' /etc/security/faillock.conf || echo 'No unlock time'",
            "remediate": "echo 'unlock_time = 900' | sudo tee -a /etc/security/faillock.conf",
            "rollback": "sudo sed -i '/unlock_time = 900/d' /etc/security/faillock.conf"
        },
        {
            "id": "LIN-PAM-010",
            "description": "Ensure password failed attempts lockout includes root account",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'even_deny_root' /etc/security/faillock.conf || echo 'Root not included in lockout'",
            "remediate": "echo 'even_deny_root' | sudo tee -a /etc/security/faillock.conf",
            "rollback": "sudo sed -i '/even_deny_root/d' /etc/security/faillock.conf"
        },
        
        # PAM Pwquality Module
        {
            "id": "LIN-PAM-011",
            "description": "Ensure password number of changed characters is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^minclass' /etc/security/pwquality.conf || echo 'No character class requirement'",
            "remediate": "echo 'minclass = 4' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/minclass = 4/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-012",
            "description": "Ensure minimum password length is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^minlen' /etc/security/pwquality.conf || echo 'No minimum length'",
            "remediate": "echo 'minlen = 12' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/minlen = 12/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-013",
            "description": "Ensure password same consecutive characters is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^maxrepeat' /etc/security/pwquality.conf || echo 'No consecutive character limit'",
            "remediate": "echo 'maxrepeat = 2' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/maxrepeat = 2/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-014",
            "description": "Ensure password maximum sequential characters is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^maxsequence' /etc/security/pwquality.conf || echo 'No sequential character limit'",
            "remediate": "echo 'maxsequence = 3' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/maxsequence = 3/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-015",
            "description": "Ensure password dictionary check is enabled",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^dictcheck' /etc/security/pwquality.conf || echo 'Dictionary check not enabled'",
            "remediate": "echo 'dictcheck = 1' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/dictcheck = 1/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-016",
            "description": "Ensure password quality checking is enforced",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^enforcing' /etc/security/pwquality.conf || echo 'Quality checking not enforced'",
            "remediate": "echo 'enforcing = 1' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/enforcing = 1/d' /etc/security/pwquality.conf"
        },
        {
            "id": "LIN-PAM-017",
            "description": "Ensure password quality is enforced for the root user",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^enforce_for_root' /etc/security/pwquality.conf || echo 'Root quality not enforced'",
            "remediate": "echo 'enforce_for_root' | sudo tee -a /etc/security/pwquality.conf",
            "rollback": "sudo sed -i '/enforce_for_root/d' /etc/security/pwquality.conf"
        },
        
        # PAM Pwhistory Module
        {
            "id": "LIN-PAM-018",
            "description": "Ensure password history remember is configured",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'remember=' /etc/pam.d/common-password | grep 'pam_pwhistory' || echo 'No password history'",
            "remediate": "echo 'password required pam_pwhistory.so remember=5' | sudo tee -a /etc/pam.d/common-password",
            "rollback": "sudo sed -i '/pam_pwhistory.so remember=5/d' /etc/pam.d/common-password"
        },
        {
            "id": "LIN-PAM-019",
            "description": "Ensure password history is enforced for the root user",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'enforce_for_root' /etc/pam.d/common-password | grep 'pam_pwhistory' || echo 'Root history not enforced'",
            "remediate": "echo 'password required pam_pwhistory.so remember=5 enforce_for_root' | sudo tee -a /etc/pam.d/common-password",
            "rollback": "sudo sed -i '/pam_pwhistory.so remember=5 enforce_for_root/d' /etc/pam.d/common-password"
        },
        {
            "id": "LIN-PAM-020",
            "description": "Ensure pam_pwhistory includes use_authtok",
            "category": LinuxRuleCategory.ACCESS_CONTROL,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'use_authtok' /etc/pam.d/common-password | grep 'pam_pwhistory' || echo 'use_authtok not configured'",
            "remediate": "echo 'password required pam_pwhistory.so remember=5 use_authtok' | sudo tee -a /etc/pam.d/common-password",
            "rollback": "sudo sed -i '/pam_pwhistory.so remember=5 use_authtok/d' /etc/pam.d/common-password"
        },

        # ========================================
        # 8. USER ACCOUNTS AND ENVIRONMENT (NTRO Section 7)
        # ========================================
        
        # Shadow Password Suite Parameters
        {
            "id": "LIN-USER-003",
            "description": "Ensure password expiration is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^PASS_MAX_DAYS' /etc/login.defs | grep -E '^[0-9]+$' || echo 'No password expiration'",
            "remediate": "echo 'PASS_MAX_DAYS 90' | sudo tee -a /etc/login.defs",
            "rollback": "sudo sed -i '/PASS_MAX_DAYS 90/d' /etc/login.defs"
        },
        {
            "id": "LIN-USER-004",
            "description": "Ensure minimum password days is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^PASS_MIN_DAYS' /etc/login.defs | grep -E '^[0-9]+$' || echo 'No minimum password days'",
            "remediate": "echo 'PASS_MIN_DAYS 7' | sudo tee -a /etc/login.defs",
            "rollback": "sudo sed -i '/PASS_MIN_DAYS 7/d' /etc/login.defs"
        },
        {
            "id": "LIN-USER-005",
            "description": "Ensure password expiration warning days is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "grep '^PASS_WARN_AGE' /etc/login.defs | grep -E '^[0-9]+$' || echo 'No password warning'",
            "remediate": "echo 'PASS_WARN_AGE 7' | sudo tee -a /etc/login.defs",
            "rollback": "sudo sed -i '/PASS_WARN_AGE 7/d' /etc/login.defs"
        },
        {
            "id": "LIN-USER-006",
            "description": "Ensure strong password hashing algorithm is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^ENCRYPT_METHOD' /etc/login.defs | grep -q 'SHA512' || echo 'Weak hashing algorithm'",
            "remediate": "echo 'ENCRYPT_METHOD SHA512' | sudo tee -a /etc/login.defs",
            "rollback": "sudo sed -i '/ENCRYPT_METHOD SHA512/d' /etc/login.defs"
        },
        {
            "id": "LIN-USER-007",
            "description": "Ensure inactive password lock is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^INACTIVE' /etc/default/useradd | grep -E '^[0-9]+$' || echo 'No inactive lock'",
            "remediate": "echo 'INACTIVE=30' | sudo tee -a /etc/default/useradd",
            "rollback": "sudo sed -i '/INACTIVE=30/d' /etc/default/useradd"
        },
        {
            "id": "LIN-USER-008",
            "description": "Ensure all users last password change date is in the past",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3 > 0 && $5 == \"\" {print $1}' /etc/shadow || echo 'All users have password change dates'",
            "remediate": "echo 'Manual: Set password change dates for users'",
            "rollback": "echo 'Manual: Remove password change dates'"
        },
        
        # Root and System Accounts
        {
            "id": "LIN-USER-009",
            "description": "Ensure root is the only UID 0 account",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "critical",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3 == 0 {print $1}' /etc/passwd | wc -l | grep -q '^1$' || echo 'Multiple UID 0 accounts'",
            "remediate": "echo 'Manual: Remove duplicate UID 0 accounts'",
            "rollback": "echo 'Manual: Restore duplicate UID 0 accounts'"
        },
        {
            "id": "LIN-USER-010",
            "description": "Ensure root is the only GID 0 account",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "critical",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3 == 0 {print $1}' /etc/group | wc -l | grep -q '^1$' || echo 'Multiple GID 0 groups'",
            "remediate": "echo 'Manual: Remove duplicate GID 0 groups'",
            "rollback": "echo 'Manual: Restore duplicate GID 0 groups'"
        },
        {
            "id": "LIN-USER-011",
            "description": "Ensure group root is the only GID 0 group",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "critical",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3 == 0 {print $1}' /etc/group | grep -q '^root$' || echo 'Root group not GID 0'",
            "remediate": "echo 'Manual: Ensure root group has GID 0'",
            "rollback": "echo 'Manual: Change root group GID'"
        },
        {
            "id": "LIN-USER-012",
            "description": "Ensure root account access is controlled",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^root:' /etc/passwd | grep -q '/bin/bash' || echo 'Root shell not bash'",
            "remediate": "echo 'Manual: Ensure root has secure shell'",
            "rollback": "echo 'Manual: Change root shell'"
        },
        {
            "id": "LIN-USER-013",
            "description": "Ensure root path integrity",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "echo $PATH | grep -q '::' || echo 'No empty PATH elements'",
            "remediate": "echo 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' | sudo tee -a /root/.bashrc",
            "rollback": "sudo sed -i '/export PATH=/d' /root/.bashrc"
        },
        {
            "id": "LIN-USER-014",
            "description": "Ensure root user umask is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^umask' /root/.bashrc || echo 'No root umask'",
            "remediate": "echo 'umask 027' | sudo tee -a /root/.bashrc",
            "rollback": "sudo sed -i '/umask 027/d' /root/.bashrc"
        },
        {
            "id": "LIN-USER-015",
            "description": "Ensure system accounts do not have a valid login shell",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$1!=\"root\" && $3<1000 && $7!=\"/usr/sbin/nologin\" && $7!=\"/bin/false\" {print $1}' /etc/passwd || echo 'All system accounts have nologin'",
            "remediate": "echo 'Manual: Set system accounts to nologin'",
            "rollback": "echo 'Manual: Restore system account shells'"
        },
        {
            "id": "LIN-USER-016",
            "description": "Ensure accounts without a valid login shell are locked",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$7==\"/usr/sbin/nologin\" || $7==\"/bin/false\" {print $1}' /etc/passwd | xargs -I {} passwd -S {} | grep -q 'L' || echo 'All nologin accounts locked'",
            "remediate": "echo 'Manual: Lock nologin accounts'",
            "rollback": "echo 'Manual: Unlock nologin accounts'"
        },
        
        # User Default Environment
        {
            "id": "LIN-USER-017",
            "description": "Ensure nologin is not listed in /etc/shells",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep -q '/usr/sbin/nologin' /etc/shells || echo 'nologin not in shells'",
            "remediate": "sudo sed -i '/\\/usr\\/sbin\\/nologin/d' /etc/shells",
            "rollback": "echo '/usr/sbin/nologin' | sudo tee -a /etc/shells"
        },
        {
            "id": "LIN-USER-018",
            "description": "Ensure default user shell timeout is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "grep '^TMOUT' /etc/profile || echo 'No shell timeout'",
            "remediate": "echo 'TMOUT=600' | sudo tee -a /etc/profile",
            "rollback": "sudo sed -i '/TMOUT=600/d' /etc/profile"
        },
        {
            "id": "LIN-USER-019",
            "description": "Ensure default user umask is configured",
            "category": LinuxRuleCategory.USER_ACCOUNTS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^umask' /etc/profile || echo 'No default umask'",
            "remediate": "echo 'umask 027' | sudo tee -a /etc/profile",
            "rollback": "sudo sed -i '/umask 027/d' /etc/profile"
        },

        # ========================================
        # 9. LOGGING AND AUDITING (NTRO Section 8)
        # ========================================
        
        # System Logging - systemd-journald
        {
            "id": "LIN-LOG-002",
            "description": "Ensure journald service is enabled and active",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active systemd-journald || echo 'journald not active'",
            "remediate": "sudo systemctl enable systemd-journald && sudo systemctl start systemd-journald",
            "rollback": "sudo systemctl disable systemd-journald && sudo systemctl stop systemd-journald"
        },
        {
            "id": "LIN-LOG-003",
            "description": "Ensure journald log file access is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^Storage=' /etc/systemd/journald.conf || echo 'No storage configuration'",
            "remediate": "echo 'Storage=persistent' | sudo tee -a /etc/systemd/journald.conf",
            "rollback": "sudo sed -i '/Storage=persistent/d' /etc/systemd/journald.conf"
        },
        {
            "id": "LIN-LOG-004",
            "description": "Ensure journald log file rotation is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^SystemMaxUse=' /etc/systemd/journald.conf || echo 'No rotation configuration'",
            "remediate": "echo 'SystemMaxUse=100M' | sudo tee -a /etc/systemd/journald.conf",
            "rollback": "sudo sed -i '/SystemMaxUse=100M/d' /etc/systemd/journald.conf"
        },
        {
            "id": "LIN-LOG-005",
            "description": "Ensure only one logging system is in use",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active rsyslog || echo 'rsyslog not active'",
            "remediate": "sudo systemctl stop rsyslog && sudo systemctl disable rsyslog",
            "rollback": "sudo systemctl enable rsyslog && sudo systemctl start rsyslog"
        },
        
        # System Logging - rsyslog
        {
            "id": "LIN-LOG-006",
            "description": "Ensure rsyslog is installed",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*rsyslog' || echo 'rsyslog not installed'",
            "remediate": "sudo apt-get install rsyslog",
            "rollback": "sudo apt-get remove rsyslog"
        },
        {
            "id": "LIN-LOG-007",
            "description": "Ensure rsyslog service is enabled and active",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active rsyslog || echo 'rsyslog not active'",
            "remediate": "sudo systemctl enable rsyslog && sudo systemctl start rsyslog",
            "rollback": "sudo systemctl disable rsyslog && sudo systemctl stop rsyslog"
        },
        {
            "id": "LIN-LOG-008",
            "description": "Ensure journald is configured to send logs to rsyslog",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^ForwardToSyslog=' /etc/systemd/journald.conf | grep -q 'yes' || echo 'journald not forwarding to rsyslog'",
            "remediate": "echo 'ForwardToSyslog=yes' | sudo tee -a /etc/systemd/journald.conf",
            "rollback": "sudo sed -i '/ForwardToSyslog=yes/d' /etc/systemd/journald.conf"
        },
        {
            "id": "LIN-LOG-009",
            "description": "Ensure rsyslog log file creation mode is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^\\$FileCreateMode' /etc/rsyslog.conf || echo 'No file creation mode'",
            "remediate": "echo '$FileCreateMode 0640' | sudo tee -a /etc/rsyslog.conf",
            "rollback": "sudo sed -i '/\\$FileCreateMode 0640/d' /etc/rsyslog.conf"
        },
        {
            "id": "LIN-LOG-010",
            "description": "Ensure rsyslog logging is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^\\*\\..*\\/var\\/log\\/' /etc/rsyslog.conf || echo 'No logging configuration'",
            "remediate": "echo '*.info;mail.none;authpriv.none;cron.none                /var/log/messages' | sudo tee -a /etc/rsyslog.conf",
            "rollback": "sudo sed -i '/\\*\\.info;mail\\.none;authpriv\\.none;cron\\.none/d' /etc/rsyslog.conf"
        },
        {
            "id": "LIN-LOG-011",
            "description": "Ensure rsyslog is configured to send logs to a remote log host",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^\\*\\..*@' /etc/rsyslog.conf || echo 'No remote logging'",
            "remediate": "echo 'Manual: Configure remote log host'",
            "rollback": "echo 'Manual: Remove remote logging'"
        },
        {
            "id": "LIN-LOG-012",
            "description": "Ensure rsyslog is not configured to receive logs from a remote client",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^\\$ModLoad imudp' /etc/rsyslog.conf || echo 'No UDP input module'",
            "remediate": "echo 'Manual: Remove UDP input module'",
            "rollback": "echo 'Manual: Add UDP input module'"
        },
        {
            "id": "LIN-LOG-013",
            "description": "Ensure logrotate is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "ls /etc/logrotate.d/ | wc -l | grep -q '^[0-9]' || echo 'No logrotate configuration'",
            "remediate": "echo 'Manual: Configure logrotate'",
            "rollback": "echo 'Manual: Remove logrotate configuration'"
        },
        
        # Logfiles
        {
            "id": "LIN-LOG-014",
            "description": "Ensure access to all logfiles has been configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "find /var/log -type f -perm /o+rwx || echo 'All logfiles have secure permissions'",
            "remediate": "sudo find /var/log -type f -exec chmod 640 {} \\;",
            "rollback": "sudo find /var/log -type f -exec chmod 644 {} \\;"
        },
        
        # System Auditing - auditd Service
        {
            "id": "LIN-AUDIT-001",
            "description": "Ensure auditd packages are installed",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*auditd' || echo 'auditd not installed'",
            "remediate": "sudo apt-get install auditd audispd-plugins",
            "rollback": "sudo apt-get remove auditd audispd-plugins"
        },
        {
            "id": "LIN-AUDIT-002",
            "description": "Ensure auditd service is enabled and active",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active auditd || echo 'auditd not active'",
            "remediate": "sudo systemctl enable auditd && sudo systemctl start auditd",
            "rollback": "sudo systemctl disable auditd && sudo systemctl stop auditd"
        },
        {
            "id": "LIN-AUDIT-003",
            "description": "Ensure auditing for processes that start prior to auditd is enabled",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^GRUB_CMDLINE_LINUX=' /etc/default/grub | grep -q 'audit=1' || echo 'Boot audit not enabled'",
            "remediate": "sudo sed -i 's/GRUB_CMDLINE_LINUX=\".*\"/GRUB_CMDLINE_LINUX=\"audit=1\"/' /etc/default/grub && sudo update-grub",
            "rollback": "sudo sed -i 's/audit=1//' /etc/default/grub && sudo update-grub"
        },
        {
            "id": "LIN-AUDIT-004",
            "description": "Ensure audit_backlog_limit is sufficient",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^GRUB_CMDLINE_LINUX=' /etc/default/grub | grep -q 'audit_backlog_limit=' || echo 'No backlog limit'",
            "remediate": "sudo sed -i 's/GRUB_CMDLINE_LINUX=\".*\"/GRUB_CMDLINE_LINUX=\"audit=1 audit_backlog_limit=8192\"/' /etc/default/grub && sudo update-grub",
            "rollback": "sudo sed -i 's/audit_backlog_limit=8192//' /etc/default/grub && sudo update-grub"
        },
        
        # Data Retention
        {
            "id": "LIN-AUDIT-005",
            "description": "Ensure audit log storage size is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^max_log_file=' /etc/audit/auditd.conf || echo 'No log file size limit'",
            "remediate": "echo 'max_log_file = 100' | sudo tee -a /etc/audit/auditd.conf",
            "rollback": "sudo sed -i '/max_log_file = 100/d' /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-006",
            "description": "Ensure audit logs are not automatically deleted",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^max_log_file_action=' /etc/audit/auditd.conf | grep -q 'keep_logs' || echo 'Logs may be deleted'",
            "remediate": "echo 'max_log_file_action = keep_logs' | sudo tee -a /etc/audit/auditd.conf",
            "rollback": "sudo sed -i '/max_log_file_action = keep_logs/d' /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-007",
            "description": "Ensure system is disabled when audit logs are full",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^space_left_action=' /etc/audit/auditd.conf | grep -q 'email' || echo 'No space left action'",
            "remediate": "echo 'space_left_action = email' | sudo tee -a /etc/audit/auditd.conf",
            "rollback": "sudo sed -i '/space_left_action = email/d' /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-008",
            "description": "Ensure system warns when audit logs are low on space",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^admin_space_left_action=' /etc/audit/auditd.conf | grep -q 'halt' || echo 'No admin space action'",
            "remediate": "echo 'admin_space_left_action = halt' | sudo tee -a /etc/audit/auditd.conf",
            "rollback": "sudo sed -i '/admin_space_left_action = halt/d' /etc/audit/auditd.conf"
        },
        
        # auditd Rules
        {
            "id": "LIN-AUDIT-009",
            "description": "Ensure changes to system administration scope (sudoers) is collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'sudoers' /etc/audit/rules.d/audit.rules || echo 'No sudoers audit rule'",
            "remediate": "echo '-w /etc/sudoers -p wa -k scope' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/sudoers.*scope/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-010",
            "description": "Ensure actions as another user are always logged",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'actions' /etc/audit/rules.d/audit.rules || echo 'No actions audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -C euid!=uid -F euid=0 -F auid!=4294967295 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/actions.*privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-011",
            "description": "Ensure events that modify the sudo log file are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'sudo.log' /etc/audit/rules.d/audit.rules || echo 'No sudo log audit rule'",
            "remediate": "echo '-w /var/log/sudo.log -p wa -k actions' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/sudo.log.*actions/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-012",
            "description": "Ensure events that modify date and time information are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'time-change' /etc/audit/rules.d/audit.rules || echo 'No time change audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/time-change/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-013",
            "description": "Ensure events that modify the system's network environment are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'system-locale' /etc/audit/rules.d/audit.rules || echo 'No system locale audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/system-locale/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-014",
            "description": "Ensure use of privileged commands are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'privileged' /etc/audit/rules.d/audit.rules || echo 'No privileged commands audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S execve -C uid!=euid -F euid=0 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-015",
            "description": "Ensure unsuccessful file access attempts are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'access' /etc/audit/rules.d/audit.rules || echo 'No file access audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S open,openat,open_by_handle_at -F exit=-EACCES -k access' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/access/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-016",
            "description": "Ensure events that modify user/group information are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'identity' /etc/audit/rules.d/audit.rules || echo 'No identity audit rule'",
            "remediate": "echo '-w /etc/group -p wa -k identity' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/identity/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-017",
            "description": "Ensure discretionary access control permission modification events are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'perm_mod' /etc/audit/rules.d/audit.rules || echo 'No permission modification audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/perm_mod/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-018",
            "description": "Ensure successful file system mounts are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'mounts' /etc/audit/rules.d/audit.rules || echo 'No mounts audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S mount -F auid>=1000 -F auid!=4294967295 -k mounts' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/mounts/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-019",
            "description": "Ensure session initiation information is collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'session' /etc/audit/rules.d/audit.rules || echo 'No session audit rule'",
            "remediate": "echo '-w /var/run/utmp -p wa -k session' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/session/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-020",
            "description": "Ensure login and logout events are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'logins' /etc/audit/rules.d/audit.rules || echo 'No logins audit rule'",
            "remediate": "echo '-w /var/log/lastlog -p wa -k logins' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/logins/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-021",
            "description": "Ensure file deletion events by users are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'delete' /etc/audit/rules.d/audit.rules || echo 'No delete audit rule'",
            "remediate": "echo '-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/delete/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-022",
            "description": "Ensure events that modify the system's Mandatory Access Controls are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'MAC-policy' /etc/audit/rules.d/audit.rules || echo 'No MAC policy audit rule'",
            "remediate": "echo '-w /etc/selinux/ -p wa -k MAC-policy' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/MAC-policy/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-023",
            "description": "Ensure successful and unsuccessful attempts to use the chcon command are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'chcon' /etc/audit/rules.d/audit.rules || echo 'No chcon audit rule'",
            "remediate": "echo '-a always,exit -F path=/usr/bin/chcon -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/chcon.*privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-024",
            "description": "Ensure successful and unsuccessful attempts to use the setfacl command are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'setfacl' /etc/audit/rules.d/audit.rules || echo 'No setfacl audit rule'",
            "remediate": "echo '-a always,exit -F path=/usr/bin/setfacl -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/setfacl.*privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-025",
            "description": "Ensure successful and unsuccessful attempts to use the chacl command are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep 'chacl' /etc/audit/rules.d/audit.rules || echo 'No chacl audit rule'",
            "remediate": "echo '-a always,exit -F path=/usr/bin/chacl -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/chacl.*privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-026",
            "description": "Ensure successful and unsuccessful attempts to use the usermod command are collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'usermod' /etc/audit/rules.d/audit.rules || echo 'No usermod audit rule'",
            "remediate": "echo '-a always,exit -F path=/usr/sbin/usermod -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/usermod.*privileged/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-027",
            "description": "Ensure kernel module loading unloading and modification is collected",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep 'modules' /etc/audit/rules.d/audit.rules || echo 'No modules audit rule'",
            "remediate": "echo '-w /sbin/insmod -p x -k modules' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/modules/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-028",
            "description": "Ensure the audit configuration is immutable",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^-e 2' /etc/audit/rules.d/audit.rules || echo 'Audit config not immutable'",
            "remediate": "echo '-e 2' | sudo tee -a /etc/audit/rules.d/audit.rules",
            "rollback": "sudo sed -i '/^-e 2/d' /etc/audit/rules.d/audit.rules"
        },
        {
            "id": "LIN-AUDIT-029",
            "description": "Ensure the running and on disk configuration is the same",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "auditctl -s | grep 'enabled' | grep -q '1' || echo 'Audit not enabled'",
            "remediate": "sudo systemctl restart auditd",
            "rollback": "sudo systemctl stop auditd"
        },
        
        # auditd File Access
        {
            "id": "LIN-AUDIT-030",
            "description": "Ensure audit log files mode is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /var/log/audit/audit.log | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure audit log permissions'",
            "remediate": "sudo chmod 640 /var/log/audit/audit.log",
            "rollback": "sudo chmod 644 /var/log/audit/audit.log"
        },
        {
            "id": "LIN-AUDIT-031",
            "description": "Ensure audit log files owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%U' /var/log/audit/audit.log | grep -q 'root' || echo 'Audit log not owned by root'",
            "remediate": "sudo chown root:root /var/log/audit/audit.log",
            "rollback": "sudo chown audit:audit /var/log/audit/audit.log"
        },
        {
            "id": "LIN-AUDIT-032",
            "description": "Ensure audit log files group owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%G' /var/log/audit/audit.log | grep -q 'root' || echo 'Audit log group not root'",
            "remediate": "sudo chgrp root /var/log/audit/audit.log",
            "rollback": "sudo chgrp audit /var/log/audit/audit.log"
        },
        {
            "id": "LIN-AUDIT-033",
            "description": "Ensure the audit log file directory mode is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /var/log/audit | grep -E '^[0-7][0-7][0-4]' || echo 'Insecure audit directory permissions'",
            "remediate": "sudo chmod 750 /var/log/audit",
            "rollback": "sudo chmod 755 /var/log/audit"
        },
        {
            "id": "LIN-AUDIT-034",
            "description": "Ensure audit configuration files mode is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/audit/auditd.conf | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure audit config permissions'",
            "remediate": "sudo chmod 640 /etc/audit/auditd.conf",
            "rollback": "sudo chmod 644 /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-035",
            "description": "Ensure audit configuration files owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%U' /etc/audit/auditd.conf | grep -q 'root' || echo 'Audit config not owned by root'",
            "remediate": "sudo chown root:root /etc/audit/auditd.conf",
            "rollback": "sudo chown audit:audit /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-036",
            "description": "Ensure audit configuration files group owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%G' /etc/audit/auditd.conf | grep -q 'root' || echo 'Audit config group not root'",
            "remediate": "sudo chgrp root /etc/audit/auditd.conf",
            "rollback": "sudo chgrp audit /etc/audit/auditd.conf"
        },
        {
            "id": "LIN-AUDIT-037",
            "description": "Ensure audit tools mode is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /usr/sbin/auditctl | grep -E '^[0-7][0-7][0-4]' || echo 'Insecure audit tools permissions'",
            "remediate": "sudo chmod 750 /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace",
            "rollback": "sudo chmod 755 /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace"
        },
        {
            "id": "LIN-AUDIT-038",
            "description": "Ensure audit tools owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%U' /usr/sbin/auditctl | grep -q 'root' || echo 'Audit tools not owned by root'",
            "remediate": "sudo chown root:root /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace",
            "rollback": "sudo chown audit:audit /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace"
        },
        {
            "id": "LIN-AUDIT-039",
            "description": "Ensure audit tools group owner is configured",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%G' /usr/sbin/auditctl | grep -q 'root' || echo 'Audit tools group not root'",
            "remediate": "sudo chgrp root /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace",
            "rollback": "sudo chgrp audit /usr/sbin/auditctl /usr/sbin/aureport /usr/sbin/ausearch /usr/sbin/autrace"
        },
        
        # Integrity Checking
        {
            "id": "LIN-AUDIT-040",
            "description": "Ensure AIDE is installed",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep '^ii.*aide' || echo 'AIDE not installed'",
            "remediate": "sudo apt-get install aide",
            "rollback": "sudo apt-get remove aide"
        },
        {
            "id": "LIN-AUDIT-041",
            "description": "Ensure filesystem integrity is regularly checked",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "crontab -l | grep aide || echo 'No AIDE cron job'",
            "remediate": "echo '0 5 * * * /usr/bin/aide --check' | sudo crontab -",
            "rollback": "sudo crontab -r"
        },
        {
            "id": "LIN-AUDIT-042",
            "description": "Ensure cryptographic mechanisms are used to protect the integrity of audit tools",
            "category": LinuxRuleCategory.LOGGING_AUDITING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "grep '^RULES=' /etc/aide/aide.conf | grep -q 'sha256' || echo 'No cryptographic integrity'",
            "remediate": "echo 'RULES = sha256' | sudo tee -a /etc/aide/aide.conf",
            "rollback": "sudo sed -i '/RULES = sha256/d' /etc/aide/aide.conf"
        },

        # ========================================
        # 10. SYSTEM MAINTENANCE (NTRO Section 9)
        # ========================================
        
        # System File Permissions
        {
            "id": "LIN-SYS-001",
            "description": "Ensure permissions on /etc/passwd- are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/passwd- | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure passwd- permissions'",
            "remediate": "sudo chmod 644 /etc/passwd-",
            "rollback": "sudo chmod 666 /etc/passwd-"
        },
        {
            "id": "LIN-SYS-002",
            "description": "Ensure permissions on /etc/group are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/group | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure group permissions'",
            "remediate": "sudo chmod 644 /etc/group",
            "rollback": "sudo chmod 666 /etc/group"
        },
        {
            "id": "LIN-SYS-003",
            "description": "Ensure permissions on /etc/group- are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/group- | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure group- permissions'",
            "remediate": "sudo chmod 644 /etc/group-",
            "rollback": "sudo chmod 666 /etc/group-"
        },
        {
            "id": "LIN-SYS-004",
            "description": "Ensure permissions on /etc/shadow- are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/shadow- | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure shadow- permissions'",
            "remediate": "sudo chmod 640 /etc/shadow-",
            "rollback": "sudo chmod 666 /etc/shadow-"
        },
        {
            "id": "LIN-SYS-005",
            "description": "Ensure permissions on /etc/gshadow are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/gshadow | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure gshadow permissions'",
            "remediate": "sudo chmod 640 /etc/gshadow",
            "rollback": "sudo chmod 666 /etc/gshadow"
        },
        {
            "id": "LIN-SYS-006",
            "description": "Ensure permissions on /etc/gshadow- are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/gshadow- | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure gshadow- permissions'",
            "remediate": "sudo chmod 640 /etc/gshadow-",
            "rollback": "sudo chmod 666 /etc/gshadow-"
        },
        {
            "id": "LIN-SYS-007",
            "description": "Ensure permissions on /etc/shells are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/shells | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure shells permissions'",
            "remediate": "sudo chmod 644 /etc/shells",
            "rollback": "sudo chmod 666 /etc/shells"
        },
        {
            "id": "LIN-SYS-008",
            "description": "Ensure permissions on /etc/security/opasswd are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/security/opasswd | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure opasswd permissions'",
            "remediate": "sudo chmod 600 /etc/security/opasswd",
            "rollback": "sudo chmod 666 /etc/security/opasswd"
        },
        {
            "id": "LIN-SYS-009",
            "description": "Ensure world writable files and directories are secured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "find / -type f -perm -002 -exec ls -ld {} \\; || echo 'No world writable files'",
            "remediate": "echo 'Manual: Secure world writable files'",
            "rollback": "echo 'Manual: Restore world writable permissions'"
        },
        {
            "id": "LIN-SYS-010",
            "description": "Ensure no files or directories without an owner and a group exist",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "find / -nouser -o -nogroup || echo 'All files have owner and group'",
            "remediate": "echo 'Manual: Fix orphaned files'",
            "rollback": "echo 'Manual: Restore orphaned files'"
        },
        {
            "id": "LIN-SYS-011",
            "description": "Ensure SUID and SGID files are reviewed",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "find / -type f \\( -perm -4000 -o -perm -2000 \\) -exec ls -ld {} \\; || echo 'No SUID/SGID files'",
            "remediate": "echo 'Manual: Review SUID/SGID files'",
            "rollback": "echo 'Manual: Restore SUID/SGID files'"
        },
        
        # Local User and Group Settings
        {
            "id": "LIN-SYS-012",
            "description": "Ensure accounts in /etc/passwd use shadowed passwords",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$2 != \"x\" {print $1}' /etc/passwd || echo 'All accounts use shadowed passwords'",
            "remediate": "echo 'Manual: Convert to shadowed passwords'",
            "rollback": "echo 'Manual: Convert from shadowed passwords'"
        },
        {
            "id": "LIN-SYS-013",
            "description": "Ensure /etc/shadow password fields are not empty",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$2 == \"\" {print $1}' /etc/shadow || echo 'All shadow password fields filled'",
            "remediate": "echo 'Manual: Set passwords for empty fields'",
            "rollback": "echo 'Manual: Clear password fields'"
        },
        {
            "id": "LIN-SYS-014",
            "description": "Ensure all groups in /etc/passwd exist in /etc/group",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '{print $4}' /etc/passwd | sort -u | while read gid; do grep -q \":$gid:\" /etc/group || echo \"Group $gid missing\"; done || echo 'All groups exist'",
            "remediate": "echo 'Manual: Create missing groups'",
            "rollback": "echo 'Manual: Remove groups'"
        },
        {
            "id": "LIN-SYS-015",
            "description": "Ensure shadow group is empty",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$1==\"shadow\" {print $4}' /etc/group | grep -q '^$' || echo 'Shadow group not empty'",
            "remediate": "echo 'Manual: Remove users from shadow group'",
            "rollback": "echo 'Manual: Add users to shadow group'"
        },
        {
            "id": "LIN-SYS-016",
            "description": "Ensure no duplicate UIDs exist",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '{print $3}' /etc/passwd | sort -n | uniq -d || echo 'No duplicate UIDs'",
            "remediate": "echo 'Manual: Fix duplicate UIDs'",
            "rollback": "echo 'Manual: Restore duplicate UIDs'"
        },
        {
            "id": "LIN-SYS-017",
            "description": "Ensure no duplicate GIDs exist",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '{print $3}' /etc/group | sort -n | uniq -d || echo 'No duplicate GIDs'",
            "remediate": "echo 'Manual: Fix duplicate GIDs'",
            "rollback": "echo 'Manual: Restore duplicate GIDs'"
        },
        {
            "id": "LIN-SYS-018",
            "description": "Ensure no duplicate user names exist",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '{print $1}' /etc/passwd | sort | uniq -d || echo 'No duplicate usernames'",
            "remediate": "echo 'Manual: Fix duplicate usernames'",
            "rollback": "echo 'Manual: Restore duplicate usernames'"
        },
        {
            "id": "LIN-SYS-019",
            "description": "Ensure no duplicate group names exist",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "awk -F: '{print $1}' /etc/group | sort | uniq -d || echo 'No duplicate group names'",
            "remediate": "echo 'Manual: Fix duplicate group names'",
            "rollback": "echo 'Manual: Restore duplicate group names'"
        },
        {
            "id": "LIN-SYS-020",
            "description": "Ensure local interactive user home directories are configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3>=1000 && $7!=\"/usr/sbin/nologin\" && $7!=\"/bin/false\" {print $6}' /etc/passwd | while read dir; do [ -d \"$dir\" ] || echo \"Home directory $dir missing\"; done || echo 'All home directories exist'",
            "remediate": "echo 'Manual: Create missing home directories'",
            "rollback": "echo 'Manual: Remove home directories'"
        },
        {
            "id": "LIN-SYS-021",
            "description": "Ensure local interactive user dot files access is configured",
            "category": LinuxRuleCategory.SYSTEM_MAINTENANCE,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "awk -F: '$3>=1000 && $7!=\"/usr/sbin/nologin\" && $7!=\"/bin/false\" {print $6}' /etc/passwd | while read dir; do [ -d \"$dir\" ] && find \"$dir\" -name '.*' -perm /o+rwx; done || echo 'All dot files secure'",
            "remediate": "echo 'Manual: Secure dot files'",
            "rollback": "echo 'Manual: Restore dot file permissions'"
        },

        # SSH Security Rules
        {
            "id": "LIN-SSH-001",
            "description": "Disable SSH root login",
            "category": LinuxRuleCategory.SSH_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'grep "^PermitRootLogin" /etc/ssh/sshd_config || echo "PermitRootLogin no"',
            "remediate": 'sudo sed -i "s/^PermitRootLogin.*/PermitRootLogin no/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "rollback": 'sudo sed -i "s/^PermitRootLogin.*/PermitRootLogin yes/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "expected": "PermitRootLogin no",
            "rationale": "Prevents direct root login via SSH, reducing attack surface"
        },
        
        {
            "id": "LIN-SSH-002",
            "description": "Set SSH protocol version to 2",
            "category": LinuxRuleCategory.SSH_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'grep "^Protocol" /etc/ssh/sshd_config || echo "Protocol 1"',
            "remediate": 'echo "Protocol 2" | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "rollback": 'sudo sed -i "/^Protocol 2/d" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "expected": "Protocol 2",
            "rationale": "SSH Protocol 1 has known security vulnerabilities"
        },
        
        {
            "id": "LIN-SSH-003",
            "description": "Disable SSH password authentication",
            "category": LinuxRuleCategory.SSH_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'grep "^PasswordAuthentication" /etc/ssh/sshd_config || echo "PasswordAuthentication yes"',
            "remediate": 'sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication no/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "rollback": 'sudo sed -i "s/^PasswordAuthentication.*/PasswordAuthentication yes/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "expected": "PasswordAuthentication no",
            "rationale": "Key-based authentication is more secure than passwords"
        },
        
        {
            "id": "LIN-SSH-004",
            "description": "Set SSH idle timeout",
            "category": LinuxRuleCategory.SSH_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'grep "^ClientAliveInterval" /etc/ssh/sshd_config || echo "ClientAliveInterval 0"',
            "remediate": 'echo "ClientAliveInterval 300" | sudo tee -a /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "rollback": 'sudo sed -i "/^ClientAliveInterval 300/d" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "expected": "ClientAliveInterval 300",
            "rationale": "Prevents idle SSH sessions from staying open indefinitely"
        },
        
        # Firewall Rules
        {
            "id": "LIN-FW-001",
            "description": "Enable UFW firewall",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["linux", "ubuntu"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'sudo ufw status | grep "Status:" | cut -d" " -f2 || echo "inactive"',
            "remediate": 'sudo ufw --force enable',
            "rollback": 'sudo ufw --force disable',
            "expected": "active",
            "rationale": "Firewall provides essential network security"
        },
        
        {
            "id": "LIN-FW-002",
            "description": "Enable firewalld (RHEL/CentOS)",
            "category": LinuxRuleCategory.HOST_FIREWALL,
            "os": ["centos", "rhel"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'sudo systemctl is-active firewalld || echo "inactive"',
            "remediate": 'sudo systemctl enable firewalld && sudo systemctl start firewalld',
            "rollback": 'sudo systemctl stop firewalld && sudo systemctl disable firewalld',
            "expected": "active",
            "rationale": "Firewall provides essential network security"
        },
        
        # User Management Rules
        {
            "id": "LIN-USER-001",
            "description": "Set minimum password length",
            "category": LinuxRuleCategory.USER_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'grep "^minlen" /etc/security/pwquality.conf | cut -d"=" -f2 | tr -d " " || echo "8"',
            "remediate": 'echo "minlen = 12" | sudo tee -a /etc/security/pwquality.conf',
            "rollback": 'sudo sed -i "/^minlen = 12/d" /etc/security/pwquality.conf',
            "expected": "12",
            "rationale": "Longer passwords are more secure"
        },
        
        {
            "id": "LIN-USER-002",
            "description": "Set password complexity requirements",
            "category": LinuxRuleCategory.USER_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'grep "^dcredit" /etc/security/pwquality.conf | cut -d"=" -f2 | tr -d " " || echo "0"',
            "remediate": 'echo "dcredit = -1" | sudo tee -a /etc/security/pwquality.conf && echo "ucredit = -1" | sudo tee -a /etc/security/pwquality.conf && echo "lcredit = -1" | sudo tee -a /etc/security/pwquality.conf && echo "ocredit = -1" | sudo tee -a /etc/security/pwquality.conf',
            "rollback": 'sudo sed -i "/^[duol]credit = -1/d" /etc/security/pwquality.conf',
            "expected": "-1",
            "rationale": "Complex passwords are harder to crack"
        },
        
        # Kernel Security Rules
        {
            "id": "LIN-KERNEL-001",
            "description": "Enable ASLR (Address Space Layout Randomization)",
            "category": LinuxRuleCategory.KERNEL_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": 'sysctl kernel.randomize_va_space | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "kernel.randomize_va_space = 2" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/kernel.randomize_va_space = 2/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "2",
            "rationale": "ASLR makes buffer overflow attacks more difficult"
        },
        
        {
            "id": "LIN-KERNEL-002",
            "description": "Disable core dumps for SUID programs",
            "category": LinuxRuleCategory.KERNEL_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["strict"],
            "check": 'sysctl fs.suid_dumpable | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "fs.suid_dumpable = 0" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/fs.suid_dumpable = 0/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "0",
            "rationale": "Prevents sensitive information from being written to core dumps"
        },
        
        {
            "id": "LIN-KERNEL-003",
            "description": "Disable IP forwarding",
            "category": LinuxRuleCategory.KERNEL_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'sysctl net.ipv4.ip_forward | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv4.ip_forward = 0" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv4.ip_forward = 0/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "0",
            "rationale": "Prevents system from acting as a router unless needed"
        },
        
        # Service Management Rules
        {
            "id": "LIN-SVC-001",
            "description": "Disable unnecessary services",
            "category": LinuxRuleCategory.SERVICE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'systemctl is-enabled telnet.socket 2>/dev/null || echo "disabled"',
            "remediate": 'sudo systemctl disable telnet.socket 2>/dev/null || true',
            "rollback": 'sudo systemctl enable telnet.socket 2>/dev/null || true',
            "expected": "disabled",
            "rationale": "Reduces attack surface by disabling unused services"
        },
        
        {
            "id": "LIN-SVC-002",
            "description": "Disable X11 forwarding in SSH",
            "category": LinuxRuleCategory.SERVICE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": 'grep "^X11Forwarding" /etc/ssh/sshd_config || echo "X11Forwarding yes"',
            "remediate": 'sudo sed -i "s/^X11Forwarding.*/X11Forwarding no/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "rollback": 'sudo sed -i "s/^X11Forwarding.*/X11Forwarding yes/" /etc/ssh/sshd_config && sudo systemctl reload ssh',
            "expected": "X11Forwarding no",
            "rationale": "X11 forwarding can be a security risk if not properly configured"
        },
        
        # File Permission Rules
        {
            "id": "LIN-FILE-001",
            "description": "Set secure permissions on /etc/passwd",
            "category": LinuxRuleCategory.FILE_PERMISSIONS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'stat -c "%a" /etc/passwd 2>/dev/null || echo "000"',
            "remediate": 'sudo chmod 644 /etc/passwd',
            "rollback": 'sudo chmod 644 /etc/passwd',
            "expected": "644",
            "rationale": "Prevents unauthorized modification of user account information"
        },
        
        {
            "id": "LIN-FILE-002",
            "description": "Set secure permissions on /etc/shadow",
            "category": LinuxRuleCategory.FILE_PERMISSIONS,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'stat -c "%a" /etc/shadow 2>/dev/null || echo "000"',
            "remediate": 'sudo chmod 640 /etc/shadow',
            "rollback": 'sudo chmod 640 /etc/shadow',
            "expected": "640",
            "rationale": "Protects password hashes from unauthorized access"
        },
        
        # Network Security Rules
        {
            "id": "LIN-NET-001",
            "description": "Disable unused network protocols",
            "category": LinuxRuleCategory.NETWORK_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["strict"],
            "check": 'lsmod | grep dccp || echo "not_loaded"',
            "remediate": 'echo "install dccp /bin/true" | sudo tee -a /etc/modprobe.d/dccp.conf',
            "rollback": 'sudo rm -f /etc/modprobe.d/dccp.conf',
            "expected": "not_loaded",
            "rationale": "Reduces attack surface by disabling unused protocols"
        },
        
        {
            "id": "LIN-NET-002",
            "description": "Disable IP source routing",
            "category": LinuxRuleCategory.NETWORK_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'sysctl net.ipv4.conf.all.accept_source_route | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv4.conf.all.accept_source_route = 0" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv4.conf.all.accept_source_route = 0/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "0",
            "rationale": "Prevents IP source routing attacks"
        },
        
        # Logging Rules
        {
            "id": "LIN-LOG-001",
            "description": "Enable audit logging",
            "category": LinuxRuleCategory.LOGGING,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'systemctl is-active auditd 2>/dev/null || echo "inactive"',
            "remediate": 'sudo systemctl enable auditd && sudo systemctl start auditd',
            "rollback": 'sudo systemctl stop auditd && sudo systemctl disable auditd',
            "expected": "active",
            "rationale": "Audit logging helps track security events"
        },
        
        # Package Management Rules
        {
            "id": "LIN-PKG-001",
            "description": "Enable automatic security updates",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["ubuntu"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'grep "^APT::Periodic::Unattended-Upgrade" /etc/apt/apt.conf.d/20auto-upgrades | cut -d"\\"" -f2 || echo "0"',
            "remediate": 'echo "APT::Periodic::Unattended-Upgrade \\"1\\";" | sudo tee -a /etc/apt/apt.conf.d/20auto-upgrades',
            "rollback": 'sudo sed -i "/APT::Periodic::Unattended-Upgrade/d" /etc/apt/apt.conf.d/20auto-upgrades',
            "expected": "1",
            "rationale": "Keeps system updated with security patches"
        },
        
        {
            "id": "LIN-PKG-002",
            "description": "Remove unnecessary packages",
            "category": LinuxRuleCategory.PACKAGE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": 'dpkg -l | grep -E "^(telnet|rsh|rlogin)" | wc -l || echo "0"',
            "remediate": 'sudo apt-get remove -y telnet rsh-client rlogin 2>/dev/null || true',
            "rollback": 'sudo apt-get install -y telnet rsh-client rlogin 2>/dev/null || true',
            "expected": "0",
            "rationale": "Removes potentially insecure network tools"
        },
        
        # RHEL/CentOS Specific Rules
        {
            "id": "LIN-RHEL-001",
            "description": "Enable automatic security updates (RHEL/CentOS)",
            "category": LinuxRuleCategory.RHEL_SPECIFIC,
            "os": ["centos", "rhel"],
            "severity": "high",
            "level": ["basic", "moderate", "strict"],
            "check": 'systemctl is-enabled dnf-automatic.timer 2>/dev/null || echo "disabled"',
            "remediate": 'sudo systemctl enable dnf-automatic.timer && sudo systemctl start dnf-automatic.timer',
            "rollback": 'sudo systemctl stop dnf-automatic.timer && sudo systemctl disable dnf-automatic.timer',
            "expected": "enabled",
            "rationale": "Keeps RHEL/CentOS systems updated with security patches"
        },
        
        {
            "id": "LIN-RHEL-002",
            "description": "Configure SELinux enforcing mode",
            "category": LinuxRuleCategory.APPARMOR_SELINUX,
            "os": ["centos", "rhel"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": 'getenforce 2>/dev/null || echo "Disabled"',
            "remediate": 'sudo setenforce 1 && echo "SELINUX=enforcing" | sudo tee /etc/selinux/config',
            "rollback": 'sudo setenforce 0 && echo "SELINUX=permissive" | sudo tee /etc/selinux/config',
            "expected": "Enforcing",
            "rationale": "SELinux provides mandatory access control for enhanced security"
        },
        
        {
            "id": "LIN-RHEL-003",
            "description": "Remove unnecessary RHEL/CentOS packages",
            "category": LinuxRuleCategory.RHEL_SPECIFIC,
            "os": ["centos", "rhel"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": 'rpm -qa | grep -E "(telnet|rsh|rlogin)" | wc -l || echo "0"',
            "remediate": 'sudo dnf remove -y telnet rsh rlogin 2>/dev/null || true',
            "rollback": 'sudo dnf install -y telnet rsh rlogin 2>/dev/null || true',
            "expected": "0",
            "rationale": "Removes potentially insecure network tools"
        },
        
        # AppArmor/SELinux Advanced Rules
        {
            "id": "LIN-APPARMOR-001",
            "description": "Enable AppArmor (Ubuntu/Debian)",
            "category": LinuxRuleCategory.APPARMOR_SELINUX,
            "os": ["ubuntu", "debian"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": 'aa-status 2>/dev/null | head -1 || echo "AppArmor is not enabled"',
            "remediate": 'sudo systemctl enable apparmor && sudo systemctl start apparmor',
            "rollback": 'sudo systemctl stop apparmor && sudo systemctl disable apparmor',
            "expected": "apparmor module is loaded",
            "rationale": "AppArmor provides mandatory access control for Ubuntu/Debian"
        },
        
        {
            "id": "LIN-APPARMOR-002",
            "description": "Set AppArmor profiles to enforce mode",
            "category": LinuxRuleCategory.APPARMOR_SELINUX,
            "os": ["ubuntu", "debian"],
            "severity": "medium",
            "level": ["strict"],
            "check": 'aa-status 2>/dev/null | grep "enforce" | wc -l || echo "0"',
            "remediate": 'sudo aa-enforce /etc/apparmor.d/* 2>/dev/null || true',
            "rollback": 'sudo aa-complain /etc/apparmor.d/* 2>/dev/null || true',
            "expected": "1",
            "rationale": "Enforces AppArmor profiles for maximum security"
        },
        
        # Advanced Kernel Security Rules
        {
            "id": "LIN-KERNEL-004",
            "description": "Disable IPv6 if not needed",
            "category": LinuxRuleCategory.KERNEL_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["strict"],
            "check": 'sysctl net.ipv6.conf.all.disable_ipv6 | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv6.conf.all.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv6.conf.all.disable_ipv6 = 1/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "1",
            "rationale": "Reduces attack surface if IPv6 is not needed"
        },
        
        {
            "id": "LIN-KERNEL-005",
            "description": "Enable SYN flood protection",
            "category": LinuxRuleCategory.KERNEL_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'sysctl net.ipv4.tcp_syncookies | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv4.tcp_syncookies = 1" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv4.tcp_syncookies = 1/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "1",
            "rationale": "Protects against SYN flood attacks"
        },
        
        # Advanced Systemd Security Rules
        {
            "id": "LIN-SYSTEMD-001",
            "description": "Set systemd service security options",
            "category": LinuxRuleCategory.SERVICE_MANAGEMENT,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["strict"],
            "check": 'systemctl show ssh | grep "NoNewPrivileges" | cut -d"=" -f2 || echo "no"',
            "remediate": 'sudo systemctl edit ssh --drop-in=override.conf && echo "[Service]\nNoNewPrivileges=yes" | sudo tee /etc/systemd/system/ssh.service.d/override.conf && sudo systemctl daemon-reload',
            "rollback": 'sudo rm -f /etc/systemd/system/ssh.service.d/override.conf && sudo systemctl daemon-reload',
            "expected": "yes",
            "rationale": "Prevents services from gaining new privileges"
        },
        
        # Container Security Rules
        {
            "id": "LIN-CONTAINER-001",
            "description": "Secure Docker daemon configuration",
            "category": LinuxRuleCategory.CONTAINER_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": 'grep "tcp://" /etc/docker/daemon.json 2>/dev/null || echo "not_configured"',
            "remediate": 'echo "{\"hosts\": [\"unix:///var/run/docker.sock\"]}" | sudo tee /etc/docker/daemon.json && sudo systemctl restart docker',
            "rollback": 'sudo rm -f /etc/docker/daemon.json && sudo systemctl restart docker',
            "expected": "not_configured",
            "rationale": "Disables Docker daemon TCP socket for security"
        },
        
        {
            "id": "LIN-CONTAINER-002",
            "description": "Enable Docker content trust",
            "category": LinuxRuleCategory.CONTAINER_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["strict"],
            "check": 'echo $DOCKER_CONTENT_TRUST || echo "0"',
            "remediate": 'echo "export DOCKER_CONTENT_TRUST=1" | sudo tee -a /etc/environment',
            "rollback": 'sudo sed -i "/export DOCKER_CONTENT_TRUST=1/d" /etc/environment',
            "expected": "1",
            "rationale": "Ensures only signed images can be pulled"
        },
        
        # Advanced Network Security Rules
        {
            "id": "LIN-NET-003",
            "description": "Disable ICMP redirects",
            "category": LinuxRuleCategory.NETWORK_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'sysctl net.ipv4.conf.all.accept_redirects | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv4.conf.all.accept_redirects = 0" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv4.conf.all.accept_redirects = 0/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "0",
            "rationale": "Prevents ICMP redirect attacks"
        },
        
        {
            "id": "LIN-NET-004",
            "description": "Enable reverse path filtering",
            "category": LinuxRuleCategory.NETWORK_SECURITY,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": 'sysctl net.ipv4.conf.all.rp_filter | cut -d"=" -f2 | tr -d " "',
            "remediate": 'echo "net.ipv4.conf.all.rp_filter = 1" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p',
            "rollback": 'sudo sed -i "/net.ipv4.conf.all.rp_filter = 1/d" /etc/sysctl.conf && sudo sysctl -p',
            "expected": "1",
            "rationale": "Prevents IP spoofing attacks"
        },

        # ========================================
        # 3. SERVICES RULES (NTRO Section 3)
        # ========================================
        
        # Server Services
        {
            "id": "LIN-SVC-001",
            "description": "Ensure autofs services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active autofs || echo 'autofs not active'",
            "remediate": "sudo systemctl stop autofs && sudo systemctl disable autofs",
            "rollback": "sudo systemctl enable autofs && sudo systemctl start autofs"
        },
        {
            "id": "LIN-SVC-002",
            "description": "Ensure avahi daemon services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active avahi-daemon || echo 'avahi-daemon not active'",
            "remediate": "sudo systemctl stop avahi-daemon && sudo systemctl disable avahi-daemon",
            "rollback": "sudo systemctl enable avahi-daemon && sudo systemctl start avahi-daemon"
        },
        {
            "id": "LIN-SVC-003",
            "description": "Ensure dhcp server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active isc-dhcp-server || echo 'dhcp server not active'",
            "remediate": "sudo systemctl stop isc-dhcp-server && sudo systemctl disable isc-dhcp-server",
            "rollback": "sudo systemctl enable isc-dhcp-server && sudo systemctl start isc-dhcp-server"
        },
        {
            "id": "LIN-SVC-004",
            "description": "Ensure dns server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active bind9 || echo 'dns server not active'",
            "remediate": "sudo systemctl stop bind9 && sudo systemctl disable bind9",
            "rollback": "sudo systemctl enable bind9 && sudo systemctl start bind9"
        },
        {
            "id": "LIN-SVC-005",
            "description": "Ensure dnsmasq services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active dnsmasq || echo 'dnsmasq not active'",
            "remediate": "sudo systemctl stop dnsmasq && sudo systemctl disable dnsmasq",
            "rollback": "sudo systemctl enable dnsmasq && sudo systemctl start dnsmasq"
        },
        {
            "id": "LIN-SVC-006",
            "description": "Ensure ftp server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active vsftpd || echo 'ftp server not active'",
            "remediate": "sudo systemctl stop vsftpd && sudo systemctl disable vsftpd",
            "rollback": "sudo systemctl enable vsftpd && sudo systemctl start vsftpd"
        },
        {
            "id": "LIN-SVC-007",
            "description": "Ensure ldap server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active slapd || echo 'ldap server not active'",
            "remediate": "sudo systemctl stop slapd && sudo systemctl disable slapd",
            "rollback": "sudo systemctl enable slapd && sudo systemctl start slapd"
        },
        {
            "id": "LIN-SVC-008",
            "description": "Ensure message access server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active dovecot || echo 'mail server not active'",
            "remediate": "sudo systemctl stop dovecot && sudo systemctl disable dovecot",
            "rollback": "sudo systemctl enable dovecot && sudo systemctl start dovecot"
        },
        {
            "id": "LIN-SVC-009",
            "description": "Ensure network file system services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active nfs-server || echo 'nfs server not active'",
            "remediate": "sudo systemctl stop nfs-server && sudo systemctl disable nfs-server",
            "rollback": "sudo systemctl enable nfs-server && sudo systemctl start nfs-server"
        },
        {
            "id": "LIN-SVC-010",
            "description": "Ensure nis server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active ypserv || echo 'nis server not active'",
            "remediate": "sudo systemctl stop ypserv && sudo systemctl disable ypserv",
            "rollback": "sudo systemctl enable ypserv && sudo systemctl start ypserv"
        },
        {
            "id": "LIN-SVC-011",
            "description": "Ensure print server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active cups || echo 'print server not active'",
            "remediate": "sudo systemctl stop cups && sudo systemctl disable cups",
            "rollback": "sudo systemctl enable cups && sudo systemctl start cups"
        },
        {
            "id": "LIN-SVC-012",
            "description": "Ensure rpcbind services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active rpcbind || echo 'rpcbind not active'",
            "remediate": "sudo systemctl stop rpcbind && sudo systemctl disable rpcbind",
            "rollback": "sudo systemctl enable rpcbind && sudo systemctl start rpcbind"
        },
        {
            "id": "LIN-SVC-013",
            "description": "Ensure rsync services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active rsync || echo 'rsync server not active'",
            "remediate": "sudo systemctl stop rsync && sudo systemctl disable rsync",
            "rollback": "sudo systemctl enable rsync && sudo systemctl start rsync"
        },
        {
            "id": "LIN-SVC-014",
            "description": "Ensure samba file server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active smbd || echo 'samba server not active'",
            "remediate": "sudo systemctl stop smbd && sudo systemctl disable smbd",
            "rollback": "sudo systemctl enable smbd && sudo systemctl start smbd"
        },
        {
            "id": "LIN-SVC-015",
            "description": "Ensure snmp services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active snmpd || echo 'snmp server not active'",
            "remediate": "sudo systemctl stop snmpd && sudo systemctl disable snmpd",
            "rollback": "sudo systemctl enable snmpd && sudo systemctl start snmpd"
        },
        {
            "id": "LIN-SVC-016",
            "description": "Ensure tftp server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active tftpd-hpa || echo 'tftp server not active'",
            "remediate": "sudo systemctl stop tftpd-hpa && sudo systemctl disable tftpd-hpa",
            "rollback": "sudo systemctl enable tftpd-hpa && sudo systemctl start tftpd-hpa"
        },
        {
            "id": "LIN-SVC-017",
            "description": "Ensure web proxy server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active squid || echo 'proxy server not active'",
            "remediate": "sudo systemctl stop squid && sudo systemctl disable squid",
            "rollback": "sudo systemctl enable squid && sudo systemctl start squid"
        },
        {
            "id": "LIN-SVC-018",
            "description": "Ensure web server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active apache2 || echo 'web server not active'",
            "remediate": "sudo systemctl stop apache2 && sudo systemctl disable apache2",
            "rollback": "sudo systemctl enable apache2 && sudo systemctl start apache2"
        },
        {
            "id": "LIN-SVC-019",
            "description": "Ensure xinetd services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active xinetd || echo 'xinetd not active'",
            "remediate": "sudo systemctl stop xinetd && sudo systemctl disable xinetd",
            "rollback": "sudo systemctl enable xinetd && sudo systemctl start xinetd"
        },
        {
            "id": "LIN-SVC-020",
            "description": "Ensure X window server services are not in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active gdm3 || echo 'X server not active'",
            "remediate": "sudo systemctl stop gdm3 && sudo systemctl disable gdm3",
            "rollback": "sudo systemctl enable gdm3 && sudo systemctl start gdm3"
        },
        {
            "id": "LIN-SVC-021",
            "description": "Ensure mail transfer agent is configured for local-only mode",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "grep '^inet_interfaces' /etc/postfix/main.cf | grep localhost || echo 'MTA not local-only'",
            "remediate": "echo 'inet_interfaces = localhost' | sudo tee -a /etc/postfix/main.cf && sudo systemctl restart postfix",
            "rollback": "sudo sed -i '/inet_interfaces = localhost/d' /etc/postfix/main.cf && sudo systemctl restart postfix"
        },
        
        # Client Services
        {
            "id": "LIN-SVC-022",
            "description": "Ensure NIS Client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep nis || echo 'nis client not installed'",
            "remediate": "sudo apt-get remove --purge nis",
            "rollback": "sudo apt-get install nis"
        },
        {
            "id": "LIN-SVC-023",
            "description": "Ensure rsh client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep rsh-client || echo 'rsh client not installed'",
            "remediate": "sudo apt-get remove --purge rsh-client",
            "rollback": "sudo apt-get install rsh-client"
        },
        {
            "id": "LIN-SVC-024",
            "description": "Ensure talk client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep talk || echo 'talk client not installed'",
            "remediate": "sudo apt-get remove --purge talk",
            "rollback": "sudo apt-get install talk"
        },
        {
            "id": "LIN-SVC-025",
            "description": "Ensure telnet client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "high",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep telnet || echo 'telnet client not installed'",
            "remediate": "sudo apt-get remove --purge telnet",
            "rollback": "sudo apt-get install telnet"
        },
        {
            "id": "LIN-SVC-026",
            "description": "Ensure ldap client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep ldap-utils || echo 'ldap client not installed'",
            "remediate": "sudo apt-get remove --purge ldap-utils",
            "rollback": "sudo apt-get install ldap-utils"
        },
        {
            "id": "LIN-SVC-027",
            "description": "Ensure ftp client is not installed",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "dpkg -l | grep ftp || echo 'ftp client not installed'",
            "remediate": "sudo apt-get remove --purge ftp",
            "rollback": "sudo apt-get install ftp"
        },
        
        # Time Synchronization
        {
            "id": "LIN-SVC-028",
            "description": "Ensure time synchronization is in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["basic", "moderate", "strict"],
            "check": "systemctl is-active systemd-timesyncd 2>/dev/null || systemctl is-active chrony 2>/dev/null || echo 'No time sync'",
            "remediate": "sudo systemctl enable systemd-timesyncd && sudo systemctl start systemd-timesyncd",
            "rollback": "sudo systemctl stop systemd-timesyncd && sudo systemctl disable systemd-timesyncd",
            "expected": "active"
        },
        {
            "id": "LIN-SVC-029",
            "description": "Ensure a single time synchronization daemon is in use",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "low",
            "level": ["moderate", "strict"],
            "check": "systemctl is-active systemd-timesyncd && ! systemctl is-active chrony || echo 'Multiple time sync'",
            "remediate": "sudo systemctl stop chrony && sudo systemctl disable chrony",
            "rollback": "sudo systemctl enable chrony && sudo systemctl start chrony"
        },
        
        # Job Schedulers
        {
            "id": "LIN-SVC-030",
            "description": "Ensure cron daemon is enabled and active",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["basic", "moderate", "strict"],
            "check": "systemctl is-active cron 2>/dev/null || echo 'cron not active'",
            "remediate": "sudo systemctl enable cron && sudo systemctl start cron",
            "rollback": "sudo systemctl stop cron && sudo systemctl disable cron",
            "expected": "active"
        },
        {
            "id": "LIN-SVC-031",
            "description": "Ensure permissions on /etc/crontab are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/crontab | grep -E '^[0-6][0-4][0-4]' || echo 'Insecure crontab permissions'",
            "remediate": "sudo chmod 600 /etc/crontab",
            "rollback": "sudo chmod 644 /etc/crontab"
        },
        {
            "id": "LIN-SVC-032",
            "description": "Ensure permissions on /etc/cron.hourly are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/cron.hourly | grep -E '^[0-7][0-7][0-5]' || echo 'Insecure cron.hourly permissions'",
            "remediate": "sudo chmod 755 /etc/cron.hourly",
            "rollback": "sudo chmod 777 /etc/cron.hourly"
        },
        {
            "id": "LIN-SVC-033",
            "description": "Ensure permissions on /etc/cron.daily are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/cron.daily | grep -E '^[0-7][0-7][0-5]' || echo 'Insecure cron.daily permissions'",
            "remediate": "sudo chmod 755 /etc/cron.daily",
            "rollback": "sudo chmod 777 /etc/cron.daily"
        },
        {
            "id": "LIN-SVC-034",
            "description": "Ensure permissions on /etc/cron.weekly are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/cron.weekly | grep -E '^[0-7][0-7][0-5]' || echo 'Insecure cron.weekly permissions'",
            "remediate": "sudo chmod 755 /etc/cron.weekly",
            "rollback": "sudo chmod 777 /etc/cron.weekly"
        },
        {
            "id": "LIN-SVC-035",
            "description": "Ensure permissions on /etc/cron.monthly are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/cron.monthly | grep -E '^[0-7][0-7][0-5]' || echo 'Insecure cron.monthly permissions'",
            "remediate": "sudo chmod 755 /etc/cron.monthly",
            "rollback": "sudo chmod 777 /etc/cron.monthly"
        },
        {
            "id": "LIN-SVC-036",
            "description": "Ensure permissions on /etc/cron.d are configured",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "stat -c '%a' /etc/cron.d | grep -E '^[0-7][0-7][0-5]' || echo 'Insecure cron.d permissions'",
            "remediate": "sudo chmod 755 /etc/cron.d",
            "rollback": "sudo chmod 777 /etc/cron.d"
        },
        {
            "id": "LIN-SVC-037",
            "description": "Ensure crontab is restricted to authorized users",
            "category": LinuxRuleCategory.SERVICES,
            "os": ["linux", "ubuntu", "centos"],
            "severity": "medium",
            "level": ["moderate", "strict"],
            "check": "ls -la /etc/cron.allow /etc/cron.deny 2>/dev/null || echo 'No cron restrictions'",
            "remediate": "echo 'root' | sudo tee /etc/cron.allow && sudo rm -f /etc/cron.deny",
            "rollback": "sudo rm -f /etc/cron.allow"
        }
    ]


def get_rules_by_category(category: LinuxRuleCategory) -> List[Dict[str, Any]]:
    """
    Get rules filtered by category
    
    Args:
        category: Rule category to filter by
        
    Returns:
        List of rules in the specified category
    """
    all_rules = get_linux_hardening_rules()
    return [rule for rule in all_rules if rule.get('category') == category]


def get_rules_by_severity(severity: str) -> List[Dict[str, Any]]:
    """
    Get rules filtered by severity
    
    Args:
        severity: Severity level to filter by
        
    Returns:
        List of rules with the specified severity
    """
    all_rules = get_linux_hardening_rules()
    return [rule for rule in all_rules if rule.get('severity') == severity]


def get_rules_by_level(level: str) -> List[Dict[str, Any]]:
    """
    Get rules filtered by hardening level
    
    Args:
        level: Hardening level to filter by
        
    Returns:
        List of rules for the specified level
    """
    all_rules = get_linux_hardening_rules()
    return [rule for rule in all_rules if level in rule.get('level', [])]
