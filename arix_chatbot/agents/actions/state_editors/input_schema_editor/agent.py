from arix_chatbot.agents.actions.state_editors.utils.query_utils import edit_section_query
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.state_manager.state_store import SessionState
from arix_chatbot.jobs.job import Job
from typing import Tuple
from pathlib import Path


class InputSchemaEditor(Worker):
    agent_id: str = aid.INPUT_SCHEMA_EDITOR

    def __init__(self, manager_id: str = aid.MAIN):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:

        current_job: Job = self.get_last_pending_job(state)
        feed_status(state, f"Changing the input data schema as per user request...")
        response = edit_section_query(
            state=state,
            prompt_path=(Path(__file__).parent / "input_schema_prompt.ptxt").as_posix(),
            config_path=(Path(__file__).parent / "input_schema_config.json").as_posix(),
            edit_job=current_job,
        )
        if response is None:
            return state, WorkerStatus.ERROR

        missing_info = response.get('missing_info', None)
        if missing_info:
            state.response_requests.append(
                f"The task input schema is missing the following information: {missing_info}. "
                f"Please include this information in your next response.")

        if response.get("schema"):
            state.input_data_schema = response["schema"]

        return state, WorkerStatus.COMPLETED
