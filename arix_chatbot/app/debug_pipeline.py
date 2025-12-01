from arix_chatbot.app.ai_factory_pipeline import print_wrapped, AiFactoryPipeline
from arix_chatbot.state_manager.state_store import SessionStatus
from arix_chatbot.app.agent_registry import AgentRegistry
from arix_chatbot.agents.agents_pool import AGENTS
from typing import Union
import asyncio
import pickle


def load_checkpoint(checkpoint: str = Union[None, str], pipeline: AiFactoryPipeline = None) -> Union[None, str]:
    if checkpoint is None:
        return None

    checkpoint_state = pickle.load(open(checkpoint, "rb"))
    checkpoint_state.status = SessionStatus.HANDOFF.value
    pipeline.state_store.store_state(checkpoint_state.run_id, checkpoint_state)
    return checkpoint_state.run_id


def save_checkpoint(state, path: str = None):
    pickle.dump(state, open(path, "wb"))


def run_human_feedback_loop(state, pipeline: AiFactoryPipeline):
    run_id = state.run_id
    while state.status == SessionStatus.WAIT_HUMAN:
        print("============== AI ====================")
        for msg in state.user_outbox:
            print_wrapped(f"{msg['msg']}")
        print("======================================")

        user_input = input(">>")
        asyncio.run(pipeline.inject_human_input(run_id, user_input))
        state = asyncio.run(pipeline.get_run_state(run_id))
    return state


def print_summary(state):
    print_wrapped("============== FINAL OUTPUT ====================")
    print_wrapped(state.agents_context["intentRouter"]["task_definition"])
    print_wrapped(state.agents_context["intentRouter"]["data_type"])
    print_wrapped("Classes:")
    for cls in eval(state.agents_context["intentRouter"]["classes"]):
        print_wrapped(f"{cls['name']}: {cls['definition']}")


def main(checkpoint_to_load: str = None, checkpoint_save_path: str = None):
    agents_store_ = AgentRegistry(agents=AGENTS)
    pipeline = AiFactoryPipeline(agents_store=agents_store_, initial_agent=AGENTS[0].agent_id)

    run_id = load_checkpoint(checkpoint=checkpoint_to_load, pipeline=pipeline)
    state = asyncio.run(pipeline.start_run(run_id=run_id))
    state = run_human_feedback_loop(state, pipeline)

    if checkpoint_save_path is not None:
        save_checkpoint(state, path=checkpoint_save_path)

    if state.status == SessionStatus.ERROR:
        print_wrapped("============== ERROR ====================")
        print_wrapped(state.error)
        exit(1)


if __name__ == '__main__':
    # LOAD_CHECKPOINT = "/Users/omernagar/Documents/Data/small_world/checkpoints/state_checkpoint.pkl"
    LOAD_CHECKPOINT = None
    SAVE_CHECKPOINT = "/Users/omernagar/Documents/Data/small_world/checkpoints/deep_dive_task_state_checkpoint.pkl"
    # SAVE_CHECKPOINT = None
    main(checkpoint_to_load=LOAD_CHECKPOINT, checkpoint_save_path=SAVE_CHECKPOINT)
