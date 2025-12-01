from arix_chat.agents.legacy.intent_router.constants import GREETINGS
from arix_chat.agents.legacy.intent_router.intent_router_agent import chat_inquire_general_classification_task_definition
from arix_chat.state_manager.state_store import SessionState, SessionStatus
from arix_chat.agents.base.worker import Worker


class IntentRouter(Worker):
    def __init__(self, agent_id: str = "intentRouter", manager_id: str = "navigator"):
        super().__init__(agent_id, manager_id)

    def init_context(self, state: SessionState) -> dict:
        context = {
            # History of the conversation
            "latest_assistant_question": "none",
            "conversation_history": "no-history",

            # Task details
            "task_definition": "not provided",
            "data_type": "not provided",
            "classes": "not provided",

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

        latest_assistant_question = context["latest_assistant_question"]
        conversation_history = context["conversation_history"]
        task_definition = context["task_definition"]
        data_type = context["data_type"]
        classes = context["classes"]
        n_interactions = context["n_interactions"]

        if n_interactions == 0:
            # first interaction - send greeting
            respond_to_user = GREETINGS
            new_status = SessionStatus.WAIT_HUMAN

            context["latest_assistant_question"] = respond_to_user
            context["n_interactions"] = n_interactions + 1
            out_messages = {
                "user": {"type": "text", "msg": respond_to_user}
            }
            return self.update_state(state, context, out_messages, new_status.value)

        user_response = inbox.get("user", [{"msg": "great, whats next?"}])[-1]["msg"]

        response, data_type, task_definition, classes, conversation_history, user_approved = (
            chat_inquire_general_classification_task_definition(
                task_definition=task_definition,
                data_type=data_type,
                classes=classes,
                latest_assistant_question=latest_assistant_question,
                conversation_history=conversation_history,
                latest_user_response=user_response
            ))

        response = response.strip() if response.strip() != "" else "ops, missed your response"
        context["latest_assistant_question"] = response
        context["conversation_history"] = conversation_history

        context["data_type"] = data_type
        context["task_definition"] = task_definition
        context["classes"] = classes

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



