import copy
from langchain_core.messages import HumanMessage
from utils.file_loader import load_prompt
from utils.llm_utils import store_token_usage
from adapters.az_table_client import store_message, update_state
from adapters.az_blob_client import append_message_to_blob

from typing import Any, Dict

def formulate_question(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Formulates a follow-up question using the LLM.
    Args:
        state: The current interview state dictionary.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("LLM instance must be provided to formulate_question.")
    chat_history = copy.deepcopy(state["chat_history"])
    question_prompt = load_prompt(directory="interview", name="moderator").format(
        instruction=state["next_step_suggestion"]
    )
    message = HumanMessage(content=question_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    state["ai_message"] = response.content
    return state

def polish_question(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Polishes the generated question for clarity and style.
    Args:
        state: The current interview state dictionary.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("LLM instance must be provided to polish_question.")
    chat_history = copy.deepcopy(state["chat_history"])
    polisher_prompt = load_prompt(directory="interview", name="question_polisher").format(ai_message=state["ai_message"])
    message = HumanMessage(content=polisher_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])
    state["ai_message"] = response.content
    state["probing_count"] -= 1  # Decrease probing count after polishing the question
    store_message(chat_history_id=state["chat_history_id"], role="assistant", message=response.content, message_tag=state["current_topic"])
    append_message_to_blob(message=response.content, interview_id=state["interview_id"], chat_id=state["chat_history_id"], role="assistant")
    update_state(state=state)
    return state
