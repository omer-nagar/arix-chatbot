from typing import Dict, Optional, List
from arix_chatbot.agents.base.base_agent import BaseAgent


class AgentRegistry:
    """Registry for managing all available agents."""

    def __init__(self, agents: List[BaseAgent] = None):
        self.agents: Dict[str, BaseAgent] = {}
        if agents:
            for agent in agents:
                self.register_agent(agent)

    def register_agent(self, agent: BaseAgent):
        """Register an agent in the registry."""
        self.agents[agent.agent_id] = agent
        print(f"Registered agent: {agent.agent_id}")

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self.agents.keys())

    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Get information about an agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        return {
            "agent_id": agent_id,
            "type": type(agent).__name__
        }

    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            print(f"Unregistered agent: {agent_id}")
            return True
        return False
