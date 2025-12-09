from arix_chatbot.agents.actions.main_action_orchestrator.agent import MainActionHandler
from arix_chatbot.agents.actions.state_editors.input_data_editor.agent import InputDataEditor
from arix_chatbot.agents.actions.state_editors.input_schema_editor.agent import InputSchemaEditor
from arix_chatbot.agents.actions.state_editors.llm_task_initializer.agent import LlmTaskInitializer
from arix_chatbot.agents.actions.state_editors.output_schema_editor.agent import OutputSchemaEditor
from arix_chatbot.agents.actions.state_editors.task_authors_note_editor.agent import TaskAuthorNotesEditor
from arix_chatbot.agents.actions.state_editors.task_detailed_instruction_editor.agent import \
    TaskDetailedInstructionEditor
from arix_chatbot.agents.actions.state_editors.task_goal_editor.agent import TaskGoalEditor
from arix_chatbot.agents.actions.state_editors.tasl_global_guidlnes_editor.agent import TaskGlobalGuidelinesEditor
from arix_chatbot.agents.workflow.history_manager.agent import HistoryManager
from arix_chatbot.agents.workflow.output_handler.agent import OutputHandler
from arix_chatbot.agents.workflow.planner.agent import Planner
from arix_chatbot.agents.workflow.user_intent_router.agent import UserIntentRouter
from arix_chatbot.agents.main_chat_orchestrator.main_agent import MainChatOrchestrator
from arix_chatbot.agents.agent_ids import AgentID


AGENTS = [
    MainChatOrchestrator(managed_agents=[
        AgentID.MAIN_ACTION_HANDLER,
        AgentID.OUTPUT_HANDLER,
        AgentID.HISTORY_MANAGER,
        AgentID.PLANNER,
        AgentID.INPUT_DATA_EDITOR,
        AgentID.LLM_TASK_INITIALIZER,
        AgentID.TASK_GOAL_EDITOR,
        AgentID.TASK_GLOBAL_GUIDELINES_EDITOR,
        AgentID.TASK_DETAILED_INSTRUCTIONS_EDITOR,
        AgentID.TASK_AUTHOR_NOTES_EDITOR,
        AgentID.INPUT_SCHEMA_EDITOR,
        AgentID.OUTPUT_SCHEMA_EDITOR,
    ]),
    InputDataEditor(),
    OutputHandler(),
    Planner(),
    LlmTaskInitializer(),
    TaskGoalEditor(),
    TaskDetailedInstructionEditor(),
    TaskGlobalGuidelinesEditor(),
    TaskAuthorNotesEditor(),
    InputSchemaEditor(),
    OutputSchemaEditor(),
    HistoryManager()
]
