from typing import Tuple
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus
from arix_chatbot.agents.base.base_agent import BaseAgent


class WorkerStatus:
    WAIT_HUMAN = "WAIT_HUMAN"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class Worker(BaseAgent):
    """Interface for worker agents that perform specific tasks."""
    agent_id = "worker_agent"

    def __init__(self, manager_id: str):
        super().__init__()
        self._manager = manager_id

    async def handle(self, state: SessionState) -> SessionState:
        """Main handler method - must be implemented by all agents."""
        state, worker_status = await self.process_task(state)
        if worker_status == SessionStatus.ERROR:
            state.status = SessionStatus.ERROR
        elif worker_status == SessionStatus.WAIT_HUMAN:
            state.status = SessionStatus.WAIT_HUMAN

        is_waiting_fo_human = state.status == SessionStatus.WAIT_HUMAN

        if is_waiting_fo_human:
            return state

        # handoff to manager
        if len(state.pending_handoff) > 0:
            next_owner_id = state.pending_handoff[-1]
            state.pending_handoff = state.pending_handoff[:-1]
        else:
            next_owner_id = None
        state.owner_agent_id = next_owner_id
        return state

    async def process_task(self, state: SessionState) -> Tuple[SessionState, SessionStatus]:
        """Process a specific task."""
        raise NotImplementedError("Worker agents must implement the process_task method.")
