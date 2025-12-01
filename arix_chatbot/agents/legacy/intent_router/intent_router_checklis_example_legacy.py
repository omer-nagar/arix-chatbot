from arix_chat.agents.legacy.intent_router.constants import GREETINGS
from arix_chat.state_manager.state_store import SessionState, SessionStatus
from arix_chat.agents.legacy.utils.checklist import Checklist, TaskStatus
from arix_chat.agents.base.worker import Worker
from typing import Tuple, Union, Dict
from typing import Protocol


class TaskExecution(Protocol):
    def __call__(self, inbox: dict, checkpoint: dict) -> Tuple[TaskStatus, dict, dict]: ...


class IntentRouter(Worker):
    def __init__(self, agent_id: str = "intentRouter", manager_id: str = "navigator"):
        super().__init__(agent_id, manager_id)
        # ordered dict
        self._task_mapper: Dict[str, TaskExecution] = {
            "input_type": self._handle_input_type,
            "task_description": self._handle_task_description,
            # "number_of_classes": self._handle_number_of_classes,
            # "class_names": self._handle_class_names
        }

    def fallback_task(self, inbox, checkpoint) -> Tuple[TaskStatus, dict, dict]:
        user_outbox = {
            "type": "chat",
            "msg": GREETINGS
        }

        task_status = TaskStatus.WAIT_HUMAN
        outbox = {
            "user": [user_outbox]
        }
        return task_status, checkpoint, outbox

    def _handle_input_type(self, inbox, checkpoint) -> Tuple[TaskStatus, dict, dict]:
        user_outbox = {
            "type": "chat",
            "msg": "Welcome to AI Factory"
        }

        task_status = TaskStatus.WAIT_HUMAN
        outbox = {
            "user": [user_outbox]
        }
        return task_status, checkpoint, outbox

    def _handle_task_description(self, inbox, checkpoint) -> Tuple[TaskStatus, dict, dict]:
        pass

    def init_context(self, state: SessionState) -> dict:
        context = {
            "checklist": Checklist([
                "input_type",
                "task_description",
                "number_of_classes",
                "class_names"
            ]).todict(),
            "checkpoint": {}
        }
        return context

    def update_state(self, state: SessionState, context: dict, outbox: dict, new_worker_status: str) -> SessionState:
        # Update status
        state.status = new_worker_status

        # Update context
        state.agents_context[self.agent_id] = context

        # Update outbox
        for dest, msgs in outbox.items():
            if dest == "user":
                state.user_outbox.extend(msgs)
                continue
            state.agents_inbox[dest] = state.agents_inbox.get(dest, []) + msgs
        return state

    def get_worker_status(self, checklist):
        if checklist.all_completed():
            return SessionStatus.HANDOFF.value

        if checklist.is_errors():
            return SessionStatus.ERROR.value

        if checklist.is_waiting_human():
            return SessionStatus.WAIT_HUMAN.value

        return SessionStatus.HANDOFF.value

    def get_next_task(self, checklist: Checklist) -> Union[str, None]:
        # Prioritize
        #  1. WAIT_HUMAN
        #  2. IN_PROGRESS
        #  3. TODO_

        if checklist.all_completed():
            return None

        if checklist.is_errors():
            return None

        for task_id, task_status in checklist:
            if task_status == TaskStatus.WAIT_HUMAN:
                return task_id

        for task_id, task_status in checklist:
            if task_status in [TaskStatus.IN_PROGRESS]:
                return task_id

        for task_id, task_status in checklist:
            if task_status in [TaskStatus.TODO]:
                return task_id

        return None

    async def process_task(self, state: SessionState) -> SessionState:
        # Implement the logic to process the task and return an AgentPayload

        # Get inbox and context
        inbox = self.get_inbox(state)
        context = self.get_context(state)
        checklist = Checklist.fromdict(context["checklist"])
        task_id = self.get_next_task(checklist)


        if task_id is None:
            new_state = self.update_state(state, context, {}, SessionStatus.ERROR.value)
            new_state.error = f"in process_task agent_id: <{self.agent_id}>: no tasks left to do"

        cp = context["checkpoint"].get(task_id, {})
        task_inbox = inbox.get(task_id, {})

        task_func = self._task_mapper.get(task_id, self.fallback_task)
        task_status, cp, outbox = task_func(inbox=task_inbox, checkpoint=cp)
        checklist.set_status(task_id, task_status)
        context["checklist"] = checklist.todict()

        new_worker_status = self.get_worker_status(checklist)
        new_state = self.update_state(state, context, outbox, new_worker_status)
        return new_state



