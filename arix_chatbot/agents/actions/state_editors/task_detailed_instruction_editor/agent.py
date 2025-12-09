from arix_chatbot.agents.actions.state_editors.utils.query_utils import edit_section_query
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.state_manager.state_store import SessionState
from arix_chatbot.jobs.job import Job
from pathlib import Path
from typing import Tuple


class TaskDetailedInstructionEditor(Worker):
    agent_id: str = aid.TASK_DETAILED_INSTRUCTIONS_EDITOR

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    def render_crts(self, criteria_list):
        return "\n".join([f"\t * [{crt['criterion_type']}] {crt['criterion_content']}" for crt in criteria_list])

    def render_unit_crts(self, unit):
        unit_name = unit.get('unit_name', '---')
        crts = unit.get('criteria', [])
        rendered = f"**{unit_name}:**\n"
        rendered += self.render_crts(crts)
        return rendered

    def render_logical_units(self, logical_units):
        return "\n\n".join([self.render_unit_crts(unit) for unit in logical_units])

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:

        current_job: Job = self.get_last_pending_job(state)
        feed_status(state, f"Changing the task detailed instructions as per user request...")
        response = edit_section_query(
            state=state,
            prompt_path=(Path(__file__).parent / "task_detailed_description_prompt.ptxt").as_posix(),
            config_path=(Path(__file__).parent / "task_detailed_description_config.json").as_posix(),
            edit_job=current_job,
        )
        if response is None:
            return state, WorkerStatus.ERROR

        missing_info = response.get('missing_info', None)
        if missing_info:
            state.response_requests.append(
                f"The task input schema is missing the following information: {missing_info}. "
                f"Please include this information in your next response.")

        task_criteria = {
            'description': response.get("description", None),
            'criteria': response.get("logical_units", None),
            'rendered': f"{ response.get('description', '')} \n\n### Criteria: {self.render_logical_units(response.get('logical_units', []))}"
        }
        state.task_detailed_instructions = task_criteria

        return state, WorkerStatus.COMPLETED
