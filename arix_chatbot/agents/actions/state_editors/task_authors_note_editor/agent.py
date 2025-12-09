from arix_chatbot.agents.actions.state_editors.utils.query_utils import edit_section_query
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.state_manager.state_store import SessionState
from arix_chatbot.jobs.job import Job
from typing import Tuple
from pathlib import Path


class TaskAuthorNotesEditor(Worker):
    agent_id: str = aid.TASK_AUTHOR_NOTES_EDITOR

    def __init__(self, manager_id: str = aid.MAIN):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        current_job: Job = self.get_last_pending_job(state)
        feed_status(state, f"Changing task goal based on user request ...")
        response = edit_section_query(
            state=state,
            prompt_path=(Path(__file__).parent / "author_notes_prompt.ptxt").as_posix(),
            config_path=(Path(__file__).parent / "author_notes_config.json").as_posix(),
            edit_job=current_job,
        )
        if response is None:
            return state, WorkerStatus.ERROR

        missing_info = response.get('missing_info', None)
        if missing_info:
            state.response_requests.append(f"The task goal is missing the following information: {missing_info}. Please provide the necessary details.")

        if response.get("author_notes"):
            state.task_author_notes = response['author_notes']
        return state, WorkerStatus.COMPLETED
