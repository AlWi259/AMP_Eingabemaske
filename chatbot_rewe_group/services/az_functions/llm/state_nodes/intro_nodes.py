from utils.file_loader import load_prompt
from utils.llm_utils import store_token_usage
from adapters.az_table_client import store_message, update_state
from adapters.az_blob_client import append_message_to_blob
from typing import Any, Dict

def interview_intro(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Handles the interview introduction phase, including follow-ups and evaluation.
    Args:
        state: The current interview state dictionary.
        llm: The language model instance to use.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to interview_intro")
    state["open_topics"].remove(state["current_topic"])
    start_prompt = load_prompt(directory="interview", name="start_interview").format(
        intro_points=state["current_topic_points"]
    )
    response = llm.invoke(start_prompt)
    state["ai_message"] = response.content
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    state["interview_status"] = 1 # Set interview status to 1 to indicate interview has started
    
    store_message(chat_history_id=state["chat_history_id"], role="assistant", message=response.content, message_tag=state["current_topic"])
    append_message_to_blob(message=response.content, interview_id=state["interview_id"], chat_id=state["chat_history_id"], role="assistant")
    update_state(state=state)
    return state
