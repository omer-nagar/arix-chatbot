from __future__ import annotations
from arix_chatbot.jobs.job_ids import JobID
from typing import ClassVar, Optional, List
from dataclasses import dataclass
from arix_chatbot.jobs.job import Job, JOB_REGISTRY


@dataclass
class UserIntentRouterJob(Job):
    """
    Job representing the output handler step:
    responsible for generating / storing the final response to the user.
    """
    job_type: ClassVar[str] = JobID.USER_INTENT
    # Payload this job is about
    user_followup_jobs: Optional[List] = None


@dataclass
class OutputHandlerJob(Job):
    """
    Job representing the output handler step:
    responsible for generating / storing the final response to the user.
    """
    job_type: ClassVar[str] = JobID.OUTPUT_HANDLER
    # Payload this job is about
    response_to_user: Optional[str] = None

