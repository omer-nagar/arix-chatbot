from __future__ import annotations
from typing import Any, Dict, Mapping, Type, TypeVar, ClassVar, Optional, List

from arix_chatbot.jobs import JOB_REGISTRY
from arix_chatbot.jobs.job_ids import JobID
from dataclasses import dataclass, fields
from abc import ABC


class JobStatus:
    PENDING = "PENDING"
    ASSIGNED_TO_AGENT = "ASSIGNED_TO_AGENT"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


TJob = TypeVar("TJob", bound="Job")



@dataclass
class Job(ABC):
    # Mandatory fields for all jobs
    job_id: str
    report_to: str
    worker_id: str
    status: JobStatus
    turn_index: int
    content: Optional[str] = None
    required_context: Optional[List] = None

    # Each subclass should override this
    job_type: ClassVar[str] = JobID.BASE

    @classmethod
    def from_dict(cls: Type[TJob], data: Mapping[str, Any]) -> TJob:
        """
        - Job.from_dict: factory, uses 'job_type' + JOB_REGISTRY.
        - Subclass.from_dict: constructs that subclass directly.

        Behavior:
        - Ignores unknown keys.
        - Requires 'job_id', 'agent_id', and 'status'.
        - Coerces status string -> JobStatus.
        """
        # ---------- Factory mode: Job.from_dict(...) ----------
        job_type = data.get("job_type")
        if not job_type:
            raise ValueError("Missing 'job_type' for Job.from_dict")

        concrete_cls = JOB_REGISTRY.get(job_type)
        if concrete_cls is None:
            raise ValueError(f"Unknown job_type {job_type!r}")

        # ---------- Direct subclass mode: .from_dict(...) ----------
        field_names = {f.name for f in fields(cls)}

        init_kwargs: Dict[str, Any] = {
            key: value for key, value in data.items() if key in field_names
        }

        required_fields = {"job_id", "report_to", "worker_id", "status", "turn_index"}
        missing = required_fields - init_kwargs.keys()
        if missing:
            raise ValueError(
                f"Missing required field(s) {missing} for {cls.__name__}: {missing}"
            )

        # Coerce string → JobStatus if needed
        status_value = init_kwargs["status"]
        if not isinstance(status_value, JobStatus):
            init_kwargs["status"] = status_value

        return concrete_cls(**init_kwargs)  # type: ignore[arg-type]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Job (or subclass) to a plain dict.

        - Dataclass fields only.
        - Enum values are converted to their .value.
        - Adds 'job_type' for reconstruction via Job.from_dict.
        """
        out: Dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            out[f.name] = value

        out["job_type"] = self.job_type
        return out