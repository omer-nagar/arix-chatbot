from arix_chatbot.agents.actions.main_action_orchestrator.agent import MainActionHandler
from arix_chatbot.agents.io_agents.user_intent_router.agent import UserIntentRouter
from arix_chatbot.agents.main_chat_orchestrator.main_agent import MainChatOrchestrator
from arix_chatbot.agents.agent_ids import AgentID


main = MainChatOrchestrator(managed_agents=[
    AgentID.MAIN_ACTION_HANDLER,
    AgentID.OUTPUT_HANDLER,
    AgentID.HISTORY_MANAGER
])
main_action_handler = MainActionHandler(managed_agents=[AgentID.USER_INTENT_ROUTER])
user_intent_router = UserIntentRouter()

AGENTS = [main, main_action_handler, user_intent_router]
