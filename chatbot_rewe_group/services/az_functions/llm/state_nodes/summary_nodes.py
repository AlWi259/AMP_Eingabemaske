import copy
from langchain_core.messages import HumanMessage
from utils.file_loader import load_prompt, load_topics
from utils.llm_utils import store_token_usage
from adapters.az_blob_client import append_data_to_blob
from adapters.az_table_client import update_state

from models.pydantic import PydanticModels as pydantic_models

from typing import Any, Dict

def generate_interview_yggs(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Generates Yggdrasil summaries from the chat history using the LLM.
    Args:
        chat_history: The chat history as a list of messages.
        llm: The language model instance to use.
    Returns:
        Dict with function and general Yggs.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to generate_interview_yggs")

    chat_history = copy.deepcopy(state["chat_history"])
    ygg_prompt = load_prompt(directory="yggs", name="generate_interview_ygg").format(
        topic=state["current_topic_name"]
    )
    prompt_message = HumanMessage(content=ygg_prompt)
    chat_history.append(prompt_message)
    response = llm.invoke(chat_history)

    ygg = {
        "topic_id": state["current_topic"],
        "topic_name": state["current_topic_name"],
        "ygg": response.content  # Store the raw response content
    }

    append_data_to_blob('temporary-data', ygg, state["interview_id"], state["user_id"], state["chat_history_id"])

    return {
        "topic_summary": response.content
    }

def summarize_chat_history(state: Dict[str, Any], llm=None) -> Dict[str, Any]:
    """
    Summarizes the entire chat history and stores results.
    Args:
        state: The current interview state dictionary.
        llm: The language model instance to use.
    Returns:
        The updated interview state dictionary.
    """
    if llm is None:
        raise ValueError("llm instance must be provided to summarize_chat_history")
    chat_history = copy.deepcopy(state["chat_history"])
    summary_prompt = load_prompt(directory="report", name="summary").format(
        topics=load_topics(name="copilot"),
        summary=state["user_information"],
        current_topic=state["current_topic_name"]
    )
    message = HumanMessage(content=summary_prompt)
    chat_history.append(message)
    response = llm.invoke(chat_history)
    # state["llm_metadata"] = store_token_usage(response, state["llm_metadata"])

    update_state(state=state)

    state["user_information"] = response.content
    return state
