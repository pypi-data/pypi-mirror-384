"""
Linux Agent Manager for OS Forge

Manages multiple Linux agents and provides coordination capabilities.
Handles agent discovery, health monitoring, and distributed rule execution.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .linux_agent import LinuxAgent
from .linux_rules import get_linux_hardening_rules, LinuxRuleCategory
from ..common.base_agent import RuleResult, AgentStatus


class LinuxAgentManager:
    """
    Manager for Linux agents
    
    Provides capabilities for:
    - Agent discovery and registration
    - Health monitoring
    - Distributed rule execution
    - Load balancing
    - Agent coordination
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, LinuxAgent] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.rules = get_linux_hardening_rules()
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = {}
        
        # Register local agent
        self._register_local_agent()
    
    def _register_local_agent(self):
        """Register the local Linux agent"""
        try:
            local_agent = LinuxAgent("local-linux-agent")
            self.agents[local_agent.agent_id] = local_agent
            self.logger.info(f"Registered local agent: {local_agent.agent_id}")
        except Exception as e:
            self.logger.error(f"Failed to register local agent: {e}")
    
    def register_agent(self, agent: LinuxAgent) -> bool:
        """
        Register a new agent
        
        Args:
            agent: LinuxAgent instance to register
            
        Returns:
            bool: True if registration successful
        """
        try:
            if agent.agent_id in self.agents:
                self.logger.warning(f"Agent {agent.agent_id} already registered")
                return False
            
            self.agents[agent.agent_id] = agent
            self.logger.info(f"Registered agent: {agent.agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return False
            
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[LinuxAgent]:
        """
        Get agent by ID
        
        Args:
            agent_id: Agent ID
            
        Returns:
            LinuxAgent instance or None
        """
        return self.agents.get(agent_id)
    
    def get_healthy_agents(self) -> List[LinuxAgent]:
        """
        Get list of healthy agents
        
        Returns:
            List of healthy LinuxAgent instances
        """
        healthy_agents = []
        for agent in self.agents.values():
            agent.update_heartbeat()
            if agent.status == AgentStatus.HEALTHY:
                healthy_agents.append(agent)
        return healthy_agents
    
    def get_agents_by_capability(self, capability: str) -> List[LinuxAgent]:
        """
        Get agents that have a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agents with the capability
        """
        capable_agents = []
        for agent in self.agents.values():
            if capability in agent.capabilities:
                capable_agents.append(agent)
        return capable_agents
    
    def health_check_all_agents(self) -> Dict[str, AgentStatus]:
        """
        Perform health check on all agents
        
        Returns:
            Dict mapping agent IDs to their status
        """
        statuses = {}
        for agent_id, agent in self.agents.items():
            try:
                agent.update_heartbeat()
                statuses[agent_id] = agent.status
                self.last_health_check[agent_id] = datetime.utcnow()
            except Exception as e:
                self.logger.error(f"Health check failed for agent {agent_id}: {e}")
                statuses[agent_id] = AgentStatus.UNHEALTHY
        
        return statuses
    
    def execute_rule_on_agent(self, agent: LinuxAgent, rule: Dict[str, Any], dry_run: bool = True) -> RuleResult:
        """
        Execute a rule on a specific agent
        
        Args:
            agent: Target agent
            rule: Rule to execute
            dry_run: Whether to perform dry run
            
        Returns:
            RuleResult from the execution
        """
        try:
            if dry_run:
                return agent.check_rule(rule)
            else:
                return agent.remediate_rule(rule, dry_run=False)
        except Exception as e:
            return RuleResult(
                rule_id=rule['id'],
                description=rule['description'],
                status="error",
                error=f"Agent execution error: {str(e)}"
            )
    
    def execute_rule_distributed(self, rule: Dict[str, Any], dry_run: bool = True) -> List[RuleResult]:
        """
        Execute a rule on all healthy agents
        
        Args:
            rule: Rule to execute
            dry_run: Whether to perform dry run
            
        Returns:
            List of RuleResult from all agents
        """
        healthy_agents = self.get_healthy_agents()
        if not healthy_agents:
            self.logger.warning("No healthy agents available for rule execution")
            return []
        
        results = []
        
        # Execute rule on all healthy agents in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_agent = {
                executor.submit(self.execute_rule_on_agent, agent, rule, dry_run): agent
                for agent in healthy_agents
            }
            
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    result.agent_id = agent.agent_id
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Rule execution failed on agent {agent.agent_id}: {e}")
                    results.append(RuleResult(
                        rule_id=rule['id'],
                        description=rule['description'],
                        status="error",
                        error=f"Execution error: {str(e)}",
                        agent_id=agent.agent_id
                    ))
        
        return results
    
    def execute_rules_by_category(self, category: LinuxRuleCategory, dry_run: bool = True) -> Dict[str, List[RuleResult]]:
        """
        Execute all rules in a category on all healthy agents
        
        Args:
            category: Rule category to execute
            dry_run: Whether to perform dry run
            
        Returns:
            Dict mapping rule IDs to their results
        """
        category_rules = [rule for rule in self.rules if rule.get('category') == category]
        results = {}
        
        for rule in category_rules:
            rule_results = self.execute_rule_distributed(rule, dry_run)
            results[rule['id']] = rule_results
        
        return results
    
    def execute_rules_by_level(self, level: str, dry_run: bool = True) -> Dict[str, List[RuleResult]]:
        """
        Execute all rules for a specific hardening level
        
        Args:
            level: Hardening level (basic, moderate, strict)
            dry_run: Whether to perform dry run
            
        Returns:
            Dict mapping rule IDs to their results
        """
        level_rules = [rule for rule in self.rules if level in rule.get('level', [])]
        results = {}
        
        for rule in level_rules:
            rule_results = self.execute_rule_distributed(rule, dry_run)
            results[rule['id']] = rule_results
        
        return results
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered agents
        
        Returns:
            Dict containing agent statistics
        """
        total_agents = len(self.agents)
        healthy_agents = len(self.get_healthy_agents())
        
        # Get capability counts
        capability_counts = {}
        for agent in self.agents.values():
            for capability in agent.capabilities:
                capability_counts[capability] = capability_counts.get(capability, 0) + 1
        
        # Get OS distribution
        os_counts = {}
        for agent in self.agents.values():
            os_type = agent.os_type
            os_counts[os_type] = os_counts.get(os_type, 0) + 1
        
        return {
            'total_agents': total_agents,
            'healthy_agents': healthy_agents,
            'unhealthy_agents': total_agents - healthy_agents,
            'capability_counts': capability_counts,
            'os_distribution': os_counts,
            'last_health_check': self.last_health_check
        }
    
    def cleanup_inactive_agents(self, max_age_minutes: int = 30) -> int:
        """
        Remove agents that haven't been seen for too long
        
        Args:
            max_age_minutes: Maximum age in minutes before removal
            
        Returns:
            Number of agents removed
        """
        removed_count = 0
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        inactive_agents = []
        for agent_id, last_check in self.last_health_check.items():
            if last_check < cutoff_time:
                inactive_agents.append(agent_id)
        
        for agent_id in inactive_agents:
            if self.unregister_agent(agent_id):
                removed_count += 1
                self.logger.info(f"Removed inactive agent: {agent_id}")
        
        return removed_count
    
    def shutdown(self):
        """Shutdown the agent manager"""
        self.executor.shutdown(wait=True)
        self.logger.info("Linux Agent Manager shutdown complete")
