from llm_orchestrator.agents.llm_op_agent import LlmOpAgent
from llm_orchestrator.tasks.assignment import Assignment
from llm_orchestrator.tasks.builder import build_task
from llm_orchestrator.msg.messanger import load_ptxt
from tenacity import wait_fixed, stop_after_attempt, retry
from llm_orchestrator.agents.agent import Agent
from pathlib import Path
import json


ASSIGNMENT_JSON = Path(__file__).parent / "data_collection_config_template.json"
PROMPT_PTXT = Path(__file__).parent / "data_collection_prompt_template.ptxt"


def chat_agent(name, llm, assignment_config) -> Agent:
    data_collection_json = json.load(open(ASSIGNMENT_JSON.as_posix(), 'r'))
    assignment_config_json = json.load(open(assignment_config, 'r'))
    for item in data_collection_json:
        if item.get('class_definitions', "NA") == '__FIELDS__':
            item['class_definitions'] = {d['name']: f"field {d['name']} is being referenced in assignment response" for d in assignment_config_json}
    task = build_task(assignment_config_json + data_collection_json)
    prompt = load_ptxt(PROMPT_PTXT.as_posix())

    assignment = Assignment(name=name,
                            description="",
                            task=task)

    agent = LlmOpAgent(name="mece_agent",
                       llm=llm,
                       llm_args={"api_key": "~/.ssh/gpt_orchestrator_key.pk", "max_tokens": 10000, "temperature": 0.1},
                       assignments=[assignment],
                       prompt=prompt)
    return agent


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def chat_with_data_collection_agent(
        data_collection_ptxt,
        data_collection_config,
        data_collection_state,
        conversation_history,
        latest_assistant_response,
        user_message,
        response_structure_guidelines="",
        conversation_behavior_guidelines="",
        llm="gpt-4o",
        llm_first_call=None
    ):

    # raed guidelines
    data_to_collect_guidelines = data_collection_ptxt.read_text()
    field_to_extract = json.load(open(data_collection_config.as_posix(), 'r'))
    field_to_extract_str = json.dumps(field_to_extract)

    # set llm model
    llm_first_call = llm if llm_first_call is None else llm_first_call
    llm = llm_first_call if user_message == "__INIT__" else llm

    # call agent
    name = "chat"
    referenced_fields_picklist = [f['name'] for f in field_to_extract]
    agent = chat_agent(name=name, llm=llm, assignment_config=data_collection_config.as_posix())
    out = agent.execute(
        field_to_extract=field_to_extract_str,
        data_to_collect_guidelines=data_to_collect_guidelines,
        data_collection_state=data_collection_state,
        conversation_history=conversation_history,
        latest_assistant_response=latest_assistant_response,
        user_message=user_message,
        response_structure_guidelines=response_structure_guidelines,
        conversation_behavior_guidelines=conversation_behavior_guidelines,
        referenced_fields_picklist=referenced_fields_picklist
    )

    # extract outputs
    user_approved = out[f'{name}.user_approved']
    assistant_response = out[f'{name}.assistant_response']
    referenced_fields = out.get(f"{name}.referenced_fields", [])
    data_collection_state = {
        f['name']: out.get(f"{name}.{f['name']}", None) for f in field_to_extract
    }
    return user_approved, assistant_response, data_collection_state, referenced_fields
