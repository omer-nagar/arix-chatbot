import json
from pathlib import Path

from arix_chatbot.jobs.job import Job
from arix_chatbot.llm_query.chat_contextual_query.query import ChatContextualQuery
from arix_chatbot.state_manager.state_store import SessionState


def edit_section_query(state: SessionState, prompt_path: str, config_path: str, edit_job: Job) -> dict | None:
    job_content = edit_job.content
    if not job_content:
        return None

    required_context = edit_job.required_context if edit_job.required_context else []
    chat = ChatContextualQuery(
        name="user_intent",
        prompt=Path(prompt_path).read_text(),
        config=json.loads(Path(config_path).read_text()),
        task_goal="task_goal" in required_context,
        input_data_description="input_data_description" in required_context,
        task_detailed_instructions="task_detailed_instructions" in required_context,
        task_global_guidelines="task_global_guidelines" in required_context,
        task_author_notes="task_author_notes" in required_context,
        input_data_schema="input_data_schema" in required_context,
        output_data_schema="output_data_schema" in required_context,
        llm='deepseek-chat',
    )
    response = chat.query(state, user_intent=job_content)
    return response
