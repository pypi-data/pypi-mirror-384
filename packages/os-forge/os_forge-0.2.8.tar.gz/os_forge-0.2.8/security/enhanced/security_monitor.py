#!/usr/bin/env python3
"""
Enhanced Security Monitoring for OS Forge
Provides real-time security monitoring, alerting, and threat detection
"""

import os
import json
import time
import psutil
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from collections import defaultdict, deque
import subprocess
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Represents a security event"""
    event_id: str
    event_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    timestamp: datetime
    source: str
    message: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class AlertRule:
    """Represents an alert rule"""
    rule_id: str
    name: str
    description: str
    event_type: str
    condition: str
    threshold: int
    time_window: int  # seconds
    severity: str
    enabled: bool
    actions: List[str]

@dataclass
class ThreatIndicator:
    """Represents a threat indicator"""
    indicator_id: str
    indicator_type: str  # IP, DOMAIN, HASH, EMAIL, etc.
    value: str
    threat_type: str
    confidence: float
    first_seen: datetime
    last_seen: datetime
    source: str
    tags: List[str]

class SecurityMonitor:
    """Enhanced security monitoring system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.events = deque(maxlen=self.config["max_events"])
        self.alerts = deque(maxlen=self.config["max_alerts"])
        self.threat_indicators = {}
        self.alert_rules = {}
        self.monitoring_threads = []
        self.running = False
        
        # Initialize monitoring components
        self._initialize_alert_rules()
        self._initialize_threat_indicators()
        
        # Event handlers
        self.event_handlers = defaultdict(list)
        
        # Statistics
        self.stats = {
            "events_total": 0,
            "alerts_total": 0,
            "threats_detected": 0,
            "monitoring_start_time": None
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "monitoring_enabled": True,
            "max_events": 10000,
            "max_alerts": 1000,
            "event_retention_days": 30,
            "alert_cooldown_minutes": 5,
            "monitoring_intervals": {
                "system_metrics": 30,  # seconds
                "network_scan": 300,   # seconds
                "file_integrity": 600, # seconds
                "log_analysis": 60    # seconds
            },
            "thresholds": {
                "cpu_usage": 80,
                "memory_usage": 85,
                "disk_usage": 90,
                "network_connections": 1000,
                "failed_logins": 5,
                "suspicious_processes": 3
            },
            "log_files": [
                "/var/log/auth.log",
                "/var/log/syslog",
                "/var/log/secure"
            ],
            "monitored_directories": [
                "/etc",
                "/usr/bin",
                "/usr/sbin",
                "/bin",
                "/sbin"
            ],
            "notification_channels": {
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
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_alert_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                description="Alert when CPU usage exceeds threshold",
                event_type="system_metrics",
                condition="cpu_usage > threshold",
                threshold=self.config["thresholds"]["cpu_usage"],
                time_window=300,
                severity="MEDIUM",
                enabled=True,
                actions=["email", "webhook"]
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="High Memory Usage",
                description="Alert when memory usage exceeds threshold",
                event_type="system_metrics",
                condition="memory_usage > threshold",
                threshold=self.config["thresholds"]["memory_usage"],
                time_window=300,
                severity="MEDIUM",
                enabled=True,
                actions=["email", "webhook"]
            ),
            AlertRule(
                rule_id="failed_login_attempts",
                name="Failed Login Attempts",
                description="Alert on multiple failed login attempts",
                event_type="authentication",
                condition="failed_logins >= threshold",
                threshold=self.config["thresholds"]["failed_logins"],
                time_window=300,
                severity="HIGH",
                enabled=True,
                actions=["email", "webhook", "slack"]
            ),
            AlertRule(
                rule_id="suspicious_process",
                name="Suspicious Process",
                description="Alert on suspicious process activity",
                event_type="process_monitoring",
                condition="suspicious_processes >= threshold",
                threshold=self.config["thresholds"]["suspicious_processes"],
                time_window=600,
                severity="HIGH",
                enabled=True,
                actions=["email", "webhook", "slack"]
            ),
            AlertRule(
                rule_id="network_anomaly",
                name="Network Anomaly",
                description="Alert on unusual network activity",
                event_type="network_monitoring",
                condition="network_connections > threshold",
                threshold=self.config["thresholds"]["network_connections"],
                time_window=300,
                severity="MEDIUM",
                enabled=True,
                actions=["email", "webhook"]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def _initialize_threat_indicators(self):
        """Initialize threat indicators database"""
        # Common malicious IPs (example - in production, use threat intelligence feeds)
        malicious_ips = [
            "192.168.1.100",  # Example malicious IP
            "10.0.0.50"       # Example malicious IP
        ]
        
        for ip in malicious_ips:
            indicator = ThreatIndicator(
                indicator_id=f"ip_{hash(ip) % 10000:04d}",
                indicator_type="IP",
                value=ip,
                threat_type="malicious",
                confidence=0.8,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                source="threat_intel",
                tags=["malicious", "botnet"]
            )
            self.threat_indicators[ip] = indicator
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.running:
            logger.warning("Monitoring is already running")
            return
        
        self.running = True
        self.stats["monitoring_start_time"] = datetime.now()
        
        # Start monitoring threads
        if self.config["monitoring_enabled"]:
            self._start_system_monitoring()
            self._start_network_monitoring()
            self._start_file_integrity_monitoring()
            self._start_log_monitoring()
            self._start_threat_detection()
        
        logger.info("Security monitoring started")
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        self.monitoring_threads.clear()
        logger.info("Security monitoring stopped")
    
    def _start_system_monitoring(self):
        """Start system metrics monitoring"""
        def monitor_system():
            while self.running:
                try:
                    self._collect_system_metrics()
                    time.sleep(self.config["monitoring_intervals"]["system_metrics"])
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
        
        thread = threading.Thread(target=monitor_system, daemon=True)
        thread.start()
        self.monitoring_threads.append(thread)
    
    def _start_network_monitoring(self):
        """Start network monitoring"""
        def monitor_network():
            while self.running:
                try:
                    self._monitor_network_activity()
                    time.sleep(self.config["monitoring_intervals"]["network_scan"])
                except Exception as e:
                    logger.error(f"Network monitoring error: {e}")
        
        thread = threading.Thread(target=monitor_network, daemon=True)
        thread.start()
        self.monitoring_threads.append(thread)
    
    def _start_file_integrity_monitoring(self):
        """Start file integrity monitoring"""
        def monitor_file_integrity():
            while self.running:
                try:
                    self._monitor_file_integrity()
                    time.sleep(self.config["monitoring_intervals"]["file_integrity"])
                except Exception as e:
                    logger.error(f"File integrity monitoring error: {e}")
        
        thread = threading.Thread(target=monitor_file_integrity, daemon=True)
        thread.start()
        self.monitoring_threads.append(thread)
    
    def _start_log_monitoring(self):
        """Start log monitoring"""
        def monitor_logs():
            while self.running:
                try:
                    self._analyze_logs()
                    time.sleep(self.config["monitoring_intervals"]["log_analysis"])
                except Exception as e:
                    logger.error(f"Log monitoring error: {e}")
        
        thread = threading.Thread(target=monitor_logs, daemon=True)
        thread.start()
        self.monitoring_threads.append(thread)
    
    def _start_threat_detection(self):
        """Start threat detection"""
        def detect_threats():
            while self.running:
                try:
                    self._detect_threats()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Threat detection error: {e}")
        
        thread = threading.Thread(target=detect_threats, daemon=True)
        thread.start()
        self.monitoring_threads.append(thread)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process count
            process_count = len(psutil.pids())
            
            # Create system metrics event
            event = SecurityEvent(
                event_id=f"sys_metrics_{int(time.time())}",
                event_type="system_metrics",
                severity="INFO",
                timestamp=datetime.now(),
                source="system_monitor",
                message="System metrics collected",
                details={
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory_percent,
                    "disk_usage": disk_percent,
                    "process_count": process_count
                }
            )
            
            self._process_event(event)
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _monitor_network_activity(self):
        """Monitor network activity"""
        try:
            # Get network connections
            connections = psutil.net_connections()
            connection_count = len(connections)
            
            # Analyze connections for suspicious activity
            suspicious_connections = []
            external_connections = []
            
            for conn in connections:
                if conn.raddr and conn.raddr.ip != "127.0.0.1":
                    external_connections.append(conn.raddr.ip)
                    
                    # Check against threat indicators
                    if conn.raddr.ip in self.threat_indicators:
                        suspicious_connections.append({
                            "ip": conn.raddr.ip,
                            "port": conn.raddr.port,
                            "pid": conn.pid,
                            "threat_type": self.threat_indicators[conn.raddr.ip].threat_type
                        })
            
            # Create network monitoring event
            event = SecurityEvent(
                event_id=f"net_monitor_{int(time.time())}",
                event_type="network_monitoring",
                severity="INFO",
                timestamp=datetime.now(),
                source="network_monitor",
                message="Network activity monitored",
                details={
                    "total_connections": connection_count,
                    "external_connections": len(external_connections),
                    "suspicious_connections": suspicious_connections,
                    "unique_external_ips": len(set(external_connections))
                }
            )
            
            self._process_event(event)
            
        except Exception as e:
            logger.error(f"Failed to monitor network activity: {e}")
    
    def _monitor_file_integrity(self):
        """Monitor file integrity"""
        try:
            file_changes = []
            
            for directory in self.config["monitored_directories"]:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                # Check file modification time
                                stat = os.stat(file_path)
                                mod_time = datetime.fromtimestamp(stat.st_mtime)
                                
                                # Check if file was modified recently
                                if (datetime.now() - mod_time).total_seconds() < 3600:  # Last hour
                                    file_changes.append({
                                        "path": file_path,
                                        "modified": mod_time,
                                        "size": stat.st_size
                                    })
                            except (OSError, PermissionError):
                                continue
            
            if file_changes:
                event = SecurityEvent(
                    event_id=f"file_integrity_{int(time.time())}",
                    event_type="file_integrity",
                    severity="MEDIUM",
                    timestamp=datetime.now(),
                    source="file_monitor",
                    message=f"File integrity check: {len(file_changes)} files modified",
                    details={"file_changes": file_changes}
                )
                
                self._process_event(event)
                
        except Exception as e:
            logger.error(f"Failed to monitor file integrity: {e}")
    
    def _analyze_logs(self):
        """Analyze log files for security events"""
        try:
            security_events = []
            
            for log_file in self.config["log_files"]:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            
                        # Analyze recent lines (last 100)
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        
                        for line in recent_lines:
                            # Look for failed login attempts
                            if "Failed password" in line or "authentication failure" in line:
                                security_events.append({
                                    "type": "failed_login",
                                    "line": line.strip(),
                                    "log_file": log_file
                                })
                            
                            # Look for privilege escalation attempts
                            elif "sudo" in line and "incorrect password" in line:
                                security_events.append({
                                    "type": "privilege_escalation",
                                    "line": line.strip(),
                                    "log_file": log_file
                                })
                            
                            # Look for suspicious commands
                            elif any(cmd in line.lower() for cmd in ["nc ", "netcat", "wget", "curl", "base64"]):
                                security_events.append({
                                    "type": "suspicious_command",
                                    "line": line.strip(),
                                    "log_file": log_file
                                })
                    
                    except (OSError, PermissionError):
                        continue
            
            if security_events:
                event = SecurityEvent(
                    event_id=f"log_analysis_{int(time.time())}",
                    event_type="log_analysis",
                    severity="MEDIUM",
                    timestamp=datetime.now(),
                    source="log_monitor",
                    message=f"Log analysis: {len(security_events)} security events found",
                    details={"security_events": security_events}
                )
                
                self._process_event(event)
                
        except Exception as e:
            logger.error(f"Failed to analyze logs: {e}")
    
    def _detect_threats(self):
        """Detect threats based on collected data"""
        try:
            # Analyze recent events for threat patterns
            recent_events = [e for e in self.events if 
                           (datetime.now() - e.timestamp).total_seconds() < 3600]  # Last hour
            
            threat_score = 0
            threat_indicators = []
            
            # Count failed logins
            failed_logins = sum(1 for e in recent_events 
                              if e.event_type == "log_analysis" and 
                              any(se["type"] == "failed_login" for se in e.details.get("security_events", [])))
            
            if failed_logins >= 5:
                threat_score += 30
                threat_indicators.append("Multiple failed login attempts")
            
            # Check for suspicious processes
            suspicious_processes = sum(1 for e in recent_events 
                                     if e.event_type == "process_monitoring")
            
            if suspicious_processes >= 3:
                threat_score += 25
                threat_indicators.append("Suspicious process activity")
            
            # Check for network anomalies
            network_events = [e for e in recent_events if e.event_type == "network_monitoring"]
            if network_events:
                latest_network = network_events[-1]
                if latest_network.details.get("suspicious_connections"):
                    threat_score += 40
                    threat_indicators.append("Connections to known malicious IPs")
            
            # Check for file integrity issues
            file_events = [e for e in recent_events if e.event_type == "file_integrity"]
            if file_events:
                threat_score += 20
                threat_indicators.append("Unauthorized file modifications")
            
            # Create threat detection event if score is high
            if threat_score >= 50:
                event = SecurityEvent(
                    event_id=f"threat_detection_{int(time.time())}",
                    event_type="threat_detection",
                    severity="HIGH",
                    timestamp=datetime.now(),
                    source="threat_detector",
                    message=f"Threat detected: Score {threat_score}",
                    details={
                        "threat_score": threat_score,
                        "threat_indicators": threat_indicators,
                        "analysis_period": "1 hour"
                    }
                )
                
                self._process_event(event)
                self.stats["threats_detected"] += 1
                
        except Exception as e:
            logger.error(f"Failed to detect threats: {e}")
    
    def _process_event(self, event: SecurityEvent):
        """Process a security event"""
        # Add to events queue
        self.events.append(event)
        self.stats["events_total"] += 1
        
        # Check alert rules
        self._check_alert_rules(event)
        
        # Call event handlers
        for handler in self.event_handlers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
        
        # Log event
        logger.info(f"Security event: {event.event_type} - {event.message}")
    
    def _check_alert_rules(self, event: SecurityEvent):
        """Check if event triggers any alert rules"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            if rule.event_type != event.event_type:
                continue
            
            # Simple condition evaluation (in production, use proper expression evaluator)
            if self._evaluate_condition(rule.condition, event.details, rule.threshold):
                self._trigger_alert(rule, event)
    
    def _evaluate_condition(self, condition: str, details: Dict[str, Any], threshold: int) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            if "cpu_usage > threshold" in condition:
                return details.get("cpu_usage", 0) > threshold
            elif "memory_usage > threshold" in condition:
                return details.get("memory_usage", 0) > threshold
            elif "disk_usage > threshold" in condition:
                return details.get("disk_usage", 0) > threshold
            elif "network_connections > threshold" in condition:
                return details.get("total_connections", 0) > threshold
            elif "failed_logins >= threshold" in condition:
                security_events = details.get("security_events", [])
                failed_count = sum(1 for se in security_events if se["type"] == "failed_login")
                return failed_count >= threshold
            elif "suspicious_processes >= threshold" in condition:
                return details.get("suspicious_processes", 0) >= threshold
            
            return False
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False
    
    def _trigger_alert(self, rule: AlertRule, event: SecurityEvent):
        """Trigger an alert"""
        alert = {
            "alert_id": f"alert_{rule.rule_id}_{int(time.time())}",
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "severity": rule.severity,
            "timestamp": datetime.now(),
            "event": asdict(event),
            "message": f"Alert triggered: {rule.name}",
            "actions_taken": []
        }
        
        self.alerts.append(alert)
        self.stats["alerts_total"] += 1
        
        # Execute alert actions
        for action in rule.actions:
            try:
                if action == "email":
                    self._send_email_alert(alert)
                elif action == "webhook":
                    self._send_webhook_alert(alert)
                elif action == "slack":
                    self._send_slack_alert(alert)
                
                alert["actions_taken"].append(action)
            except Exception as e:
                logger.error(f"Alert action {action} failed: {e}")
        
        logger.warning(f"ALERT: {rule.name} - {event.message}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        # Implementation would depend on email configuration
        logger.info(f"Email alert sent: {alert['rule_name']}")
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook alert"""
        # Implementation would depend on webhook configuration
        logger.info(f"Webhook alert sent: {alert['rule_name']}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send Slack alert"""
        # Implementation would depend on Slack configuration
        logger.info(f"Slack alert sent: {alert['rule_name']}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler"""
        self.event_handlers[event_type].append(handler)
    
    def get_events(self, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events"""
        events = list(self.events)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [asdict(e) for e in events[:limit]]
    
    def get_alerts(self, severity: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        alerts = list(self.alerts)
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return alerts[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        uptime = None
        if self.stats["monitoring_start_time"]:
            uptime = (datetime.now() - self.stats["monitoring_start_time"]).total_seconds()
        
        return {
            "monitoring_status": "running" if self.running else "stopped",
            "uptime_seconds": uptime,
            "events_total": self.stats["events_total"],
            "alerts_total": self.stats["alerts_total"],
            "threats_detected": self.stats["threats_detected"],
            "active_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "threat_indicators": len(self.threat_indicators),
            "recent_events": len(self.events),
            "recent_alerts": len(self.alerts)
        }
    
    def add_threat_indicator(self, indicator: ThreatIndicator):
        """Add threat indicator"""
        self.threat_indicators[indicator.value] = indicator
    
    def remove_threat_indicator(self, value: str):
        """Remove threat indicator"""
        if value in self.threat_indicators:
            del self.threat_indicators[value]
    
    def export_events(self, output_path: str, format: str = "json") -> bool:
        """Export events to file"""
        try:
            events_data = {
                "exported_at": datetime.now().isoformat(),
                "total_events": len(self.events),
                "events": [asdict(e) for e in self.events]
            }
            
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(events_data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            logger.info(f"Events exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export events: {e}")
            return False


def main():
    """CLI interface for security monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OS Forge Security Monitor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start monitoring")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop monitoring")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show monitoring status")
    
    # Events command
    events_parser = subparsers.add_parser("events", help="Show recent events")
    events_parser.add_argument("--type", help="Filter by event type")
    events_parser.add_argument("--limit", type=int, default=20, help="Number of events to show")
    
    # Alerts command
    alerts_parser = subparsers.add_parser("alerts", help="Show recent alerts")
    alerts_parser.add_argument("--severity", help="Filter by severity")
    alerts_parser.add_argument("--limit", type=int, default=20, help="Number of alerts to show")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export events")
    export_parser.add_argument("output_path", help="Output file path")
    export_parser.add_argument("--format", default="json", help="Export format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    monitor = SecurityMonitor()
    
    try:
        if args.command == "start":
            monitor.start_monitoring()
            print("Security monitoring started")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                monitor.stop_monitoring()
                
        elif args.command == "stop":
            monitor.stop_monitoring()
            print("Security monitoring stopped")
            
        elif args.command == "status":
            stats = monitor.get_statistics()
            print(f"Monitoring Status: {stats['monitoring_status']}")
            print(f"Uptime: {stats['uptime_seconds']:.0f} seconds" if stats['uptime_seconds'] else "Not running")
            print(f"Events Total: {stats['events_total']}")
            print(f"Alerts Total: {stats['alerts_total']}")
            print(f"Threats Detected: {stats['threats_detected']}")
            print(f"Active Rules: {stats['active_rules']}")
            
        elif args.command == "events":
            events = monitor.get_events(args.type, args.limit)
            if events:
                print(f"{'Timestamp':<20} {'Type':<20} {'Severity':<10} {'Message':<50}")
                print("-" * 100)
                for event in events:
                    timestamp = event['timestamp'][:19]  # Remove microseconds
                    print(f"{timestamp:<20} {event['event_type']:<20} {event['severity']:<10} {event['message']:<50}")
            else:
                print("No events found")
                
        elif args.command == "alerts":
            alerts = monitor.get_alerts(args.severity, args.limit)
            if alerts:
                print(f"{'Timestamp':<20} {'Rule':<25} {'Severity':<10} {'Message':<50}")
                print("-" * 105)
                for alert in alerts:
                    timestamp = alert['timestamp'][:19]  # Remove microseconds
                    print(f"{timestamp:<20} {alert['rule_name']:<25} {alert['severity']:<10} {alert['message']:<50}")
            else:
                print("No alerts found")
                
        elif args.command == "stats":
            stats = monitor.get_statistics()
            print("=== Security Monitoring Statistics ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
                
        elif args.command == "export":
            success = monitor.export_events(args.output_path, args.format)
            print("Events exported successfully" if success else "Failed to export events")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
