"""
Operating System Detection Utilities
Provides comprehensive OS detection and system information gathering
"""

import platform
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class OSDetector:
    """
    Comprehensive operating system detection and information gathering
    
    Provides detailed OS information including:
    - OS type and version
    - Distribution information
    - Architecture details
    - Kernel information
    - Package manager detection
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._cache = {}
    
    def detect_os(self) -> Dict[str, Any]:
        """
        Detect comprehensive OS information
        
        Returns:
            Dict containing detailed OS information
        """
        if 'os_info' in self._cache:
            return self._cache['os_info']
        
        os_info = {
            'type': self._detect_os_type(),
            'version': self._detect_os_version(),
            'distribution': self._detect_distribution(),
            'architecture': self._detect_architecture(),
            'kernel': self._detect_kernel(),
            'package_manager': self._detect_package_manager(),
            'capabilities': self._detect_capabilities()
        }
        
        self._cache['os_info'] = os_info
        return os_info
    
    def _detect_os_type(self) -> str:
        """Detect basic OS type"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif system == "darwin":
            return "macos"
        else:
            return "unknown"
    
    def _detect_os_version(self) -> str:
        """Detect OS version"""
        try:
            if platform.system() == "Windows":
                return platform.version()
            else:
                return platform.release()
        except Exception:
            return "unknown"
    
    def _detect_distribution(self) -> Dict[str, str]:
        """Detect Linux distribution information"""
        dist_info = {
            'name': 'unknown',
            'version': 'unknown',
            'codename': 'unknown',
            'id': 'unknown'
        }
        
        if platform.system() != "Linux":
            return dist_info
        
        # Try /etc/os-release first (modern systems)
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        value = value.strip('"')
                        if key == "NAME":
                            dist_info['name'] = value
                        elif key == "VERSION_ID":
                            dist_info['version'] = value
                        elif key == "VERSION_CODENAME":
                            dist_info['codename'] = value
                        elif key == "ID":
                            dist_info['id'] = value
        except Exception:
            pass
        
        # Fallback to lsb_release
        if dist_info['name'] == 'unknown':
            try:
                result = subprocess.run(
                    ["lsb_release", "-a"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "Distributor ID:" in line:
                            dist_info['name'] = line.split(":", 1)[1].strip()
                        elif "Release:" in line:
                            dist_info['version'] = line.split(":", 1)[1].strip()
                        elif "Codename:" in line:
                            dist_info['codename'] = line.split(":", 1)[1].strip()
            except Exception:
                pass
        
        return dist_info
    
    def _detect_architecture(self) -> str:
        """Detect system architecture"""
        try:
            return platform.machine()
        except Exception:
            return "unknown"
    
    def _detect_kernel(self) -> Dict[str, str]:
        """Detect kernel information"""
        kernel_info = {
            'version': 'unknown',
            'release': 'unknown',
            'type': 'unknown'
        }
        
        try:
            kernel_info['version'] = platform.release()
            kernel_info['release'] = platform.version()
            
            # Detect kernel type
            if platform.system() == "Linux":
                kernel_info['type'] = "linux"
            elif platform.system() == "Windows":
                kernel_info['type'] = "windows"
            elif platform.system() == "Darwin":
                kernel_info['type'] = "darwin"
                
        except Exception:
            pass
        
        return kernel_info
    
    def _detect_package_manager(self) -> Optional[str]:
        """Detect available package manager"""
        if platform.system() != "Linux":
            return None
        
        package_managers = {
            'apt': ['/usr/bin/apt', '/usr/bin/apt-get'],
            'yum': ['/usr/bin/yum'],
            'dnf': ['/usr/bin/dnf'],
            'zypper': ['/usr/bin/zypper'],
            'pacman': ['/usr/bin/pacman'],
            'apk': ['/sbin/apk']
        }
        
        for pm, paths in package_managers.items():
            for path in paths:
                if Path(path).exists():
                    return pm
        
        return None
    
    def _detect_capabilities(self) -> Dict[str, bool]:
        """Detect system capabilities"""
        capabilities = {
            'sudo': False,
            'systemctl': False,
            'ufw': False,
            'iptables': False,
            'firewalld': False,
            'selinux': False,
            'apparmor': False,
            'docker': False,
            'podman': False
        }
        
        # Check for sudo
        try:
            result = subprocess.run(
                ["which", "sudo"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['sudo'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for systemctl
        try:
            result = subprocess.run(
                ["which", "systemctl"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['systemctl'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for UFW
        try:
            result = subprocess.run(
                ["which", "ufw"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['ufw'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for iptables
        try:
            result = subprocess.run(
                ["which", "iptables"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['iptables'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for firewalld
        try:
            result = subprocess.run(
                ["which", "firewall-cmd"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['firewalld'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for SELinux
        try:
            result = subprocess.run(
                ["which", "getenforce"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['selinux'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for AppArmor
        try:
            result = subprocess.run(
                ["which", "aa-status"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['apparmor'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for Docker
        try:
            result = subprocess.run(
                ["which", "docker"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['docker'] = result.returncode == 0
        except Exception:
            pass
        
        # Check for Podman
        try:
            result = subprocess.run(
                ["which", "podman"], 
                capture_output=True, 
                timeout=5
            )
            capabilities['podman'] = result.returncode == 0
        except Exception:
            pass
        
        return capabilities
    
    def get_os_family(self) -> str:
        """Get OS family for rule matching"""
        os_info = self.detect_os()
        
        if os_info['type'] == 'windows':
            return 'windows'
        elif os_info['type'] == 'linux':
            dist_id = os_info['distribution']['id']
            if dist_id in ['ubuntu', 'debian']:
                return 'ubuntu'
            elif dist_id in ['centos', 'rhel', 'fedora']:
                return 'centos'
            else:
                return 'linux'
        elif os_info['type'] == 'macos':
            return 'macos'
        else:
            return 'unknown'
    
    def is_compatible_with_rule(self, rule_os: list) -> bool:
        """
        Check if current OS is compatible with a rule
        
        Args:
            rule_os: List of supported OS types from rule
            
        Returns:
            bool: True if compatible
        """
        os_family = self.get_os_family()
        return os_family in rule_os or 'linux' in rule_os or 'windows' in rule_os
