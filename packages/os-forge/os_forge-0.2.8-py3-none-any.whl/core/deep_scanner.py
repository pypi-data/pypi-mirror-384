"""
Deep Security Scanner for OS Forge

Provides comprehensive, minute-by-minute security scanning with:
- Real-time monitoring
- Continuous compliance checking
- Automated remediation
- Cross-platform support
- Detailed reporting and alerting
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import signal
import sys

from agents.common.os_detector import OSDetector
from policies.engine import PolicyEngine
from security.executor import SecureCommandExecutor
from database.manager import DatabaseManager


@dataclass
class ScanResult:
    """Result of a single scan operation"""
    timestamp: datetime
    rule_id: str
    rule_name: str
    status: str  # pass, fail, error, skip
    severity: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    remediation_applied: bool = False
    compliance_score: float = 0.0


@dataclass
class ScanSession:
    """Complete scan session results"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    error_rules: int = 0
    skipped_rules: int = 0
    compliance_score: float = 0.0
    scan_level: str = "basic"
    os_type: str = "unknown"
    results: List[ScanResult] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []


class DeepSecurityScanner:
    """
    Comprehensive deep security scanner with continuous monitoring capabilities
    
    Features:
    - Real-time security monitoring
    - Automated remediation
    - Cross-platform support
    - Detailed compliance reporting
    - Alert system for critical issues
    - Historical trend analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._default_config()
        
        # Initialize components
        self.os_detector = OSDetector(self.logger)
        self.policy_engine = PolicyEngine()
        self.secure_executor = SecureCommandExecutor()
        self.db_manager = DatabaseManager()
        
        # OS information
        self.os_info = self.os_detector.detect_os()
        
        # Scanning state
        self.is_running = False
        self.current_session: Optional[ScanSession] = None
        self.scan_history: List[ScanSession] = []
        
        # Monitoring threads
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Alert thresholds
        self.alert_thresholds = {
            'critical': 0.8,  # Alert if compliance drops below 80%
            'high': 0.9,      # Alert if compliance drops below 90%
            'medium': 0.95    # Alert if compliance drops below 95%
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for deep scanning"""
        return {
            'scan_interval': 60,  # Scan every minute
            'scan_levels': ['basic', 'moderate', 'strict'],
            'auto_remediate': True,
            'max_remediation_attempts': 3,
            'alert_on_critical': True,
            'alert_on_compliance_drop': True,
            'compliance_threshold': 0.9,
            'log_level': 'INFO',
            'output_format': 'json',
            'save_reports': True,
            'report_directory': './scan_reports',
            'enable_notifications': False,
            'notification_channels': ['console', 'file'],
            'retention_days': 30
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
    
    async def initialize(self) -> bool:
        """Initialize the scanner and database connection"""
        try:
            # Initialize database
            await self.db_manager.initialize()
            
            # Create report directory
            report_dir = Path(self.config['report_directory'])
            report_dir.mkdir(exist_ok=True)
            
            self.logger.info("Deep Security Scanner initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scanner: {e}")
            return False
    
    async def run_single_scan(self, level: str = "basic", auto_remediate: bool = True) -> ScanSession:
        """
        Run a single comprehensive security scan
        
        Args:
            level: Scan level (basic, moderate, strict)
            auto_remediate: Whether to automatically apply fixes
            
        Returns:
            ScanSession: Complete scan results
        """
        session_id = f"scan_{int(time.time())}"
        start_time = datetime.now()
        
        self.logger.info(f"Starting deep security scan (Level: {level}, Auto-remediate: {auto_remediate})")
        
        # Create scan session
        session = ScanSession(
            session_id=session_id,
            start_time=start_time,
            scan_level=level,
            os_type=self.os_info['type']
        )
        
        try:
            # Get applicable rules
            rules = self.policy_engine.get_applicable_rules(level, self.os_info['type'])
            session.total_rules = len(rules)
            
            self.logger.info(f"Found {len(rules)} applicable rules for {self.os_info['type']}")
            
            # Execute rules
            for rule in rules:
                result = await self._execute_rule(rule, auto_remediate)
                session.results.append(result)
                
                # Update counters
                if result.status == "pass":
                    session.passed_rules += 1
                elif result.status == "fail":
                    session.failed_rules += 1
                elif result.status == "error":
                    session.error_rules += 1
                else:
                    session.skipped_rules += 1
            
            # Calculate compliance score
            session.compliance_score = self._calculate_compliance_score(session.results)
            session.end_time = datetime.now()
            
            # Save session to database
            await self._save_scan_session(session)
            
            # Generate report
            if self.config['save_reports']:
                await self._generate_report(session)
            
            # Check for alerts
            await self._check_alerts(session)
            
            self.logger.info(f"Scan completed: {session.passed_rules}/{session.total_rules} passed, "
                           f"Compliance: {session.compliance_score:.2%}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            session.end_time = datetime.now()
            return session
    
    async def _execute_rule(self, rule: Dict[str, Any], auto_remediate: bool) -> ScanResult:
        """Execute a single rule and return detailed results"""
        start_time = time.time()
        
        try:
            # Execute the rule
            rule_result = self.policy_engine.execute_rule(rule, dry_run=not auto_remediate)
            
            execution_time = time.time() - start_time
            
            # Create detailed result
            result = ScanResult(
                timestamp=datetime.now(),
                rule_id=rule_result.rule_id,
                rule_name=rule_result.description,
                status=rule_result.status,
                severity=rule.get('severity', 'medium'),
                old_value=rule_result.old_value,
                new_value=rule_result.new_value,
                error_message=rule_result.error,
                execution_time=execution_time,
                remediation_applied=not auto_remediate and rule_result.status == "pass",
                compliance_score=self._calculate_rule_compliance_score(rule_result)
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ScanResult(
                timestamp=datetime.now(),
                rule_id=rule.get('id', 'unknown'),
                rule_name=rule.get('description', 'Unknown rule'),
                status="error",
                severity=rule.get('severity', 'medium'),
                error_message=str(e),
                execution_time=execution_time,
                compliance_score=0.0
            )
    
    def _calculate_compliance_score(self, results: List[ScanResult]) -> float:
        """Calculate overall compliance score"""
        if not results:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        severity_weights = {
            'critical': 4.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        
        for result in results:
            weight = severity_weights.get(result.severity, 1.0)
            total_weight += weight
            
            if result.status == "pass":
                weighted_score += weight
            elif result.status == "fail":
                weighted_score += weight * 0.0  # No points for failed rules
            elif result.status == "error":
                weighted_score += weight * 0.0  # No points for errors
            else:  # skip
                weighted_score += weight * 0.5  # Half points for skipped rules
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_rule_compliance_score(self, rule_result) -> float:
        """Calculate compliance score for a single rule"""
        if rule_result.status == "pass":
            return 1.0
        elif rule_result.status == "fail":
            return 0.0
        elif rule_result.status == "error":
            return 0.0
        else:  # skip
            return 0.5
    
    async def _save_scan_session(self, session: ScanSession):
        """Save scan session to database"""
        try:
            # Convert to dict for database storage
            session_data = {
                'session_id': session.session_id,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'total_rules': session.total_rules,
                'passed_rules': session.passed_rules,
                'failed_rules': session.failed_rules,
                'error_rules': session.error_rules,
                'skipped_rules': session.skipped_rules,
                'compliance_score': session.compliance_score,
                'scan_level': session.scan_level,
                'os_type': session.os_type,
                'results': [asdict(result) for result in session.results]
            }
            
            await self.db_manager.create_scan_session(session_data)
            
        except Exception as e:
            self.logger.warning(f"Failed to save scan session to database: {e}")
    
    async def _generate_report(self, session: ScanSession):
        """Generate detailed scan report"""
        try:
            report_dir = Path(self.config['report_directory'])
            timestamp = session.start_time.strftime("%Y%m%d_%H%M%S")
            
            if self.config['output_format'] == 'json':
                report_file = report_dir / f"scan_report_{session.session_id}_{timestamp}.json"
                
                report_data = {
                    'session': asdict(session),
                    'summary': {
                        'total_rules': session.total_rules,
                        'passed_rules': session.passed_rules,
                        'failed_rules': session.failed_rules,
                        'error_rules': session.error_rules,
                        'skipped_rules': session.skipped_rules,
                        'compliance_score': session.compliance_score,
                        'scan_duration': (session.end_time - session.start_time).total_seconds() if session.end_time else 0
                    },
                    'os_info': self.os_info,
                    'config': self.config
                }
                
                with open(report_file, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                self.logger.info(f"Report saved to: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
    
    async def _check_alerts(self, session: ScanSession):
        """Check for alert conditions and send notifications"""
        try:
            alerts = []
            
            # Check compliance threshold
            if session.compliance_score < self.config['compliance_threshold']:
                alerts.append({
                    'type': 'compliance_drop',
                    'severity': 'high',
                    'message': f"Compliance score dropped to {session.compliance_score:.2%} (threshold: {self.config['compliance_threshold']:.2%})",
                    'session_id': session.session_id
                })
            
            # Check for critical failures
            critical_failures = [r for r in session.results if r.severity == 'critical' and r.status == 'fail']
            if critical_failures:
                alerts.append({
                    'type': 'critical_failure',
                    'severity': 'critical',
                    'message': f"Found {len(critical_failures)} critical security failures",
                    'session_id': session.session_id,
                    'failed_rules': [r.rule_id for r in critical_failures]
                })
            
            # Send alerts
            for alert in alerts:
                await self._send_alert(alert)
                
        except Exception as e:
            self.logger.error(f"Failed to check alerts: {e}")
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert notification"""
        try:
            if 'console' in self.config['notification_channels']:
                self.logger.warning(f"ALERT [{alert['severity'].upper()}]: {alert['message']}")
            
            if 'file' in self.config['notification_channels']:
                alert_file = Path(self.config['report_directory']) / 'alerts.log'
                with open(alert_file, 'a') as f:
                    f.write(f"{datetime.now().isoformat()} - {alert['severity'].upper()} - {alert['message']}\n")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
    
    def start_continuous_monitoring(self, level: str = "basic", interval: int = None):
        """
        Start continuous monitoring with minute-by-minute scanning
        
        Args:
            level: Scan level (basic, moderate, strict)
            interval: Scan interval in seconds (default from config)
        """
        if self.is_running:
            self.logger.warning("Continuous monitoring is already running")
            return
        
        scan_interval = interval or self.config['scan_interval']
        self.logger.info(f"Starting continuous monitoring (Level: {level}, Interval: {scan_interval}s)")
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(level, scan_interval),
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitoring_loop(self, level: str, interval: int):
        """Main monitoring loop"""
        self.logger.info("Continuous monitoring started")
        
        while not self.stop_event.is_set():
            try:
                # Run scan
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                session = loop.run_until_complete(self.run_single_scan(level, self.config['auto_remediate']))
                
                # Store session
                self.scan_history.append(session)
                self.current_session = session
                
                # Cleanup old sessions
                self._cleanup_old_sessions()
                
                loop.close()
                
                # Wait for next scan
                self.stop_event.wait(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self.stop_event.wait(interval)  # Wait before retrying
        
        self.logger.info("Continuous monitoring stopped")
    
    def _cleanup_old_sessions(self):
        """Clean up old scan sessions based on retention policy"""
        try:
            retention_days = self.config['retention_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Remove old sessions from memory
            self.scan_history = [
                session for session in self.scan_history
                if session.start_time > cutoff_date
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sessions: {e}")
    
    def stop(self):
        """Stop continuous monitoring"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping continuous monitoring...")
        self.is_running = False
        self.stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scanner status"""
        return {
            'is_running': self.is_running,
            'os_info': self.os_info,
            'current_session': asdict(self.current_session) if self.current_session else None,
            'total_scans': len(self.scan_history),
            'config': self.config,
            'uptime': self._get_uptime()
        }
    
    def _get_uptime(self) -> Optional[float]:
        """Get scanner uptime in seconds"""
        if not self.scan_history:
            return None
        
        first_scan = min(session.start_time for session in self.scan_history)
        return (datetime.now() - first_scan).total_seconds()
    
    async def get_compliance_trend(self, days: int = 7) -> Dict[str, Any]:
        """Get compliance trend over specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_sessions = [
                session for session in self.scan_history
                if session.start_time > cutoff_date
            ]
            
            if not recent_sessions:
                return {'trend': [], 'average_compliance': 0.0}
            
            # Sort by timestamp
            recent_sessions.sort(key=lambda x: x.start_time)
            
            trend_data = []
            total_compliance = 0.0
            
            for session in recent_sessions:
                trend_data.append({
                    'timestamp': session.start_time.isoformat(),
                    'compliance_score': session.compliance_score,
                    'total_rules': session.total_rules,
                    'passed_rules': session.passed_rules,
                    'failed_rules': session.failed_rules
                })
                total_compliance += session.compliance_score
            
            average_compliance = total_compliance / len(recent_sessions)
            
            return {
                'trend': trend_data,
                'average_compliance': average_compliance,
                'total_scans': len(recent_sessions),
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get compliance trend: {e}")
            return {'trend': [], 'average_compliance': 0.0, 'error': str(e)}


# CLI interface for deep scanner
async def main():
    """Main entry point for deep scanner CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OS Forge Deep Security Scanner')
    parser.add_argument('--level', choices=['basic', 'moderate', 'strict'], default='basic',
                       help='Scan level')
    parser.add_argument('--interval', type=int, default=60,
                       help='Scan interval in seconds for continuous monitoring')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    parser.add_argument('--auto-remediate', action='store_true', default=True,
                       help='Automatically apply fixes')
    parser.add_argument('--config', type=str,
                       help='Configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Create scanner
    scanner = DeepSecurityScanner(config)
    
    # Initialize
    if not await scanner.initialize():
        print("Failed to initialize scanner")
        return
    
    try:
        if args.continuous:
            # Start continuous monitoring
            scanner.start_continuous_monitoring(args.level, args.interval)
            
            print(f"Continuous monitoring started (Level: {args.level}, Interval: {args.interval}s)")
            print("Press Ctrl+C to stop...")
            
            # Keep running until interrupted
            while scanner.is_running:
                await asyncio.sleep(1)
        else:
            # Run single scan
            session = await scanner.run_single_scan(args.level, args.auto_remediate)
            
            print(f"\nScan completed:")
            print(f"  Total rules: {session.total_rules}")
            print(f"  Passed: {session.passed_rules}")
            print(f"  Failed: {session.failed_rules}")
            print(f"  Errors: {session.error_rules}")
            print(f"  Compliance: {session.compliance_score:.2%}")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        scanner.stop()
    
    except Exception as e:
        print(f"Error: {e}")
        scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())

