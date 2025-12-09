from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.jobs.job import JobStatus, Job
from arix_chatbot.jobs.user_interactions import PlanWorkflowJob
from arix_chatbot.llm_query.chat_contextual_query.query import ChatContextualQuery
from arix_chatbot.state_manager.state_store import SessionState, Action
from typing import Tuple
from pathlib import Path
import json


class Planner(Worker):
    agent_id: str = aid.PLANNER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        current_job: PlanWorkflowJob = self.get_last_pending_job(state)

        turn_index = state.turn_index
        last_user_message = state.last_user_message.get('msg', None)

        if turn_index <= 1 and last_user_message in [None, '']:
            state.set_job_status(current_job.job_id, JobStatus.SUCCESS)
            return state, WorkerStatus.COMPLETED

        feed_status(state, "Planning next steps based on user intent...")
        chat = ChatContextualQuery(
            name="user_intent",
            prompt=(Path(__file__).parent / "planner_prompt.ptxt").read_text(),
            config=json.loads((Path(__file__).parent / "planner_response_config.json").read_text()),
            input_data_description=True,
            task_detailed_instructions=True,
            task_global_guidelines=True,
            task_author_notes=True,
            input_data_schema=True,
            output_data_schema=True,
            llm='gpt-5',
        )
        workflow = chat.query(state)
        if not workflow:
            workflow = {
                'high_level_intent': "cant not extract user intentions",
                'workflow': []
            }

        feed_status(state, f"{workflow['high_level_intent']}")
        state.report_action(Action(agent_id=self.agent_id, action=f"user wants to: {workflow['high_level_intent']}"))
        state.report_action(Action(agent_id=self.agent_id, action=f"planned workflow: {workflow['workflow']}"))
        state.update_job(current_job.job_id, user_intention=workflow.get('high_level_intent', ''), workflow=workflow.get('workflow', []))
        return state, WorkerStatus.COMPLETED
