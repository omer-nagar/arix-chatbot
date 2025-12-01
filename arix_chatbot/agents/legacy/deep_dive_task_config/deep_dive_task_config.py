from arix_chat.agents.legacy.deep_dive_task_config.data_collection_aget import generate_task_config
from arix_chat.state_manager.state_store import SessionState, SessionStatus
from arix_chat.agents.base.worker import Worker
import json


def render_labeling_spec_md(spec: dict) -> str:
    md = []

    # HEADER
    md.append(f"# Task: {spec.get('task_name','')}\n")

    # Task definition
    md.append("## Task Definition")
    md.append(spec.get("detailed_task_definition","") + "\n")

    # Classes
    class_criteria = spec.get("class_criteria", [])
    if class_criteria:
        md.append("## Class Definitions\n")
        for cls in class_criteria:
            md.append(f"### **{cls['name']}**")
            md.append(f"_Definition_: {cls.get('definition','')}\n")

            if cls.get("policies"):
                md.append("**Policies:**")
                for p in cls["policies"]:
                    md.append(f"- {p}")
                md.append("")

    # Global Guidelines
    global_guidelines = spec.get("global_guidelines", [])
    if global_guidelines:
        md.append("## Global Guidelines\n")
        for g in global_guidelines:
            md.append(f"- {g}")

    return "\n".join(md)


class DeepDiveTaskConfig(Worker):
    def __init__(self, agent_id: str = "deepDiveTaskConfig", manager_id: str = "main_navigator"):
        super().__init__(agent_id, manager_id)

    def init_context(self, state: SessionState) -> dict:
        inbox = self.get_inbox(state)
        task_definition = json.dumps(inbox.get('main_navigator', {'task_definition': 'not provided'})['task_definition'])
        conversation_history = inbox.get('main_navigator', {'conversation_history': ''})['conversation_history']
        conversation_history = f"#User wants to generate a model:\n{task_definition}\n\n---\n{conversation_history}"

        context = {
            # History of the conversation
            "latest_assistant_response": "none",
            "conversation_history": conversation_history,

            # Task details
            "task_name": None,
            "detailed_task_definition": None,
            "class_criteria": None,
            "global_guidelines": None,

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

        n_interactions = context["n_interactions"]
        latest_assistant_response = context["latest_assistant_response"]
        conversation_history = context["conversation_history"]

        task_name = context["task_name"]
        detailed_task_definition = context["detailed_task_definition"]
        class_criteria = context["class_criteria"]
        global_guidelines = context["global_guidelines"]
        data_collection_state = {
            "task_name": task_name,
            "detailed_task_definition": detailed_task_definition,
            "class_criteria": class_criteria,
            "global_guidelines": global_guidelines
        }

        user_response = inbox.get("user", [{"msg": "Great, Whats next?"}])[-1]["msg"]
        user_approved, response, data_collection_state, referenced_fields = generate_task_config(
            data_collection_state=data_collection_state,
            conversation_history=conversation_history,
            latest_assistant_response=latest_assistant_response,
            user_message=user_response,
            init=n_interactions == 0
        )

        response = response.strip() if response.strip() != "" else "ops, missed your response"
        context["latest_assistant_question"] = response
        context["conversation_history"] = conversation_history

        context["task_name"] = data_collection_state.get("task_name", task_name)
        context["detailed_task_definition"] = data_collection_state.get("detailed_task_definition", detailed_task_definition)
        context["class_criteria"] = data_collection_state.get("class_criteria", class_criteria)
        context["global_guidelines"] = data_collection_state.get("global_guidelines", global_guidelines)
        context["n_interactions"] = n_interactions + 1

        if user_approved == "approved":
            context["worker_done"] = True
            new_status = SessionStatus.HANDOFF
            out_messages = {}
        else:
            new_status = SessionStatus.WAIT_HUMAN
            current_spec = f"\n---\n{render_labeling_spec_md(data_collection_state)}\n---\n"
            out_messages = {
                "user": {"type": "text", "msg": f"{current_spec}{response}"}
            }

        state = self.update_state(state, context, out_messages, new_status.value)
        return state



