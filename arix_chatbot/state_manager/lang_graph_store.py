from arix_chatbot.state_manager.state_store import StateStore, SessionState
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import Optional, Dict, Any
from datetime import datetime
from time import sleep
import uuid


class LangGraphStore(StateStore):
    """
    Persists your free-form dict state inside LangGraph's checkpoint store.
    Each run_id maps to a thread; the entire pipeline state lives under one key.
    """
    def __init__(self, conn_string: str = "sqlite:///ai_factory_sessions.db"):
        if not conn_string:
            raise ValueError("Connection string cannot be empty")
        try:
            # Context manager is fine; we "enter" once and keep the saver.
            self._ctx = SqliteSaver.from_conn_string(conn_string)
            self.checkpoint = self._ctx.__enter__()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize database: {e}")

    def make_config(self, run_id: str, ns: str = "sessions"):
        return {
            "configurable": {
                "checkpoint_ns": ns,
                "thread_id": run_id,
            }
        }

    def make_checkpoint(self, state: SessionState, *, checkpoint_id: str | None = None, version: int | None = None):
        """
        Build a LangGraph-style checkpoint object.
        """
        v = version if version is not None else (len(state.timeline) or 1)
        return {
            "id": checkpoint_id or str(uuid.uuid4()),   # REQUIRED
            "v": int(v),                                # REQUIRED (version int)
            "ts": datetime.utcnow().isoformat(),
            "channel_values": state,
            "pending_writes": {},
            # "parent": prev_id,                        # OPTIONAL (chaining)
        }

    def make_metadata(self, state: SessionState):
        return {
            "status": state.status,
            "owner_agent_id": state.owner_agent_id,
            "pipeline": ",".join(state.pipeline),
        }

    def make_new_versions(self, state: SessionState):
        return {
            "timeline": len(state.timeline),
        }

    def _put(self, config, checkpoint, metadata, new_versions):
        """
        Compatibility wrapper: use .atomic() if present, otherwise call put() directly.
        """
        atomic = getattr(self.checkpoint, "atomic", None)
        if callable(atomic):
            with atomic() as txn:
                return txn.put(config, checkpoint, metadata, new_versions)
        else:
            return self.checkpoint.put(config, checkpoint, metadata, new_versions)

    def get_state(self, run_id: str) -> Optional[SessionState]:
        snap = self.checkpoint.get(self.make_config(run_id))
        if snap is None:
            return None
        return snap['channel_values']

    def store_state(self, run_id: str, state: SessionState, *, ns: str = "sessions"):
        config = self.make_config(run_id, ns=ns)
        # Use a fresh checkpoint id per write to avoid unique-id collisions
        checkpoint = self.make_checkpoint(state)
        metadata = self.make_metadata(state)
        new_versions = self.make_new_versions(state)

        try:
            self._put(config, checkpoint, metadata, new_versions)
            # TODO: Check how to wait for sql to write ?
            sleep(1)
        except Exception as e:
            raise RuntimeError(f"Failed to store state for run {run_id}: {e}")

    def append_inbox(self, run_id: str, agent_id: str, msg: Dict[str, Any]) -> None:
        state = self.get_state(run_id) or {}
        inbox = state.setdefault("inbox", {})
        inbox.setdefault(agent_id, []).append(msg)
        self.store_state(run_id, state)

    def append_timeline(self, run_id: str, event: Dict[str, Any]) -> None:
        state = self.get_state(run_id) or {}
        state.setdefault("timeline", []).append({
            "timestamp": datetime.now().isoformat(), **event
        })
        self.store_state(run_id, state)
