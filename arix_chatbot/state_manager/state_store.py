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
        "type": msg_type,
        "msg": content
    }


class SessionStatus:
    HANDOFF = "HANDOFF"
    WAIT_HUMAN = "WAIT_HUMAN"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


@dataclass
class Action:
    agent_id: str
    action: str

    def todict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "action": self.action
        }



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
    chat_summary: str = None
    last_user_message: Optional[Dict[str, Any]] = None
    next_response: Optional[Dict[str, Any]] = None

    # GLOBAL CONTEXT
    global_context: Dict[str, Any] = field(default_factory=dict)

    # ASSIGNMENT DATA
    task_goal: Dict[str, Any] = field(default_factory=dict)
    input_data_description: str = None
    task_detailed_instructions: Dict[str, Any] = field(default_factory=dict)
    task_global_guidelines: Dict[str, Any] = field(default_factory=dict)
    task_author_notes: str = None

    # DATA SCHEMA
    input_data_schema: Dict[str, Any] = field(default_factory=dict)
    output_data_schema: Dict[str, Any] = field(default_factory=dict)

    # CHAT LOG
    chat_action_stack: List[Dict[str, Any]] = field(default_factory=list)

    # RESPONSE REQUESTS
    response_requests: List[str] = field(default_factory=list)

    # STATE DATA
    pipeline: List[str] = field(default_factory=list)
    agents_inbox: Dict[str, Any] = field(default_factory=dict)
    agents_context: Dict[str, Any] = field(default_factory=dict)
    user_outbox: List[Optional[dict]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    # METADATA
    user_info: Dict[str, Any] = field(default_factory=dict)
    session_info: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def report_action(self, action: Action) -> None:
        self.chat_action_stack.append(action.todict())

    def add_job(self, job: Job) -> None:
        job_id = str(job.job_id)
        job_status = job.status
        self.job_types[job_id] = job.job_type
        self.jobs[job_id] = job.to_dict()
        self.job_status[job_id] = job_status

    def get_job(self, job_id: str) -> Any:
        if job_id not in self.jobs:
            return None

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

    def get_status(self) -> str:
        return self.status

    def clear_before_turn(self) -> None:
        self.agents_inbox = {}
        self.agents_context = {}
        self.user_outbox = []
        self.chat_action_stack = []
        self.jobs = {}
        self.job_status = {}
        self.job_types = {}

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
