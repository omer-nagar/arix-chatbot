from arix_chatbot.agents.agent_ids import AgentID
from arix_chatbot.jobs.job import Job, JobStatus
from arix_chatbot.state_manager.state_store import SessionState, SessionStatus
from typing import Dict, Any, Optional
from abc import ABC
import asyncio
import logging


class BaseAgent(ABC):
    """Base interface for all agents."""
    agent_id: str = "base_agent"

    def __init__(self, timeout_seconds: Optional[int] = None):
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(f"agent.{self.agent_id}")

    def set_manager(self, manager_id: str) -> None:
        self.manager_id = manager_id

    def log_action_to_chat_log(self, state, action: str) -> None:
        state.add_to_chat_log({
            "agent_id": self.agent_id,
            "action": action
        })

    def get_jobs(self, state: SessionState, role: str) -> Any:
        """
        role = "execute"|"manage"
        :param state:
        :param role:
        :return:
        """
        open_jobs = state.get_open_jobs()
        if role == "managed":
            todos = [job for job in open_jobs if job.report_to == self.agent_id]
        elif role == "execute":
            todos = [job for job in open_jobs if job.worker_id == self.agent_id]
        else:
            raise ValueError(f"Invalid role '{role}' for get_jobs")
        return todos

    def get_last_pending_job(self, state: SessionState) -> Job or None:
        jobs_todo = self.get_jobs(state, role="execute")
        jobs_todo = [job for job in jobs_todo if job.status not in [JobStatus.SUCCESS, JobStatus.FAILED]]
        if len(jobs_todo) == 0:
            return None
        else:
            job = jobs_todo[-1]
            return job

    def get_inbox(self, state: SessionState, clear=False) -> Dict:
        inbox = state.agents_inbox.get(self.agent_id, {})
        if clear:
            self.clear_inbox(state)
        return inbox

    def clear_inbox(self, state: SessionState) -> None:
        state.agents_inbox[self.agent_id] = []

    def send_message(self, state: SessionState, recipient: str, msg: Dict, mode="overwrite", sender=None) -> None:
        """
        Send a message to another agent's inbox.
        :param state: The current session state.
        :param recipient: The recipient agent ID or "user".
        :param msg: The message to send
        :param mode: "overwrite"|"append" - whether to overwrite or append to existing messages.
        """
        if recipient == AgentID.user:
            assert "type" in msg and "msg" in msg, "User message must contain 'type' and 'msg' fields"
            msg["from"] = self.agent_id if sender is None else sender

            if state.user_outbox is not None and len(state.user_outbox) != 0 and mode == "overwrite":
                # raise warning - previous message will be overwritten
                self.logger.warning("Overwriting existing user outbox message")

            if mode == "append" and state.user_outbox:
                # append to existing user outbox message
                state.user_outbox.append(msg)
            elif (mode == "append" and not state.user_outbox) or mode == "overwrite":
                state.user_outbox = [msg]
            else:
                raise ValueError(f"Invalid mode '{mode}' for send_message to user")
            return

        # recipient is another agent
        recipient_inbox = state.agents_inbox.get(recipient, {})
        if mode == "overwrite":
            recipient_inbox[self.agent_id if sender is None else sender] = msg
        elif mode == "append":
            # get existing messages from current agent to recipient agent
            agent_to_recipient = recipient_inbox.get(self.agent_id, {})
            agent_to_recipient.update(msg)

            # from current agent to recipient agent
            recipient_inbox[self.agent_id if sender is None else sender] = agent_to_recipient
        else:
            raise ValueError(f"Invalid mode '{mode}' for send_message")
        state.agents_inbox[recipient] = recipient_inbox

    def init_context(self, state: SessionState) -> Dict:
        context = {}
        return context

    def get_context(self, state: SessionState) -> Dict:
        """Extract context from the inbox messages."""
        # Implement context extraction logic based on your message structure
        context = state.agents_context.get(self.agent_id, {})
        if not context:
            return self.init_context(state)
        return context

    def update_state_context(self, state: SessionState, context: Dict) -> None:
        state.agents_context[self.agent_id] = context

    async def handle(self, state: SessionState) -> SessionState:
        """Main handler method - must be implemented by all agents."""
        pass

    async def handle_with_timeout(self, state: SessionState) -> SessionState:
        """Wrapper that adds timeout handling to the handle method."""
        if self.timeout_seconds is None:
            # No timeout specified, call handle directly
            return await self.handle(state)

        try:
            # Use asyncio.wait_for to implement timeout
            result = await asyncio.wait_for(
                self.handle(state),
                timeout=self.timeout_seconds
            )
            return result

        except asyncio.TimeoutError:
            self.logger.warning(f"Agent {self.agent_id} timed out after {self.timeout_seconds} seconds")
            state.status = SessionStatus.ERROR.value
            state.error_message = f"Agent {self.agent_id} timed out after {self.timeout_seconds} seconds"
            return state

        except Exception as e:
            self.logger.error(f"Agent {self.agent_id} encountered an error: {str(e)}")
            state.status = SessionStatus.ERROR.value
            state.error_message = f"Agent {self.agent_id} error: {str(e)}"
            return state