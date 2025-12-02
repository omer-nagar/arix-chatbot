from arix_chatbot.state_manager.state_store import SessionState, SessionStatus, MessageType, compose_message
from arix_chatbot.jobs.user_interactions import OutputHandlerJob
from arix_chatbot.agents.base.navigator import Navigator
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.jobs.job import JobStatus, Job
from typing import List, Tuple, Union


class MainChatOrchestrator(Navigator):
    """Navigator agent that manages the workflow of other agents."""
    agent_id: str = aid.MAIN

    def __init__(self, managed_agents: List[str] = None):
        super().__init__(managed_agents=managed_agents)

    def assign_pipeline_jobs(self, state: SessionState) -> List:
        state.add_job(Job(
            job_id=aid.MAIN_ACTION_HANDLER,
            report_to=self.agent_id,
            worker_id=aid.MAIN_ACTION_HANDLER,
            status=JobStatus.ASSIGNED_TO_AGENT,
            turn_index=state.turn_index
        ))

        state.add_job(OutputHandlerJob(
            job_id=aid.OUTPUT_HANDLER,
            report_to=self.agent_id,
            worker_id=aid.OUTPUT_HANDLER,
            status=JobStatus.ASSIGNED_TO_AGENT,
            turn_index=state.turn_index
        ))

        state.add_job(Job(
            job_id=aid.HISTORY_MANAGER,
            report_to=self.agent_id,
            worker_id=aid.HISTORY_MANAGER,
            status=JobStatus.ASSIGNED_TO_AGENT,
            turn_index=state.turn_index
        ))

        # order ->
        return [aid.MAIN_ACTION_HANDLER, aid.OUTPUT_HANDLER, aid.HISTORY_MANAGER]

    def all_jobs_completed(self, state: SessionState) -> bool:
        managed_jobs = self.get_jobs(state, role="managed")
        todo = {
            aid.MAIN_ACTION_HANDLER: False,
            aid.OUTPUT_HANDLER: False,
            aid.HISTORY_MANAGER: False
        }

        for job in managed_jobs:
            todo[job.worker_id] = job.status in [JobStatus.SUCCESS, JobStatus.FAILED]
        return all(todo.values())

    def get_response_to_user(self, state):
        res_job = [job for job in self.get_jobs(state, role="managed") if job.worker_id == aid.OUTPUT_HANDLER]
        if len(res_job) == 0 or res_job[0].status != JobStatus.SUCCESS:
            return None
        return res_job[0].get_response_to_user()

    def next_agents(self, state: SessionState) -> Tuple[SessionState, Union[List, None]]:
        """Register a new managed agent."""

        # add user message to state
        inbox = self.get_inbox(state, clear=True)

        # check if entry point -> new user message -> launch pipeline
        if aid.user in inbox:
            state.turn_index += 1
            user_message = inbox[aid.user]
            state.last_user_message = user_message[-1]
            return state, self.assign_pipeline_jobs(state)

        # check if all jobs are completed -> send response to user and complete session
        if self.all_jobs_completed(state):
            # Finalize
            system_response = self.get_response_to_user(state)
            error_response = "opps, something went wrong. Please try again later."
            system_response = error_response if system_response is None else system_response
            self.send_message(state, aid.user, compose_message(msg_type=MessageType.CHAT, content=system_response))

        # nothing to do, wait for user input
        state.set_status(SessionStatus.WAIT_HUMAN)
        return state, None
