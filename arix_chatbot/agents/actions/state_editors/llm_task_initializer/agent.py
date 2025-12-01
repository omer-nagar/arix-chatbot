from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.jobs.job import JobStatus, Job
from arix_chatbot.jobs.user_interactions import UserIntentRouterJob
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus
from typing import Tuple
import uuid


class UserIntentRouter(Worker):
    agent_id: str = aid.USER_INTENT_ROUTER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:

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
        return state, WorkerStatus.COMPLETED
