from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.io_agents.output_handler.templeate_messages import GREETINGS
from arix_chatbot.jobs.job import JobStatus, Job
from arix_chatbot.jobs.user_interactions import UserIntentRouterJob
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus, compose_message, MessageType
from typing import Tuple
import uuid


class HistoryManager(Worker):
    agent_id: str = aid.HISTORY_MANAGER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        return state, WorkerStatus.COMPLETED
