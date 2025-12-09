from __future__ import annotations
from arix_chatbot.jobs.job_ids import JobID
from typing import ClassVar, Optional, List
from dataclasses import dataclass
from arix_chatbot.jobs.job import Job


@dataclass
class PlanWorkflowJob(Job):
    """
    Job representing the output handler step:
    responsible for generating / storing the final response to the user.
    """
    job_type: ClassVar[str] = JobID.PLAN_A_WORKFLOW
    # Payload this job is about
    user_intention: Optional[str] = None
    workflow: Optional[List] = None


@dataclass
class CreateResponseJob(Job):
    """
    Job representing the output handler step:
    responsible for generating / storing the final response to the user.
    """
    job_type: ClassVar[str] = JobID.CREATE_RESPONSE
    # Payload this job is about
    response_to_user: Optional[str] = None

