from llm_orchestrator.msg.messanger import extract_role_content_blocks, TemplatedMessage, TemplateSession
from llm_orchestrator.agents.llm_op_agent import LlmOpAgent
from llm_orchestrator.tasks.assignment import Assignment
from llm_orchestrator.tasks.builder import build_task
from arix_chatbot import env
from pathlib import Path


PROMPT_PTXT = Path(__file__).parent / "prompt_template.ptxt"


class ChatContextualQuery:
    def __init__(self,
                 name,
                 prompt,
                 config: dict,
                 llm="gpt-5-nano",
                 max_tokens=2048,
                 temperature=0.7,
                 conversation_history=True,
                 latest_assistant_response=True,
                 latest_user_message=True,
                 actions_stack=True,
                 task_goal=True,
                 input_data_description=False,
                 task_detailed_instructions=False,
                 task_global_guidelines=False,
                 task_author_notes=False,
                 input_data_schema=False,
                 output_data_schema=False
    ):
        # Basic setup
        self._name = name
        self._llm = llm

        # include context flags
        self._include_conversation_history = conversation_history
        self._include_latest_assistant_response = latest_assistant_response
        self._include_latest_user_message = latest_user_message
        self._include_actions_stack = actions_stack
        self._include_task_goal = task_goal
        self._include_input_data_description = input_data_description
        self._include_task_detailed_instructions = task_detailed_instructions
        self._include_task_global_guidelines = task_global_guidelines
        self._include_task_author_notes = task_author_notes
        self._include_input_data_schema = input_data_schema
        self._include_output_data_schema = output_data_schema

        # LLM agent setup arguments
        self._query_prompt = prompt
        self._base_prompt = PROMPT_PTXT.read_text()
        self._config = config
        self._response_config = build_task(config)

        self._max_tokens = max_tokens
        self._temperature = temperature
        self._prompt = self._build_prompt()
        self._llm_agent = self.get_llm_agent()

    def build_state_msg(self):
        content = ""
        if self._include_task_goal:
            content += "## Task Goal\n{{__task_goal__}}\n\n"
        if self._include_input_data_description:
            content += "## Input Data Description\n{{__input_data_description__}}\n\n"
        if self._include_task_detailed_instructions:
            content += "## Task Detailed Instructions\n{{__task_detailed_instructions__}}\n\n"
        if self._include_task_global_guidelines:
            content += "## Task Global Guidelines\n{{__task_global_guidelines__}}\n\n"
        if self._include_task_author_notes:
            content += "## Task Author Notes\n{{__task_author_notes__}}\n\n"
        if self._include_input_data_schema:
            content += "## Input Data Schema\n{{__input_data_schema__}}\n\n"
        if self._include_output_data_schema:
            content += "## Output Data Schema\n{{__output_data_schema__}}\n\n"

        if content == "":
            return None

        return {"role": "system", "template": content}

    def _build_prompt(self):
        base_prompt = extract_role_content_blocks(self._base_prompt)
        (conversation_history_msg, latest_assistant_response_msg, latest_user_message_msg,
         actions_stack_msg, final_base_msg) = base_prompt
        state_msg = self.build_state_msg()
        prompt = []
        if self._include_conversation_history:
            prompt.append(conversation_history_msg)
        if self._include_latest_assistant_response:
            prompt.append(latest_assistant_response_msg)
        if self._include_latest_user_message:
            prompt.append(latest_user_message_msg)
        if self._include_actions_stack:
            prompt.append(actions_stack_msg)
        if state_msg is not None:
            prompt.append(state_msg)
        prompt.extend(extract_role_content_blocks(self._query_prompt))
        prompt = TemplateSession([TemplatedMessage(**msg) for msg in prompt])
        return prompt

    def get_llm_agent(self):
        assignment = Assignment(name=self._name,
                                description="",
                                task=self._response_config)

        agent = LlmOpAgent(name=self._name,
                           llm=self._llm,
                           llm_args={
                               "max_tokens": self._max_tokens,
                               "temperature": self._temperature
                           },
                           assignments=[assignment],
                           prompt=self._prompt, assignment_prefix=False)
        return agent

    def query(self, state, **kwargs):
        kwargs.update({
            "__conversation_history__": state.chat_summary if state.chat_summary is not None else "N/A",
            "__latest_assistant_response__": state.next_response if state.next_response is not None else "N/A",
            "__latest_user_message__": state.last_user_message['msg'] if state.last_user_message is not None else "N/A",
            "__actions_stack__": str(state.chat_action_stack) if len(state.chat_action_stack) > 0 else "N/A",
            "__task_goal__": str(state.task_goal) if len(state.task_goal) > 0 else "N/A",
            "__input_data_description__": state.input_data_description if state.input_data_description is not None else "N/A",
            "__task_detailed_instructions__": str(state.task_detailed_instructions) if len(state.task_detailed_instructions) > 0 else "N/A",
            "__task_global_guidelines__": str(state.task_global_guidelines) if len(state.task_global_guidelines) > 0 else "N/A",
            "__task_author_notes__": str(state.task_author_notes) if state.task_author_notes is not None else "N/A",
            "__input_data_schema__": str(state.input_data_schema) if len(state.input_data_schema) > 0 else "N/A",
            "__output_data_schema__": str(state.output_data_schema) if len(state.output_data_schema) > 0 else "N/A"
        })
        kwargs = {k: v for k, v in kwargs.items() if k in self._prompt.placeholders}
        response = self._llm_agent.execute(**kwargs)
        return response
