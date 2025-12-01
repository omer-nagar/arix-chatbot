from arix_chat.state_manager.state_store import SessionState, SessionStatus
from arix_chat.agents.base.navigator import Navigator
from typing import List, Dict, Tuple, Union

TASK_DEF_TEMPLATE = """
### General Task Definition
{task_definition}

### General Data type
{data_type}

### Classes
{classes}
"""


DEFINITION_COMPLETE = """
**Your model configuration is complete.**

We’ve captured your requirements and will now begin building your model.
When it’s ready, the model status will update to **Ready** in the dashboard.

You will then be able to:

* Access it programmatically via the API
* Test it directly in the UI

We’ll notify you once the model is available.
"""

class MainNavigator(Navigator):
    """Navigator agent that manages the workflow of other agents."""

    def __init__(self, agent_id: str = "main_navigator", managed_agents: List[str] = None):
        super().__init__(agent_id, managed_agents=managed_agents)
        self._pipeline = ["intentRouter", "taskPlanner", "toolSelector", "executor"]

    def _is_intent_router_done(self, state: SessionState) -> bool:
        """Check if the intent router has completed its task."""
        return state.agents_context.get('intentRouter', {}).get('worker_done', False)

    def is_deep_dive_data_done(self, state: SessionState) -> bool:
        """Check if the deep dive data agent has completed its task."""
        return state.agents_context.get('deepDiveData', {}).get('worker_done', False)

    def is_deep_dive_task_config_done(self, state: SessionState) -> bool:
        """Check if the deep dive task config agent has completed its task."""
        return state.agents_context.get('deepDiveTaskConfig', {}).get('worker_done', False)

    def deep_dive_data_init_message(self, state) -> Dict:
        intent_context = state.agents_context.get('intentRouter', {})
        task_definition = intent_context.get('task_definition', 'not provided')
        data_type = intent_context.get('data_type', 'not provided')
        classes = '\n'.join([f"{item.get('name', 'N/A')}: {item.get('definition', 'N/A')}"
                             for item in eval(intent_context.get('classes', 'not provided'))])

        task_def = TASK_DEF_TEMPLATE.format(
            task_definition=task_definition,
            data_type=data_type,
            classes=classes
        )
        return {
            "task_definition": task_def,
            'conversation_history': intent_context.get('conversation_history', 'no-history')
        }

    def get_transfer_last_user_massage(self, state: SessionState, from_agent: str, to_agent: str):
        user_message = state.agents_inbox.get(from_agent, {}).get('user', [{'type': 'chat', 'msg': "great, whats next?"}])
        target_mailbox = state.agents_inbox.get(to_agent, {})
        target_mailbox['user'] = user_message
        state.agents_inbox[to_agent] = target_mailbox

    def deep_dive_task_def_init_message(self, state) -> Dict:

        # TODO handle None - send back to intent router?

        init_message = self.deep_dive_data_init_message(state)
        deep_dive_context = state.agents_context.get('deepDiveData', {})
        data_domain = deep_dive_context.get('domain', 'not provided')
        text_type = deep_dive_context.get('text_type', 'not provided')
        init_message.update({
            "domain": data_domain,
            "text_type": text_type,
            "conversation_history": deep_dive_context.get('conversation_history', 'no-history'),
        })
        return init_message

    def next_agents(self, state: SessionState) -> Tuple[SessionState, Union[str, None]]:
        """Register a new managed agent."""
        next_agent = None
        if not self._is_intent_router_done(state):
            # Intent router is done, move to the next agent in the pipeline
            next_agent = 'intentRouter'
        elif not self.is_deep_dive_data_done(state):
            # Deep dive into data
            self.send_message(state, 'deepDiveData', self.deep_dive_data_init_message(state))
            self.get_transfer_last_user_massage(state, 'intentRouter', 'deepDiveData')
            next_agent = 'deepDiveData'
        elif not self.is_deep_dive_task_config_done(state):
            # Deep dive task config is done, complete the session
            self.send_message(state, 'deepDiveTaskConfig', self.deep_dive_task_def_init_message(state))
            self.get_transfer_last_user_massage(state, 'deepDiveData', 'deepDiveTaskConfig')
            next_agent = 'deepDiveTaskConfig'
        else:
            state.status = SessionStatus.COMPLETED.value
            self.send_message(state, "user", {"type": "notification", "msg": DEFINITION_COMPLETE})
        return state, next_agent


