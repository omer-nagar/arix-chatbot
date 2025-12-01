from arix_chatbot.jobs.user_interactions import UserIntentRouterJob
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from typing import List, Tuple, Union
from arix_chatbot.agents.base.navigator import Navigator
from arix_chatbot.jobs.job import JobStatus


class MainActionHandler(Navigator):
    """Navigator agent that manages the workflow of other agents."""
    agent_id: str = aid.MAIN_ACTION_HANDLER

    def __init__(self, managed_agents: List[str] = None):
        super().__init__(managed_agents=managed_agents)

    def next_agents(self, state: SessionState) -> Tuple[SessionState, Union[List, None]]:
        """Register a new managed agent."""
        next_job = self.get_last_pending_job(state)

        ## STEP 1: Ask for follow-up jobs if there is a pending job to be assigned
        if next_job is not None:
            # there is already a pending job
            state.add_job(UserIntentRouterJob(
                job_id=aid.USER_INTENT_ROUTER,
                report_to=self.agent_id,
                worker_id=aid.USER_INTENT_ROUTER,
                status=JobStatus.ASSIGNED_TO_AGENT,
                turn_index=state.turn_index
            ))
            state.set_job_status(next_job.job_id, JobStatus.SUCCESS)
            return state, [aid.USER_INTENT_ROUTER]

        ## STEP 2: Assign follow-up jobs to respective agents
        user_intent_router_job = state.get_job(aid.USER_INTENT_ROUTER)
        if user_intent_router_job is not None:
            todos = user_intent_router_job.user_followup_jobs
            next_agents = []
            for job_id in todos:
                job = state.get_job(job_id)
                next_agents.append(job.worker_id)
                state.set_job_status(job.job_id, JobStatus.ASSIGNED_TO_AGENT)
            return state, next_agents

        managed_jobs = self.get_jobs(state, role="managed")
        if all([job.status in [JobStatus.SUCCESS, JobStatus.FAILED] for job in managed_jobs]):
            state.set_status(SessionStatus.COMPLETED)

        return state, None

