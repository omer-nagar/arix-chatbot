from llm_orchestrator.agents.llm_op_agent import LlmOpAgent
from tenacity import retry, wait_fixed, stop_after_attempt
from llm_orchestrator.tasks.builder import task_from_json
from llm_orchestrator.tasks.assignment import Assignment
from llm_orchestrator.msg.messanger import load_ptxt
from arix_chat.agents.legacy.intent_router.constants import GREETINGS
from llm_orchestrator.agents.agent import Agent
from pathlib import Path


ASSIGNMENT_JSON = Path(__file__).parent / "deep_dive_data_task_definition.json"
PROMPT_PTXT = Path(__file__).parent / "deep_dive_data_task_prompt.ptxt"


def chat_agent() -> Agent:
    task = task_from_json(ASSIGNMENT_JSON.as_posix())
    prompt = load_ptxt(PROMPT_PTXT.as_posix())

    assignment = Assignment(name="chat_response", name_prefix="generate_next_",
                            description="intelligent intermediary between the user and the model-building process",
                            task=task)

    agent = LlmOpAgent(name="intelligent_ml_assistant",
                       llm="gpt-4o",
                       llm_args={"api_key": "~/.ssh/gpt_orchestrator_key.pk"},
                       assignments=[assignment],
                       prompt=prompt)
    return agent


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def chat_deep_dive_data(task_definition, domain, text_type, user_wants_to_provide_its_own_data,
                        conversation_history, latest_assistant_question, latest_user_response):
    agent = chat_agent()
    out = agent.execute(
        task_definition=task_definition,
        domain=domain,
        text_type=text_type,
        user_wants_to_provide_its_own_data=user_wants_to_provide_its_own_data,
        conversation_history=conversation_history,
        latest_assistant_question=latest_assistant_question,
        latest_user_response=latest_user_response
    )

    response = out['chat_response.assistant_response']
    domain = out.get('chat_response.domain', domain)
    text_type = out.get('chat_response.text_type', text_type)
    user_wants_to_provide_its_own_data = str(out.get('chat_response.user_wants_to_provide_its_own_data', user_wants_to_provide_its_own_data))

    conversation_history = out.get('chat_response.history', conversation_history)
    user_approved = out.get('chat_response.user_approved', False)
    return response, domain, text_type, user_wants_to_provide_its_own_data, conversation_history, user_approved


if __name__ == '__main__':
    latest_assistant_question = GREETINGS
    conversation_history = "no-history"
    task_definition = "not provided"
    domain = "not provided"
    text_type = "not provided"
    user_wants_to_provide_its_own_data = "not provided"
    user_approved = ""

    while user_approved != "approved":
        print(latest_assistant_question)
        user_response = input(f"User: ")
        response, data_type, task_definition, classes, conversation_history, user_approved = chat_deep_dive_data(
            task_definition=task_definition,
            domain=domain,
            text_type=text_type,
            user_wants_to_provide_its_own_data=user_wants_to_provide_its_own_data,
            conversation_history=conversation_history,
            latest_assistant_question=latest_assistant_question,
            latest_user_response=user_response
        )

        latest_assistant_question = response

    pass



