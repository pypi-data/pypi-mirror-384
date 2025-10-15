"""
macOS Agent Manager for OS Forge

Manages multiple macOS agents and provides coordination capabilities.
Handles agent discovery, health monitoring, and distributed rule execution.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .macos_agent import MacOSAgent
from .macos_rules import get_macos_hardening_rules, MacOSRuleCategory
from ..common.base_agent import RuleResult, AgentStatus


class MacOSAgentManager:
    """
    Manager for macOS agents
    
    Provides capabilities for:
    - Agent discovery and registration
    - Health monitoring
    - Distributed rule execution
    - Load balancing
    - Agent coordination
    """
    
    def __init__(self, max_workers: int = 4):
        self.logger = logging.getLogger(__name__)
        self.agents: Dict[str, MacOSAgent] = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.rules = get_macos_hardening_rules()
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = {}
        
        # Register local agent
        self._register_local_agent()
    
    def _register_local_agent(self):
        """Register the local macOS agent"""
        try:
            local_agent = MacOSAgent("local-macos-agent")
            self.agents[local_agent.agent_id] = local_agent
            self.logger.info(f"Registered local agent: {local_agent.agent_id}")
        except Exception as e:
            self.logger.error(f"Failed to register local agent: {e}")
    
    def register_agent(self, agent: MacOSAgent) -> bool:
        """
        Register a new macOS agent
        
        Args:
            agent: MacOSAgent instance to register
            
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
        Unregister a macOS agent
        
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
    
    def get_agent(self, agent_id: str) -> Optional[MacOSAgent]:
        """
        Get a specific agent by ID
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            MacOSAgent or None if not found
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs
        
        Returns:
            List of agent IDs
        """
        return list(self.agents.keys())
    
    def health_check_all(self) -> Dict[str, AgentStatus]:
        """
        Perform health check on all agents
        
        Returns:
            Dict mapping agent IDs to their health status
        """
        health_status = {}
        
        for agent_id, agent in self.agents.items():
            try:
                status = agent.health_check()
                health_status[agent_id] = status
                self.last_health_check[agent_id] = datetime.utcnow()
                
            except Exception as e:
                self.logger.error(f"Health check failed for agent {agent_id}: {e}")
                health_status[agent_id] = AgentStatus.ERROR
        
        return health_status
    
    def get_healthy_agents(self) -> List[MacOSAgent]:
        """
        Get list of healthy agents
        
        Returns:
            List of healthy MacOSAgent instances
        """
        healthy_agents = []
        
        for agent in self.agents.values():
            if agent.status == AgentStatus.HEALTHY:
                healthy_agents.append(agent)
        
        return healthy_agents
    
    def execute_rule_on_agent(self, agent: MacOSAgent, rule: Dict[str, Any], 
                            operation: str = "check") -> RuleResult:
        """
        Execute a rule on a specific agent
        
        Args:
            agent: MacOSAgent instance
            rule: Rule dictionary
            operation: Operation to perform (check, remediate, rollback)
            
        Returns:
            RuleResult: Result of the operation
        """
        try:
            if operation == "check":
                return agent.check_rule(rule)
            elif operation == "remediate":
                return agent.remediate_rule(rule, dry_run=False)
            elif operation == "rollback":
                return agent.rollback_rule(rule)
            else:
                return RuleResult(
                    rule_id=rule["id"],
                    description=rule["description"],
                    status=RuleStatus.ERROR,
                    old_value="N/A",
                    new_value="N/A",
                    error=f"Unknown operation: {operation}"
                )
                
        except Exception as e:
            self.logger.error(f"Error executing rule {rule['id']} on agent {agent.agent_id}: {e}")
            return RuleResult(
                rule_id=rule["id"],
                description=rule["description"],
                status=RuleStatus.ERROR,
                old_value="N/A",
                new_value="N/A",
                error=str(e)
            )
    
    def execute_rule_distributed(self, rule: Dict[str, Any], 
                               operation: str = "check") -> List[RuleResult]:
        """
        Execute a rule on all healthy agents
        
        Args:
            rule: Rule dictionary
            operation: Operation to perform (check, remediate, rollback)
            
        Returns:
            List of RuleResult from all agents
        """
        healthy_agents = self.get_healthy_agents()
        
        if not healthy_agents:
            self.logger.warning("No healthy agents available for rule execution")
            return []
        
        results = []
        
        # Execute rule on all healthy agents concurrently
        with self.executor as executor:
            future_to_agent = {
                executor.submit(self.execute_rule_on_agent, agent, rule, operation): agent
                for agent in healthy_agents
            }
            
            for future in as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error executing rule on agent {agent.agent_id}: {e}")
                    results.append(RuleResult(
                        rule_id=rule["id"],
                        description=rule["description"],
                        status=RuleStatus.ERROR,
                        old_value="N/A",
                        new_value="N/A",
                        error=str(e)
                    ))
        
        return results
    
    def get_rules_by_category(self, category: MacOSRuleCategory) -> List[Dict[str, Any]]:
        """
        Get rules filtered by category
        
        Args:
            category: MacOSRuleCategory enum value
            
        Returns:
            List of rules in the specified category
        """
        return [rule for rule in self.rules if rule.get("category") == category.value]
    
    def get_rules_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        Get rules filtered by hardening level
        
        Args:
            level: Hardening level (basic, moderate, strict)
            
        Returns:
            List of rules for the specified level
        """
        return [rule for rule in self.rules if level in rule.get("level", [])]
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule by ID
        
        Args:
            rule_id: Rule ID to find
            
        Returns:
            Rule dictionary or None if not found
        """
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get manager statistics
        
        Returns:
            Dict containing various statistics
        """
        total_agents = len(self.agents)
        healthy_agents = len(self.get_healthy_agents())
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents,
            "total_rules": len(self.rules),
            "rules_by_category": {
                category.value: len(self.get_rules_by_category(category))
                for category in MacOSRuleCategory
            },
            "rules_by_level": {
                level: len(self.get_rules_by_level(level))
                for level in ["basic", "moderate", "strict"]
            }
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        self.logger.info("MacOS Agent Manager cleaned up")
