from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.state_manager.state_store import SessionState
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.llm_query.query import LLMQuery
from pathlib import Path
from typing import Tuple


class HistoryManager(Worker):
    agent_id: str = aid.HISTORY_MANAGER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        self._config_path = Path(__file__).parent / "history_response_config.json"
        self._prompt_path = Path(__file__).parent / "history_prompt.ptxt"
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        res = LLMQuery(
            name="history_manager",
            prompt=self._prompt_path.as_posix(),
            config=self._config_path.as_posix(),
            llm='deepseek-chat',
        ).query(
            chat_history=state.chat_summary,
            last_user_message=state.last_user_message,
            action_committed=state.chat_action_stack,
            assistant_response=state.next_response
        )
        if 'history_summary' in res and res['history_summary'] is not None:
            state.chat_summary = res['history_summary']
        return state, WorkerStatus.COMPLETED
