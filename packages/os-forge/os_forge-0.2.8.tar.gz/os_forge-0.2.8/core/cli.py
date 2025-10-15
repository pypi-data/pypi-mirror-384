"""
Command Line Interface for OS Forge

Typer-based CLI for running hardening checks and managing the system.
"""

import typer
import uvicorn
import json
import asyncio
from typing import Optional
from pathlib import Path

from database.manager import db_manager, init_db, get_db
from database.mongodb_schemas import HardeningResult
from reporting.generator import ReportGenerator
from agents.linux.linux_agent import LinuxAgent
from agents.windows.windows_agent import WindowsAgent
from agents.macos.macos_agent import MacOSAgent
from agents.common.os_detector import OSDetector
from agents.linux.linux_rules import get_linux_hardening_rules
from agents.windows.windows_rules import get_windows_hardening_rules
from agents.macos.macos_rules import get_macos_hardening_rules
from .config import Config


# Initialize components
os_detector = OSDetector()
current_os = os_detector.detect_os()

# Initialize PolicyEngine
from policies.engine import PolicyEngine
policy_engine = PolicyEngine()

# Initialize appropriate rules module based on OS
if current_os['type'] == "linux":
    rules_module = get_linux_hardening_rules
elif current_os['type'] == "windows":
    rules_module = get_windows_hardening_rules
elif current_os['type'] == "macos":
    rules_module = get_macos_hardening_rules
else:
    # Fallback to Linux rules for unknown OS
    rules_module = get_linux_hardening_rules

report_generator = ReportGenerator()

# Create CLI app
cli = typer.Typer(help="OS Forge CLI - System Hardening Tool")


@cli.command()
def check(
    level: str = typer.Option("basic", help="Hardening level (basic/moderate/strict)"),
    dry_run: bool = typer.Option(True, "--dry-run", "--no-dry-run", help="Dry run mode (no changes)"),
    category: Optional[str] = typer.Option(None, help="Rule category filter"),
    mongodb_uri: Optional[str] = typer.Option(None, help="MongoDB URI (overrides environment variable)")
):
    """Check system against hardening rules"""
    import asyncio
    
    async def _check():
        typer.echo(f"Running OS Forge check (Level: {level}, Dry Run: {dry_run})")
        typer.echo(f"Detected OS: {current_os['type']}")
        typer.echo(f"OS Distribution: {current_os.get('distribution', {}).get('name', 'Unknown')}")
        typer.echo(f"Agent Type: {type(policy_engine).__name__}")
        
        # Override MongoDB URI if provided via CLI
        if mongodb_uri:
            import os
            os.environ["MONGODB_URI"] = mongodb_uri
            # Reinitialize the database manager with new URI
            from database.mongodb_config import MongoDBConfig
            db_manager.manager.config = MongoDBConfig()
        
        rules = rules_module()
        
        # Filter by level
        if level:
            rules = [rule for rule in rules if level in rule.get("level", [])]
        
        # Filter by category
        if category:
            rules = [rule for rule in rules if rule.get("category") == category]
        
        typer.echo(f"Found {len(rules)} applicable rules")
        
        # Initialize database if not dry run (to store results)
        if not dry_run:
            try:
                await db_manager.initialize()
            except Exception as e:
                typer.echo(f"Warning: Could not initialize database: {e}")
                typer.echo("Continuing without database storage...")
        
        results = []
        for rule in rules:
            try:
                # Execute rule with appropriate dry_run setting
                rule_result = policy_engine.execute_rule(rule, dry_run=dry_run)
                
                result = {
                    "rule_id": rule_result.rule_id,
                    "description": rule_result.description,
                    "status": rule_result.status,
                    "old_value": rule_result.old_value,
                    "new_value": rule_result.new_value,
                    "error": rule_result.error
                }
                
                # Store result in MongoDB (if available)
                try:
                    # Generate scan session ID for this run
                    import uuid
                    scan_session_id = str(uuid.uuid4())
                    
                    result_data = {
                        "rule_id": result["rule_id"],
                        "rule_name": result["description"],
                        "rule_category": rule.get("category", "unknown"),
                        "hostname": "localhost",  # TODO: Get actual hostname
                        "os_type": current_os['type'],
                        "os_version": current_os.get('version', 'unknown'),
                        "hardening_level": level,
                        "status": result["status"],
                        "severity": rule.get("severity", "medium"),
                        "scan_session_id": scan_session_id,
                        "old_value": result.get("old_value"),
                        "new_value": result.get("new_value"),
                        "rollback_data": {"rollback_command": rule.get("rollback", ""), "original_value": result.get("old_value")},
                        "is_remediated": not dry_run and result["status"] == "pass",
                        "is_rollback_available": bool(rule.get("rollback"))
                    }
                    await db_manager.create_hardening_result(result_data)
                except Exception as e:
                    # MongoDB not available, continue without storage
                    pass
                
                results.append(result)
                
                # Color-coded output
                status_color = {
                    "pass": typer.colors.GREEN,
                    "fail": typer.colors.RED,
                    "error": typer.colors.YELLOW
                }.get(result.get("status"), typer.colors.WHITE)
                
                typer.secho(
                    f"  {result['rule_id']}: {result['description']} - {result['status'].upper()}", 
                    fg=status_color
                )
                
                if result.get("old_value"):
                    typer.echo(f"    Current: {result['old_value']}")
                if result.get("error"):
                    typer.echo(f"    Error: {result['error']}")
                    
            except Exception as e:
                error_result = {
                    "rule_id": rule["id"],
                    "description": rule["description"],
                    "status": "error",
                    "error": str(e)
                }
                results.append(error_result)
                typer.secho(f"  {rule['id']}: {rule['description']} - ERROR", fg=typer.colors.RED)
                typer.echo(f"    Error: {str(e)}")
        
        # Summary
        passed = sum(1 for r in results if r.get("status") == "pass")
        failed = sum(1 for r in results if r.get("status") == "fail")
        errors = sum(1 for r in results if r.get("status") == "error")
        
        typer.echo("\nSummary:")
        typer.secho(f"  Passed: {passed}", fg=typer.colors.GREEN)
        typer.secho(f"  Failed: {failed}", fg=typer.colors.RED)
        typer.secho(f"  Errors: {errors}", fg=typer.colors.YELLOW)
        
        if not dry_run:
            await db_manager.close()
    
    asyncio.run(_check())


@cli.command()
def server(
    port: int = typer.Option(Config.DEFAULT_PORT, help="Server port"),
    host: str = typer.Option(Config.DEFAULT_HOST, help="Server host")
):
    """Start the FastAPI server"""
    typer.echo(f"Starting OS Forge server on {host}:{port}")
    
    # Import the app here to avoid circular imports
    from .api import app
    uvicorn.run(app, host=host, port=port)


@cli.command()
def report():
    """Generate and display compliance report"""
    import asyncio
    
    async def _report():
        typer.echo("Generating compliance report...")
        
        # Check if MongoDB is available
        if not db_manager.manager.config.is_enabled():
            typer.echo("MongoDB not configured. Database features are disabled.")
            typer.echo("To enable database features, set MONGODB_URI environment variable.")
            typer.echo("You can still run hardening checks with: os-forge check")
            return
        
        # Initialize database
        try:
            await db_manager.initialize()
        except Exception as e:
            typer.echo(f"Warning: Could not initialize database: {e}")
            typer.echo("Database features are disabled. Set MONGODB_URI environment variable to enable.")
            return
        
        # Get results from MongoDB
        results = await db_manager.get_hardening_results("localhost", 20)
        
        if not results:
            typer.echo("No results found. Run a check first!")
            return
        
        # Calculate summary
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "pass")
        failed = sum(1 for r in results if r.get("status") == "fail")
        errors = sum(1 for r in results if r.get("status") == "error")
        score = (passed / total * 100) if total > 0 else 0
        
        typer.echo("\nLatest Compliance Report")
        typer.echo("=" * 50)
        typer.secho(f"Passed: {passed}/{total} ({score:.1f}%)", fg=typer.colors.GREEN)
        typer.secho(f"Failed: {failed}/{total}", fg=typer.colors.RED)
        typer.secho(f"Errors: {errors}/{total}", fg=typer.colors.YELLOW)
        
        typer.echo("\nRecent Results:")
        for result in results[:10]:  # Show latest 10
            status_color = {
                "pass": typer.colors.GREEN,
                "fail": typer.colors.RED,
                "error": typer.colors.YELLOW
            }.get(result.get("status"), typer.colors.WHITE)
            
            typer.secho(
                f"  {result.get('rule_id', 'unknown')}: {result.get('status', 'unknown').upper()}", 
                fg=status_color
            )
        
        typer.echo(f"\nView full HTML report at: http://localhost:{Config.DEFAULT_PORT}/report")
        
        await db_manager.close()
    
    asyncio.run(_report())


@cli.command()
def rollback(rule_id: str = typer.Argument(help="Rule ID to rollback")):
    """Rollback a specific hardening rule"""
    import asyncio
    
    async def _rollback():
        typer.echo(f"Rolling back rule: {rule_id}")
        
        # Check if MongoDB is available
        if not db_manager.manager.config.is_enabled():
            typer.echo("MongoDB not configured. Database features are disabled.")
            typer.echo("To enable database features, set MONGODB_URI environment variable.")
            typer.echo("You can still run hardening checks with: os-forge check")
            return
        
        try:
            # Initialize database
            try:
                await db_manager.initialize()
            except Exception as e:
                typer.echo(f"Warning: Could not initialize database: {e}")
                typer.echo("Database features are disabled. Set MONGODB_URI environment variable to enable.")
                return
            
            # Get the latest result for this rule from MongoDB
            results = await db_manager.get_hardening_results("localhost", 100)
            latest_result = None
            
            for result in results:
                if result.get("rule_id") == rule_id:
                    latest_result = result
                    break
            
            if not latest_result:
                typer.secho(f"No results found for rule {rule_id}", fg=typer.colors.RED)
                return
                
            if not latest_result.get("rollback_data"):
                typer.secho(f"No rollback data available for rule {rule_id}", fg=typer.colors.RED)
                return
            
            # Get the rule definition
            rules = rules_module()
            rule = next((r for r in rules if r['id'] == rule_id), None)
            
            if not rule:
                typer.secho(f"Rule {rule_id} not found", fg=typer.colors.RED)
                return
            
            # Parse rollback data
            rollback_data = latest_result.get("rollback_data", {})
            
            # Execute rollback
            rollback_result = policy_engine.rollback_rule(rule, rollback_data)
            
            if rollback_result.status.value == "pass":
                typer.secho(f"Successfully rolled back rule {rule_id}", fg=typer.colors.GREEN)
                typer.echo(f"Old value: {rollback_result.old_value}")
                typer.echo(f"New value: {rollback_result.new_value}")
            else:
                typer.secho(f"Rollback failed for rule {rule_id}", fg=typer.colors.RED)
                if rollback_result.error:
                    typer.echo(f"Error: {rollback_result.error}")
                    
        except Exception as e:
            typer.secho(f"Rollback failed: {str(e)}", fg=typer.colors.RED)
        finally:
            await db_manager.close()
    
    asyncio.run(_rollback())


@cli.command()
def list_rollbacks():
    """List available rollback options"""
    import asyncio
    
    async def _list_rollbacks():
        typer.echo("Available rollback options:")
        
        # Check if MongoDB is available
        if not db_manager.manager.config.is_enabled():
            typer.echo("MongoDB not configured. Database features are disabled.")
            typer.echo("To enable database features, set MONGODB_URI environment variable.")
            typer.echo("You can still run hardening checks with: os-forge check")
            return
        
        # Initialize database
        try:
            await db_manager.initialize()
        except Exception as e:
            typer.echo(f"Warning: Could not initialize database: {e}")
            typer.echo("Database features are disabled. Set MONGODB_URI environment variable to enable.")
            return
        
        # Get results from MongoDB
        results = await db_manager.get_hardening_results("localhost", 100)
        
        # Get unique rule IDs with rollback data
        unique_rules = {}
        for result in results:
            rule_id = result.get("rule_id")
            if rule_id and result.get("rollback_data") and result.get("status") != "rollback_success":
                if rule_id not in unique_rules:
                    unique_rules[rule_id] = result
        
        rollback_count = 0
        for rule_id, result in unique_rules.items():
            typer.echo(f"  {rule_id}: {result.get('rule_name', 'Unknown')}")
            typer.echo(f"    Status: {result.get('status', 'unknown')}, Applied: {result.get('created_at', 'unknown')}")
            rollback_count += 1
        
        if rollback_count == 0:
            typer.echo("No rollback options available")
        else:
            typer.echo(f"\nUse 'os-forge rollback <rule_id>' to rollback a specific rule")
        
        await db_manager.close()
    
    asyncio.run(_list_rollbacks())


@cli.command()
def pdf_report(output: str = typer.Option("os_forge_report.pdf", help="Output PDF filename")):
    """Generate PDF compliance report"""
    import asyncio
    
    async def _pdf_report():
        typer.echo(f"Generating PDF report: {output}")
        
        # Check if MongoDB is available
        if not db_manager.manager.config.is_enabled():
            typer.echo("MongoDB not configured. Database features are disabled.")
            typer.echo("To enable database features, set MONGODB_URI environment variable.")
            typer.echo("You can still run hardening checks with: os-forge check")
            return
        
        # Initialize database
        try:
            await db_manager.initialize()
        except Exception as e:
            typer.echo(f"Warning: Could not initialize database: {e}")
            typer.echo("Database features are disabled. Set MONGODB_URI environment variable to enable.")
            return
        
        # Get results from MongoDB
        results = await db_manager.get_hardening_results("localhost", 100)
        
        if not results:
            typer.echo("No results found. Run a check first!")
            return
        
        try:
            # Convert MongoDB results to format expected by report generator
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "rule_id": result.get("rule_id", "unknown"),
                    "description": result.get("rule_name", "Unknown"),
                    "severity": result.get("severity", "medium"),
                    "status": result.get("status", "unknown"),
                    "old_value": result.get("old_value"),
                    "new_value": result.get("new_value"),
                    "timestamp": result.get("created_at", "unknown")
                })
            
            pdf_buffer = report_generator.generate_pdf_report(formatted_results, current_os)
            
            # Write to file
            with open(output, 'wb') as f:
                f.write(pdf_buffer.read())
            
            typer.secho(f"PDF report generated: {output}", fg=typer.colors.GREEN)
            
        except ImportError:
            typer.secho("ReportLab not installed. Install with: pip install reportlab", fg=typer.colors.RED)
        except Exception as e:
            typer.secho(f"Failed to generate PDF: {str(e)}", fg=typer.colors.RED)
        finally:
            await db_manager.close()
    
    asyncio.run(_pdf_report())


@cli.command()
def info():
    """Show system information"""
    typer.echo("OS Forge - System Information")
    typer.echo(f"Detected OS: {current_os['type']}")
    typer.echo(f"OS Distribution: {current_os.get('distribution', {}).get('name', 'Unknown')}")
    typer.echo(f"Agent Type: {type(policy_engine).__name__}")
    
    rules = rules_module()
    typer.echo(f"Total Rules: {len(rules)}")
    
    # Count by level
    level_counts = {}
    for rule in rules:
        for level in rule.get("level", []):
            level_counts[level] = level_counts.get(level, 0) + 1
    
    for level, count in sorted(level_counts.items()):
        typer.echo(f"  {level.title()}: {count} rules")
    
    # Count by category
    category_counts = {}
    for rule in rules:
        category = rule.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
    
    typer.echo("\nRules by Category:")
    for category, count in sorted(category_counts.items()):
        typer.echo(f"  {category}: {count} rules")


@cli.command()
def deep_scan(
    level: str = typer.Option("basic", help="Hardening level (basic/moderate/strict)"),
    continuous: bool = typer.Option(False, "--continuous", help="Run continuous monitoring"),
    interval: int = typer.Option(60, help="Scan interval in seconds for continuous monitoring"),
    auto_remediate: bool = typer.Option(True, "--auto-remediate", "--no-auto-remediate", help="Automatically apply fixes"),
    mongodb_uri: Optional[str] = typer.Option(None, help="MongoDB URI (overrides environment variable)")
):
    """Run comprehensive deep security scan with minute-by-minute monitoring"""
    import asyncio
    from core.deep_scanner import DeepSecurityScanner
    
    async def _deep_scan():
        typer.echo(f"Starting Deep Security Scanner (Level: {level})")
        typer.echo(f"Detected OS: {current_os['type']}")
        typer.echo(f"OS Distribution: {current_os.get('distribution', {}).get('name', 'Unknown')}")
        
        # Override MongoDB URI if provided via CLI
        if mongodb_uri:
            import os
            os.environ["MONGODB_URI"] = mongodb_uri
        
        # Create scanner
        scanner = DeepSecurityScanner()
        
        # Initialize
        if not await scanner.initialize():
            typer.echo("Failed to initialize deep scanner", err=True)
            return
        
        try:
            if continuous:
                # Start continuous monitoring
                scanner.start_continuous_monitoring(level, interval)
                
                typer.echo(f"Continuous monitoring started (Level: {level}, Interval: {interval}s)")
                typer.echo("Press Ctrl+C to stop...")
                
                # Keep running until interrupted
                while scanner.is_running:
                    await asyncio.sleep(1)
            else:
                # Run single scan
                session = await scanner.run_single_scan(level, auto_remediate)
                
                typer.echo(f"\nDeep Scan completed:")
                typer.echo(f"  Total rules: {session.total_rules}")
                typer.echo(f"  Passed: {session.passed_rules}")
                typer.echo(f"  Failed: {session.failed_rules}")
                typer.echo(f"  Errors: {session.error_rules}")
                typer.echo(f"  Compliance: {session.compliance_score:.2%}")
                
                # Show detailed results
                if session.results:
                    typer.echo(f"\nDetailed Results:")
                    for result in session.results:
                        status_color = {
                            "pass": typer.colors.GREEN,
                            "fail": typer.colors.RED,
                            "error": typer.colors.YELLOW,
                            "skip": typer.colors.BLUE,
                        }
                        
                        typer.secho(
                            f"  {result.rule_id}: {result.rule_name} - {result.status.upper()}",
                            fg=status_color.get(result.status, typer.colors.WHITE)
                        )
                        if result.error_message:
                            typer.secho(f"    Error: {result.error_message}", fg=typer.colors.RED)
                        if result.remediation_applied:
                            typer.secho(f"    ✓ Remediation applied", fg=typer.colors.GREEN)
        
        except KeyboardInterrupt:
            typer.echo("\nShutting down deep scanner...")
            scanner.stop()
        
        except Exception as e:
            typer.echo(f"Deep scan error: {e}", err=True)
            scanner.stop()
    
    asyncio.run(_deep_scan())


def main():
    """Main entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()

