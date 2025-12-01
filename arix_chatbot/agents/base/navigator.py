from arix_chatbot.state_manager.state_store import SessionState
from arix_chatbot.agents.base.base_agent import BaseAgent
from typing import List, Union, Tuple

DEFAULT_OWNER = "main_navigator"


class Navigator(BaseAgent):
    """Interface for manager agents that coordinate other agents."""
    agent_id = "navigator"

    def __init__(self, managed_agents: List[str]):
        super().__init__()
        self.managed_agents = managed_agents

    def set_error(self, state: SessionState, error_msg: str) -> SessionState:
        state.status = "ERROR"
        state.error = error_msg
        return state

    async def handle(self, state: SessionState) -> SessionState:
        """Process the current state and determine the next agent to handle the task."""

        # Determine the next agent to handle the task
        state, next_owner_ids = self.next_agents(state)
        if next_owner_ids is not None and any([owner_id not in self.managed_agents for owner_id in next_owner_ids]):
            return self.set_error(state, f"Next owner(s) {next_owner_ids} not managed by navigator {self.agent_id}")
        next_owner_ids = next_owner_ids if next_owner_ids is not None else []

        # If we are passing to a new agent, push current owner to stack -> for returning when done
        next_owner_id = None
        if len(next_owner_ids) > 0:
            state.pending_handoff.append(state.owner_agent_id)
            # If multiple next owners specified, push all but the first to stack - first is the immediate next owner
            state.pending_handoff.extend(reversed(next_owner_ids[1:]))
            next_owner_id = next_owner_ids[0]

        # If no next owner specified, pop from stack or use default
        if len(next_owner_ids) == 0 and len(state.pending_handoff) > 0:
            next_owner_id = state.pending_handoff[-1]
            state.pending_handoff = state.pending_handoff[:-1]
        # elif next_owner_id is None:
        #     next_owner_id = DEFAULT_OWNER

        state.owner_agent_id = next_owner_id
        return state

    def next_agents(self, state: SessionState) -> Tuple[SessionState, Union[List, None]]:
        """Register a new managed agent."""
        raise NotImplementedError("This method should be overridden by subclasses.")


