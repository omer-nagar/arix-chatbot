from arix_chatbot.agents.actions.main_action_orchestrator.agent import MainActionHandler
from arix_chatbot.agents.actions.state_editors.llm_task_initializer.agent import LlmTaskInitializer
from arix_chatbot.agents.io_agents.history_manager.agent import HistoryManager
from arix_chatbot.agents.io_agents.output_handler.agent import OutputHandler
from arix_chatbot.agents.io_agents.user_intent_router.agent import UserIntentRouter
from arix_chatbot.agents.main_chat_orchestrator.main_agent import MainChatOrchestrator
from arix_chatbot.agents.agent_ids import AgentID


AGENTS = [
    MainChatOrchestrator(managed_agents=[
        AgentID.MAIN_ACTION_HANDLER,
        AgentID.OUTPUT_HANDLER,
        AgentID.HISTORY_MANAGER
    ]),
    MainActionHandler(managed_agents=[
        AgentID.USER_INTENT_ROUTER,
        AgentID.LLM_TASK_INITIALIZER
    ]),
    OutputHandler(),
    UserIntentRouter(),
    LlmTaskInitializer(),
    HistoryManager()
]
