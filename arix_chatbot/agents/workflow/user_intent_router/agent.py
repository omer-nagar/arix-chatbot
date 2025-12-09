from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.jobs.job import JobStatus, Job
from arix_chatbot.jobs.user_interactions import PlanWorkflowJob
from arix_chatbot.llm_query.chat_contextual_query.query import ChatContextualQuery
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus, Action
from typing import Tuple
from pathlib import Path
import json


class UserIntentRouter(Worker):
    agent_id: str = aid.USER_INTENT_ROUTER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        current_job: PlanWorkflowJob = self.get_last_pending_job(state)

        turn_index = state.turn_index
        last_user_message = state.last_user_message.get('msg', None)

        if turn_index <= 1 and last_user_message in [None, '']:
            state.set_job_status(current_job.job_id, JobStatus.SUCCESS)
            return state, WorkerStatus.COMPLETED

        chat = ChatContextualQuery(
            name="user_intent",
            prompt=(Path(__file__).parent / "intent_extraction_prompt.ptxt").read_text(),
            config=json.loads((Path(__file__).parent / "intent_response_config.json").read_text()),
            input_data_description=True,
            task_detailed_instructions=True,
            task_global_guidelines=True,
            task_author_notes=True,
            input_data_schema=True,
            output_data_schema=True
        )
        user_intentions = chat.query(state)
        if not user_intentions:
            user_intentions = {"user_intentions": []}

        state.report_action(Action(agent_id=self.agent_id, action=f"Extracted user intentions: {user_intentions}"))
        state.update_job(current_job.job_id, user_intentions=user_intentions.get("user_intentions", []))
        return state, WorkerStatus.COMPLETED
