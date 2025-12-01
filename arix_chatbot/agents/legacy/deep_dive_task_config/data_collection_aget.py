from arix_chat.agents.legacy.helpers.data_collection_session.data_collection_agent import chat_with_data_collection_agent
from arix_chat.app.ai_factory_pipeline import print_wrapped
from pathlib import Path
import json


DATA_TO_COLLECT_CONFIG = Path(__file__).parent / "task_config_collection_definition.json"
DATA_TO_COLLECT_GUIDELINES = Path(__file__).parent / "task_config_collection_guidelines.ptxt"


CONVERSATION_BEHAVIOR_GUIDELINES = """
* **Assume the user always sees the referenced fields before the assistant response, formatted as:**
  `{referenced_fields}`
  `---`
  `{assistant_response}`
* in assistant_response refer the updated fields that are displayed above the message naturally"
"""


def generate_task_config(data_collection_state,
                         conversation_history,
                         latest_assistant_response,
                         user_message, init=False):

    user_message = user_message if not init else "__INIT__"

    user_approved, assistant_response, data_collection_state, referenced_fields = (
        chat_with_data_collection_agent(
            data_collection_ptxt=DATA_TO_COLLECT_GUIDELINES,
            data_collection_config=DATA_TO_COLLECT_CONFIG,
            data_collection_state=data_collection_state,
            conversation_history=conversation_history,
            latest_assistant_response=latest_assistant_response,
            user_message=user_message,
            response_structure_guidelines="",
            conversation_behavior_guidelines=CONVERSATION_BEHAVIOR_GUIDELINES,
            llm="gpt-4o",
            llm_first_call="gpt-5"
        ))
    return user_approved, assistant_response, data_collection_state, referenced_fields


def render(text):
    # try json
    try:
        if isinstance(text, str):
            obj = json.loads(text)
        else:
            obj = text
        return f"\n{json.dumps(obj, indent=2)}"
    except:
        return text


if __name__ == '__main__':
    history_ = 'User wants to refine this definition: \n### General Task Definition\nEmail topic classification\n\n### General Data type\nemails\n\n### Classes\nspam: Emails classified as unsolicited or irrelevant messages.\nwork: Emails related to professional or business activities.\nprivate: Emails meant for personal or non-professional communication.\nsales: Emails focused on selling products or services.\nbillings: Emails related to invoices or payment information.\n'
    user_approved_ = "not-approved"
    assistant_message_last_ = "none"
    user_response_ = "__INIT__"
    data_collection_state_ = "__INIT__"

    while user_approved_ != "approved":
        user_approved_, assistant_message_last_, data_collection_state_, referenced_fields_ = generate_task_config(
            data_collection_state=data_collection_state_,
            conversation_history=history_,
            latest_assistant_response=assistant_message_last_,
            user_message=user_response_
        )

        if assistant_message_last_ is not None:
            print("===================      CURRENT       ===================")
            try:
                to_disp = {field: data_collection_state_[field] for field in referenced_fields_}
                print_wrapped(json.dumps(to_disp, indent=2))
            except:
                print_wrapped(str(data_collection_state_))

            print("=================== Assistant Question ===================")
            print_wrapped(assistant_message_last_)
            print("==========================================================")
        user_response = input(f"User: ")
    pass



