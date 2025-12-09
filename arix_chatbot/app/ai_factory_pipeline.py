from arix_chatbot.agents.agent_ids import AgentID
from arix_chatbot.state_manager.state_store import StateStore, SessionState, SessionStatus
from arix_chatbot.state_manager.sql_state_store import SqlStateStore
from arix_chatbot.app.agent_registry import AgentRegistry
from typing import Optional, Dict, Any
from datetime import datetime
import textwrap
import uuid


SQLITE_DB_URL = "/Users/omernagar/Documents/sqlite"


class AiFactoryPipeline:
    def __init__(self, agents_store: AgentRegistry = None, state_store: StateStore = None, root_agent: str = None) -> object:
        self.agent_registry = agents_store or AgentRegistry()
        # self.state_store = state_store or LangGraphStore(f"{SQLITE_DB_URL}/ai_factory_runs.db")
        self.state_store = state_store or SqlStateStore()
        self.active_runs = {}
        self._root_agent = root_agent

    async def start_run(self, user_input: str = '', initial_agent: str = None, run_id=None) -> SessionState:
        """Start a new run with an initial agent."""
        self._root_agent = initial_agent or self._root_agent

        if run_id:
            state = self.state_store.get_state(run_id)
            assert state is not None, f"Run ID {run_id} does not exist."
        else:
            run_id = str(uuid.uuid4())
            state = SessionState(
                run_id=run_id,
                pipeline=[self._root_agent],
                owner_agent_id=self._root_agent,
                agents_inbox={
                    self._root_agent: {
                        "user": [{
                            "type": "chat",
                            "msg": user_input}]}
                },
                timeline=[{
                    "timestamp": datetime.now().isoformat(),
                    "event": "started",
                    "agent_id": self._root_agent}]
            )

        # Process with initial agent
        state = await self.process_run(run_id, state)
        self.state_store.store_state(run_id, state)
        return state

    async def process_run(self, run_id: str, state) -> SessionState:
        """Process a run with the current owner agent."""

        # state.user_outbox = []
        if not state:
            raise ValueError(f"Run {run_id} not found")

        # print(f"Running - \nRun ID: {run_id} \nAgent ID: {state.owner_agent_id}")
        # print("====")

        owner_agent_id = state.owner_agent_id

        if not owner_agent_id:
            state.owner_agent_id = self._root_agent
            state.pipeline.append(self._root_agent)
            owner_agent_id = self._root_agent

        agent = self.agent_registry.get_agent(owner_agent_id)

        # Let agent handle the state
        state = await agent.handle(state)

        # Process agent response
        new_state = await self.process_agent_response(run_id, state)
        return new_state

    async def process_agent_response(self, run_id: str, state):
        """Process the response from an agent."""
        prev_owner = state.owner_agent_id

        # print(f"Processing response")
        if state.status == SessionStatus.HANDOFF:
            # print(f"HANDOFF to: {state.owner_agent_id}\n===")
            state.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "handoff",
                "from_agent": prev_owner,  # <- now correctly logs previous owner
                "to_agent": state.owner_agent_id,
            })

            # Continue processing with the new owner agent
            return await self.process_run(run_id, state)

        elif state.status == SessionStatus.WAIT_HUMAN:
            # print(f"WAIT_HUMAN\n===")
            state.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "ask_human",
                "agent_id": state.owner_agent_id
            })

        elif state.status == SessionStatus.COMPLETED:
            # print(f"COMPLETED\n===")
            state.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "completed",
                "agent_id": state.owner_agent_id
            })

        elif state.status == SessionStatus.ERROR:
            # print(f"ERROR\n===")
            state.error = state.error
            state.timeline.append({
                "timestamp": datetime.now().isoformat(),
                "event": "error",
                "agent_id": state.owner_agent_id,
                "error": state.error
            })

        return state

    async def inject_human_input(self, run_id: str, user_input: str) -> SessionState:
        """Inject human input into a waiting run."""
        state = self.state_store.get_state(run_id)
        state.turn_index += 1
        state.clear_before_turn()

        # Add human input to inbox
        owner_agent_id = state.owner_agent_id

        # If no owner, assign to root agent
        if not owner_agent_id:
            state.owner_agent_id = self._root_agent
            state.pipeline.append(self._root_agent)
            owner_agent_id = self._root_agent

        # send user input to the owner agent's inbox
        if owner_agent_id not in state.agents_inbox:
            state.agents_inbox[owner_agent_id] = {}

        state.agents_inbox[owner_agent_id] = {
            AgentID.user: [{
                "type": "chat",
                "msg": user_input
            }]}

        # Resume processing
        state.status = SessionStatus.HANDOFF
        state = await self.process_run(run_id, state)
        self.state_store.store_state(run_id, state)
        return state

    async def get_run_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a run."""
        return self.state_store.get_state(run_id)


def print_wrapped(text: str, width: int = 140, *, break_long_words: bool = False) -> None:
    """
    Print `text` wrapped to at most `width` chars per line.

    Args:
        text: The input text (can include multiple paragraphs).
        width: Max line length.
        break_long_words: If True, very long tokens (e.g., long URLs) may be split
                          to obey `width`. If False, such tokens can exceed width.
    """
    wrapper = textwrap.TextWrapper(
        width=width,
        break_long_words=break_long_words,
        break_on_hyphens=break_long_words,
        replace_whitespace=True,
        drop_whitespace=True,
    )

    # Preserve blank lines between paragraphs
    for para in text.splitlines():
        if para.strip() == "":
            print()  # blank line
        else:
            print(wrapper.fill(para))




