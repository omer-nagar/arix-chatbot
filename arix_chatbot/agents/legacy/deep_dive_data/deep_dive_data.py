from arix_chat.agents.legacy.deep_dive_data.deep_dive_data_agent import chat_deep_dive_data
from arix_chat.state_manager.state_store import SessionState, SessionStatus
from arix_chat.agents.base.worker import Worker


class DeepDiveData(Worker):
    def __init__(self, agent_id: str = "deepDiveData", manager_id: str = "main_navigator"):
        super().__init__(agent_id, manager_id)

    def init_context(self, state: SessionState) -> dict:
        inbox = self.get_inbox(state)

        context = {
            # History of the conversation
            "latest_assistant_response": "none",
            "conversation_history": inbox.get('main_navigator', {'conversation_history': 'no-history'})['conversation_history'],
            "task_definition": inbox.get('main_navigator', {'task_definition': 'not provided'})['task_definition'],

            # Task details
            "domain": "not provided",
            "text_type": "not provided",
            "user_wants_to_provide_its_own_data": "not provided",

            # Other info
            "n_interactions": 0,
            "worker_done": False
        }
        return context

    def update_state(self, state: SessionState, context: dict, outbox: dict, new_worker_status: str) -> SessionState:
        # Update context
        self.update_state_context(state, context)

        # Update status
        self.update_status(state, new_worker_status)

        # Update outbox
        for recipient, msgs in outbox.items():
            self.send_message(state, recipient, msgs)
        return state

    async def process_task(self, state: SessionState) -> SessionState:
        # Implement the logic to process the task and return an AgentPayload

        # Get inbox and context
        inbox = self.get_inbox(state)
        context = self.get_context(state)

        latest_assistant_question = context["latest_assistant_response"]
        conversation_history = context["conversation_history"]
        domain = context["domain"]
        text_type = context["text_type"]
        user_wants_to_provide_its_own_data = context["user_wants_to_provide_its_own_data"]
        n_interactions = context["n_interactions"]
        task_definition = context["task_definition"]

        user_response = inbox.get("user", [{"msg": "Great, Whats next?"}])[-1]["msg"]
        response, domain, text_type, user_wants_to_provide_its_own_data, conversation_history, user_approved = (
            chat_deep_dive_data(
                task_definition=task_definition,
                domain=domain,
                text_type=text_type,
                user_wants_to_provide_its_own_data=user_wants_to_provide_its_own_data,
                conversation_history=conversation_history,
                latest_assistant_question=latest_assistant_question,
                latest_user_response=user_response
            ))

        response = response.strip() if response.strip() != "" else "ops, missed your response"
        context["latest_assistant_question"] = response
        context["conversation_history"] = conversation_history

        context["domain"] = domain
        context["text_type"] = text_type
        context["user_wants_to_provide_its_own_data"] = user_wants_to_provide_its_own_data

        context["n_interactions"] = n_interactions + 1

        if user_approved == "approved":
            context["worker_done"] = True
            new_status = SessionStatus.HANDOFF
            out_messages = {}
        else:
            new_status = SessionStatus.WAIT_HUMAN
            out_messages = {
                "user": {"type": "text", "msg": response}
            }

        state = self.update_state(state, context, out_messages, new_status.value)
        return state



