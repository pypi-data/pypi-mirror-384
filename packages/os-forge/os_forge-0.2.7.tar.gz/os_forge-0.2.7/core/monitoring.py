"""
Advanced Monitoring and Alerting System for OS Forge

Provides real-time monitoring, alerting, and notification capabilities:
- Real-time security event monitoring
- Multi-channel alerting (console, file, email, webhook)
- Compliance trend analysis
- Automated incident response
- Dashboard and reporting
"""

import asyncio
import logging
import json
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import threading
import time


@dataclass
class Alert:
    """Security alert data structure"""
    alert_id: str
    timestamp: datetime
    severity: str  # critical, high, medium, low
    category: str  # compliance, security, system, performance
    title: str
    message: str
    source: str  # rule_id, system_event, etc.
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    name: str
    type: str  # console, file, email, webhook, slack
    enabled: bool = True
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class AlertManager:
    """
    Advanced alert management system with multiple notification channels
    
    Features:
    - Multi-channel alerting (console, file, email, webhook, Slack)
    - Alert deduplication and throttling
    - Escalation policies
    - Alert history and analytics
    - Custom alert rules and conditions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()
        
        # Alert storage
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Notification channels
        self.channels: Dict[str, NotificationChannel] = {}
        self._setup_channels()
        
        # Alert rules and conditions
        self.alert_rules: List[Dict[str, Any]] = []
        self._setup_default_rules()
        
        # Deduplication and throttling
        self.alert_cache: Dict[str, datetime] = {}
        self.throttle_config = self.config.get('throttling', {})
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': {},
            'alerts_by_category': {},
            'notifications_sent': 0,
            'last_alert_time': None
        }
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for alert manager"""
        return {
            'channels': {
                'console': {'enabled': True, 'level': 'INFO'},
                'file': {'enabled': True, 'file': './alerts.log'},
                'email': {'enabled': False, 'smtp_server': '', 'smtp_port': 587, 'username': '', 'password': '', 'to': []},
                'webhook': {'enabled': False, 'url': '', 'headers': {}},
                'slack': {'enabled': False, 'webhook_url': '', 'channel': '#security-alerts'}
            },
            'throttling': {
                'enabled': True,
                'window_minutes': 5,
                'max_alerts_per_window': 10,
                'cooldown_minutes': 30
            },
            'escalation': {
                'enabled': True,
                'levels': ['low', 'medium', 'high', 'critical'],
                'escalation_delay_minutes': 15
            },
            'retention': {
                'max_alerts_in_memory': 1000,
                'archive_after_days': 30
            }
        }
    
    def _setup_channels(self):
        """Setup notification channels based on configuration"""
        for name, config in self.config['channels'].items():
            if config.get('enabled', False):
                self.channels[name] = NotificationChannel(
                    name=name,
                    type=name,
                    enabled=True,
                    config=config
                )
                self.logger.info(f"Enabled notification channel: {name}")
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        self.alert_rules = [
            {
                'name': 'critical_compliance_drop',
                'condition': lambda data: data.get('compliance_score', 1.0) < 0.7,
                'severity': 'critical',
                'category': 'compliance',
                'title': 'Critical Compliance Drop',
                'message': 'System compliance has dropped below 70%'
            },
            {
                'name': 'high_security_failure',
                'condition': lambda data: data.get('critical_failures', 0) > 0,
                'severity': 'high',
                'category': 'security',
                'title': 'Critical Security Failures Detected',
                'message': 'One or more critical security rules have failed'
            },
            {
                'name': 'system_error_rate',
                'condition': lambda data: data.get('error_rate', 0.0) > 0.1,
                'severity': 'medium',
                'category': 'system',
                'title': 'High Error Rate Detected',
                'message': 'System error rate has exceeded 10%'
            },
            {
                'name': 'scan_failure',
                'condition': lambda data: data.get('scan_status') == 'failed',
                'severity': 'high',
                'category': 'system',
                'title': 'Security Scan Failed',
                'message': 'Security scan execution has failed'
            }
        ]
    
    async def process_scan_results(self, scan_data: Dict[str, Any]):
        """Process scan results and generate alerts based on rules"""
        try:
            # Check alert rules
            for rule in self.alert_rules:
                if rule['condition'](scan_data):
                    alert = Alert(
                        alert_id=f"{rule['name']}_{int(time.time())}",
                        timestamp=datetime.now(),
                        severity=rule['severity'],
                        category=rule['category'],
                        title=rule['title'],
                        message=rule['message'],
                        source='scan_results',
                        metadata=scan_data
                    )
                    
                    await self.send_alert(alert)
            
            # Check for specific compliance issues
            compliance_score = scan_data.get('compliance_score', 1.0)
            if compliance_score < 0.9:
                alert = Alert(
                    alert_id=f"compliance_warning_{int(time.time())}",
                    timestamp=datetime.now(),
                    severity='medium' if compliance_score >= 0.8 else 'high',
                    category='compliance',
                    title='Compliance Warning',
                    message=f'System compliance is at {compliance_score:.1%}',
                    source='compliance_monitor',
                    metadata={'compliance_score': compliance_score}
                )
                
                await self.send_alert(alert)
            
            # Check for failed rules
            failed_rules = scan_data.get('failed_rules', [])
            if failed_rules:
                critical_failures = [r for r in failed_rules if r.get('severity') == 'critical']
                if critical_failures:
                    alert = Alert(
                        alert_id=f"critical_failures_{int(time.time())}",
                        timestamp=datetime.now(),
                        severity='critical',
                        category='security',
                        title='Critical Security Failures',
                        message=f'Found {len(critical_failures)} critical security failures',
                        source='rule_execution',
                        metadata={'failed_rules': critical_failures}
                    )
                    
                    await self.send_alert(alert)
        
        except Exception as e:
            self.logger.error(f"Failed to process scan results for alerts: {e}")
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through all enabled channels"""
        try:
            # Check throttling
            if self._should_throttle(alert):
                self.logger.debug(f"Alert throttled: {alert.alert_id}")
                return False
            
            # Store alert
            self.alerts.append(alert)
            self.alert_history.append(alert)
            
            # Update statistics
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_severity'][alert.severity] = self.stats['alerts_by_severity'].get(alert.severity, 0) + 1
            self.stats['alerts_by_category'][alert.category] = self.stats['alerts_by_category'].get(alert.category, 0) + 1
            self.stats['last_alert_time'] = alert.timestamp
            
            # Send through all channels
            success_count = 0
            for channel_name, channel in self.channels.items():
                if channel.enabled:
                    try:
                        await self._send_to_channel(alert, channel)
                        success_count += 1
                        self.stats['notifications_sent'] += 1
                    except Exception as e:
                        self.logger.error(f"Failed to send alert to {channel_name}: {e}")
            
            # Cleanup old alerts
            self._cleanup_old_alerts()
            
            self.logger.info(f"Alert sent: {alert.title} ({success_count}/{len(self.channels)} channels)")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False
    
    def _should_throttle(self, alert: Alert) -> bool:
        """Check if alert should be throttled"""
        if not self.throttle_config.get('enabled', True):
            return False
        
        # Check for duplicate alerts
        alert_key = f"{alert.category}_{alert.severity}_{alert.source}"
        now = datetime.now()
        
        if alert_key in self.alert_cache:
            last_alert_time = self.alert_cache[alert_key]
            cooldown_minutes = self.throttle_config.get('cooldown_minutes', 30)
            
            if (now - last_alert_time).total_seconds() < cooldown_minutes * 60:
                return True
        
        # Check alert rate
        window_minutes = self.throttle_config.get('window_minutes', 5)
        window_start = now - timedelta(minutes=window_minutes)
        
        recent_alerts = [a for a in self.alerts if a.timestamp > window_start]
        max_alerts = self.throttle_config.get('max_alerts_per_window', 10)
        
        if len(recent_alerts) >= max_alerts:
            return True
        
        # Update cache
        self.alert_cache[alert_key] = now
        return False
    
    async def _send_to_channel(self, alert: Alert, channel: NotificationChannel):
        """Send alert to specific channel"""
        if channel.type == 'console':
            await self._send_to_console(alert, channel)
        elif channel.type == 'file':
            await self._send_to_file(alert, channel)
        elif channel.type == 'email':
            await self._send_to_email(alert, channel)
        elif channel.type == 'webhook':
            await self._send_to_webhook(alert, channel)
        elif channel.type == 'slack':
            await self._send_to_slack(alert, channel)
    
    async def _send_to_console(self, alert: Alert, channel: NotificationChannel):
        """Send alert to console"""
        severity_colors = {
            'critical': '\033[91m',  # Red
            'high': '\033[93m',      # Yellow
            'medium': '\033[94m',     # Blue
            'low': '\033[92m'         # Green
        }
        
        color = severity_colors.get(alert.severity, '\033[0m')
        reset = '\033[0m'
        
        print(f"{color}[{alert.severity.upper()}] {alert.title}{reset}")
        print(f"  Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Category: {alert.category}")
        print(f"  Message: {alert.message}")
        if alert.metadata:
            print(f"  Metadata: {json.dumps(alert.metadata, indent=2)}")
        print()
    
    async def _send_to_file(self, alert: Alert, channel: NotificationChannel):
        """Send alert to file"""
        file_path = channel.config.get('file', './alerts.log')
        
        alert_data = {
            'timestamp': alert.timestamp.isoformat(),
            'severity': alert.severity,
            'category': alert.category,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'metadata': alert.metadata
        }
        
        with open(file_path, 'a') as f:
            f.write(f"{json.dumps(alert_data)}\n")
    
    async def _send_to_email(self, alert: Alert, channel: NotificationChannel):
        """Send alert via email"""
        config = channel.config
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = config['username']
        msg['To'] = ', '.join(config['to'])
        msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"
        
        # Create body
        body = f"""
Security Alert: {alert.title}

Severity: {alert.severity.upper()}
Category: {alert.category}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{alert.message}

Source: {alert.source}

Metadata:
{json.dumps(alert.metadata, indent=2) if alert.metadata else 'None'}

---
OS Forge Security Monitoring System
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()
    
    async def _send_to_webhook(self, alert: Alert, channel: NotificationChannel):
        """Send alert via webhook"""
        config = channel.config
        
        payload = {
            'alert_id': alert.alert_id,
            'timestamp': alert.timestamp.isoformat(),
            'severity': alert.severity,
            'category': alert.category,
            'title': alert.title,
            'message': alert.message,
            'source': alert.source,
            'metadata': alert.metadata
        }
        
        headers = config.get('headers', {'Content-Type': 'application/json'})
        
        response = requests.post(
            config['url'],
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Webhook failed with status {response.status_code}")
    
    async def _send_to_slack(self, alert: Alert, channel: NotificationChannel):
        """Send alert to Slack"""
        config = channel.config
        
        # Create Slack message
        severity_emoji = {
            'critical': ':red_circle:',
            'high': ':orange_circle:',
            'medium': ':yellow_circle:',
            'low': ':green_circle:'
        }
        
        emoji = severity_emoji.get(alert.severity, ':white_circle:')
        
        slack_message = {
            'channel': config['channel'],
            'text': f"{emoji} *{alert.title}*",
            'attachments': [
                {
                    'color': self._get_slack_color(alert.severity),
                    'fields': [
                        {'title': 'Severity', 'value': alert.severity.upper(), 'short': True},
                        {'title': 'Category', 'value': alert.category, 'short': True},
                        {'title': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'short': True},
                        {'title': 'Source', 'value': alert.source, 'short': True},
                        {'title': 'Message', 'value': alert.message, 'short': False}
                    ]
                }
            ]
        }
        
        if alert.metadata:
            slack_message['attachments'][0]['fields'].append({
                'title': 'Metadata',
                'value': f"```{json.dumps(alert.metadata, indent=2)}```",
                'short': False
            })
        
        response = requests.post(
            config['webhook_url'],
            json=slack_message,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Slack webhook failed with status {response.status_code}")
    
    def _get_slack_color(self, severity: str) -> str:
        """Get Slack color for severity"""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'good',
            'low': 'good'
        }
        return colors.get(severity, 'good')
    
    def _cleanup_old_alerts(self):
        """Cleanup old alerts based on retention policy"""
        try:
            max_alerts = self.config['retention']['max_alerts_in_memory']
            
            if len(self.alerts) > max_alerts:
                # Keep only the most recent alerts
                self.alerts = self.alerts[-max_alerts:]
            
            # Cleanup old cache entries
            now = datetime.now()
            cutoff_time = now - timedelta(hours=24)
            
            self.alert_cache = {
                k: v for k, v in self.alert_cache.items()
                if v > cutoff_time
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old alerts: {e}")
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        return {
            'total_alerts': self.stats['total_alerts'],
            'alerts_by_severity': self.stats['alerts_by_severity'],
            'alerts_by_category': self.stats['alerts_by_category'],
            'notifications_sent': self.stats['notifications_sent'],
            'last_alert_time': self.stats['last_alert_time'].isoformat() if self.stats['last_alert_time'] else None,
            'active_channels': len([c for c in self.channels.values() if c.enabled]),
            'recent_alerts': len([a for a in self.alerts if a.timestamp > datetime.now() - timedelta(hours=24)])
        }
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        
        return [asdict(alert) for alert in recent_alerts]


class SecurityMonitor:
    """
    Comprehensive security monitoring system
    
    Features:
    - Real-time system monitoring
    - File integrity monitoring
    - Process monitoring
    - Network activity monitoring
    - Log analysis
    - Anomaly detection
    """
    
    def __init__(self, alert_manager: AlertManager, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()
        self.alert_manager = alert_manager
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_threads: List[threading.Thread] = []
        self.stop_event = threading.Event()
        
        # Monitoring data
        self.baseline_data: Dict[str, Any] = {}
        self.current_data: Dict[str, Any] = {}
        
        # Statistics
        self.monitor_stats = {
            'files_monitored': 0,
            'processes_monitored': 0,
            'network_connections': 0,
            'log_events_analyzed': 0,
            'anomalies_detected': 0
        }
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for security monitor"""
        return {
            'file_monitoring': {
                'enabled': True,
                'paths': ['/etc', '/usr/bin', '/usr/sbin'],
                'check_interval': 300,  # 5 minutes
                'monitor_permissions': True,
                'monitor_content': False
            },
            'process_monitoring': {
                'enabled': True,
                'check_interval': 60,  # 1 minute
                'monitor_suspicious': True,
                'monitor_privilege_escalation': True
            },
            'network_monitoring': {
                'enabled': True,
                'check_interval': 120,  # 2 minutes
                'monitor_listening_ports': True,
                'monitor_connections': True
            },
            'log_monitoring': {
                'enabled': True,
                'log_files': ['/var/log/auth.log', '/var/log/syslog', '/var/log/secure'],
                'check_interval': 30,  # 30 seconds
                'analyze_patterns': True
            },
            'anomaly_detection': {
                'enabled': True,
                'thresholds': {
                    'file_changes_per_hour': 10,
                    'failed_logins_per_hour': 5,
                    'new_processes_per_hour': 20
                }
            }
        }
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.is_monitoring:
            self.logger.warning("Security monitoring is already running")
            return
        
        self.logger.info("Starting security monitoring...")
        self.is_monitoring = True
        self.stop_event.clear()
        
        # Start monitoring threads
        if self.config['file_monitoring']['enabled']:
            thread = threading.Thread(target=self._monitor_files, daemon=True)
            thread.start()
            self.monitor_threads.append(thread)
        
        if self.config['process_monitoring']['enabled']:
            thread = threading.Thread(target=self._monitor_processes, daemon=True)
            thread.start()
            self.monitor_threads.append(thread)
        
        if self.config['network_monitoring']['enabled']:
            thread = threading.Thread(target=self._monitor_network, daemon=True)
            thread.start()
            self.monitor_threads.append(thread)
        
        if self.config['log_monitoring']['enabled']:
            thread = threading.Thread(target=self._monitor_logs, daemon=True)
            thread.start()
            self.monitor_threads.append(thread)
        
        self.logger.info(f"Security monitoring started with {len(self.monitor_threads)} threads")
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        if not self.is_monitoring:
            return
        
        self.logger.info("Stopping security monitoring...")
        self.is_monitoring = False
        self.stop_event.set()
        
        # Wait for threads to finish
        for thread in self.monitor_threads:
            thread.join(timeout=5)
        
        self.monitor_threads.clear()
        self.logger.info("Security monitoring stopped")
    
    def _monitor_files(self):
        """Monitor file system changes"""
        import os
        import hashlib
        
        config = self.config['file_monitoring']
        paths = config['paths']
        interval = config['check_interval']
        
        self.logger.info(f"Starting file monitoring for paths: {paths}")
        
        # Create baseline
        baseline = {}
        for path in paths:
            if os.path.exists(path):
                baseline[path] = self._get_file_checksums(path)
        
        self.baseline_data['files'] = baseline
        
        while not self.stop_event.is_set():
            try:
                current = {}
                for path in paths:
                    if os.path.exists(path):
                        current[path] = self._get_file_checksums(path)
                
                # Compare with baseline
                changes = self._detect_file_changes(baseline, current)
                
                if changes:
                    self.logger.warning(f"File changes detected: {len(changes)} files")
                    
                    # Send alert
                    alert = Alert(
                        alert_id=f"file_changes_{int(time.time())}",
                        timestamp=datetime.now(),
                        severity='medium',
                        category='system',
                        title='File System Changes Detected',
                        message=f'Detected changes in {len(changes)} files',
                        source='file_monitor',
                        metadata={'changes': changes}
                    )
                    
                    asyncio.run(self.alert_manager.send_alert(alert))
                    
                    # Update baseline
                    baseline = current
                    self.baseline_data['files'] = baseline
                
                self.monitor_stats['files_monitored'] = sum(len(files) for files in current.values())
                
            except Exception as e:
                self.logger.error(f"File monitoring error: {e}")
            
            self.stop_event.wait(interval)
    
    def _get_file_checksums(self, path: str) -> Dict[str, str]:
        """Get checksums for all files in path"""
        import os
        import hashlib
        
        checksums = {}
        
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            checksum = hashlib.md5(content).hexdigest()
                            checksums[file_path] = checksum
                    except (PermissionError, OSError):
                        # Skip files we can't read
                        continue
        except Exception as e:
            self.logger.error(f"Error getting checksums for {path}: {e}")
        
        return checksums
    
    def _detect_file_changes(self, baseline: Dict[str, Dict[str, str]], current: Dict[str, Dict[str, str]]) -> List[str]:
        """Detect file changes between baseline and current state"""
        changes = []
        
        for path in baseline:
            if path in current:
                baseline_files = baseline[path]
                current_files = current[path]
                
                # Check for modified files
                for file_path, checksum in current_files.items():
                    if file_path in baseline_files:
                        if baseline_files[file_path] != checksum:
                            changes.append(file_path)
                    else:
                        changes.append(file_path)  # New file
        
        return changes
    
    def _monitor_processes(self):
        """Monitor running processes"""
        import psutil
        
        config = self.config['process_monitoring']
        interval = config['check_interval']
        
        self.logger.info("Starting process monitoring")
        
        baseline_processes = set()
        
        while not self.stop_event.is_set():
            try:
                current_processes = set()
                suspicious_processes = []
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
                    try:
                        proc_info = proc.info
                        current_processes.add(proc_info['name'])
                        
                        # Check for suspicious processes
                        if self._is_suspicious_process(proc_info):
                            suspicious_processes.append(proc_info)
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Detect new processes
                new_processes = current_processes - baseline_processes
                if new_processes:
                    self.logger.info(f"New processes detected: {new_processes}")
                
                # Check for suspicious processes
                if suspicious_processes:
                    alert = Alert(
                        alert_id=f"suspicious_processes_{int(time.time())}",
                        timestamp=datetime.now(),
                        severity='high',
                        category='security',
                        title='Suspicious Processes Detected',
                        message=f'Found {len(suspicious_processes)} suspicious processes',
                        source='process_monitor',
                        metadata={'processes': suspicious_processes}
                    )
                    
                    asyncio.run(self.alert_manager.send_alert(alert))
                
                baseline_processes = current_processes
                self.monitor_stats['processes_monitored'] = len(current_processes)
                
            except Exception as e:
                self.logger.error(f"Process monitoring error: {e}")
            
            self.stop_event.wait(interval)
    
    def _is_suspicious_process(self, proc_info: Dict[str, Any]) -> bool:
        """Check if process is suspicious"""
        suspicious_patterns = [
            'nc', 'netcat', 'ncat',
            'wget', 'curl',
            'base64',
            'python -c',
            'perl -e',
            'bash -c'
        ]
        
        cmdline = ' '.join(proc_info.get('cmdline', []))
        cmdline_lower = cmdline.lower()
        
        return any(pattern in cmdline_lower for pattern in suspicious_patterns)
    
    def _monitor_network(self):
        """Monitor network activity"""
        import psutil
        
        config = self.config['network_monitoring']
        interval = config['check_interval']
        
        self.logger.info("Starting network monitoring")
        
        baseline_connections = set()
        
        while not self.stop_event.is_set():
            try:
                current_connections = set()
                
                # Monitor listening ports
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'LISTEN':
                        current_connections.add(f"{conn.laddr.ip}:{conn.laddr.port}")
                
                # Detect new listening ports
                new_ports = current_connections - baseline_connections
                if new_ports:
                    self.logger.warning(f"New listening ports detected: {new_ports}")
                    
                    alert = Alert(
                        alert_id=f"new_listening_ports_{int(time.time())}",
                        timestamp=datetime.now(),
                        severity='medium',
                        category='network',
                        title='New Listening Ports Detected',
                        message=f'New ports listening: {list(new_ports)}',
                        source='network_monitor',
                        metadata={'new_ports': list(new_ports)}
                    )
                    
                    asyncio.run(self.alert_manager.send_alert(alert))
                
                baseline_connections = current_connections
                self.monitor_stats['network_connections'] = len(current_connections)
                
            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")
            
            self.stop_event.wait(interval)
    
    def _monitor_logs(self):
        """Monitor log files for security events"""
        config = self.config['log_monitoring']
        log_files = config['log_files']
        interval = config['check_interval']
        
        self.logger.info(f"Starting log monitoring for files: {log_files}")
        
        # Track file positions
        file_positions = {}
        
        while not self.stop_event.is_set():
            try:
                security_events = []
                
                for log_file in log_files:
                    if os.path.exists(log_file):
                        try:
                            # Read new lines since last check
                            if log_file not in file_positions:
                                file_positions[log_file] = 0
                            
                            with open(log_file, 'r') as f:
                                f.seek(file_positions[log_file])
                                new_lines = f.readlines()
                                file_positions[log_file] = f.tell()
                            
                            # Analyze new lines
                            for line in new_lines:
                                events = self._analyze_log_line(line, log_file)
                                security_events.extend(events)
                        
                        except (PermissionError, OSError) as e:
                            self.logger.warning(f"Cannot read log file {log_file}: {e}")
                
                # Process security events
                if security_events:
                    self.logger.info(f"Found {len(security_events)} security events in logs")
                    
                    for event in security_events:
                        alert = Alert(
                            alert_id=f"log_event_{int(time.time())}_{hash(event['line']) % 10000}",
                            timestamp=datetime.now(),
                            severity=event['severity'],
                            category='security',
                            title=event['title'],
                            message=event['description'],
                            source='log_monitor',
                            metadata={'log_file': event['log_file'], 'line': event['line']}
                        )
                        
                        asyncio.run(self.alert_manager.send_alert(alert))
                
                self.monitor_stats['log_events_analyzed'] += len(security_events)
                
            except Exception as e:
                self.logger.error(f"Log monitoring error: {e}")
            
            self.stop_event.wait(interval)
    
    def _analyze_log_line(self, line: str, log_file: str) -> List[Dict[str, Any]]:
        """Analyze a log line for security events"""
        events = []
        line_lower = line.lower()
        
        # Failed login attempts
        if 'failed password' in line_lower or 'authentication failure' in line_lower:
            events.append({
                'severity': 'medium',
                'title': 'Failed Login Attempt',
                'description': 'Failed authentication attempt detected',
                'log_file': log_file,
                'line': line.strip()
            })
        
        # Privilege escalation attempts
        elif 'sudo' in line_lower and 'incorrect password' in line_lower:
            events.append({
                'severity': 'high',
                'title': 'Privilege Escalation Attempt',
                'description': 'Failed sudo attempt with incorrect password',
                'log_file': log_file,
                'line': line.strip()
            })
        
        # Suspicious commands
        elif any(cmd in line_lower for cmd in ['nc ', 'netcat', 'wget', 'curl', 'base64']):
            events.append({
                'severity': 'high',
                'title': 'Suspicious Command Detected',
                'description': 'Potentially malicious command detected in logs',
                'log_file': log_file,
                'line': line.strip()
            })
        
        # System errors
        elif 'error' in line_lower or 'critical' in line_lower:
            events.append({
                'severity': 'medium',
                'title': 'System Error',
                'description': 'System error or critical event detected',
                'log_file': log_file,
                'line': line.strip()
            })
        
        return events
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'active_threads': len(self.monitor_threads),
            'statistics': self.monitor_stats,
            'config': self.config
        }


# Integration with deep scanner
class IntegratedSecuritySystem:
    """
    Integrated security system combining deep scanning, monitoring, and alerting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.security_monitor = SecurityMonitor(self.alert_manager, self.config.get('monitoring', {}))
        
        # Integration state
        self.is_running = False
    
    async def start_integrated_monitoring(self):
        """Start integrated security monitoring"""
        self.logger.info("Starting integrated security system...")
        
        # Start security monitoring
        self.security_monitor.start_monitoring()
        
        self.is_running = True
        self.logger.info("Integrated security system started")
    
    def stop_integrated_monitoring(self):
        """Stop integrated security monitoring"""
        self.logger.info("Stopping integrated security system...")
        
        # Stop security monitoring
        self.security_monitor.stop_monitoring()
        
        self.is_running = False
        self.logger.info("Integrated security system stopped")
    
    async def process_scan_results(self, scan_data: Dict[str, Any]):
        """Process scan results through alert system"""
        await self.alert_manager.process_scan_results(scan_data)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'is_running': self.is_running,
            'alert_manager': self.alert_manager.get_alert_statistics(),
            'security_monitor': self.security_monitor.get_monitoring_status()
        }

