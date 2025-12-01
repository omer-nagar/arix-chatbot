from typing import Optional, Dict, Any, List, Protocol
from dataclasses import dataclass, asdict, field
from arix_chatbot.jobs.job import Job
from arix_chatbot.jobs import JOB_REGISTRY


class MessageType:
    CHAT = "CHAT"
    LLM_RESPONSE_CONFIG = "LLM_RESPONSE_CONFIG"
    LLM_PROMPT = "LLM_PROMPT"
    LLM_QUERY_TEMPLATE = "LLM_QUERY_TEMPLATE"


def compose_message(msg_type: MessageType, content: Any) -> Dict[str, Any]:
    return {
        "type": msg_type.value,
        "content": content
    }


class SessionStatus:
    HANDOFF = "HANDOFF"
    WAIT_HUMAN = "WAIT_HUMAN"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


@dataclass
class SessionState:
    # STATE BASIC INFO
    run_id: str
    owner_agent_id: str
    status: str = SessionStatus.HANDOFF
    pending_handoff: List[str] = field(default_factory=list)

    # JOBS INFO
    job_status: Dict[str, str] = field(default_factory=dict)
    job_types: Dict[str, str] = field(default_factory=dict)
    jobs: Dict[str, Dict] = field(default_factory=dict)

    # CHAT HISTORY
    turn_index: int = 0
    chat_full_history: List[Dict[str, Any]] = field(default_factory=list)
    chat_summary: str = ""
    last_user_message: Optional[Dict[str, Any]] = None
    next_response: Optional[Dict[str, Any]] = None

    # GLOBAL CONTEXT
    global_context: Dict[str, Any] = field(default_factory=dict)

    # STATE DATA
    pipeline: List[str] = field(default_factory=list)
    agents_inbox: Dict[str, Any] = field(default_factory=dict)
    agents_context: Dict[str, Any] = field(default_factory=dict)
    user_outbox: List[Optional[dict]] = field(default_factory=list)
    chat_turn_log: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    # METADATA
    user_info: Dict[str, Any] = field(default_factory=dict)
    session_info: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def add_to_chat_log(self, action: Dict[str, Any]) -> None:
        action['turn_index'] = self.turn_index
        self.chat_turn_log.append(action)

    def add_job(self, job: Job) -> None:
        job_id = str(job.job_id)
        job_status = job.status
        self.job_types[job_id] = job.job_type
        self.jobs[job_id] = job.to_dict()
        self.job_status[job_id] = job_status

    def get_job(self, job_id: str) -> Any:
        cls = JOB_REGISTRY.get(self.job_types.get(str(job_id)))
        job = cls.from_dict(self.jobs.get(job_id)) if job_id in self.jobs else None
        if job.turn_index != self.turn_index:
            return None
        return job

    def clear_old_jobs(self) -> None:
        current_index = self.turn_index
        jobs_to_remove = []
        for job_id, job_data in self.jobs.items():
            job_turn_index = job_data.get('turn_index', -1)
            if job_turn_index != current_index:
                jobs_to_remove.append(job_id)
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            del self.job_status[job_id]

    def get_open_jobs(self) -> List[Job]:
        self.clear_old_jobs()

        open_jobs = []
        for job_id, status in self.job_status.items():
            if status not in [SessionStatus.COMPLETED, SessionStatus.ERROR]:
                job = self.get_job(job_id)
                if job:
                    open_jobs.append(job)
        return open_jobs

    def set_job_status(self, job_id: str, status: str) -> None:
        job = self.get_job(job_id)
        if job:
            job.status = status
            self.add_job(job)

    def update_job(self, job_id: str, **kwargs) -> None:
        job = self.get_job(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            self.add_job(job)

    def set_status(self, new_status: str) -> None:
        self.status = new_status

    def get_status(self) -> SessionStatus:
        return self.status

    def todict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def fromdict(data: Dict[str, Any]) -> 'SessionState':
        return SessionState(**data)


class StateStore(Protocol):
    def get_state(self, run_id: str) -> Optional[SessionState]: ...
    def store_state(self, run_id: str, state: SessionState) -> None: ...
    def append_inbox(self, run_id: str, agent_id: str, msg: Dict[str, Any]) -> None: ...
    def append_timeline(self, run_id: str, event: Dict[str, Any]) -> None: ...
    def delete_state(self, run_id: str) -> bool: ...
