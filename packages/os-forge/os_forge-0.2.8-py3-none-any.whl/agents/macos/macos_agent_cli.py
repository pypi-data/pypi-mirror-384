"""
macOS Agent CLI for OS Forge

Command-line interface for macOS-specific hardening operations.
Provides direct access to macOS hardening capabilities.
"""

import typer
import logging
from typing import Optional, List
from pathlib import Path

from .macos_agent import MacOSAgent
from .macos_rules import get_macos_hardening_rules, MacOSRuleCategory
from ..common.base_agent import RuleStatus


# Create CLI app
macos_cli = typer.Typer(help="macOS Agent CLI - macOS-specific hardening operations")


@macos_cli.command()
def info():
    """Show macOS agent information"""
    agent = MacOSAgent()
    agent_info = agent.get_agent_info()
    
    typer.echo("macOS Agent Information")
    typer.echo("=" * 40)
    typer.echo(f"Agent ID: {agent_info.agent_id}")
    typer.echo(f"OS Type: {agent_info.os_type}")
    typer.echo(f"OS Version: {agent_info.os_version}")
    typer.echo(f"Architecture: {agent_info.architecture}")
    typer.echo(f"Status: {agent_info.status.value}")
    typer.echo(f"Capabilities: {', '.join(agent_info.capabilities)}")
    typer.echo(f"Last Heartbeat: {agent_info.last_heartbeat}")
    typer.echo(f"Version: {agent_info.version}")


@macos_cli.command()
def health():
    """Check macOS agent health"""
    agent = MacOSAgent()
    status = agent.health_check()
    
    if status == RuleStatus.PASS:
        typer.secho("✅ macOS Agent is healthy", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ macOS Agent is unhealthy", fg=typer.colors.RED)
    
    typer.echo(f"Status: {status.value}")


@macos_cli.command()
def rules(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    level: Optional[str] = typer.Option(None, help="Filter by level (basic/moderate/strict)")
):
    """List macOS hardening rules"""
    rules = get_macos_hardening_rules()
    
    # Apply filters
    if category:
        rules = [rule for rule in rules if rule.get("category") == category]
    
    if level:
        rules = [rule for rule in rules if level in rule.get("level", [])]
    
    typer.echo(f"macOS Hardening Rules ({len(rules)} total)")
    typer.echo("=" * 50)
    
    for rule in rules:
        severity_color = {
            "critical": typer.colors.RED,
            "high": typer.colors.YELLOW,
            "medium": typer.colors.BLUE,
            "low": typer.colors.GREEN
        }.get(rule.get("severity", "medium"), typer.colors.WHITE)
        
        typer.secho(f"{rule['id']}: {rule['description']}", fg=severity_color)
        typer.echo(f"  Category: {rule.get('category', 'unknown')}")
        typer.echo(f"  Severity: {rule.get('severity', 'unknown')}")
        typer.echo(f"  Levels: {', '.join(rule.get('level', []))}")
        typer.echo()


@macos_cli.command()
def check(
    rule_id: Optional[str] = typer.Option(None, help="Check specific rule by ID"),
    category: Optional[str] = typer.Option(None, help="Check rules by category"),
    level: Optional[str] = typer.Option(None, help="Check rules by level")
):
    """Check macOS hardening rules"""
    agent = MacOSAgent()
    rules = get_macos_hardening_rules()
    
    # Apply filters
    if rule_id:
        rules = [rule for rule in rules if rule["id"] == rule_id]
    elif category:
        rules = [rule for rule in rules if rule.get("category") == category]
    elif level:
        rules = [rule for rule in rules if level in rule.get("level", [])]
    
    if not rules:
        typer.echo("No rules found matching criteria")
        return
    
    typer.echo(f"Checking {len(rules)} macOS hardening rules...")
    typer.echo()
    
    passed = 0
    failed = 0
    errors = 0
    
    for rule in rules:
        result = agent.check_rule(rule)
        
        status_color = {
            RuleStatus.PASS: typer.colors.GREEN,
            RuleStatus.FAIL: typer.colors.RED,
            RuleStatus.ERROR: typer.colors.YELLOW
        }.get(result.status, typer.colors.WHITE)
        
        typer.secho(f"{result.rule_id}: {result.description} - {result.status.value.upper()}", 
                   fg=status_color)
        
        if result.old_value:
            typer.echo(f"  Current: {result.old_value}")
        if result.error:
            typer.echo(f"  Error: {result.error}")
        
        # Count results
        if result.status == RuleStatus.PASS:
            passed += 1
        elif result.status == RuleStatus.FAIL:
            failed += 1
        else:
            errors += 1
        
        typer.echo()
    
    # Summary
    typer.echo("Summary:")
    typer.secho(f"  Passed: {passed}", fg=typer.colors.GREEN)
    typer.secho(f"  Failed: {failed}", fg=typer.colors.RED)
    typer.secho(f"  Errors: {errors}", fg=typer.colors.YELLOW)


@macos_cli.command()
def remediate(
    rule_id: Optional[str] = typer.Option(None, help="Remediate specific rule by ID"),
    category: Optional[str] = typer.Option(None, help="Remediate rules by category"),
    level: Optional[str] = typer.Option(None, help="Remediate rules by level"),
    dry_run: bool = typer.Option(True, help="Dry run mode (no changes)")
):
    """Remediate macOS hardening rules"""
    agent = MacOSAgent()
    rules = get_macos_hardening_rules()
    
    # Apply filters
    if rule_id:
        rules = [rule for rule in rules if rule["id"] == rule_id]
    elif category:
        rules = [rule for rule in rules if rule.get("category") == category]
    elif level:
        rules = [rule for rule in rules if level in rule.get("level", [])]
    
    if not rules:
        typer.echo("No rules found matching criteria")
        return
    
    mode = "DRY RUN" if dry_run else "APPLYING CHANGES"
    typer.echo(f"Remediating {len(rules)} macOS hardening rules ({mode})...")
    typer.echo()
    
    if not dry_run:
        confirm = typer.confirm("Are you sure you want to apply these changes?")
        if not confirm:
            typer.echo("Operation cancelled")
            return
    
    passed = 0
    failed = 0
    errors = 0
    
    for rule in rules:
        result = agent.remediate_rule(rule, dry_run=dry_run)
        
        status_color = {
            RuleStatus.PASS: typer.colors.GREEN,
            RuleStatus.FAIL: typer.colors.RED,
            RuleStatus.ERROR: typer.colors.YELLOW
        }.get(result.status, typer.colors.WHITE)
        
        typer.secho(f"{result.rule_id}: {result.description} - {result.status.value.upper()}", 
                   fg=status_color)
        
        if result.old_value:
            typer.echo(f"  Old: {result.old_value}")
        if result.new_value:
            typer.echo(f"  New: {result.new_value}")
        if result.error:
            typer.echo(f"  Error: {result.error}")
        
        # Count results
        if result.status == RuleStatus.PASS:
            passed += 1
        elif result.status == RuleStatus.FAIL:
            failed += 1
        else:
            errors += 1
        
        typer.echo()
    
    # Summary
    typer.echo("Summary:")
    typer.secho(f"  Passed: {passed}", fg=typer.colors.GREEN)
    typer.secho(f"  Failed: {failed}", fg=typer.colors.RED)
    typer.secho(f"  Errors: {errors}", fg=typer.colors.YELLOW)


@macos_cli.command()
def rollback(rule_id: str = typer.Argument(help="Rule ID to rollback")):
    """Rollback a specific macOS hardening rule"""
    agent = MacOSAgent()
    rules = get_macos_hardening_rules()
    
    rule = next((rule for rule in rules if rule["id"] == rule_id), None)
    if not rule:
        typer.echo(f"Rule {rule_id} not found")
        return
    
    typer.echo(f"Rolling back rule: {rule_id}")
    typer.echo(f"Description: {rule['description']}")
    
    confirm = typer.confirm("Are you sure you want to rollback this rule?")
    if not confirm:
        typer.echo("Operation cancelled")
        return
    
    result = agent.rollback_rule(rule)
    
    status_color = {
        RuleStatus.PASS: typer.colors.GREEN,
        RuleStatus.FAIL: typer.colors.RED,
        RuleStatus.ERROR: typer.colors.YELLOW
    }.get(result.status, typer.colors.WHITE)
    
    typer.secho(f"Rollback result: {result.status.value.upper()}", fg=status_color)
    
    if result.old_value:
        typer.echo(f"Old: {result.old_value}")
    if result.new_value:
        typer.echo(f"New: {result.new_value}")
    if result.error:
        typer.echo(f"Error: {result.error}")


@macos_cli.command()
def categories():
    """List available macOS rule categories"""
    typer.echo("macOS Rule Categories:")
    typer.echo("=" * 30)
    
    for category in MacOSRuleCategory:
        rules = get_macos_hardening_rules()
        count = len([rule for rule in rules if rule.get("category") == category.value])
        typer.echo(f"{category.value}: {count} rules")


if __name__ == "__main__":
    macos_cli()
