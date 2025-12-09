from arix_chatbot.agents.utils.status_feed import feed_status
from arix_chatbot.llm_query.chat_contextual_query.query import ChatContextualQuery
from arix_chatbot.state_manager.state_store import SessionState, compose_message, MessageType
from arix_chatbot.agents.workflow.output_handler.templeate_messages import GREETINGS
from arix_chatbot.agents.base.worker import Worker, WorkerStatus
from arix_chatbot.agents.agent_ids import AgentID as aid
from pathlib import Path
from typing import Tuple
import json


class OutputHandler(Worker):
    agent_id: str = aid.OUTPUT_HANDLER

    def __init__(self, manager_id: str = aid.MAIN_ACTION_HANDLER):
        super().__init__(manager_id)

    async def process_task(self, state: SessionState) -> Tuple[SessionState, WorkerStatus]:
        turn_index = state.turn_index
        last_user_message = state.last_user_message

        if turn_index <= 1 and last_user_message in [None, '']:
            state.next_response = compose_message(msg_type=MessageType.CHAT, content=GREETINGS)
            return state, WorkerStatus.COMPLETED

        system_response_request = "\n".join(state.response_requests) if len(state.response_requests) > 0 else "N/A"

        feed_status(state, f"Thinking ...")
        chat = ChatContextualQuery(
            name="user_intent",
            prompt=(Path(__file__).parent / "response_prompt.ptxt").read_text(),
            config=json.loads((Path(__file__).parent / "response_config.json").read_text()),
            input_data_description=True,
            task_detailed_instructions=True,
            task_global_guidelines=True,
            task_author_notes=True,
            input_data_schema=True,
            output_data_schema=True,
            llm='deepseek-chat',
        )
        response = chat.query(state, system_response_request=system_response_request)
        response = response.get('response', None)
        response = response if response is not None else "Im sorry, could you please repeat that?"
        state.next_response = compose_message(msg_type=MessageType.CHAT, content=response)
        return state, WorkerStatus.COMPLETED

