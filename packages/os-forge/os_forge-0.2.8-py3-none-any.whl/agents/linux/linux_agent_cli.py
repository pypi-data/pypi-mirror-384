#!/usr/bin/env python3
"""
Linux Agent CLI for OS Forge

Command-line interface for testing and managing Linux agents.
"""

import argparse
import json
import sys
from typing import Optional

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.linux.linux_agent import LinuxAgent
from agents.linux.linux_agent_manager import LinuxAgentManager
from agents.linux.linux_rules import get_linux_hardening_rules, LinuxRuleCategory


def print_rule_result(result, verbose: bool = False):
    """Print a rule result in a formatted way"""
    status_colors = {
        "pass": "\033[92m",  # Green
        "fail": "\033[91m",  # Red
        "error": "\033[93m",  # Yellow
        "skip": "\033[94m"   # Blue
    }
    reset_color = "\033[0m"
    
    color = status_colors.get(result.status, "")
    print(f"{color}[{result.status.upper()}]{reset_color} {result.rule_id}: {result.description}")
    
    if verbose:
        if result.old_value:
            print(f"  Current: {result.old_value}")
        if result.new_value:
            print(f"  New: {result.new_value}")
        if result.error:
            print(f"  Error: {result.error}")
        if result.execution_time:
            print(f"  Time: {result.execution_time:.2f}s")


def cmd_info(args):
    """Show agent information"""
    agent = LinuxAgent()
    info = agent.get_system_info()
    
    print("Linux Agent Information")
    print("=" * 50)
    print(f"Agent ID: {info['agent_info'].agent_id}")
    print(f"OS Type: {info['agent_info'].os_type}")
    print(f"OS Version: {info['agent_info'].os_version}")
    print(f"Architecture: {info['agent_info'].architecture}")
    print(f"Status: {info['agent_info'].status}")
    print(f"Capabilities: {', '.join(info['agent_info'].capabilities)}")
    
    if args.verbose:
        print("\nDetailed System Info:")
        print(json.dumps(info, indent=2, default=str))


def cmd_health(args):
    """Check agent health"""
    agent = LinuxAgent()
    status = agent.health_check()
    
    print(f"Agent Health: {status}")
    
    if args.verbose:
        info = agent.get_linux_specific_info()
        print("\nLinux-specific Info:")
        print(json.dumps(info, indent=2, default=str))


def cmd_list_rules(args):
    """List available rules"""
    rules = get_linux_hardening_rules()
    
    if args.category:
        rules = [r for r in rules if r.get('category') == args.category]
    
    if args.severity:
        rules = [r for r in rules if r.get('severity') == args.severity]
    
    if args.level:
        rules = [r for r in rules if args.level in r.get('level', [])]
    
    print(f"Found {len(rules)} rules")
    print()
    
    for rule in rules:
        print(f"{rule['id']}: {rule['description']}")
        print(f"  Category: {rule.get('category', 'N/A')}")
        print(f"  Severity: {rule.get('severity', 'N/A')}")
        print(f"  Level: {', '.join(rule.get('level', []))}")
        if args.verbose:
            print(f"  Rationale: {rule.get('rationale', 'N/A')}")
        print()


def cmd_check(args):
    """Check a specific rule"""
    agent = LinuxAgent()
    rules = get_linux_hardening_rules()
    
    # Find the rule
    rule = next((r for r in rules if r['id'] == args.rule_id), None)
    if not rule:
        print(f"Rule {args.rule_id} not found")
        return
    
    print(f"Checking rule: {rule['id']}")
    result = agent.check_rule(rule)
    print_rule_result(result, args.verbose)


def cmd_remediate(args):
    """Remediate a specific rule"""
    agent = LinuxAgent()
    rules = get_linux_hardening_rules()
    
    # Find the rule
    rule = next((r for r in rules if r['id'] == args.rule_id), None)
    if not rule:
        print(f"Rule {args.rule_id} not found")
        return
    
    print(f"Remediating rule: {rule['id']}")
    result = agent.remediate_rule(rule, dry_run=args.dry_run)
    print_rule_result(result, args.verbose)


def cmd_run_category(args):
    """Run all rules in a category"""
    manager = LinuxAgentManager()
    category = LinuxRuleCategory(args.category)
    
    print(f"Running rules in category: {category}")
    results = manager.execute_rules_by_category(category, dry_run=args.dry_run)
    
    for rule_id, rule_results in results.items():
        print(f"\nRule: {rule_id}")
        for result in rule_results:
            print_rule_result(result, args.verbose)


def cmd_run_level(args):
    """Run all rules for a level"""
    manager = LinuxAgentManager()
    
    print(f"Running rules for level: {args.level}")
    results = manager.execute_rules_by_level(args.level, dry_run=args.dry_run)
    
    for rule_id, rule_results in results.items():
        print(f"\nRule: {rule_id}")
        for result in rule_results:
            print_rule_result(result, args.verbose)


def cmd_manager_stats(args):
    """Show manager statistics"""
    manager = LinuxAgentManager()
    stats = manager.get_agent_statistics()
    
    print("Linux Agent Manager Statistics")
    print("=" * 50)
    print(f"Total Agents: {stats['total_agents']}")
    print(f"Healthy Agents: {stats['healthy_agents']}")
    print(f"Unhealthy Agents: {stats['unhealthy_agents']}")
    
    print("\nCapability Distribution:")
    for capability, count in stats['capability_counts'].items():
        print(f"  {capability}: {count}")
    
    print("\nOS Distribution:")
    for os_type, count in stats['os_distribution'].items():
        print(f"  {os_type}: {count}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Linux Agent CLI for OS Forge")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show agent information")
    info_parser.set_defaults(func=cmd_info)
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check agent health")
    health_parser.set_defaults(func=cmd_health)
    
    # List rules command
    list_parser = subparsers.add_parser("list", help="List available rules")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument("--severity", help="Filter by severity")
    list_parser.add_argument("--level", help="Filter by level")
    list_parser.set_defaults(func=cmd_list_rules)
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check a specific rule")
    check_parser.add_argument("rule_id", help="Rule ID to check")
    check_parser.set_defaults(func=cmd_check)
    
    # Remediate command
    remediate_parser = subparsers.add_parser("remediate", help="Remediate a specific rule")
    remediate_parser.add_argument("rule_id", help="Rule ID to remediate")
    remediate_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    remediate_parser.set_defaults(func=cmd_remediate)
    
    # Run category command
    run_cat_parser = subparsers.add_parser("run-category", help="Run all rules in a category")
    run_cat_parser.add_argument("category", help="Category to run")
    run_cat_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    run_cat_parser.set_defaults(func=cmd_run_category)
    
    # Run level command
    run_level_parser = subparsers.add_parser("run-level", help="Run all rules for a level")
    run_level_parser.add_argument("level", help="Level to run (basic, moderate, strict)")
    run_level_parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    run_level_parser.set_defaults(func=cmd_run_level)
    
    # Manager stats command
    stats_parser = subparsers.add_parser("stats", help="Show manager statistics")
    stats_parser.set_defaults(func=cmd_manager_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
