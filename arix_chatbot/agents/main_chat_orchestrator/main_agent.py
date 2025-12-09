from arix_chatbot.state_manager.state_store import SessionState, SessionStatus, MessageType, compose_message
from arix_chatbot.jobs.user_interactions import PlanWorkflowJob
from arix_chatbot.agents.utils.checklist import Checklist
from arix_chatbot.agents.base.navigator import Navigator
from arix_chatbot.agents.agent_ids import AgentID as aid
from arix_chatbot.jobs.job import JobStatus, Job
from typing import List, Tuple, Union, Dict
import uuid


class MainChatOrchestrator(Navigator):
    """Navigator agent that manages the workflow of other agents."""
    agent_id: str = aid.MAIN

    def __init__(self, managed_agents: List[str] = None):
        self._plan_workflow_step = "plan_workflow"
        self._launch_workflow_step = "launch_workflow"
        self._update_history_step = "update_history"
        self._work_mapper = {
            "generate_response": {"agent_id": aid.OUTPUT_HANDLER, "job": Job},
            "compose_full_task_and_config": {"agent_id": aid.LLM_TASK_INITIALIZER, "job": Job},
            "edit_input_data_description": {"agent_id": aid.INPUT_DATA_EDITOR, "job": Job},
            "edit_main_goal": {"agent_id": aid.TASK_GOAL_EDITOR, "job": Job},
            "edit_detailed_task_instructions": {"agent_id": aid.TASK_DETAILED_INSTRUCTIONS_EDITOR, "job": Job},
            "edit_global_guidelines": {"agent_id": aid.TASK_GLOBAL_GUIDELINES_EDITOR, "job": Job},
            "edit_author_note": {"agent_id": aid.TASK_AUTHOR_NOTES_EDITOR, "job": Job},
            "edit_input_schema": {"agent_id": aid.INPUT_SCHEMA_EDITOR, "job": Job},
            "edit_output_schema": {"agent_id": aid.OUTPUT_SCHEMA_EDITOR, "job": Job},
        }

        self._pipeline_stages = [
            self._plan_workflow_step,
            self._launch_workflow_step,
            self._update_history_step
        ]
        super().__init__(managed_agents=managed_agents)

    def crate_generate_response_job(self):
        pass

    def init_context(self, state: SessionState) -> Dict:
        return {
            "flow_planner_job_id": str(uuid.uuid4()),
            "checklist": Checklist(tasks=self._pipeline_stages).todict()
        }

    def is_first_entry(self, state: SessionState, context: Dict) -> bool:
        """Check if this is the first entry point of the conversation."""
        checklist = Checklist.fromdict(context["checklist"])
        return state.turn_index == 0 and not checklist.is_done(self._plan_workflow_step)

    def generate_hello_message(self, state: SessionState, context: Dict) -> Tuple[SessionState, List[str]]:
        """Handle the first entry point of the conversation."""
        # nothing to do, just send hello
        checklist = Checklist.fromdict(context["checklist"])
        # nothing to do yet - mark all steps as done
        checklist.set_done(self._plan_workflow_step)
        checklist.set_done(self._launch_workflow_step)
        checklist.set_done(self._update_history_step)

        self.update_context(state, context, checklist=checklist.todict())
        return state, [aid.OUTPUT_HANDLER]

    def plan_workflow(self, state: SessionState, context: Dict) -> Tuple[SessionState, List[str]]:
        """Process new user input and update state accordingly."""
        # add user message to state
        inbox = self.get_inbox(state, clear=True)

        user_message = inbox[aid.user]
        state.last_user_message = user_message[-1]
        state.add_job(PlanWorkflowJob(
            job_id=context["flow_planner_job_id"],
            report_to=self.agent_id,
            worker_id=aid.PLANNER,
            status=JobStatus.ASSIGNED_TO_AGENT,
            turn_index=state.turn_index
        ))

        checklist = Checklist.fromdict(context["checklist"])
        checklist.set_done(self._plan_workflow_step)
        self.update_context(state, context, checklist=checklist.todict())
        return state, [aid.PLANNER]

    def launch_workflow(self, state: SessionState, context: Dict) -> Tuple[SessionState, List[str]]:
        flow_job: PlanWorkflowJob = state.get_job(context["flow_planner_job_id"])
        checklist = Checklist.fromdict(context["checklist"])

        assigned_jobs = []
        next_agents = []
        if flow_job is not None and flow_job.workflow is not None and len(flow_job.workflow) > 0:
            # Assign jobs based on the planned workflow
            for work_to_do in flow_job.workflow:
                try:
                    work_name = work_to_do['agent_id'].lower()
                    if work_name == "generate_response":
                        state.response_requests.append(work_to_do.get('content', "N/A"))
                        continue

                    job_content = work_to_do['content']
                    required_context = work_to_do['related_context']
                    work_components = self._work_mapper[work_name]

                    work_agent_id = work_components["agent_id"]
                    job_cls = work_components["job"]

                    job = job_cls(
                        job_id=str(uuid.uuid4()),
                        report_to=self.agent_id,
                        worker_id=work_agent_id,
                        status=JobStatus.ASSIGNED_TO_AGENT,
                        turn_index=state.turn_index,
                        content=job_content,
                        required_context=required_context
                    )

                    state.add_job(job)
                    assigned_jobs.append(job)
                    next_agents.append(work_agent_id)
                except KeyError:
                    continue

        # Any workflow must end with response generation
        next_agents.append(aid.OUTPUT_HANDLER)

        checklist.set_done(self._launch_workflow_step)
        self.update_context(state, context, checklist=checklist.todict())
        return state, next_agents

    def respond_to_user(self, state: SessionState) -> SessionState:
        # send system response to user
        system_response = state.next_response
        error_response = compose_message(
            msg_type=MessageType.CHAT,
            content="opps, something went wrong. Please try again later."
        )
        system_response = error_response if system_response is None else system_response
        self.send_message(state, aid.user, system_response)

        # reset state for next user input
        state.chat_full_history.extend([state.last_user_message, system_response])
        state.next_response = None
        state.last_user_message = None

        # nothing to do, wait for user input
        state.set_status(SessionStatus.WAIT_HUMAN)
        return state

    def next_agents(self, state: SessionState) -> Tuple[SessionState, Union[List, None]]:
        """Register a new managed agent."""

        # add user message to state
        context = self.get_context(state)
        checklist = Checklist.fromdict(context["checklist"])

        if self.is_first_entry(state, context):
            return self.generate_hello_message(state, context)
        elif not checklist.is_done(self._plan_workflow_step):
            return self.plan_workflow(state, context)
        elif not checklist.is_done(self._launch_workflow_step):
            return self.launch_workflow(state, context)
        elif not checklist.is_done(self._update_history_step):
            # update chat history and respond to user
            checklist.set_done(self._update_history_step)
            self.update_context(state, context, checklist=checklist.todict())
            return state, [aid.HISTORY_MANAGER]

        return self.respond_to_user(state), None

