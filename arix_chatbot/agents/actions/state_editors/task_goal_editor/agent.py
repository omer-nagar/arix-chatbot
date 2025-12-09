from arix_chatbot.agents.actions.state_editors.utils.query_utils import edit_section_query
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.jobs.job import Job
from arix_chatbot.jobs.user_interactions import PlanWorkflowJob
from arix_chatbot.llm_query.chat_contextual_query.query import ChatContextualQuery
from arix_chatbot.state_manager.state_store import SessionState
from pathlib import Path
from typing import Tuple
import json


class TaskGoalEditor(Worker):
    agent_id: str = aid.TASK_GOAL_EDITOR

    def __init__(self, manager_id: str = aid.MAIN):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState, system_response_request=None) -> Tuple[SessionState, WorkerStatus]:

        current_job: Job = self.get_last_pending_job(state)
        feed_status(state, f"Changing task goal based on user request ...")
        response = edit_section_query(
            state=state,
            prompt_path=(Path(__file__).parent / "edit_task_goal_prompt.ptxt").as_posix(),
            config_path=(Path(__file__).parent / "edit_task_goal_config.json").as_posix(),
            edit_job=current_job,
        )
        if response is None:
            return state, WorkerStatus.ERROR

        missing_info = response.get('missing-info-in-goal', None)
        if missing_info:
            state.response_requests.append(f"The task goal is missing the following information: {missing_info}. Please provide the necessary details.")

        goal_str = ""
        if response.get("context"):
            goal_str += f"### Context:\n{response['context']}\n"
        if response.get("core-objective"):
            goal_str += f"### Core Objective:\n{response['core-objective']}\n"
        if goal_str != "":
            state.task_goal = goal_str.strip()

        return state, WorkerStatus.COMPLETED
