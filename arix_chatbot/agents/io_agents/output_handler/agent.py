from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.io_agents.output_handler.templeate_messages import GREETINGS
from arix_chatbot.jobs.job import JobStatus, Job
from arix_chatbot.jobs.user_interactions import UserIntentRouterJob
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus, compose_message, MessageType
from typing import Tuple
import uuid




class OutputHandler(Worker):
    agent_id: str = aid.OUTPUT_HANDLER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        turn_index = state.turn_index
        last_user_message = state.last_user_message.get('msg', None)

        if turn_index <= 1 and last_user_message in [None, '']:
            self.send_message(state, aid.user, compose_message(msg_type=MessageType.CHAT, content=GREETINGS))
            return state, WorkerStatus.COMPLETED

        current_job: UserIntentRouterJob = self.get_last_pending_job(state)
        job_id = str(uuid.uuid4())
        state.add_job(Job(
            job_id=job_id,
            report_to=current_job.report_to,
            worker_id="BALA_BALA",
            status=JobStatus.SUCCESS,
            turn_index=state.turn_index
        ))
        state.update_job(current_job.job_id, user_followup_jobs=[job_id])
        state.set_job_status(current_job.job_id, JobStatus.SUCCESS)
        return state, WorkerStatus.WAIT_HUMAN
