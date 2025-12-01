from __future__ import annotations
import json
import time
import uuid
from typing import Optional, Any, Dict
from datetime import datetime
from contextlib import contextmanager

# Assuming these types exist as in your snippet:
from arix_chatbot.state_manager.state_store import StateStore, SessionState

from sqlalchemy import (
    Table, Column, String, Integer, DateTime, JSON, MetaData,
    create_engine, select, insert, update, UniqueConstraint
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, DatabaseError


def _to_jsonable(obj: Any) -> Any:
    """
    Convert SessionState (or any object) to something json.dumps can handle.
    - If it has .dict(), use it (pydantic-like)
    - If it has __dict__, use that
    - If it's already a dict/list/primitive, leave it
    """
    try:
        if hasattr(obj, "dict") and callable(obj.dict):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return vars(obj)
    except Exception:
        pass
    return obj


def _serialize_state(state: SessionState) -> Dict[str, Any]:
    # Ensure we store a plain JSON structure
    try:
        return json.loads(json.dumps(_to_jsonable(state), default=str))
    except TypeError:
        # Fallback: stringify unknowns
        return json.loads(json.dumps(_to_jsonable(state), default=str))


def _infer_version_from_state(state: SessionState) -> int:
    # Try to track your semantic version from timeline length; fallback to 1
    try:
        v = getattr(state, "timeline", None)
        return int(len(v) if v is not None else 1)
    except Exception:
        return 1


class SqlStateStore(StateStore):
    """
    Durable state store independent of LangGraph.
    Maintains:
      - sessions(run_id, ns) -> last state snapshot + version + metadata
      - checkpoints(id, run_id, ns, version, ts, state, metadata)
    Works with Postgres or SQLite.
    """

    def __init__(self, conn_string: str = "sqlite:///ai_factory_sessions.db"):
        if not conn_string:
            raise ValueError("Connection string cannot be empty")

        self.engine: Engine = create_engine(conn_string, future=True)

        # SQLite durability tuning (safe defaults)
        if conn_string.startswith("sqlite"):
            with self.engine.begin() as conn:
                conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
                conn.exec_driver_sql("PRAGMA synchronous=FULL;")
                conn.exec_driver_sql("PRAGMA foreign_keys=ON;")

        self.meta = MetaData()

        # Latest snapshot per (ns, run_id)
        self.sessions = Table(
            "sessions",
            self.meta,
            Column("ns", String(64), nullable=False),
            Column("run_id", String(128), nullable=False),
            Column("version", Integer, nullable=False),
            Column("updated_at", DateTime, nullable=False),
            Column("state", JSON, nullable=False),
            Column("metadata", JSON, nullable=False),
            UniqueConstraint("ns", "run_id", name="uq_sessions_ns_run"),
        )

        # Append-only log for history/restore
        self.checkpoints = Table(
            "checkpoints",
            self.meta,
            Column("id", String(64), primary_key=True),
            Column("ns", String(64), nullable=False, index=True),
            Column("run_id", String(128), nullable=False, index=True),
            Column("version", Integer, nullable=False, index=True),
            Column("ts", DateTime, nullable=False),
            Column("state", JSON, nullable=False),
            Column("metadata", JSON, nullable=False),
        )

        self.meta.create_all(self.engine)

    @contextmanager
    def _tx(self):
        """
        Context manager that opens a transaction.
        For SQLite we explicitly do BEGIN IMMEDIATE to reduce writer races.
        """
        with self.engine.begin() as conn:
            if str(self.engine.url).startswith("sqlite"):
                conn.exec_driver_sql("BEGIN IMMEDIATE;")
            yield conn

    def _retryable(self, fn, *, retries: int = 5, base_sleep: float = 0.08):
        """
        Retry transient errors (locks, deadlocks).
        """
        for attempt in range(retries):
            try:
                return fn()
            except (OperationalError, DatabaseError) as e:
                # Common transient patterns across drivers
                msg = str(e).lower()
                transient = any(
                    k in msg
                    for k in [
                        "deadlock", "could not serialize", "locked", "timeout", "busy"
                    ]
                )
                if attempt < retries - 1 and transient:
                    time.sleep(base_sleep * (2 ** attempt))
                    continue
                raise

    # ---- Public API -----------------------------------------------------

    def get_state(self, run_id: str, *, ns: str = "sessions") -> Optional[SessionState]:
        """
        Returns the latest stored state or None.
        """
        def _read():
            with self._tx() as conn:
                row = conn.execute(
                    select(self.sessions.c.state)
                    .where(
                        (self.sessions.c.ns == ns) &
                        (self.sessions.c.run_id == run_id)
                    )
                ).fetchone()
                if not row:
                    return None
                data = row[0]
                # If your SessionState is a pydantic/dataclass, reconstruct here if desired.
                # For now, we return the raw dict (or you can plug in a converter).
                return data  # type: ignore[return-value]

        return SessionState.fromdict(self._retryable(_read))

    def store_state(self, run_id: str, state: SessionState, *, ns: str = "sessions"):
        """
        Atomically write:
          - Upsert latest snapshot in sessions
          - Append a checkpoint row
        No sleeps; durability is ensured by COMMIT.
        """
        state_json = _serialize_state(state)
        version = _infer_version_from_state(state)
        ts = datetime.utcnow()

        # Build metadata: keep yours minimal but extendable
        metadata = {
            "status": state_json.get("status"),
            "owner_agent_id": state_json.get("owner_agent_id"),
            "pipeline": ",".join(state_json.get("pipeline", []) or []),
        }

        checkpoint_id = str(uuid.uuid4())

        def _write():
            with self._tx() as conn:
                # Upsert sessions (portable pattern)
                existing = conn.execute(
                    select(self.sessions.c.version)
                    .where((self.sessions.c.ns == ns) & (self.sessions.c.run_id == run_id))
                    .with_for_update(nowait=False, of=self.sessions)  # lock row if exists
                ).fetchone()

                if existing:
                    conn.execute(
                        update(self.sessions)
                        .where((self.sessions.c.ns == ns) & (self.sessions.c.run_id == run_id))
                        .values(
                            version=version,
                            updated_at=ts,
                            state=state_json,
                            metadata=metadata,
                        )
                    )
                else:
                    conn.execute(
                        insert(self.sessions).values(
                            ns=ns,
                            run_id=run_id,
                            version=version,
                            updated_at=ts,
                            state=state_json,
                            metadata=metadata,
                        )
                    )

                conn.execute(
                    insert(self.checkpoints).values(
                        id=checkpoint_id,
                        ns=ns,
                        run_id=run_id,
                        version=version,
                        ts=ts,
                        state=state_json,
                        metadata=metadata,
                    )
                )

        self._retryable(_write)

    # Optional: fetch specific checkpoint or history
    def get_history(self, run_id: str, *, ns: str = "sessions", limit: int = 50):
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(
                    self.checkpoints.c.id,
                    self.checkpoints.c.version,
                    self.checkpoints.c.ts,
                    self.checkpoints.c.state,
                    self.checkpoints.c.metadata,
                )
                .where((self.checkpoints.c.ns == ns) & (self.checkpoints.c.run_id == run_id))
                .order_by(self.checkpoints.c.version.desc())
                .limit(limit)
            ).fetchall()
            return [dict(r._mapping) for r in rows]
