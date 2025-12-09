from arix_chatbot.agents.actions.state_editors.utils.query_utils import edit_section_query
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.jobs.job import Job
from arix_chatbot.state_manager.state_store import SessionState
from typing import Tuple
from pathlib import Path


class TaskGlobalGuidelinesEditor(Worker):
    agent_id: str = aid.TASK_GLOBAL_GUIDELINES_EDITOR

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:


        current_job: Job = self.get_last_pending_job(state)
        feed_status(state, f"Changing task global guidelines based on user request ...")
        response = edit_section_query(
            state=state,
            prompt_path=(Path(__file__).parent / "global_guidelines_prompt.ptxt").as_posix(),
            config_path=(Path(__file__).parent / "global_guidelines_config.json").as_posix(),
            edit_job=current_job,
        )
        if response is None:
            return state, WorkerStatus.ERROR

        missing_info = response.get('missing_info', None)
        if missing_info:
            state.response_requests.append(f"The task global guidelines is missing the following information: {missing_info}. "
                                           f"Please provide the necessary details.")

        if response.get("guidelines"):
            state.task_global_guidelines = {
                'guidelines': response.get("guidelines"),
                'rendered': "\n".join([f"\t * [{crt['type']}] {crt['content']}" for crt in response.get('guidelines', [])])
            }

        return state, WorkerStatus.COMPLETED