#!/usr/bin/env python3
"""
Security Integration Module for OS Forge
Integrates all enhanced security features into a unified system
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from vulnerability_scanner import VulnerabilityScanner, ScanResult
from secrets_manager import SecretsManager
from security_monitor import SecurityMonitor
from security_config import SecurityConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityIntegration:
    """Unified security integration system"""
    
    def __init__(self, config_dir: str = "./security"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize security components
        self.vulnerability_scanner = VulnerabilityScanner()
        self.secrets_manager = SecretsManager()
        self.security_monitor = SecurityMonitor()
        self.config_manager = SecurityConfigManager()
        
        # Integration state
        self.integration_status = {
            "vulnerability_scanner": False,
            "secrets_manager": False,
            "security_monitor": False,
            "config_manager": False
        }
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all security components"""
        try:
            # Initialize vulnerability scanner
            self.vulnerability_scanner = VulnerabilityScanner()
            self.integration_status["vulnerability_scanner"] = True
            logger.info("Vulnerability scanner initialized")
            
            # Initialize secrets manager
            self.secrets_manager = SecretsManager()
            self.integration_status["secrets_manager"] = True
            logger.info("Secrets manager initialized")
            
            # Initialize security monitor
            self.security_monitor = SecurityMonitor()
            self.integration_status["security_monitor"] = True
            logger.info("Security monitor initialized")
            
            # Initialize config manager
            self.config_manager = SecurityConfigManager()
            self.integration_status["config_manager"] = True
            logger.info("Security config manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize security components: {e}")
    
    def run_comprehensive_security_scan(self, directory: str = None) -> Dict[str, Any]:
        """Run comprehensive security scan using all components"""
        logger.info("Starting comprehensive security scan")
        
        scan_results = {
            "scan_id": f"comprehensive_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "summary": {
                "total_vulnerabilities": 0,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 0,
                "medium_vulnerabilities": 0,
                "low_vulnerabilities": 0,
                "secrets_found": 0,
                "compliance_score": 0.0,
                "security_events": 0
            },
            "recommendations": []
        }
        
        try:
            # 1. Vulnerability Scan
            if self.integration_status["vulnerability_scanner"]:
                logger.info("Running vulnerability scan...")
                vuln_result = self.vulnerability_scanner.scan_directory(directory)
                scan_results["components"]["vulnerability_scan"] = {
                    "status": "completed",
                    "files_scanned": vuln_result.total_files_scanned,
                    "vulnerabilities_found": len(vuln_result.vulnerabilities),
                    "scan_duration": vuln_result.scan_duration,
                    "summary": vuln_result.summary
                }
                
                # Update overall summary
                scan_results["summary"]["total_vulnerabilities"] = vuln_result.summary["total"]
                scan_results["summary"]["critical_vulnerabilities"] = vuln_result.summary["CRITICAL"]
                scan_results["summary"]["high_vulnerabilities"] = vuln_result.summary["HIGH"]
                scan_results["summary"]["medium_vulnerabilities"] = vuln_result.summary["MEDIUM"]
                scan_results["summary"]["low_vulnerabilities"] = vuln_result.summary["LOW"]
                
                # Generate recommendations based on vulnerabilities
                if vuln_result.summary["CRITICAL"] > 0:
                    scan_results["recommendations"].append("CRITICAL: Address critical vulnerabilities immediately")
                if vuln_result.summary["HIGH"] > 0:
                    scan_results["recommendations"].append("HIGH: Address high-severity vulnerabilities")
                if vuln_result.summary["MEDIUM"] > 0:
                    scan_results["recommendations"].append("MEDIUM: Review and address medium-severity vulnerabilities")
            
            # 2. Secrets Scan
            if self.integration_status["secrets_manager"]:
                logger.info("Scanning for hardcoded secrets...")
                secrets_list = self.secrets_manager.list_secrets()
                scan_results["components"]["secrets_scan"] = {
                    "status": "completed",
                    "secrets_found": len(secrets_list),
                    "secrets": secrets_list
                }
                
                scan_results["summary"]["secrets_found"] = len(secrets_list)
                
                if len(secrets_list) > 0:
                    scan_results["recommendations"].append("SECRETS: Review and secure hardcoded secrets")
            
            # 3. Security Monitoring
            if self.integration_status["security_monitor"]:
                logger.info("Checking security monitoring status...")
                monitor_stats = self.security_monitor.get_statistics()
                recent_events = self.security_monitor.get_events(limit=50)
                recent_alerts = self.security_monitor.get_alerts(limit=20)
                
                scan_results["components"]["security_monitoring"] = {
                    "status": "completed",
                    "monitoring_status": monitor_stats["monitoring_status"],
                    "total_events": monitor_stats["events_total"],
                    "total_alerts": monitor_stats["alerts_total"],
                    "threats_detected": monitor_stats["threats_detected"],
                    "recent_events": len(recent_events),
                    "recent_alerts": len(recent_alerts)
                }
                
                scan_results["summary"]["security_events"] = monitor_stats["events_total"]
                
                if monitor_stats["threats_detected"] > 0:
                    scan_results["recommendations"].append("THREATS: Investigate detected security threats")
                if monitor_stats["alerts_total"] > 0:
                    scan_results["recommendations"].append("ALERTS: Review security alerts")
            
            # 4. Compliance Check
            if self.integration_status["config_manager"]:
                logger.info("Running compliance check...")
                baselines = self.config_manager.get_baselines_by_os("linux")  # Default to Linux
                
                if baselines:
                    # Use first baseline for compliance check
                    baseline = baselines[0]
                    
                    # Create mock system state for compliance check
                    system_state = self._create_mock_system_state()
                    compliance_result = self.config_manager.validate_compliance(
                        baseline.baseline_id, system_state
                    )
                    
                    scan_results["components"]["compliance_check"] = {
                        "status": "completed",
                        "baseline_id": baseline.baseline_id,
                        "baseline_name": baseline.name,
                        "compliance_percentage": compliance_result["compliance_percentage"],
                        "overall_status": compliance_result["overall_status"],
                        "compliant_policies": compliance_result["compliant_policies"],
                        "total_policies": compliance_result["total_policies"]
                    }
                    
                    scan_results["summary"]["compliance_score"] = compliance_result["compliance_percentage"]
                    
                    if compliance_result["compliance_percentage"] < 80:
                        scan_results["recommendations"].append("COMPLIANCE: Improve security compliance score")
            
            # Generate overall recommendations
            self._generate_overall_recommendations(scan_results)
            
            logger.info("Comprehensive security scan completed")
            return scan_results
            
        except Exception as e:
            logger.error(f"Comprehensive security scan failed: {e}")
            scan_results["error"] = str(e)
            return scan_results
    
    def _create_mock_system_state(self) -> Dict[str, Any]:
        """Create mock system state for compliance checking"""
        return {
            # Password policy
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "password_history": 5,
            "max_age_days": 90,
            
            # Network security
            "firewall_enabled": True,
            "default_deny": True,
            "ssh_port": 22,
            "allow_http": True,
            "allow_https": True,
            "block_telnet": True,
            "block_ftp": True,
            
            # System hardening
            "disable_root_login": True,
            "disable_guest_account": True,
            "enable_audit_logging": True,
            "disable_unnecessary_services": True,
            "enable_aslr": True,
            "disable_core_dumps": True,
            "secure_umask": "027",
            
            # Data protection
            "encrypt_sensitive_data": True,
            "encrypt_data_in_transit": True,
            "backup_encryption": True,
            "secure_deletion": True,
            "data_classification": True,
            "access_logging": True,
            
            # Application security
            "input_validation": True,
            "output_encoding": True,
            "sql_injection_protection": True,
            "xss_protection": True,
            "csrf_protection": True,
            "secure_headers": True,
            "session_security": True
        }
    
    def _generate_overall_recommendations(self, scan_results: Dict[str, Any]):
        """Generate overall security recommendations"""
        recommendations = scan_results["recommendations"]
        
        # Overall security score calculation
        total_score = 100
        deductions = 0
        
        # Deduct for vulnerabilities
        deductions += scan_results["summary"]["critical_vulnerabilities"] * 20
        deductions += scan_results["summary"]["high_vulnerabilities"] * 10
        deductions += scan_results["summary"]["medium_vulnerabilities"] * 5
        deductions += scan_results["summary"]["low_vulnerabilities"] * 2
        
        # Deduct for secrets
        deductions += scan_results["summary"]["secrets_found"] * 15
        
        # Deduct for compliance
        compliance_score = scan_results["summary"]["compliance_score"]
        if compliance_score < 80:
            deductions += (80 - compliance_score) * 0.5
        
        # Deduct for security events
        if scan_results["summary"]["security_events"] > 100:
            deductions += 10
        
        security_score = max(0, total_score - deductions)
        
        # Add overall recommendations
        if security_score >= 90:
            recommendations.append("EXCELLENT: Security posture is excellent")
        elif security_score >= 75:
            recommendations.append("GOOD: Security posture is good with room for improvement")
        elif security_score >= 60:
            recommendations.append("FAIR: Security posture needs improvement")
        else:
            recommendations.append("POOR: Security posture requires immediate attention")
        
        scan_results["summary"]["security_score"] = security_score
        scan_results["summary"]["security_rating"] = self._get_security_rating(security_score)
    
    def _get_security_rating(self, score: float) -> str:
        """Get security rating based on score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 40:
            return "POOR"
        else:
            return "CRITICAL"
    
    def start_security_monitoring(self):
        """Start comprehensive security monitoring"""
        logger.info("Starting security monitoring")
        
        try:
            if self.integration_status["security_monitor"]:
                self.security_monitor.start_monitoring()
                logger.info("Security monitoring started successfully")
            else:
                logger.error("Security monitor not initialized")
                
        except Exception as e:
            logger.error(f"Failed to start security monitoring: {e}")
    
    def stop_security_monitoring(self):
        """Stop security monitoring"""
        logger.info("Stopping security monitoring")
        
        try:
            if self.integration_status["security_monitor"]:
                self.security_monitor.stop_monitoring()
                logger.info("Security monitoring stopped successfully")
            else:
                logger.error("Security monitor not initialized")
                
        except Exception as e:
            logger.error(f"Failed to stop security monitoring: {e}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_status": "unknown"
        }
        
        try:
            # Vulnerability scanner status
            if self.integration_status["vulnerability_scanner"]:
                dashboard_data["components"]["vulnerability_scanner"] = {
                    "status": "active",
                    "last_scan": "N/A"  # Would be stored in real implementation
                }
            
            # Secrets manager status
            if self.integration_status["secrets_manager"]:
                secrets_count = len(self.secrets_manager.list_secrets())
                dashboard_data["components"]["secrets_manager"] = {
                    "status": "active",
                    "secrets_count": secrets_count
                }
            
            # Security monitor status
            if self.integration_status["security_monitor"]:
                monitor_stats = self.security_monitor.get_statistics()
                dashboard_data["components"]["security_monitor"] = {
                    "status": monitor_stats["monitoring_status"],
                    "events_total": monitor_stats["events_total"],
                    "alerts_total": monitor_stats["alerts_total"],
                    "threats_detected": monitor_stats["threats_detected"]
                }
            
            # Config manager status
            if self.integration_status["config_manager"]:
                policies_count = len(self.config_manager.get_enabled_policies())
                baselines_count = len(self.config_manager.baselines)
                dashboard_data["components"]["config_manager"] = {
                    "status": "active",
                    "policies_count": policies_count,
                    "baselines_count": baselines_count
                }
            
            # Determine overall status
            active_components = sum(1 for comp in dashboard_data["components"].values() 
                                  if comp["status"] == "active" or comp["status"] == "running")
            total_components = len(dashboard_data["components"])
            
            if active_components == total_components:
                dashboard_data["overall_status"] = "healthy"
            elif active_components > 0:
                dashboard_data["overall_status"] = "degraded"
            else:
                dashboard_data["overall_status"] = "unhealthy"
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            dashboard_data["error"] = str(e)
            return dashboard_data
    
    def export_security_report(self, output_path: str, format: str = "json") -> bool:
        """Export comprehensive security report"""
        try:
            logger.info(f"Exporting security report to {output_path}")
            
            # Get comprehensive scan results
            scan_results = self.run_comprehensive_security_scan()
            
            # Get dashboard data
            dashboard_data = self.get_security_dashboard_data()
            
            # Combine data
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "comprehensive_security_assessment",
                    "version": "1.0"
                },
                "scan_results": scan_results,
                "dashboard_data": dashboard_data,
                "integration_status": self.integration_status
            }
            
            # Export based on format
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(report_data, f, indent=2, default=str)
            elif format.lower() == "html":
                self._export_html_report(report_data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Security report exported successfully to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export security report: {e}")
            return False
    
    def _export_html_report(self, report_data: Dict[str, Any], output_path: str):
        """Export HTML security report"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OS Forge Security Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .critical {{ color: #d32f2f; font-weight: bold; }}
                .high {{ color: #f57c00; font-weight: bold; }}
                .medium {{ color: #fbc02d; font-weight: bold; }}
                .low {{ color: #388e3c; font-weight: bold; }}
                .good {{ color: #4caf50; font-weight: bold; }}
                .poor {{ color: #f44336; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>OS Forge Security Report</h1>
                <p><strong>Generated:</strong> {report_data['report_metadata']['generated_at']}</p>
                <p><strong>Report Type:</strong> {report_data['report_metadata']['report_type']}</p>
            </div>
            
            <div class="section">
                <h2>Security Summary</h2>
                <div class="metric">
                    <strong>Security Score:</strong> {report_data['scan_results']['summary'].get('security_score', 'N/A')}
                </div>
                <div class="metric">
                    <strong>Security Rating:</strong> <span class="{report_data['scan_results']['summary'].get('security_rating', 'unknown').lower()}">{report_data['scan_results']['summary'].get('security_rating', 'N/A')}</span>
                </div>
                <div class="metric">
                    <strong>Total Vulnerabilities:</strong> {report_data['scan_results']['summary']['total_vulnerabilities']}
                </div>
                <div class="metric">
                    <strong>Critical:</strong> <span class="critical">{report_data['scan_results']['summary']['critical_vulnerabilities']}</span>
                </div>
                <div class="metric">
                    <strong>High:</strong> <span class="high">{report_data['scan_results']['summary']['high_vulnerabilities']}</span>
                </div>
                <div class="metric">
                    <strong>Medium:</strong> <span class="medium">{report_data['scan_results']['summary']['medium_vulnerabilities']}</span>
                </div>
                <div class="metric">
                    <strong>Low:</strong> <span class="low">{report_data['scan_results']['summary']['low_vulnerabilities']}</span>
                </div>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for rec in report_data['scan_results']['recommendations']:
            html_content += f"<li>{rec}</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Component Status</h2>
        """
        
        for component, status in report_data['dashboard_data']['components'].items():
            html_content += f"""
                <div class="metric">
                    <strong>{component.replace('_', ' ').title()}:</strong> {status['status']}
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)


def main():
    """CLI interface for security integration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OS Forge Security Integration")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Run comprehensive security scan")
    scan_parser.add_argument("--directory", "-d", default="./", help="Directory to scan")
    scan_parser.add_argument("--output", "-o", help="Output file for results")
    scan_parser.add_argument("--format", "-f", choices=["json", "html"], default="json", help="Output format")
    
    # Monitor commands
    monitor_start_parser = subparsers.add_parser("monitor-start", help="Start security monitoring")
    monitor_stop_parser = subparsers.add_parser("monitor-stop", help="Stop security monitoring")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Get security dashboard data")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate security report")
    report_parser.add_argument("output_path", help="Output file path")
    report_parser.add_argument("--format", "-f", choices=["json", "html"], default="html", help="Report format")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    integration = SecurityIntegration()
    
    try:
        if args.command == "scan":
            results = integration.run_comprehensive_security_scan(args.directory)
            
            # Print summary
            print(f"\n=== Security Scan Results ===")
            print(f"Scan ID: {results['scan_id']}")
            print(f"Timestamp: {results['timestamp']}")
            print(f"Security Score: {results['summary'].get('security_score', 'N/A')}")
            print(f"Security Rating: {results['summary'].get('security_rating', 'N/A')}")
            print(f"Total Vulnerabilities: {results['summary']['total_vulnerabilities']}")
            print(f"Critical: {results['summary']['critical_vulnerabilities']}")
            print(f"High: {results['summary']['high_vulnerabilities']}")
            print(f"Medium: {results['summary']['medium_vulnerabilities']}")
            print(f"Low: {results['summary']['low_vulnerabilities']}")
            print(f"Secrets Found: {results['summary']['secrets_found']}")
            print(f"Compliance Score: {results['summary']['compliance_score']:.1f}%")
            
            print(f"\n=== Recommendations ===")
            for rec in results['recommendations']:
                print(f"- {rec}")
            
            # Save results if output specified
            if args.output:
                if args.format == "json":
                    with open(args.output, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                else:
                    integration._export_html_report({"scan_results": results}, args.output)
                print(f"\nResults saved to: {args.output}")
        
        elif args.command == "monitor-start":
            integration.start_security_monitoring()
            print("Security monitoring started")
            
            # Keep running
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping monitoring...")
                integration.stop_security_monitoring()
        
        elif args.command == "monitor-stop":
            integration.stop_security_monitoring()
            print("Security monitoring stopped")
        
        elif args.command == "dashboard":
            dashboard_data = integration.get_security_dashboard_data()
            print(f"\n=== Security Dashboard ===")
            print(f"Overall Status: {dashboard_data['overall_status']}")
            print(f"Timestamp: {dashboard_data['timestamp']}")
            
            print(f"\n=== Component Status ===")
            for component, status in dashboard_data['components'].items():
                print(f"{component}: {status['status']}")
        
        elif args.command == "report":
            success = integration.export_security_report(args.output_path, args.format)
            print("Security report generated successfully" if success else "Failed to generate security report")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
