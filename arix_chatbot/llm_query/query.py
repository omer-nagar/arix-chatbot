from llm_orchestrator.agents.llm_op_agent import LlmOpAgent
from llm_orchestrator.tasks.assignment import Assignment
from llm_orchestrator.tasks.builder import build_task, task_from_json
from llm_orchestrator.msg.messanger import load_ptxt


class LLMQuery:
    def __init__(self,
                 name,
                 prompt: str,
                 config: str,
                 llm="gpt-5-nano",
                 max_tokens=2048,
                 temperature=0.7,
    ):
        # Basic setup
        self._name = name
        self._llm = llm

        # LLM agent setup arguments
        self._prompt = load_ptxt(prompt)
        self._response_config = task_from_json(config)

        self._max_tokens = max_tokens
        self._temperature = temperature
        self._llm_agent = self.get_llm_agent()

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

    def query(self, **kwargs):
        return self._llm_agent.execute(**kwargs)
