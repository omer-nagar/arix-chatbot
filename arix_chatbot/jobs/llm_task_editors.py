from __future__ import annotations
from arix_chatbot.jobs.job_ids import JobID
from typing import ClassVar, Optional, List
from dataclasses import dataclass
from arix_chatbot.jobs.job import Job, JOB_REGISTRY


@dataclass
class TaskEditorJob(Job):
    """
    Job representing the output handler step:
    responsible for generating / storing the final response to the user.
    """
    job_type: ClassVar[str] = JobID.TASK_EDITOR
    # Payload this job is about
    required_context: Optional[List] = None

