from llm_orchestrator.agents.llm_op_agent import LlmOpAgent
from tenacity import retry, wait_fixed, stop_after_attempt
from llm_orchestrator.tasks.builder import task_from_json
from llm_orchestrator.tasks.assignment import Assignment
from llm_orchestrator.msg.messanger import load_ptxt
from llm_orchestrator.agents.agent import Agent
from pathlib import Path


ASSIGNMENT_JSON = Path(__file__).parent / "intent_router_task_definition.json"
PROMPT_JSON = Path(__file__).parent / "intent_router_task_prompt.ptxt"


def chat_agent() -> Agent:
    task = task_from_json(ASSIGNMENT_JSON.as_posix())
    prompt = load_ptxt(PROMPT_JSON.as_posix())

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
def chat_inquire_general_classification_task_definition(task_definition, data_type, classes, conversation_history, latest_assistant_question, latest_user_response):
    agent = chat_agent()
    out = agent.execute(
        task_definition=task_definition,
        data_type=data_type,
        classes=classes,
        conversation_history=conversation_history,
        latest_assistant_question=latest_assistant_question,
        latest_user_response=latest_user_response
    )

    response = out['chat_response.assistant_response']
    data_type = out.get('chat_response.data_type', data_type)
    task_definition = out.get('chat_response.task_definition', task_definition)
    classes = str(out.get('chat_response.classes', classes))

    conversation_history = out.get('chat_response.history', conversation_history)
    user_approved = out.get('chat_response.user_approved', False)
    return response, data_type, task_definition, classes, conversation_history, user_approved


# if __name__ == '__main__':
#     latest_assistant_question = GREETINGS
#     conversation_history = "no-history"
#     task_definition = "not provided"
#     data_type = "not provided"
#     classes = "not provided"
#     user_approved = ""
#
#     while user_approved != "approved":
#         print(latest_assistant_question)
#         user_response = input(f"User: ")
#         response, data_type, task_definition, classes, conversation_history, user_approved = chat_inquire_general_classification_task_definition(
#             task_definition=task_definition,
#             data_type=data_type,
#             classes=classes,
#             latest_assistant_question=latest_assistant_question,
#             conversation_history=conversation_history,
#             latest_user_response=user_response
#         )
#
#         latest_assistant_question = response
#
#     pass



